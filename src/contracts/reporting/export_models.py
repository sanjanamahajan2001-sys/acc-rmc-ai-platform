"""Canonical Typed Report Contracts for Full Dashboard Summary & Authoritative Export.

Provides structured DTOs for:
- Executive Dashboard Summary (4 Groups)
- Statistical Quality Control & Production Metrics (including Grade Performance Matrix)
- Strength Prediction & Model Lineage
- Material Consumption, Batching Variance & Weighment Tolerance (IS 4926 Annex E)
- Binder Intensity & Efficiency Metrics
- Optimization Run & Candidate Evaluation
- Recipe Impact Matrix & Candidate Diagnostics
- Cost & Commercial Impact Matrix
- Actionable Findings & Engineering Review Points
- Recommendation Governance & Human Review State
- Audit Provenance & Report Generation Metadata
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportMetadataDTO(BaseModel):
    """Metadata describing the generated report document."""
    report_title: str = "ACC Ready-Mix Concrete Operations & Optimization Report"
    document_type: str = "AUTHORITATIVE_EXECUTIVE_REPORT"
    generated_at: str
    generated_by_user_id: Optional[str] = None
    generated_by_username: str = "System"
    platform_version: str = "1.0.0"
    compliance_standard: str = "IS 456:2000 / IS 10262:2019 / IS 4926:2003"
    environment: str = "Production"


class DashboardScopeContextDTO(BaseModel):
    """Filter and execution context for the dashboard report."""
    plant_code: Optional[str] = None
    plant_name: Optional[str] = None
    recipe_code: Optional[str] = None
    recipe_name: Optional[str] = None
    grade_code: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    selected_run_id: Optional[str] = None
    selected_candidate_id: Optional[str] = None


# =========================================================================
# Executive Dashboard Summary: 4 Factual Groups
# =========================================================================

class ExecutiveSummaryQualityProductionDTO(BaseModel):
    """Group A: Quality & Production Metrics."""
    grades_evaluated: int = 0
    total_batches_produced: int = 0
    total_volume_m3: float = 0.0
    batches_tested_28d: int = 0
    specimens_tested_28d: int = 0
    mean_strength_28d_mpa: Optional[float] = None
    quality_compliance_percent: Optional[float] = None
    strength_variability_sigma_mpa: Optional[float] = None
    strength_cov_percent: Optional[float] = None
    weighment_accuracy_percent: Optional[float] = None


class ExecutiveSummaryStrengthPredictionDTO(BaseModel):
    """Group B: Strength Prediction & Model Lineage."""
    platform_active_model: str = "—"
    platform_model_version: str = "—"
    model_used_for_optimization_run: str = "—"
    validation_status: str = "Limited Validation"
    target_characteristic_fck_mpa: Optional[float] = None
    target_mean_strength_fck_prime_mpa: Optional[float] = None
    predicted_strength_mpa: Optional[float] = None
    prediction_margin_mpa: Optional[float] = None
    prediction_mean_abs_error_mae: Optional[float] = None


class ExecutiveSummaryMixOptimizationDTO(BaseModel):
    """Group C: Mix Optimization."""
    has_optimization_run: bool = False
    optimization_run_id: Optional[str] = None
    optimization_objective: str = "—"
    total_candidates_evaluated: int = 0
    feasible_candidates_count: int = 0
    pareto_optimal_count: int = 0
    selected_candidate_identifier: Optional[str] = None
    binder_intensity_kg_m3: Optional[float] = None
    water_binder_ratio: Optional[float] = None
    yield_m3: Optional[float] = None
    recipe_impact_summary: str = "—"


class ExecutiveSummaryGovernanceCommercialDTO(BaseModel):
    """Group D: Governance & Commercial Status."""
    engineering_feasibility: str = "—"
    review_status: str = "PENDING_REVIEW"
    human_reviewer_username: Optional[str] = None
    human_reviewer_role: Optional[str] = None
    review_timestamp: Optional[str] = None
    review_reason_code: Optional[str] = None
    pricing_configuration_status: str = "NOT_CONFIGURED"
    pricing_source_description: str = "Pricing Source: Not Configured"
    cost_per_m3_inr: Optional[float] = None
    cost_delta_per_m3_inr: Optional[float] = None
    production_activation_status: str = "PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE"
    production_activation_notice: str = "Production activation is outside the current phase."


class ExecutiveDashboardSummaryDTO(BaseModel):
    """Consolidated factual executive dashboard summary."""
    quality_and_production: ExecutiveSummaryQualityProductionDTO
    strength_prediction: ExecutiveSummaryStrengthPredictionDTO
    mix_optimization: ExecutiveSummaryMixOptimizationDTO
    governance_and_commercial: ExecutiveSummaryGovernanceCommercialDTO


# =========================================================================
# Detailed Domain Sections & Matrices
# =========================================================================

class GradePerformanceItemDTO(BaseModel):
    """Individual grade/mix performance item per IS 456."""
    recipe_code: str
    recipe_name: str
    grade: str
    target_fck_mpa: float
    target_mean_strength_mpa: float
    total_batches: int
    tested_28d_batches: int
    tested_28d_specimens: int = 0
    mean_strength_mpa: Optional[float] = None
    standard_deviation_mpa: Optional[float] = None
    cov_percent: Optional[float] = None
    strength_margin_mpa: Optional[float] = None
    compliance_percent: Optional[float] = None
    status: str = "CONTROLLED"


class QualityProductionReportDTO(BaseModel):
    """Detailed Statistical Quality Control & Production Metrics."""
    total_produced_volume_m3: float = 0.0
    total_production_batches: int = 0
    active_plants_count: int = 0
    compliance_rate_percent: float = 0.0
    mean_strength_28d_mpa: Optional[float] = None
    median_strength_28d_mpa: Optional[float] = None
    target_fck_mpa: Optional[float] = None
    design_target_mean_fck_prime_mpa: Optional[float] = None
    strength_margin_mpa: Optional[float] = None
    batch_variation_sigma_mpa: Optional[float] = None
    coefficient_of_variation_percent: Optional[float] = None
    tested_batches_count: int = 0
    tested_specimens_count: int = 0
    histogram_intervals: List[Dict[str, Any]] = Field(default_factory=list)
    recent_batches: List[Dict[str, Any]] = Field(default_factory=list)
    mix_performance_matrix: List[GradePerformanceItemDTO] = Field(default_factory=list)


class WeighmentComponentToleranceDTO(BaseModel):
    """IS 4926:2003 Annex E component-level weighment tolerance record."""
    category_code: str
    category_name: str
    tolerance_pct: float
    record_count: int
    compliant_count: int
    non_compliant_count: int
    compliance_rate_pct: Optional[float] = None
    mean_abs_variance_pct: float = 0.0


class RecipeEfficiencyItemDTO(BaseModel):
    """Recipe-level binder intensity and material efficiency record."""
    recipe_code: str
    total_batches: int
    tested_28d_batches: int
    cement_kg_m3: float
    total_binder_kg_m3: float
    actual_wb_ratio: Optional[float] = None
    mean_28d_strength_mpa: Optional[float] = None
    binder_intensity_kg_per_m3_per_mpa: Optional[float] = None
    reliability_status: str = "HIGH_CONFIDENCE"


class MaterialConsumptionReportDTO(BaseModel):
    """Detailed Material Consumption, Weighment Variance & W/B Efficiency."""
    total_material_batched_kg: float = 0.0
    total_binder_batched_kg: float = 0.0
    total_water_batched_kg: float = 0.0
    average_binder_intensity_kg_m3: float = 0.0
    water_to_binder_ratio: Optional[float] = None
    water_to_cement_ratio: Optional[float] = None
    weighment_compliance_rate_percent: Optional[float] = None
    total_evaluated_weighments: int = 0
    tolerance_breaches_count: int = 0
    material_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    component_tolerances: List[WeighmentComponentToleranceDTO] = Field(default_factory=list)
    recipe_efficiency_matrix: List[RecipeEfficiencyItemDTO] = Field(default_factory=list)
    planned_water_kg: float = 0.0
    actual_water_kg: float = 0.0
    raw_water_variance_kg: float = 0.0
    raw_water_variance_pct: float = 0.0
    moisture_telemetry_status: str = "LIMITED"
    moisture_operational_note: str = ""


class ModelMonitoringReportDTO(BaseModel):
    """Model Monitoring, Validation Accuracy & Feature Importance."""
    active_model_version: str = "—"
    algorithm_name: str = "—"
    deployment_status: str = "ACTIVE"
    validation_status: str = "Limited Validation"
    evaluation_samples_count: int = 0
    mae_mpa: Optional[float] = None
    rmse_mpa: Optional[float] = None
    r2_score: Optional[float] = None
    mean_residual_bias_mpa: Optional[float] = None
    residual_std_deviation_mpa: Optional[float] = None
    feature_importances: List[Dict[str, Any]] = Field(default_factory=list)


class RetrospectiveBacktestReportDTO(BaseModel):
    """Retrospective Model Backtest against historical 28-day tested batches."""
    model_version: str = "v1.0.0"
    algorithm_name: str = "Random Forest Regressor"
    evaluation_pairs_count: int = 0
    mae_mpa: Optional[float] = None
    rmse_mpa: Optional[float] = None
    r2_score: Optional[float] = None
    mean_residual_bias_mpa: Optional[float] = None
    residual_std_deviation_mpa: Optional[float] = None
    validation_status: str = "Limited sample"
    sample_size_warning: str = "Only 20 genuine model evaluation pairs are currently available; sample size is insufficient for reliable final model-performance assessment."


class CandidateDetailDTO(BaseModel):
    """Individual candidate evaluated under optimization run."""
    candidate_id: str
    candidate_identifier: str
    is_feasible: bool
    is_pareto_optimal: bool
    predicted_strength_mpa: Optional[float] = None
    strength_margin_mpa: Optional[float] = None
    binder_intensity_kg_m3: float
    water_binder_ratio: float
    yield_m3: float
    cost_per_m3: Optional[float] = None
    cost_status: str = "NOT_CONFIGURED"
    review_status: str = "PENDING_REVIEW"
    reviewed_by_username: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_decision_reason: Optional[str] = None
    review_comments: Optional[str] = None
    constituents: List[Dict[str, Any]] = Field(default_factory=list)
    constraint_diagnostics: List[Dict[str, Any]] = Field(default_factory=list)


class OptimizationRunReportDTO(BaseModel):
    """Optimization Run Context, Pareto Frontier & Candidate Inventory."""
    run_id: str
    recipe_code: str
    recipe_name: Optional[str] = None
    plant_code: str
    grade_code: str
    optimization_objective: str
    run_status: str
    model_version_used: str
    target_characteristic_fck_mpa: float
    target_mean_strength_mpa: float
    total_candidates_evaluated: int
    feasible_candidates_count: int
    pareto_optimal_count: int
    evaluated_at: str
    candidates: List[CandidateDetailDTO] = Field(default_factory=list)


class MasterVsCandidateConstituentComparisonDTO(BaseModel):
    """Constituent comparison item between master baseline and candidate."""
    material_code: str
    material_name: str
    category: str
    master_qty_kg_m3: float
    candidate_qty_kg_m3: float
    delta_qty_kg_m3: float
    delta_percent: Optional[float] = None
    unit_price_inr: Optional[float] = None
    master_cost_inr_m3: Optional[float] = None
    candidate_cost_inr_m3: Optional[float] = None
    cost_delta_inr_m3: Optional[float] = None


class RecipeImpactReportDTO(BaseModel):
    """Master vs Candidate Recipe Delta Analysis."""
    candidate_identifier: str
    is_feasible: bool
    is_pareto_optimal: bool
    master_binder_kg_m3: float
    candidate_binder_kg_m3: float
    binder_delta_kg_m3: float
    binder_delta_percent: float
    master_water_binder_ratio: float
    candidate_water_binder_ratio: float
    scm_replacement_percentage: float
    scm_replacement_delta_percent: float
    constituents: List[MasterVsCandidateConstituentComparisonDTO] = Field(default_factory=list)


class CostImpactReportDTO(BaseModel):
    """Commercial Impact & Cost Evaluation."""
    pricing_status: str = "NOT_CONFIGURED"
    pricing_source_description: str = "Pricing Source: Not Configured"
    effective_date: Optional[str] = None
    master_recipe_cost_per_m3: Optional[float] = None
    candidate_cost_per_m3: Optional[float] = None
    cost_delta_per_m3: Optional[float] = None
    cost_delta_percent: Optional[float] = None
    volume_schedule_configured: bool = False
    annual_volume_m3: Optional[float] = None
    annual_cost_delta_inr: Optional[float] = None


class ActionableFindingItemDTO(BaseModel):
    """Structured actionable finding and engineering review point."""
    finding_title: str
    evidence_text: str
    impact_context: str
    engineering_review_point: str
    source_module: str
    severity: str = "INFO"  # CRITICAL, WARNING, INFO, SUCCESS


class GovernanceReportDTO(BaseModel):
    """Governance, Human Review & Audit Record."""
    review_status: str = "PENDING_REVIEW"
    reviewed_by_username: Optional[str] = None
    reviewed_by_role: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_reason_code: Optional[str] = None
    review_comments: Optional[str] = None
    production_activation_notice: str = "Production activation is outside the current phase."
    audit_event_id: Optional[str] = None


class ProvenanceReportDTO(BaseModel):
    """Authoritative Data Lineage & Provenance References."""
    source_database: str = "acc_rmc_prod"
    recipe_snapshot_version: str = "1.0.0"
    model_snapshot_id: str = "—"
    dataset_training_lineage: str = "StrenghtTrendR5 + FT7R5 + 03.02.26-K"
    governance_audit_table: str = "usr_audit_logs"
    export_engine: str = "ReportLab Platypus / Canonical Serializer"


# =========================================================================
# Canonical Full Dashboard Report DTO
# =========================================================================

class FullDashboardReportDTO(BaseModel):
    """Unified Authoritative Full Dashboard Report DTO."""
    report_metadata: ReportMetadataDTO
    dashboard_context: DashboardScopeContextDTO
    executive_summary: ExecutiveDashboardSummaryDTO
    quality_metrics: QualityProductionReportDTO
    material_consumption: MaterialConsumptionReportDTO
    model_monitoring: ModelMonitoringReportDTO
    retrospective_backtest: Optional[RetrospectiveBacktestReportDTO] = None
    optimization_run: Optional[OptimizationRunReportDTO] = None
    recipe_impact: Optional[RecipeImpactReportDTO] = None
    cost_impact: Optional[CostImpactReportDTO] = None
    governance: Optional[GovernanceReportDTO] = None
    actionable_findings: List[ActionableFindingItemDTO] = Field(default_factory=list)
    provenance: ProvenanceReportDTO
