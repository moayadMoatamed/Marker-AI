"""Pipeline state model for LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.domain import (
    ConceptSynthesis,
    DeconstructionBrief,
    RawMaterialInventory,
    SelfCritique,
    TechniqueSearchResult,
)


@dataclass
class PipelineState:
    """State object that flows through the LangGraph pipeline nodes."""

    run_id: str
    transcript: str = ""

    # Stage outputs
    deconstruction: DeconstructionBrief | None = None
    raw_material: RawMaterialInventory | None = None
    technique_search: TechniqueSearchResult | None = None
    synthesis: ConceptSynthesis | None = None
    critique: SelfCritique | None = None

    # Derived data for UI
    concepts: list[dict[str, Any]] = field(default_factory=list)
    scores: list[dict[str, Any]] = field(default_factory=list)
    images: dict[str, str] = field(default_factory=dict)

    # Flow control
    stage: str = "starting"
    error: str | None = None

    def update_concepts_and_scores(
        self,
        concepts: list[dict[str, Any]],
        scores: list[dict[str, Any]],
    ) -> None:
        self.concepts = concepts
        self.scores = scores
