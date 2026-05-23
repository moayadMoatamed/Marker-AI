"""Pydantic schemas for the concept-generation pipeline stages 2a-2e.

These schemas ARE the contract between pipeline stages. Every LLM call in the
concept pipeline uses structured output mode with these JSON schemas. The
Field(description=...) strings become the JSON Schema descriptions the model sees.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2a — Brief Deconstruction
# ═══════════════════════════════════════════════════════════════════════════════


class DeconstructionBrief(BaseModel):
    """Atomic facts extracted from the interview transcript."""

    brand_name: str = Field(description="The company or product name exactly as stated")
    name_letters: list[str] = Field(
        description="Individual letters/glyphs in the brand name, in order"
    )
    name_syllable_count: int = Field(
        description="Number of syllables in the spoken brand name", ge=1
    )
    name_etymology: str | None = Field(
        default=None,
        description="If the name has a derivation, origin, or hidden meaning — capture it verbatim",
    )
    what_company_does_in_verbs: list[str] = Field(
        description="VERBS only. What the company DOES. 'delivers shipments' is correct. 'fast and reliable' is forbidden.",
        min_length=1,
    )
    semantic_core: str = Field(
        description="One sentence describing what the company DOES, not what it believes"
    )
    emotional_register: list[str] = Field(
        description="2-4 words capturing emotional character: serious, playful, precise, warm, etc.",
        min_length=2,
        max_length=4,
    )
    audience_specifics: str = Field(
        description="Who the brand serves, with specifics: age, role, context, situation"
    )
    founder_or_origin_hook: str | None = Field(
        default=None,
        description="Founder's personal story, origin moment, or distinctive background — the human hook",
    )
    industry_visual_conventions: list[str] = Field(
        description="What EXISTING logos in this space typically look like — observation, not opinion"
    )
    stance_on_conventions: Literal["fit", "break", "subvert"] = Field(
        description="Does the brand want to fit in, break from, or subvert industry visual conventions?"
    )
    distinctive_constraints: list[str] = Field(
        description="Must-haves and must-avoids. Specific forbidden elements, colors, shapes, references"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2b — Raw Material Inventory
# ═══════════════════════════════════════════════════════════════════════════════


class LetterShapeOpportunity(BaseModel):
    """A specific visual affordance in the brand name's letter forms."""

    letters_involved: list[str] = Field(
        description="Which specific letters this opportunity involves, e.g. ['E', 'x']"
    )
    opportunity: str = Field(
        description="The specific visual affordance. What gap, shape, curve, or counter-space exists?"
    )
    example_use: str = Field(
        description="How this affordance could become meaningful — concrete, not abstract"
    )


class SemanticVisualAnchor(BaseModel):
    """A concrete visual form that encodes a brand concept."""

    concept: str = Field(
        description="The concept from what_company_does_in_verbs being encoded"
    )
    visual_candidates: list[str] = Field(
        description="3-5 concrete visual forms that ENCODE this concept. 'Delivers' → arrow, package, motion line, path, hand-extending. NOT adjectives.",
        min_length=3,
        max_length=5,
    )


