"""Stage 2c: Technique Search — exhaustive evaluation of 12 techniques against raw material."""

import json
from pathlib import Path

from src.llm.deepseek import DeepSeekClient, V4_PRO
from src.models.domain import RawMaterialInventory, TechniqueSearchResult

TECHNIQUE_TAXONOMY_PATH = Path(__file__).parent.parent.parent.parent / "references" / "techniques.md"

_technique_taxonomy_cache: str | None = None


def load_technique_taxonomy() -> str:
    global _technique_taxonomy_cache
    if _technique_taxonomy_cache is None:
        path = TECHNIQUE_TAXONOMY_PATH
        if path.exists():
            _technique_taxonomy_cache = path.read_text(encoding="utf-8")
        else:
            _technique_taxonomy_cache = "Technique taxonomy not found — load from references/techniques.md"
    return _technique_taxonomy_cache


TECHNIQUE_SEARCH_SYSTEM = """You are evaluating each of the 12 design techniques against this brand's raw material. You are NOT designing a logo yet — you are doing exhaustive search to find which techniques have genuine potential.

The conceptual move that produces iconic logos: find a visual affordance in the brand's name/meaning/story, then find the technique that unlocks it. FedEx = letterform negative space + arrow affordance in E/x gap. WWF = figure-ground silhouette + panda's distinctive markings. Amazon = letterform modification + A-to-Z semantic meaning. The technique amplifies the affordance — it is never applied in a vacuum.

For EACH technique:
- Read its definition and case study from the taxonomy.
- Study the brand's raw material (letter shapes, verb-to-form mappings, etymology hooks, semantic anchors).
- Ask: "Could this technique produce a mark whose meaning is unmistakably tied to THIS brand?"
- If yes: write a concrete, specific proposal in one sentence. Score 6-10.
- If no: say so honestly. Score 1-3. Don't fake applicability.

RULES:
1. "Applicable" means the technique would say something true and unique about THIS brand — not just "possible in general." Any technique is technically possible; the question is whether it produces something specific.
2. specific_proposal must reference letters by name or visual concepts by name. "A negative-space arrow between the E and x" is correct. "A clever negative-space element" is wrong and gets score 3.
3. Score distribution should NOT be uniform. Most brands have 2-4 strong techniques and 6-8 weak ones. Reflect that.
4. For each technique, note which gestalt principle(s) it engages: closure, figure-ground, continuity, proximity, similarity, symmetry.
5. For techniques scored 6+, apply the swap test: could another brand in the same category use this exact concept? If yes, it's not specific enough.
6. The best marks encode a fact no competitor could claim. For each technique, ask: "which specific fact about THIS brand would this technique encode?"
7. Do not write long rationales. Do not pick a winner. Just evaluate all 12 honestly.
8. After scoring all 12, check: are your top 4 scores all letterform-based techniques? If so, re-evaluate — you may be over-weighting the FedEx/Amazon pattern. Find at least one non-letterform technique that deserves a high score."""


async def run_technique_search(
    client: DeepSeekClient,
    raw_material: RawMaterialInventory,
    run_id: str = "",
) -> TechniqueSearchResult:
    taxonomy = load_technique_taxonomy()
    raw_material_json = raw_material.model_dump_json(indent=2)

    user_prompt = f"""Technique taxonomy:
<<<
{taxonomy}
>>>

Brand raw material:
<<<
{raw_material_json}
>>>

Output the JSON only."""

    return await client.structured_output(
        model=V4_PRO,
        system_prompt=TECHNIQUE_SEARCH_SYSTEM,
        user_prompt=user_prompt,
        response_model=TechniqueSearchResult,
        reasoning_effort="high",
        temperature=0.7,
        max_tokens=8192,
        run_id=run_id,
    )
