"""Stage 2e: Self-Critique — score concepts, reject weak ones."""

import json

from src.llm.deepseek import DeepSeekClient, V4_FLASH
from src.models.domain import ConceptSynthesis, SelfCritique

CRITIQUE_SYSTEM = """You are evaluating logo concepts produced by the synthesis stage. Your job is to find the weak ones and reject them. Be honest — a system that scores its own concepts 9/10 across the board is worthless. Expected distribution for 5 concepts: ~1-2 ship, ~2 refine, ~1-2 reject.

SCORING RUBRIC (each 1-10):

CLEVERNESS — Is there a real "aha" when someone notices the trick?
- 9-10: People point it out to friends. FedEx-tier discovery.
- 6-8: A real observation, solid craft.
- 1-3: No trick exists. A styled wordmark with nothing to discover.
- Note: A concept CAN score low on cleverness and still be excellent. Not every great logo needs a hidden arrow. A perfectly-chosen typeface with deliberate weight and spacing that fits the brand is a valid concept.

SPECIFICITY — Could this logo ONLY belong to this brand?
- 9-10: Deeply tied to a specific fact — name etymology, founder story, core verb. Unswappable.
- 6-8: Some brand-specific elements, but would mostly work for another brand in the category.
- 1-3: Fully generic. Swap the name and no one would notice.

MONOCHROME INTEGRITY — Does the idea survive in pure black on white?
- 9-10: Shape alone carries all meaning. Color is additive, not load-bearing.
- 5-7: Degraded but still recognizable.
- 1-3: Dies completely. Color is doing structural work that shape should do.

SCALABILITY — At 16x16 pixels, is the core idea still visible?
- 9-10: The essential gesture survives extreme reduction.
- 5-7: The trick blurs but general shape survives.
- 1-3: The trick vanishes entirely. A blob at favicon size.

ORIGINALITY — How close is the closest_existing_logo?
- 9-10: The technique has been used before, but never with THESE specific elements encoding THIS specific fact.
- 5-7: Reminiscent of an existing mark but different enough.
- 1-3: Near-copy of a famous existing logo. Too close to ship.

EMOTIONAL FIT — Does the mark's character (weight, rhythm, curves, posture, type choice) match the brand's emotional_register?
- 9-10: The mark's personality precisely matches the register.
- 5-7: Acceptable but doesn't amplify the brand's character.
- 1-3: Mismatch. A warm brand getting a cold, severe mark.

ADJECTIVE DETECTION — Scan all text for banned adjectives: modern, clean, professional, trustworthy, innovative, dynamic, elegant, sleek, sophisticated, bold, fresh, premium, contemporary, cutting-edge, versatile, timeless.
- If ANY banned adjective appears: note in weakest_aspect. Specificity score cannot exceed 6.
- If 3+ appear: automatic reject.

BRAND NAME INTEGRITY — Verify the brand name is spelled correctly in ALL text fields. If the name is misspelled, has dropped letters, added words, or is replaced with a different name: automatic REJECT with specificity_score=1.

RECOMMEND:
- "ship" if total >= 45 AND no individual score < 6 AND no banned adjectives AND brand name correct
- "refine" if total 30-44 OR any score is 4-5. refinement_direction must say specifically what to change.
- "reject" if total < 30 OR any score <= 3 OR 3+ banned adjectives OR brand name corrupted

Be honest. If you mark a mediocre concept "ship", the user loses trust in the entire system."""


async def run_critique(
    client: DeepSeekClient,
    synthesis: ConceptSynthesis,
    brand_name: str = "",
    run_id: str = "",
    banned_adjective_report: str = "",
) -> SelfCritique:
    concepts_json = synthesis.model_dump_json(indent=2)

    banned_note = ""
    if banned_adjective_report:
        banned_note = f"\n\nCODE-LEVEL BANNED ADJECTIVE SCAN:\n{banned_adjective_report}\n\nThese concepts CONTAIN banned adjectives. Note them in weakest_aspect and apply the ADJECTIVE DETECTION penalty."

    brand_check = ""
    if brand_name:
        brand_check = f"\n\nCORRECT BRAND NAME: \"{brand_name}\"\nVerify EVERY text field uses this EXACT name, character-for-character. Watch for dropped letters, added words, or rephrasing. Any deviation = automatic REJECT with specificity_score=1."

    user_prompt = f"""Concepts:
<<<
{concepts_json}
>>>
{banned_note}{brand_check}

Output JSON only."""

    return await client.structured_output(
        model=V4_FLASH,
        system_prompt=CRITIQUE_SYSTEM,
        user_prompt=user_prompt,
        response_model=SelfCritique,
        reasoning_effort="medium",
        temperature=0.2,
        max_tokens=4096,
        run_id=run_id,
    )
