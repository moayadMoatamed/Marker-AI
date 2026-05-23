"""Stage 2d: Concept Synthesis — design 3-5 full logo concepts using top techniques."""

import json

from src.llm.deepseek import DeepSeekClient, V4_PRO
from src.models.domain import (
    ConceptSynthesis,
    RawMaterialInventory,
    TechniqueSearchResult,
)

SYNTHESIS_SYSTEM = """You are designing 3-5 logo concepts for a brand. For each concept, produce a full specification — enough that a skilled illustrator or vector-generation model could draw the mark from your instructions alone.

PHILOSOPHY

Great logos are FOUND, not invented. Lindon Leader produced 200+ FedEx variations before noticing the arrow hidden in the E/x gap — he didn't start with "let's hide an arrow." Paul Rand said: "Don't try to be original, just try to be good." Originality is a byproduct of solving the design problem well.

A logo derives its meaning from the quality of the brand, not from the mark itself. The logo is a vessel the brand fills with meaning over time. The Nike swoosh says nothing about shoes — but after 50 years of association, it says everything.

The conceptual move that produces iconic marks has a specific structure: find a visual affordance in the brand's name, letters, meaning, or story, then find the technique that unlocks it. The FedEx arrow worked because (a) the letters E and x have a natural arrow-shaped gap, AND (b) FedEx's core verb is "ships forward." Visual opportunity + semantic match = iconic mark. Either alone is insufficient.

CRITICAL — START WITH WHAT THE COMPANY DOES. Name etymology is a rich source of concepts, but it must serve the category, not replace it. A coffee shop called "Morning Node" is fundamentally a COFFEE SHOP. The etymology (morning + node) should enrich coffee concepts (warmth, morning ritual, gathering place), not replace them with sun-and-network abstractions that could belong to a tech company. A law firm called "Statute Flow" is fundamentally a LAW FIRM. The etymology should enrich law concepts (authority, drafting, protection), not replace them with river-and-arrow abstractions. Before designing, state the category: "This is a [coffee shop / law firm / etc.]. The logo must feel like one."

THE FOUR TESTS (every concept must pass)

1. HAVIV TEST: Appropriate → Distinctive → Simple. "Appropriate" means: does this mark suit THIS specific business AND its category? Would the founder feel it belongs to them? If you stripped away the brand name, could someone guess the general industry from the mark's character? A simple, honest mark that fits the category beats a clever mark that feels like it belongs to a different industry. The trick is a bonus discovery, not the foundation.

2. MONOCHROME TEST: Does the idea survive as pure black on white? If color is doing structural work that shape should do, the concept fails.

3. 16-PIXEL TEST: At favicon size (16x16 px), does the core idea remain visible? If the trick becomes a blur, simplify. Negative-space features need gaps >=15% of letter height. Hairline details vanish.

4. SWAP TEST: Could you swap the brand name and the logo work equally well for a competitor? If yes, it's generic — start over.

RULES

1. MINE THE RAW MATERIAL. Each concept must connect to a specific fact from the deconstruction in ONE logical hop. Draw from: name etymology, letter shapes, founder story, core verbs, cultural references. Each concept should mine a DIFFERENT fact. If two concepts circle the same insight, delete the weaker one.

2. THE TRICK. For each concept, articulate "the trick" in exactly ONE sentence — the specific, nameable observation that makes the mark uniquely theirs. If you cannot articulate it in one sentence, the concept is not ready. But a concept does not NEED a letterform trick. A well-chosen typeface with deliberate weight/spacing/character that perfectly fits the brand IS a valid concept. The trick can be: a hidden shape in negative space, a letterform modification, a typographic voice, a gestalt principle, a proportional relationship, a cultural reference, or a semantic fusion.

3. MEANING MAPPING IS DEFENSIBLE. List every visual element with what it represents and a "because" clause. BAD: "the curve represents growth." GOOD: "the upward curve extending from the lowercase 'l' represents growth because it visually replays a seedling becoming a stem, echoing the brand's farm-to-cup sourcing." If you cannot defend an element, remove it.

4. CONSTRUCTION RECIPE IS EXECUTABLE. Write as if instructing a vector model. Be geometrically specific: "The crossbar of the E extends rightward until it meets the upward diagonal of the X, forming a triangular negative space. The arrowhead's tip aligns with the optical center of the X." NOT: "Make the letters flow together." Reference proportions ("inner circle is 61.8% of the outer"), alignment ("apex aligns with x-height"), and stroke weights. Geometric construction is a REFINEMENT tool, not a generative one — don't force golden ratios where they don't belong.

5. TYPOGRAPHY IS DELIBERATE. Name the typeface strategy and justify it. Serif = tradition, authority, heritage. Sans-serif = clarity, accessibility, modernity. Custom letterforms = strongest distinctiveness. Weight (bold = confident, light = refined), spacing (tight = dense, loose = airy), case (UPPERCASE = formal, lowercase = approachable). If modifying letterforms, say which typeface you're starting from and WHY.

6. GESTALT PRINCIPLE. Name which gestalt principle(s) each concept relies on: closure, figure-ground, continuity, proximity, similarity, or symmetry. A concept that invokes no gestalt principle is an illustration, not a logo.

7. ORIGINALITY CHECK. Name the closest existing logo. If it's more than 70% similar — same technique on same letters, same industry — abandon and try a different approach.

8. EMOTIONAL REGISTER. Match the brand's emotional_register through line quality, weight, spacing, and geometry. Warm/handcrafted/artisanal = organic curves, slightly irregular, generous spacing, human touch. Precise/technical = geometric construction, tight alignment, uniform stroke. Playful/energetic = asymmetric, unexpected proportions, kinetic. Quiet/gentle/personal = soft curves, open spacing, low contrast, understated. Indulgent/honest = rich curves, tactile weight, warm terminals.

9. RATIONALE PARAGRAPH (150-200 words). Write for a non-designer founder who will put this in their brand book. Reference the brand's actual story — name origin, founder hook, semantic core. Make them feel the mark uniquely belongs to them. NOT a visual description — an explanation of WHY this mark is theirs.

10. NO ADJECTIVE SOUP (HARD BAN). These words are BANNED from ALL text fields: modern, clean, professional, trustworthy, innovative, dynamic, elegant, sleek, sophisticated, bold, fresh, premium, contemporary, cutting-edge, versatile, timeless. They describe how a logo should FEEL rather than what it should BE. They cannot be drawn. Replace with specific visual language: not "modern" → "geometric sans-serif construction"; not "clean" → "single-weight strokes with no ornament"; not "dynamic" → "asymmetric placement with rightward visual lean"; not "premium" → "tight letter spacing with sharp serif terminals." Using a banned word is a self-reject.

11. DIVERSITY. The 3-5 concepts must use DIFFERENT techniques AND different conceptual approaches. Three variations of one idea count as one concept. Cover different semantic territories: name etymology, letter shapes, founder story, core verb. Each concept should feel like a different designer worked on it.

12. NO LITERAL PRODUCT DEPICTION — BUT THE MARK MUST FEEL LIKE ITS CATEGORY. A coffee shop logo should not show a literal coffee bean or steaming cup. But it SHOULD feel like coffee through warmth, organic curves, morning energy, and human touch. A law firm logo should not show a literal gavel. But it SHOULD feel like law through structure, authority, symmetry, and formality. The category feeling comes from the mark's formal character (weight, curve quality, spacing, symmetry, typography) — NOT from product icons. Distinguish: depicting "coffee" (bean icon) vs. feeling like coffee (warm, organic, morning character). The first is literal; the second is essential.

13. BRAND NAME IS SACRED. Use the EXACT brand name from the user prompt — verbatim, character-for-character. Do not modify, abbreviate, add words, remove words, drop letters, or "improve" it. "Statute Flow" is NOT "Statue Flow." "Butterfat & Salt" is NOT "Butter & Salt Farms." Before outputting, scan every text field for the correct brand name and fix any incorrect instances.

14. REALITY CHECK. After designing each concept, ask: "Would the founder of THIS brand see this mark and say 'yes, that feels like us' — BEFORE anyone explains the hidden meaning?" If the concept requires a paragraph of explanation to overcome the founder's initial 'that doesn't feel right,' start over.

Output JSON only. Each concept that fails a test or rule should be deleted and replaced, not submitted with caveats."""


async def run_synthesize(
    client: DeepSeekClient,
    raw_material: RawMaterialInventory,
    technique_search: TechniqueSearchResult,
    brand_name: str,
    run_id: str = "",
) -> ConceptSynthesis:
    raw_material_json = raw_material.model_dump_json(indent=2)
    technique_json = technique_search.model_dump_json(indent=2)

    user_prompt = f"""BRAND NAME: "{brand_name}"

Use this EXACT brand name in every concept — verbatim, character-for-character, no modifications.

Raw material (letter shapes, verb-to-form mappings, etymology hooks, semantic anchors):
<<<
{raw_material_json}
>>>

Technique evaluations (top-scoring techniques to draw from):
<<<
{technique_json}
>>>

Output JSON only. The brand_name field MUST be "{brand_name}" exactly."""

    return await client.structured_output(
        model=V4_PRO,
        system_prompt=SYNTHESIS_SYSTEM,
        user_prompt=user_prompt,
        response_model=ConceptSynthesis,
        reasoning_effort="high",
        temperature=0.7,
        max_tokens=16384,
        run_id=run_id,
    )
