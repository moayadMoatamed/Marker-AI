"""FastAPI application — logo generation API.

Entry point for the Marker AI backend. Wires the LangGraph concept-generation
pipeline to HTTP endpoints and serves the frontend static build.

Run from the backend/ directory:
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import uuid
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router as api_router
from src.config import RUNS_DIR

app = FastAPI(title="Marker AI — Logo Generation", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

FRONTEND_BUILD = Path(__file__).parent.parent.parent / "frontend" / "out"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def index():
    """Serve the frontend SPA entry point if it exists, otherwise API-only."""
    index_html = FRONTEND_BUILD / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return {"service": "Marker AI", "version": "0.1.0", "docs": "/docs"}


# Serve pipeline run artifacts (images, SVGs, JSON)
app.mount("/runs", StaticFiles(directory=RUNS_DIR), name="runs")

# Mount frontend static export if it has been built
_next_dir = FRONTEND_BUILD / "_next"
if _next_dir.exists():
    app.mount("/_next", StaticFiles(directory=_next_dir), name="next_static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
