"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent
_backend_dir = Path(__file__).parent.parent
_env_path = _backend_dir / ".env"
if not _env_path.exists():
    _env_path = PROJECT_ROOT / ".env"
load_dotenv(_env_path)

REFERENCES_DIR = PROJECT_ROOT / "references"
RUNS_DIR = Path(__file__).parent.parent / "runs"

DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")

SKIP_IMAGE_GEN: bool = os.getenv("SKIP_IMAGE_GEN", "").lower() in ("true", "1")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

MODEL_PRO = "deepseek-v4-pro"
MODEL_FLASH = "deepseek-v4-flash"

REASONING_HIGH = "high"
REASONING_MEDIUM = "medium"
