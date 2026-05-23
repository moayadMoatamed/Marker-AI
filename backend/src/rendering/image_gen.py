"""OpenAI image generation client — logo presentation boards via GPT Image / DALL-E."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "gpt_image_generation_prompt"

if _PROMPT_PATH.exists():
    _TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")
else:
    _TEMPLATE = """Create a premium minimalist logo presentation board for a brand called "{BRAND_NAME}".

LOGO CONCEPT:
{LOGO_CONCEPT_DESCRIPTION}

MEANING MAPPING:
{MEANING_MAPPING}

Style: clean Swiss design, flat vector, white background, centered composition, crisp geometry, subtle futuristic feel, landscape format, Behance-quality branding presentation. No shadows, no 3D, no photorealism, no mockups."""


def _build_prompt(brand_name: str, concept_description: str, meaning_mapping_text: str) -> str:
    prompt = _TEMPLATE.replace("{BRAND_NAME}", brand_name)
    prompt = prompt.replace("{LOGO_CONCEPT_DESCRIPTION}", concept_description)
    prompt = prompt.replace("{MEANING_MAPPING}", meaning_mapping_text)

    if len(prompt) > 3900:
        prompt = prompt[:3900]
    return prompt


async def generate_logo_board(
    *,
    brand_name: str,
    one_line_idea: str,
    the_trick: str,
    construction_recipe: str,
    rationale_paragraph: str,
    meaning_mapping: list[dict[str, str]],
    output_path: Path,
    run_id: str = "",
) -> bool:
    """Generate a logo presentation board and save it to output_path. Returns True on success."""

    concept_desc = (
        f"Concept: {one_line_idea}\n"
        f"The Trick: {the_trick}\n"
        f"Construction Recipe: {construction_recipe}\n"
        f"Rationale: {rationale_paragraph}"
    )
    meaning_text = "\n".join(
        f"- {m['element']} represents {m['represents']} because {m['because']}"
        for m in meaning_mapping
    )

    prompt = _build_prompt(brand_name, concept_desc, meaning_text)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    log = logger.bind(run_id=run_id, brand_name=brand_name)

    log.info("image_gen_start", model=IMAGE_MODEL)

    response = await client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1792x1024",
        n=1,
    )

    image_data = response.data[0]

    # GPT Image models return base64 JSON directly (no URL)
    if image_data.b64_json:
        decoded = base64.b64decode(image_data.b64_json)
        output_path.write_bytes(decoded)
        log.info("image_gen_done", path=str(output_path), size_bytes=len(decoded), source="b64_json")
        return True

    # DALL-E models return a download URL
    if image_data.url:
        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.get(image_data.url)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        log.info("image_gen_done", path=str(output_path), size_bytes=len(resp.content), source="url")
        return True

    log.error("image_gen_no_data")
    return False
