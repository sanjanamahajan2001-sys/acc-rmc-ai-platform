"""Enterprise Dashboard Reporting & Telemetry API Router.

Provides database-authoritative production telemetry:
- Phase 1: Executive KPIs & Ingestion Telemetry
- Phase 2: Statistical Quality Control (SQC) 28-day concrete strength distributions
- Phase 3: Material Consumption, IS 4926 Weighment Variance & Binder Intensity Index
- Phase 4: Strength Prediction Validation & Model Monitoring (Online Telemetry & Retrospective Backtest)
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.user import User
from src.database.services.cache_token_service import CacheTokenService
from src.security.dependencies import get_current_user, get_db
from src.contracts.reporting.export_models import FullDashboardReportDTO, ExecutiveDashboardSummaryDTO
from src.services.dashboard_export_service import DashboardExportService
from src.services.statistical_quality_service import (
    StatisticalQualityService,
    StrengthDistributionDTO,
    MixPerformanceListDTO,
    StrengthTimelineListDTO,
)
from src.services.material_consumption_service import (
    MaterialConsumptionService,
    MaterialConsumptionSummaryDTO,
    BatchVarianceAnalysisDTO,
    BinderEfficiencyDTO,
)
from src.services.model_monitoring_service import (
    ModelMonitoringService,
    ModelRegistryListDTO,
    PredictionSummaryDTO,
    ActualVsPredictedResponseDTO,
    PredictionErrorTrendResponseDTO,
    ModelFeatureImportanceResponseDTO,
)

router = APIRouter(prefix="/api/v1/reporting", tags=["Reporting & Telemetry"])


class ScopeMetadataDTO(BaseModel):
    plant_code: Optional[str] = None
    recipe_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    cache_token_version: int = 1
    generated_at: str


class OperationalMetricsDTO(BaseModel):
    active_plants_count: int
    total_ingested_batches: int
    operational_batches_count: int
    historical_qc_batches_count: int
    forecast_design_batches_count: int
    quality_compliance_rate_pct: float
    total_cube_tests: int
    total_volume_m3: float
    material_consumptions_count: int
    scope_metadata: ScopeMetadataDTO


class PlantFilterOptionDTO(BaseModel):
    plant_code: str
    plant_name: str
    location: Optional[str] = None


class RecipeFilterOptionDTO(BaseModel):
    recipe_code: str
    recipe_name: str
    grade: Optional[str] = None


class DateRangeDTO(BaseModel):
    min_date: Optional[str] = None
    max_date: Optional[str] = None


class FilterOptionsDTO(BaseModel):
    plants: List[PlantFilterOptionDTO]
    recipes: List[RecipeFilterOptionDTO]
    available_date_range: DateRangeDTO


# =========================================================================
# Phase 1: Executive KPI & Ingestion Telemetry Endpoints (FROZEN)
# =========================================================================

@router.get("/metrics", response_model=OperationalMetricsDTO)
@router.get("/operational-metrics", response_model=OperationalMetricsDTO)
def get_operational_metrics(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OperationalMetricsDTO:
    """Return database-authoritative operational metrics scoped by plant, recipe, and date range."""
    # Active plants count
    plant_q = select(func.count(distinct(Plant.id))).where(Plant.is_deleted == False)
    active_plants_count = db.scalar(plant_q) or 0

    target_plant_id = None
    plant_filter_active = False
    if plant_code:
        p = db.query(Plant).filter(Plant.plant_code == plant_code, Plant.is_deleted == False).first()
        if p:
            target_plant_id = p.id
            plant_filter_active = True
        else:
            token_ver = CacheTokenService.get_token_version("reporting_metrics", db)
            return OperationalMetricsDTO(
                active_plants_count=int(active_plants_count),
                total_ingested_batches=0,
                operational_batches_count=0,
                historical_qc_batches_count=0,
                forecast_design_batches_count=0,
                quality_compliance_rate_pct=100.0,
                total_cube_tests=0,
                total_volume_m3=0.0,
                material_consumptions_count=0,
                scope_metadata=ScopeMetadataDTO(
                    plant_code=plant_code,
                    recipe_code=recipe_code,
                    date_from=date_from,
                    date_to=date_to,
                    cache_token_version=token_ver,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                ),
            )

    target_recipe_id = None
    recipe_filter_active = False
    if recipe_code:
        r = db.query(Recipe).filter(Recipe.recipe_code == recipe_code, Recipe.is_deleted == False).first()
        if r:
            target_recipe_id = r.id
            recipe_filter_active = True
        else:
            token_ver = CacheTokenService.get_token_version("reporting_metrics", db)
            return OperationalMetricsDTO(
                active_plants_count=int(active_plants_count),
                total_ingested_batches=0,
                operational_batches_count=0,
                historical_qc_batches_count=0,
                forecast_design_batches_count=0,
                quality_compliance_rate_pct=100.0,
                total_cube_tests=0,
                total_volume_m3=0.0,
                material_consumptions_count=0,
                scope_metadata=ScopeMetadataDTO(
                    plant_code=plant_code,
                    recipe_code=recipe_code,
                    date_from=date_from,
                    date_to=date_to,
                    cache_token_version=token_ver,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                ),
            )

    # Base batch query
    base_batch_q = db.query(Batch).filter(Batch.is_deleted == False)
    if plant_filter_active:
        base_batch_q = base_batch_q.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        base_batch_q = base_batch_q.filter(Batch.recipe_id == target_recipe_id)

    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
        base_batch_q = base_batch_q.filter(Batch.created_at >= start_dt)
    if date_to:
        end_dt = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
        base_batch_q = base_batch_q.filter(Batch.created_at <= end_dt)

    total_batches = base_batch_q.count()

    # Breakdown by dataset origin
    origins = (
        db.query(Batch.dataset_origin, func.count(Batch.id))
        .filter(Batch.is_deleted == False)
    )
    if plant_filter_active:
        origins = origins.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        origins = origins.filter(Batch.recipe_id == target_recipe_id)
    if date_from:
        origins = origins.filter(Batch.created_at >= start_dt)
    if date_to:
        origins = origins.filter(Batch.created_at <= end_dt)
    origin_counts = dict(origins.group_by(Batch.dataset_origin).all())

    op_batches = origin_counts.get("OPERATIONAL_LOGS", 0)
    qc_batches = origin_counts.get("HISTORICAL_QC", 0)
    forecast_batches = origin_counts.get("FORECAST_DESIGN", 0)

    # Volume calculation
    vol_q = db.query(func.sum(func.coalesce(Batch.actual_quantity_m3, Batch.planned_quantity_m3, 0.0))).filter(Batch.is_deleted == False)
    if plant_filter_active:
        vol_q = vol_q.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        vol_q = vol_q.filter(Batch.recipe_id == target_recipe_id)
    if date_from:
        vol_q = vol_q.filter(Batch.created_at >= start_dt)
    if date_to:
        vol_q = vol_q.filter(Batch.created_at <= end_dt)
    vol_res = vol_q.scalar()
    total_volume = float(vol_res) if vol_res is not None else 0.0

    # Total Cube Tests
    cube_q = (
        db.query(CubeTest)
        .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
        .join(ConcreteSample, CubeSet.sample_id == ConcreteSample.id)
        .join(Batch, ConcreteSample.batch_id == Batch.id)
        .filter(Batch.is_deleted == False)
    )
    if plant_filter_active:
        cube_q = cube_q.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        cube_q = cube_q.filter(Batch.recipe_id == target_recipe_id)
    if date_from:
        cube_q = cube_q.filter(Batch.created_at >= start_dt)
    if date_to:
        cube_q = cube_q.filter(Batch.created_at <= end_dt)
    total_cube_tests = cube_q.count()

    # Quality compliance rate (28-day break tests passing recipe target)
    tested_28d = (
        db.query(CubeTest.compressive_strength_mpa, Recipe.target_strength_mpa)
        .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
        .join(ConcreteSample, CubeSet.sample_id == ConcreteSample.id)
        .join(Batch, ConcreteSample.batch_id == Batch.id)
        .join(Recipe, Batch.recipe_id == Recipe.id)
        .filter(Batch.is_deleted == False, CubeTest.age_days == 28)
    )
    if plant_filter_active:
        tested_28d = tested_28d.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        tested_28d = tested_28d.filter(Batch.recipe_id == target_recipe_id)
    if date_from:
        tested_28d = tested_28d.filter(Batch.created_at >= start_dt)
    if date_to:
        tested_28d = tested_28d.filter(Batch.created_at <= end_dt)
    tested_28d = tested_28d.all()

    if tested_28d:
        passed = sum(1 for strength, target in tested_28d if strength is not None and target is not None and strength >= target)
        compliance_rate = round((passed / len(tested_28d)) * 100.0, 1)
    else:
        compliance_rate = 100.0 if total_batches > 0 else 0.0

    # Material consumptions count
    mat_q = db.query(BatchMaterialConsumption).join(Batch, BatchMaterialConsumption.batch_id == Batch.id).filter(Batch.is_deleted == False)
    if plant_filter_active:
        mat_q = mat_q.filter(Batch.plant_id == target_plant_id)
    if recipe_filter_active:
        mat_q = mat_q.filter(Batch.recipe_id == target_recipe_id)
    if date_from:
        mat_q = mat_q.filter(Batch.created_at >= start_dt)
    if date_to:
        mat_q = mat_q.filter(Batch.created_at <= end_dt)
    mat_consumptions = mat_q.count()

    token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

    return OperationalMetricsDTO(
        active_plants_count=int(active_plants_count),
        total_ingested_batches=total_batches,
        operational_batches_count=op_batches,
        historical_qc_batches_count=qc_batches,
        forecast_design_batches_count=forecast_batches,
        quality_compliance_rate_pct=compliance_rate,
        total_cube_tests=total_cube_tests,
        total_volume_m3=round(total_volume, 2),
        material_consumptions_count=mat_consumptions,
        scope_metadata=ScopeMetadataDTO(
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.get("/filter-options", response_model=FilterOptionsDTO)
def get_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FilterOptionsDTO:
    """Return selectable plant, recipe, and date range options for dashboard filters."""
    plants = db.query(Plant).filter(Plant.is_deleted == False).order_by(Plant.plant_code).all()
    plant_opts = [
        PlantFilterOptionDTO(plant_code=p.plant_code, plant_name=p.plant_name, location=p.location)
        for p in plants
    ]

    recipes = db.query(Recipe).filter(Recipe.is_deleted == False).order_by(Recipe.recipe_code).all()
    recipe_opts = [
        RecipeFilterOptionDTO(recipe_code=r.recipe_code, recipe_name=r.recipe_name, grade=r.grade)
        for r in recipes
    ]

    date_bounds = db.query(
        func.min(Batch.created_at).label("min_date"),
        func.max(Batch.created_at).label("max_date")
    ).filter(Batch.is_deleted == False).first()

    min_d_str = date_bounds.min_date.strftime("%Y-%m-%d") if date_bounds and date_bounds.min_date else None
    max_d_str = date_bounds.max_date.strftime("%Y-%m-%d") if date_bounds and date_bounds.max_date else None

    return FilterOptionsDTO(
        plants=plant_opts,
        recipes=recipe_opts,
        available_date_range=DateRangeDTO(min_date=min_d_str, max_date=max_d_str),
    )


# =========================================================================
# Phase 2: Statistical Quality Control Endpoints (FROZEN)
# =========================================================================

@router.get("/strength-distribution", response_model=StrengthDistributionDTO)
def get_strength_distribution(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrengthDistributionDTO:
    """Return database-authoritative 28-day compressive strength distribution and histogram."""
    return StatisticalQualityService.get_strength_distribution(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/mix-performance", response_model=MixPerformanceListDTO)
def get_mix_performance(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MixPerformanceListDTO:
    """Return concrete recipe/grade performance comparison matrix."""
    return StatisticalQualityService.get_mix_performance(
        db=db,
        plant_code=plant_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/strength-timeline", response_model=StrengthTimelineListDTO)
def get_strength_timeline(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=10, le=200, description="Max number of recent batches"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrengthTimelineListDTO:
    """Return chronological batch strength timeline (7-day and 28-day break tests)."""
    return StatisticalQualityService.get_strength_timeline(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


# =========================================================================
# Phase 3: Material Consumption & Binder Intensity Endpoints (FROZEN)
# =========================================================================

@router.get("/material-consumption", response_model=MaterialConsumptionSummaryDTO)
def get_material_consumption(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialConsumptionSummaryDTO:
    """Return database-authoritative material consumption breakdown (planned, actual, variance kg and kg/m³)."""
    return MaterialConsumptionService.get_material_summary(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/batch-variance", response_model=BatchVarianceAnalysisDTO)
def get_batch_variance(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchVarianceAnalysisDTO:
    """Return IS 4926:2003 Annex E batch weighment variance and batching accuracy analysis."""
    return MaterialConsumptionService.get_batch_variance_analysis(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/binder-efficiency", response_model=BinderEfficiencyDTO)
def get_binder_efficiency(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BinderEfficiencyDTO:
    """Return Water-to-Binder (W/B) ratios and Binder Intensity Index (kg/m³/MPa) with sample-size guardrails."""
    return MaterialConsumptionService.get_efficiency_metrics(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
    )


# =========================================================================
# Phase 4: Strength Prediction Validation & Model Monitoring Endpoints
# =========================================================================

@router.get("/prediction-summary", response_model=PredictionSummaryDTO)
def get_prediction_summary(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    model_version: Optional[str] = Query(None, description="Filter by Model Version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PredictionSummaryDTO:
    """Mode A: Prediction accuracy summary (MAE, MSE, RMSE, R², Bias) for genuine stored production predictions."""
    return ModelMonitoringService.get_prediction_summary(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        model_version=model_version,
    )


@router.get("/actual-vs-predicted", response_model=ActualVsPredictedResponseDTO)
def get_actual_vs_predicted(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    model_version: Optional[str] = Query(None, description="Filter by Model Version"),
    limit: int = Query(500, ge=10, le=1000, description="Max number of evaluation pairs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActualVsPredictedResponseDTO:
    """Mode A: Actual vs Predicted evaluation scatter pairs for genuine stored production predictions."""
    return ModelMonitoringService.get_actual_vs_predicted(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        model_version=model_version,
        limit=limit,
    )


@router.get("/prediction-error-trend", response_model=PredictionErrorTrendResponseDTO)
def get_prediction_error_trend(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    model_version: Optional[str] = Query(None, description="Filter by Model Version"),
    rolling_window: int = Query(10, ge=3, le=50, description="Moving average rolling window size"),
    limit: int = Query(200, ge=10, le=500, description="Max number of trend items"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PredictionErrorTrendResponseDTO:
    """Mode A: Chronological prediction error trend with rolling MAE over sliding window."""
    return ModelMonitoringService.get_prediction_error_trend(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        model_version=model_version,
        rolling_window=rolling_window,
        limit=limit,
    )


@router.get("/model-features", response_model=ModelFeatureImportanceResponseDTO)
def get_model_features(
    model_version: Optional[str] = Query(None, description="Model Version (defaults to active model)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelFeatureImportanceResponseDTO:
    """Extract canonical 12-feature importances or linear coefficients from serialized model artifact."""
    return ModelMonitoringService.get_feature_importance(
        db=db,
        model_version=model_version,
    )


@router.get("/model-metadata", response_model=ModelRegistryListDTO)
def get_model_metadata(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelRegistryListDTO:
    """Return model registry inventory, versions, checksums, and deployment statuses."""
    return ModelMonitoringService.get_registered_models(db=db)


@router.get("/model-backtest", response_model=ActualVsPredictedResponseDTO)
def get_model_backtest(
    model_version: Optional[str] = Query(None, description="Model Version (defaults to active model)"),
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(500, ge=10, le=1000, description="Max number of evaluation pairs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActualVsPredictedResponseDTO:
    """Mode B: Retrospective Model Backtest against historical 28-day break tests.
    
    Clearly tagged as RETROSPECTIVE_BACKTEST. Does NOT insert records into ai_predictions.
    """
    return ModelMonitoringService.get_model_backtest(
        db=db,
        model_version=model_version,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )



# =========================================================================
# Final Reporting Workstream: Full Dashboard Summary & Authoritative Export
# =========================================================================

@router.get("/executive-summary", response_model=ExecutiveDashboardSummaryDTO)
def get_executive_summary(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    run_id: Optional[str] = Query(None, description="Optional Optimization Run ID"),
    candidate_id: Optional[str] = Query(None, description="Optional Candidate ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutiveDashboardSummaryDTO:
    """Return factual 4-group Executive Dashboard Summary derived from authoritative records."""
    report_dto = DashboardExportService.build_dashboard_report_dto(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        run_id=run_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )
    return report_dto.executive_summary


@router.get("/export/json", response_model=FullDashboardReportDTO)
def export_dashboard_json(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    run_id: Optional[str] = Query(None, description="Optional Optimization Run ID"),
    candidate_id: Optional[str] = Query(None, description="Optional Candidate ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FullDashboardReportDTO:
    """Export complete canonical machine-readable dashboard report (JSON format)."""
    return DashboardExportService.build_dashboard_report_dto(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        run_id=run_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )


@router.get("/export/pdf")
def export_dashboard_pdf(
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    recipe_code: Optional[str] = Query(None, description="Filter by Recipe Code"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    run_id: Optional[str] = Query(None, description="Optional Optimization Run ID"),
    candidate_id: Optional[str] = Query(None, description="Optional Candidate ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download authoritative multi-page executive PDF report."""
    report_dto = DashboardExportService.build_dashboard_report_dto(
        db=db,
        plant_code=plant_code,
        recipe_code=recipe_code,
        date_from=date_from,
        date_to=date_to,
        run_id=run_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )
    pdf_bytes = DashboardExportService.render_pdf(report_dto)
    
    scope_str = plant_code or "AllPlants"
    date_str = date.today().isoformat()
    filename = f"ACC_RMC_Operations_Report_{scope_str}_{date_str}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
