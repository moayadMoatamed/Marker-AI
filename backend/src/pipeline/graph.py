"""LangGraph workflow for the concept generation pipeline.

Stages are nodes in a directed graph:
  deconstruct → raw_material → technique_search → synthesize → critique

Each node reads from and writes to the shared PipelineState.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

import structlog
from langgraph.graph import END, StateGraph

from src.config import RUNS_DIR, SKIP_IMAGE_GEN
from src.llm.deepseek import DeepSeekClient
from src.pipeline.state import PipelineState
from src.pipeline.nodes.deconstruct import run_deconstruct
from src.pipeline.nodes.raw_material import run_raw_material
from src.pipeline.nodes.technique_search import run_technique_search
from src.pipeline.nodes.synthesize import run_synthesize
from src.pipeline.nodes.critique import run_critique
from src.rendering.image_gen import generate_logo_board

logger = structlog.get_logger(__name__)

# Banned adjective → approved replacement
_BANNED_REPLACEMENTS: dict[str, str] = {
    "modern": "geometric sans-serif construction",
    "clean": "single-weight strokes with no ornament",
    "professional": "executed with precision",
    "trustworthy": "structurally grounded",
    "innovative": "previously unseen combination",
    "dynamic": "asymmetric placement with rightward visual lean",
    "elegant": "extended ascenders with tapered terminal curves",
    "sleek": "low-contrast monoline with compressed spacing",
    "sophisticated": "high-contrast stroke modulation with calligraphic terminals",
    "bold": "heavy stroke weight with compact spacing",
    "fresh": "open aperture with generous x-height",
    "premium": "tight letter spacing with sharp serif terminals",
    "contemporary": "current geometric approach",
    "cutting-edge": "previously unseen approach",
    "versatile": "functional across applications",
    "timeless": "rooted in typographic tradition",
}


def _scrub_text(text: str) -> tuple[str, int]:
    """Replace banned adjectives. Returns (scrubbed_text, count)."""
    count = 0
    result = text
    for banned, replacement in _BANNED_REPLACEMENTS.items():
        pattern = re.compile(r"\b" + re.escape(banned) + r"\b", re.IGNORECASE)
        matches = len(pattern.findall(result))
        if matches > 0:
            count += matches
            result = pattern.sub(replacement, result)
    return result, count


def _scrub_concept(concept_dict: dict) -> int:
    """Scrub banned adjectives from all text fields in a concept. Returns count."""
    total = 0
    for field in ("one_line_idea", "the_trick", "construction_recipe", "rationale_paragraph"):
        if field in concept_dict and isinstance(concept_dict[field], str):
            concept_dict[field], n = _scrub_text(concept_dict[field])
            total += n
    for mm in concept_dict.get("meaning_mapping", []):
        for field in ("element", "represents", "because"):
            if field in mm and isinstance(mm[field], str):
                mm[field], n = _scrub_text(mm[field])
                total += n
    return total


async def _node_deconstruct(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    deconstruction = await run_deconstruct(client, state.transcript, run_id=state.run_id)
    _persist(state.run_id, "deconstruction.json", deconstruction.model_dump())
    return {"stage": "deconstructing", "deconstruction": deconstruction}


async def _node_raw_material(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    raw_material = await run_raw_material(client, state.deconstruction, run_id=state.run_id)
    _persist(state.run_id, "raw_material.json", raw_material.model_dump())
    return {"stage": "raw_material", "raw_material": raw_material}


async def _node_technique_search(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    technique_search = await run_technique_search(client, state.raw_material, run_id=state.run_id)
    _persist(state.run_id, "technique_search.json", technique_search.model_dump())
    return {"stage": "technique_search", "technique_search": technique_search}


async def _node_synthesize(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    brand_name = state.deconstruction.brand_name
    synthesis = await run_synthesize(
        client, state.raw_material, state.technique_search, brand_name, run_id=state.run_id
    )

    # Post-synthesis banned adjective scrub
    concepts_raw = synthesis.model_dump()
    total_scrubbed = 0
    for c in concepts_raw["concepts"]:
        n = _scrub_concept(c)
        if n > 0:
            total_scrubbed += n
            logger.info("banned_adjectives_scrubbed", concept_id=c.get("concept_id", "?"), replacements=n)
    if total_scrubbed > 0:
        logger.info("banned_adjectives_scrubbed_total", total=total_scrubbed)
    _persist(state.run_id, "synthesis.json", concepts_raw)

    # Re-parse scrubbed version
    synthesis = synthesis.__class__.model_validate(concepts_raw)

    # Build banned adjective report for critique
    banned_lines: list[str] = []
    for c in synthesis.concepts:
        banned = c.contains_banned_adjectives()
        if banned:
            banned_lines.append(
                f"  - {c.concept_id}: BANNED WORDS STILL PRESENT — {', '.join(sorted(banned))}"
            )
    banned_report = "\n".join(banned_lines)

    return {
        "stage": "synthesizing",
        "synthesis": synthesis,
        "concepts": concepts_raw["concepts"],
    }


async def _node_critique(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    brand_name = state.deconstruction.brand_name
    # Build banned adjective report from synthesis
    banned_lines: list[str] = []
    if state.synthesis:
        for c in state.synthesis.concepts:
            banned = c.contains_banned_adjectives()
            if banned:
                banned_lines.append(
                    f"  - {c.concept_id}: BANNED WORDS STILL PRESENT — {', '.join(sorted(banned))}"
                )
    banned_report = "\n".join(banned_lines)
    critique = await run_critique(
        client, state.synthesis,
        brand_name=brand_name, run_id=state.run_id,
        banned_adjective_report=banned_report,
    )
    _persist(state.run_id, "critique.json", critique.model_dump())
    return {
        "stage": "critiquing",
        "critique": critique,
        "scores": critique.model_dump()["concept_scores"],
    }


async def _node_render(state: PipelineState, client: DeepSeekClient) -> dict[str, Any]:
    """Generate presentation board images for each concept."""
    if SKIP_IMAGE_GEN or not state.synthesis:
        logger.info("render_skipped", run_id=state.run_id)
        return {"stage": "rendering", "images": state.images}

    brand_name = state.deconstruction.brand_name
    images: dict[str, str] = dict(state.images)
    output_dir = RUNS_DIR / state.run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    for concept in state.synthesis.concepts:
        cid = concept.concept_id
        logger.info("render_start", run_id=state.run_id, concept_id=cid)
        try:
            filename = f"{brand_name.lower().replace(' ', '_')}_{cid}_board.png"
            filepath = output_dir / filename
            ok = await generate_logo_board(
                brand_name=brand_name,
                one_line_idea=concept.one_line_idea,
                the_trick=concept.the_trick,
                construction_recipe=concept.construction_recipe,
                rationale_paragraph=concept.rationale_paragraph,
                meaning_mapping=[m.model_dump() for m in concept.meaning_mapping],
                output_path=filepath,
                run_id=state.run_id,
            )
            if ok:
                images[cid] = filename
                logger.info("render_done", run_id=state.run_id, concept_id=cid, filename=filename)
            else:
                logger.warning("render_failed", run_id=state.run_id, concept_id=cid)
        except Exception as exc:
            logger.error("render_error", run_id=state.run_id, concept_id=cid, error=str(exc))

    return {"stage": "rendering", "images": images}


def _persist(run_id: str, filename: str, data: dict) -> None:
    """Write intermediate output to runs directory."""
    output_dir = RUNS_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / filename).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_pipeline_graph() -> StateGraph:
    """Build and compile the LangGraph concept generation pipeline.

    Returns a compiled graph ready to be invoked with a PipelineState.
    """
    client = DeepSeekClient()
    graph = StateGraph(PipelineState)

    # Wrap each async node for LangGraph compatibility
    async def deconstruct(state: PipelineState) -> dict:
        return await _node_deconstruct(state, client)

    async def raw_material(state: PipelineState) -> dict:
        return await _node_raw_material(state, client)

    async def technique_search(state: PipelineState) -> dict:
        return await _node_technique_search(state, client)

    async def synthesize(state: PipelineState) -> dict:
        return await _node_synthesize(state, client)

    async def critique(state: PipelineState) -> dict:
        return await _node_critique(state, client)

    async def render(state: PipelineState) -> dict:
        return await _node_render(state, client)

    # Add nodes
    graph.add_node("deconstruct", deconstruct)
    graph.add_node("raw_material", raw_material)
    graph.add_node("technique_search", technique_search)
    graph.add_node("synthesize", synthesize)
    graph.add_node("critique", critique)
    graph.add_node("render", render)

    # Define edges (linear pipeline)
    graph.set_entry_point("deconstruct")
    graph.add_edge("deconstruct", "raw_material")
    graph.add_edge("raw_material", "technique_search")
    graph.add_edge("technique_search", "synthesize")
    graph.add_edge("synthesize", "critique")
    graph.add_edge("critique", "render")
    graph.add_edge("render", END)

    return graph.compile()
