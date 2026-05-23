"""Stage 2b: Raw Material Inventory — identify manipulable visual opportunities."""

import json

from src.llm.deepseek import DeepSeekClient, V4_FLASH
from src.models.domain import DeconstructionBrief, RawMaterialInventory

RAW_MATERIAL_SYSTEM = """You are identifying manipulable visual opportunities in this brand's atomic facts. You are NOT designing anything yet — you are building the inventory of raw material that the synthesis stage will draw from.

Lindon Leader's FedEx arrow came from this exact process: he produced 200+ variations, noticed that tight spacing between capital E and lowercase x creates a natural arrow-shaped gap, then refined it. The arrow worked because (a) the letters E and x have an arrow-shaped gap, AND (b) FedEx's core verb is "ships forward." Visual opportunity + semantic match.

Your job is to enumerate such affordances exhaustively.

RULES:

1. LETTER-SHAPE OPPORTUNITIES. For EVERY adjacent letter pair and distinctive single letter in the brand name:
   - What shapes do these letters naturally suggest? Curves, bowls, stems, counters, terminals?
   - What gaps or negative spaces exist between adjacent letters?
   - What could happen with tighter kerning? Extended crossbars? Connected terminals?
   - Be SPECIFIC: "The bowl of 'a' and vertical stem of 'r' create a counter-space that could hold a small symbol" is correct. "The letters have interesting shapes" is wrong.
   - Produce AT LEAST 5 letter-shape opportunities naming specific letters.
   - The hidden-meaning canon (FedEx arrow, Amazon smile, Baskin-Robbins 31, Carrefour C) ALL came from this step.

2. VERB-TO-FORM MAPPING. For EVERY verb in the deconstruction's "what_company_does_in_verbs", list 3-5 concrete visual forms that ENCODE that verb:
   - "Delivers" → arrow, motion line, hand-extending, package, path
   - "Connects" → bridge, interlocking forms, continuous line, two elements meeting
   - "Grows" → upward curve, sprouting form, ascending steps, expanding circles
   NOT adjectives. "Fast" encodes as nothing; "arrow pointing right" encodes as speed.

3. NAME ETYMOLOGY MINING. If "name_etymology" is non-null, mine it aggressively:
   - A brand named "Carrefour" (French for crossroads) → intersecting paths, meeting point, two arrows
   - List EVERY visual anchor the etymology suggests.

4. SEMANTIC VISUAL ANCHORS. List concrete objects, shapes, or symbols from the brand's domain:
   - A robotics company → gears, joints, circuit traces, armatures, sensor patterns
   - A coffee roaster → bean cross-section, steam tendril, roaster drum, burr grinder
   - A bookstore → spine texture, page edge, bookmark, reading lamp, marginalia marks
   - A law firm → pen nib, signature flourish, paragraph mark, contract seal, binding element
   These are visual vocabulary the synthesis stage can combine with letterforms — NOT the logo itself.

5. FORBIDDEN CLICHES. What are the laziest moves in this brand's category?
   - Fintech: abstract geometric chevron in blue, interlocking rings
   - Coffee: stylized coffee bean, steaming cup silhouette
   - Law: scales of justice, gavel, columns, law books
   Listing these prevents the synthesis stage from drifting toward them.

6. DO NOT DESIGN. Do not propose logos, do not write rationales, do not pick a winner. Only enumerate raw material."""


async def run_raw_material(
    client: DeepSeekClient,
    deconstruction: DeconstructionBrief,
    run_id: str = "",
) -> RawMaterialInventory:
    deconstruction_json = deconstruction.model_dump_json(indent=2)
    user_prompt = f"Deconstruction:\n<<<\n{deconstruction_json}\n>>>\n\nOutput the JSON only."

    return await client.structured_output(
        model=V4_FLASH,
        system_prompt=RAW_MATERIAL_SYSTEM,
        user_prompt=user_prompt,
        response_model=RawMaterialInventory,
        reasoning_effort="medium",
        temperature=0.2,
        max_tokens=8192,
        run_id=run_id,
    )
