"""API routes for the logo generation pipeline."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import RUNS_DIR
from src.pipeline.graph import build_pipeline_graph
from src.pipeline.state import PipelineState

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api")

# ── In-memory store ──────────────────────────────────────────────────────────
runs: dict[str, PipelineState] = {}
_graph = build_pipeline_graph()


class GenerateRequest(BaseModel):
    brand_name: str = Field(
        description="The company or product name exactly as typed"
    )
    description: str = Field(
        description="Describe what the company does, who it serves, name origin, "
        "visual preferences, and any constraints. Minimum 20 characters.",
        min_length=20,
    )


class RunStatus(BaseModel):
    run_id: str
    stage: str
    concepts: list[dict[str, Any]] = []
    images: dict[str, str] = {}
    scores: list[dict[str, Any]] = []
    error: str | None = None


@router.post("/generate")
async def start_generation(req: GenerateRequest) -> dict[str, str]:
    """Kick off a pipeline run. Returns immediately with a run_id to poll."""
    run_id = uuid.uuid4().hex[:8]
    transcript = (
        f"Brand name: {req.brand_name}\n\n"
        f"Founder description: {req.description}"
    )

    state = PipelineState(run_id=run_id)
    state.transcript = transcript
    runs[run_id] = state

    asyncio.create_task(_execute_pipeline(run_id, state))
    logger.info("pipeline_started", run_id=run_id, brand_name=req.brand_name)
    return {"run_id": run_id}


@router.get("/run/{run_id}")
async def get_run_status(run_id: str) -> dict[str, Any]:
    """Poll for pipeline progress. Returns stage, concepts, scores, images, error."""
    state = runs.get(run_id)
    if not state:
        raise HTTPException(404, "Run not found")
    return {
        "run_id": state.run_id,
        "stage": state.stage,
        "concepts": state.concepts,
        "images": state.images,
        "scores": state.scores,
        "error": state.error,
    }


@router.get("/runs/{run_id}/{filename:path}")
async def serve_run_file(run_id: str, filename: str):
    """Serve a static file (PNG, SVG, JSON) from a pipeline run directory."""
    file_path = RUNS_DIR / run_id / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    ext = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
    }
    return FileResponse(file_path, media_type=media_types.get(ext, "application/octet-stream"))


async def _execute_pipeline(run_id: str, state: PipelineState) -> None:
    """Run the LangGraph pipeline with streaming — updates shared state after each node."""
    try:
        async for event in _graph.astream(state, stream_mode="values"):
            # event is the full PipelineState (dict) after each node completes.
            # Copy all fields back into the shared state so polls pick them up immediately.
            if isinstance(event, dict):
                for key, value in event.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
            logger.info("pipeline_progress", run_id=run_id, stage=state.stage)
        if state.stage != "error":
            state.stage = "complete"
        logger.info("pipeline_complete", run_id=run_id, concepts=len(state.concepts))
    except Exception as exc:
        import traceback

        traceback.print_exc()
        state.stage = "error"
        state.error = f"{type(exc).__name__}: {exc}"
        logger.error("pipeline_error", run_id=run_id, error=state.error)