class RawMaterialInventory(BaseModel):
    """Manipulable visual opportunities extracted from the deconstruction."""

    letter_shape_opportunities: list[LetterShapeOpportunity] = Field(
        description="At least 5 letter-shape opportunities. For EVERY adjacent letter pair and distinct single letter.",
        min_length=5,
    )
    semantic_visual_anchors: list[SemanticVisualAnchor] = Field(
        description="For EVERY verb in what_company_does_in_verbs, a mapping to concrete visual candidates",
        min_length=3,
    )
    etymological_hooks: list[str] = Field(
        description="Visual cues derivable from the name's etymology. Mine this hard if name_etymology is non-null."
    )
    cultural_references: list[str] = Field(
        description="Symbols, forms, visual language from the brand's specific cultural context"
    )
    forbidden_cliches: list[str] = Field(
        description="The laziest moves in this industry that must be avoided"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2c — Technique Search
# ═══════════════════════════════════════════════════════════════════════════════

# The 12-technique taxonomy
TechniqueId = Literal[
    "negative_space_letterform",
    "negative_space_silhouette",
    "letterform_modification",
    "letterform_as_symbol",
    "symbol_fusion",
    "geometric_construction",
    "gestalt_closure",
    "gestalt_continuity",
    "numeric_or_lexical_embedding",
    "cultural_or_etymological_mark",
    "ambigram_or_palindrome",
    "monogram_construction",
]

ALL_TECHNIQUE_IDS: tuple[TechniqueId, ...] = (
    "negative_space_letterform",
    "negative_space_silhouette",
    "letterform_modification",
    "letterform_as_symbol",
    "symbol_fusion",
    "geometric_construction",
    "gestalt_closure",
    "gestalt_continuity",
    "numeric_or_lexical_embedding",
    "cultural_or_etymological_mark",
    "ambigram_or_palindrome",
    "monogram_construction",
)


class TechniqueEvaluation(BaseModel):
    """Evaluation of one technique's applicability to this specific brand."""

    technique_id: TechniqueId = Field(
        description="The technique being evaluated, from the 12-technique taxonomy"
    )
    applicable: bool = Field(
        description="Can this technique produce a logo whose meaning is unmistakably tied to THIS brand?"
    )
    applicability_score: int = Field(
        description="1-10. 6-10 if applicable and specific. 1-3 if not applicable. Do not give uniform scores.",
        ge=1,
        le=10,
    )
    specific_proposal: str | None = Field(
        default=None,
        description="Concrete proposal in one sentence IF applicable. Must reference specific letters or visual concepts by name. Null if not applicable.",
    )
    why_or_why_not: str = Field(description="One sentence explaining the judgment")
    which_raw_material_it_uses: list[str] = Field(
        description="References back to stage 2b items this technique would use"
    )


class TechniqueSearchResult(BaseModel):
    """Exhaustive evaluation of all 12 techniques against the brand's raw material."""

    technique_evaluations: list[TechniqueEvaluation] = Field(
        description="Exactly 12 evaluations, one per technique in the taxonomy",
        min_length=12,
        max_length=12,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2d — Concept Synthesis
# ═══════════════════════════════════════════════════════════════════════════════


class MeaningMapping(BaseModel):
    """How one element of the mark maps to meaning."""

    element: str = Field(description="The visual element — a shape, letter, gap, curve, etc.")
    represents: str = Field(description="What this element represents")
    because: str = Field(
        description="The reasoning connecting element to meaning. 'Because...' — defend the choice."
    )


BANNED_ADJECTIVES: frozenset[str] = frozenset(
    {
        "modern",
        "clean",
        "professional",
        "trustworthy",
        "innovative",
        "dynamic",
        "elegant",
        "sleek",
        "sophisticated",
        "bold",
        "fresh",
        "premium",
        "contemporary",
        "cutting-edge",
        "versatile",
        "timeless",
    }
)


class Concept(BaseModel):
    """A single fully-specified logo concept."""

    concept_id: str = Field(description="Unique identifier for this concept within the run")
    technique_used: TechniqueId = Field(
        description="Which technique from stage 2c this concept is built on"
    )
    one_line_idea: str = Field(description="The concept in a single line")
    the_trick: str = Field(
        description="The ONE clever, non-obvious observation. If you cannot articulate it in one sentence, the concept is not ready."
    )
    meaning_mapping: list[MeaningMapping] = Field(
        description="Every element of the mark, what it represents, and the 'because' clause",
        min_length=1,
    )
    construction_recipe: str = Field(
        description="Step-by-step drawing instructions executable by an illustrator or vector model. Use coordinates loosely if helpful. Generic instructions are forbidden."
    )
    monochrome_survives: bool = Field(
        description="Would this work as pure black ink on white paper, no color?"
    )
    sixteen_px_survives: bool = Field(
        description="At favicon size (16×16px), is the core idea still visible?"
    )
    closest_existing_logo: str = Field(
        description="Name the closest existing logo. If more than 70% similar, abandon and try again."
    )
    rationale_paragraph: str = Field(
        description="150-200 words explaining the concept for a non-designer founder's brand book. Reference the brand's actual story.",
        min_length=100,
        max_length=2500,
    )

    def contains_banned_adjectives(self) -> set[str]:
        """Return any banned adjectives found in all text fields."""
        import re

        fields = [
            self.one_line_idea,
            self.rationale_paragraph,
            self.the_trick,
            self.construction_recipe,
        ] + [f"{m.element} {m.represents} {m.because}" for m in self.meaning_mapping]
        text = " ".join(fields).lower()
        found: set[str] = set()
        for adj in BANNED_ADJECTIVES:
            if re.search(r"\b" + re.escape(adj) + r"\b", text):
                found.add(adj)
        return found


class ConceptSynthesis(BaseModel):
    """3-5 fully-specified logo concepts using different techniques."""

    brand_name: str = Field(
        description="The EXACT brand name from the deconstruction — copied verbatim, not modified"
    )
    concepts: list[Concept] = Field(
        description="3-5 concepts, each using a DIFFERENT technique. Three variations of one idea is one concept, not three.",
        min_length=3,
        max_length=5,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2e — Self-Critique
# ═══════════════════════════════════════════════════════════════════════════════

Recommendation = Literal["ship", "refine", "reject"]


class ConceptScore(BaseModel):
    """Self-critique score for one concept."""

    concept_id: str = Field(description="Which concept is being scored")
    cleverness_score: int = Field(
        description="1-10. Is there a real 'aha' when someone notices the trick?", ge=1, le=10
    )
    specificity_score: int = Field(
        description="1-10. Could this logo ONLY belong to this brand?", ge=1, le=10
    )
    monochrome_score: int = Field(
        description="1-10. Does the idea survive in pure black on white?", ge=1, le=10
    )
    scalability_score: int = Field(
        description="1-10. At 16×16 pixels, is the trick still visible?", ge=1, le=10
    )
    originality_score: int = Field(
        description="1-10. How close is the closest_existing_logo from stage 2d?", ge=1, le=10
    )
    emotional_fit_score: int = Field(
        description="1-10. Does the mark's character match the brand's emotional_register?", ge=1, le=10
    )
    total: int = Field(description="Sum of all six scores (max 60)")
    weakest_aspect: str = Field(
        description="One sentence on this concept's biggest flaw"
    )
    recommend: Recommendation = Field(
        description="ship if total >= 45 and no score < 6; refine if total 30-44 or any 4-5; reject if total < 30 or any <= 3"
    )
    refinement_direction: str | None = Field(
        default=None,
        description="If recommend=refine, say specifically what to change. Otherwise null.",
    )


class SelfCritique(BaseModel):
    """Scored evaluation of all concepts from stage 2d, with explicit rejection."""

    concept_scores: list[ConceptScore] = Field(
        description="One score per concept from stage 2d. Distribution target: ~1 ship, ~2 refine, ~2 reject."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline run tracking
# ═══════════════════════════════════════════════════════════════════════════════


class PipelineRun(BaseModel):
    """Top-level container for a full pipeline run's outputs. Persist everything keyed by run_id."""

    run_id: str = Field(description="UUID for this pipeline run, threads through all log lines")
    deconstruction: DeconstructionBrief | None = None
    raw_material: RawMaterialInventory | None = None
    technique_search: TechniqueSearchResult | None = None
    synthesis: ConceptSynthesis | None = None
    critique: SelfCritique | None = None
