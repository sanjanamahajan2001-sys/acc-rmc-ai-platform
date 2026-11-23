"""Enterprise AI Mix Optimization Recipe Impact and Comparison DTO Contracts (Phase 5C)."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConstituentImpactItemDTO(BaseModel):
    """Side-by-side constituent comparison with delta calculations."""
    model_config = ConfigDict(from_attributes=True)

    material_id: Optional[str] = Field(default=None, description="Authoritative Material UUID if mapped")
    material_code: str = Field(description="Canonical material code (e.g. CEM-OPC, MAT-FA)")
    material_name: str = Field(description="Authoritative human-readable material name")
    category_code: str = Field(description="Material category (CEMENT, FLY_ASH, GGBS, WATER, COARSE_AGGREGATE, FINE_AGGREGATE, ADMIXTURE, OTHER)")

    current_quantity_kg_m3: float = Field(description="Normalized quantity in Phase 5A baseline snapshot (kg/m³)")
    candidate_quantity_kg_m3: float = Field(description="Quantity in Phase 5B candidate (kg/m³)")
    absolute_delta_kg_m3: float = Field(description="candidate_quantity - current_quantity (kg/m³)")
    percentage_delta: Optional[float] = Field(default=None, description="((candidate - current) / current) * 100 or None if current == 0")

    current_specific_gravity: float = Field(description="Authoritative SG for current recipe")
    candidate_specific_gravity: float = Field(description="Authoritative SG for candidate recipe")
    current_volume_m3: float = Field(description="Absolute volume in current recipe (m³)")
    candidate_volume_m3: float = Field(description="Absolute volume in candidate recipe (m³)")
    volume_delta_m3: float = Field(description="candidate_volume - current_volume (m³)")

    status_label: str = Field(
        default="NORMAL",
        description="NORMAL, NEW_CONSTITUENT, REMOVED_CONSTITUENT, or NO_QUANTITY"
    )


class RecipeImpactSummaryDTO(BaseModel):
    """Aggregated recipe-level deltas for binder, water, W/B ratio, and yield."""
    model_config = ConfigDict(from_attributes=True)

    current_total_binder_kg_m3: float
    candidate_total_binder_kg_m3: float
    binder_delta_kg_m3: float
    binder_percentage_delta: Optional[float] = None

    current_water_kg_m3: float
    candidate_water_kg_m3: float
    water_delta_kg_m3: float
    water_percentage_delta: Optional[float] = None

    current_water_binder_ratio: float
    candidate_water_binder_ratio: float
    water_binder_ratio_delta: float

    current_yield_m3: float
    candidate_yield_m3: float
    yield_delta_m3: float

    coarse_aggregate_delta_kg_m3: float
    fine_aggregate_delta_kg_m3: float
    admixture_delta_kg_m3: float


class CandidateEvaluationSummaryDTO(BaseModel):
    """Authoritative evaluation metrics reused directly from Phase 5B persistence."""
    model_config = ConfigDict(from_attributes=True)

    predicted_strength_mpa: float
    target_mean_strength_mpa: float
    strength_margin_mpa: float
    is_feasible: bool
    is_non_dominated: bool
    prediction_source: str
    prediction_source_semantics: str


class RecipeImpactResponseDTO(BaseModel):
    """Root response model for Phase 5C Current-vs-Candidate Recipe Impact."""
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    candidate_id: str
    candidate_identifier: str
    recipe_code: str
    grade: str
    exposure_class: str

    current_recipe_source: str = "Phase 5A immutable recipe snapshot"
    candidate_recipe_source: str = "Phase 5B persisted candidate"

    constituents: List[ConstituentImpactItemDTO]
    impact_summary: RecipeImpactSummaryDTO
    candidate_evaluation: CandidateEvaluationSummaryDTO
    evaluated_at: Optional[str] = None
