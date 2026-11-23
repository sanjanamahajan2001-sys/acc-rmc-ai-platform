"""Enterprise AI Mix Optimization Request and Response DTO Contracts (Phase 5A and 5B)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OptimizationRunTriggerRequestDTO(BaseModel):
    recipe_id: str = Field(description="Master Recipe UUID to evaluate")
    plant_code: str = Field(description="Target Plant Code for environmental and materials context")
    optimization_objective: str = Field(default="MINIMIZE_BINDER", description="MINIMIZE_BINDER, MINIMIZE_COST, or BALANCED")
    target_strength_margin_mpa: Optional[float] = Field(default=None, description="Optional custom target strength buffer (MPa)")
    parameter_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional constraint overrides for engineering study")


class RecipeConstituentSnapshotDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_id: str
    material_code: str
    material_name: str
    category_code: Optional[str] = None
    target_quantity_kg_m3: float
    engineering_unit: str = "kg"
    default_density_kg_m3: Optional[float] = None
    specific_gravity: Optional[float] = None


class RecipeSnapshotDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: str
    recipe_code: str
    recipe_name: str
    mix_design_code: Optional[str] = None
    grade: str
    target_strength_mpa: float
    water_cement_ratio: Optional[float] = None
    slump_target_mm: Optional[float] = None
    nominal_max_aggregate_size_mm: Optional[float] = None
    exposure_class: Optional[str] = None
    constituents: List[RecipeConstituentSnapshotDTO]


class ModelSnapshotDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_registry_id: Optional[str] = None
    model_name: str
    model_version: str
    framework: str
    algorithm: str
    feature_schema_version: str
    checksum: Optional[str] = None
    deployment_status: str
    validation_status: str = "ACTIVE — BASELINE MODEL (LIMITED VALIDATION)"
    prediction_source_semantics: str = "ML_MODEL (Analytical Prediction — Limited Validation)"


class TargetStrengthSnapshotDTO(BaseModel):
    characteristic_strength_fck_mpa: float
    standard_deviation_mpa: float
    standard_deviation_source: str  # "HISTORICAL_SQC_SAMPLE" or "IS456_ASSUMED_TABLE_8"
    target_mean_strength_fck_prime_mpa: float
    formula_reference: str = "f_ck_prime = fck + 1.65 * sigma (IS 456 / IS 10262)"


class ConstraintItemDTO(BaseModel):
    constraint_name: str
    standard_reference: str
    limit_value: float
    unit: str
    comparison: str  # "MINIMUM", "MAXIMUM", "RANGE"
    status: str = "ACTIVE"


class ConstraintsSnapshotDTO(BaseModel):
    exposure_class: str
    standard_edition: str = "IS 456:2000 Table 5 and IS 10262:2019"
    configuration_version: str = "1.0.0"
    items: List[ConstraintItemDTO]


class OptimizationRunResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    recipe_id: str
    recipe_code: str
    plant_code: str
    optimization_objective: str
    run_status: str
    stage_message: str
    recipe_snapshot: RecipeSnapshotDTO
    model_snapshot: ModelSnapshotDTO
    target_strength_snapshot: TargetStrengthSnapshotDTO
    constraints_snapshot: ConstraintsSnapshotDTO
    pricing_snapshot: Optional[Dict[str, Any]] = None
    candidates_count: int = 0
    created_at: str
    triggered_by_user_id: Optional[str] = None


# --- Phase 5B Candidate Evaluation DTOs ---

class ConstraintDiagnosticItemDTO(BaseModel):
    constraint_name: str
    standard_reference: str
    limit_value: float
    actual_value: float
    unit: str
    comparison: str  # "MINIMUM", "MAXIMUM", "RANGE"
    status: str  # "PASSED", "FAILED", "NOT_EVALUABLE"
    margin: float


class PhysicalVolumeDiagnosticDTO(BaseModel):
    volume_balance_actual_m3: float
    volume_balance_target_m3: float = 1.000
    volume_balance_deviation_m3: float
    volume_tolerance_limit_m3: float = 0.010
    air_volume_m3: float = 0.010
    validation_status: str  # "PASSED", "FAILED"


class CandidateConstituentDTO(BaseModel):
    material_code: str
    material_name: str
    category_code: str
    quantity_kg_m3: float
    specific_gravity: float
    absolute_volume_m3: float


class OptimizationCandidateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_identifier: str
    predicted_strength_mpa: float
    target_mean_strength_mpa: float
    characteristic_strength_fck_mpa: float
    strength_margin_mpa: float
    strength_gate_status: str  # "PASSED", "FAILED"
    prediction_source: str  # "ML_MODEL" | "HEURISTIC"
    prediction_source_semantics: str
    model_name: str
    model_version: str
    binder_intensity_kg_m3: float
    cost_per_m3: Optional[float] = None
    water_binder_ratio: float
    water_cement_ratio: float
    is_feasible: bool
    is_non_dominated: bool = False
    is_recommended: Optional[bool] = None  # Explicitly None in Phase 5B (deferred to Phase 5E)
    physical_volume_diagnostic: PhysicalVolumeDiagnosticDTO
    constraint_diagnostics: List[ConstraintDiagnosticItemDTO]
    constituents: List[CandidateConstituentDTO]


class BaselineRecipeCoordinatesDTO(BaseModel):
    recipe_code: str
    grade: str
    characteristic_strength_fck_mpa: float
    target_mean_strength_fck_prime_mpa: float
    predicted_strength_mpa: float
    binder_intensity_kg_m3: float
    cost_per_m3: Optional[float] = None
    water_binder_ratio: float


class CandidateEvaluationResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    recipe_code: str
    plant_code: str
    optimization_objective: str
    run_status: str  # "SUCCESS", "NO_FEASIBLE_CANDIDATES", "COST_NOT_CONFIGURED", "OBJECTIVE_NOT_CONFIGURED"
    stage_message: str
    total_candidates: int
    feasible_candidates_count: int
    pareto_candidates_count: int
    cost_configured: bool
    objective_configured: bool
    baseline_coordinates: BaselineRecipeCoordinatesDTO
    candidates: List[OptimizationCandidateDTO]
    evaluation_duration_ms: float
    evaluated_at: str
