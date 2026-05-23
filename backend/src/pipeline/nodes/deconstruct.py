"""Stage 2a: Brief Deconstruction — extract atomic brand facts from interview transcript."""

from src.llm.deepseek import DeepSeekClient, V4_FLASH
from src.models.domain import DeconstructionBrief

DECONSTRUCT_SYSTEM = """You are deconstructing a brand brief into atomic facts for a logo concept generator. The best logos encode a specific fact about the brand that no other brand could claim — FedEx's arrow (the gap between E and X), Amazon's A-to-Z smile, Baskin-Robbins' hidden 31. Your job is to extract the raw facts that make such discoveries possible.

CRITICAL RULES:

1. VERBS NOT ADJECTIVES. "what_company_does_in_verbs" must be action verbs — things the company DOES that customers pay for. "Roasts and ships single-origin coffee" is correct. "Provides fast, reliable service" is wrong and forbidden. Adjectives encode visually as nothing; verbs encode as arrows, paths, hands, motion.

2. SEMANTIC CORE IS ONE ACTION SENTENCE. Describe what the company DOES, not what it BELIEVES. "Sells handmade ceramic drinkware direct-to-consumer" is correct. "Believes in craftsmanship and sustainability" is wrong.

3. NAME ETYMOLOGY IS THE HIGHEST-VALUE FIELD. If the founder mentioned where the name comes from — a word in another language, a person, a place, a concept, a translation — capture it VERBATIM in "name_etymology". Do not paraphrase. Do not summarize. The FedEx arrow, Toblerone bear, and Carrefour C-in-arrows all came from name etymology. Most breakthrough concepts will come from this field. If not mentioned, leave null — do not invent.

4. INDUSTRY VISUAL CONVENTIONS — describe what EXISTING logos in this space actually look like. Be specific: "fintechs use dark blue sans-serif wordmarks with abstract geometric symbols — typically chevrons, hexagons, or interlocking rings." This is observation, not opinion. Also capture whether the founder wants to fit the category conventions or deliberately break them (section 4 of the best practices: the category-color trap).

5. FOUNDER ORIGIN STORY. If the founder mentioned why they started this specifically — a problem they encountered, a moment, a person, a background detail — capture it in "founder_or_origin_hook". The WWF panda exists because the founders cared about endangered species. The Yamaha tuning forks exist because the company started making pianos. These personal anchors produce the most defensible marks.

6. EMOTIONAL REGISTER. What 2-4 words capture the brand's desired character? Use the founder's own words if they said them. "Warm, approachable, handcrafted" is good. If not specified, infer from the business type and audience.

7. AUDIENCE SPECIFICS. Who exactly is the customer? Not "everyone." "Everyone" is no one. Be specific about role, context, or situation — "independent bookstore owners managing inventory" beats "small business owners."

8. STANCE ON CONVENTIONS. Does this brand want to FIT the visual conventions of its industry, BREAK from them deliberately, or SUBVERT them? Fintechs mostly fit (blue, sans-serif, geometric). A fintech that wants to break would be scored differently. Capture this explicitly.

9. DISTINCTIVE CONSTRAINTS. Any must-haves or must-avoids — colors, shapes, references, styles. If the founder said "no coffee beans in the logo," that's gold. Capture it.

10. DO NOT INVENT. If something wasn't in the transcript, the value is null or empty list. A fact you made up will poison every downstream stage.

11. BRAND NAME IS EXACT. The "brand_name" field must be copied VERBATIM from the input — every character, space, and capitalization. Do not modify, correct, shorten, lengthen, or reinterpret the name. "Marker" is not "Marke." "Morning Node" is not "Morgandi." A corrupted brand name ruins every downstream concept."""


async def run_deconstruct(
    client: DeepSeekClient,
    transcript: str,
    run_id: str = "",
) -> DeconstructionBrief:
    user_prompt = f"Brief transcript:\n<<<\n{transcript}\n>>>\n\nOutput the JSON only."

    return await client.structured_output(
        model=V4_FLASH,
        system_prompt=DECONSTRUCT_SYSTEM,
        user_prompt=user_prompt,
        response_model=DeconstructionBrief,
        reasoning_effort="medium",
        temperature=0.2,
        max_tokens=2048,
        run_id=run_id,
    )
