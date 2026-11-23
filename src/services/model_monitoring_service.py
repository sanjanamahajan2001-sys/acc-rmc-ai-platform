"""Strength Prediction Validation & Model Monitoring Service.

Implements database-authoritative business logic for:
1. Mode A: Production Stored Prediction Monitoring (Online Telemetry from ai_predictions)
2. Mode B: Retrospective Model Backtest (Offline Historical Model Validation)
3. Statistical Model Accuracy Metrics (MAE, MSE, RMSE, R², Mean Residual, Residual Std Dev)
4. Temporal Error Trends & Rolling MAE (Sliding Window = 10)
5. Canonical 12-Feature Importance Extraction & Mapping
6. Model Registry Inventory & Lineage Tracking

ZERO FABRICATED METRICS. STRICT SEPARATION OF STORED AND RETROSPECTIVE PREDICTIONS.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from src.database.models.ai import FeatureVector, ModelRegistry, Prediction
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.services.cache_token_service import CacheTokenService
from src.ml.training.eligibility import TrainingEligibilityService, MLBatchObservation


# =========================================================================
# DTO SCHEMAS
# =========================================================================

class ModelMetadataItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_registry_id: str
    model_name: str
    model_version: str
    framework: str
    algorithm: str
    feature_schema_version: str
    training_dataset_version: Optional[str] = None
    artifact_location: Optional[str] = None
    checksum: Optional[str] = None
    deployment_status: str  # ACTIVE, CANDIDATE, RETIRED
    deployment_timestamp: str


class ModelRegistryListDTO(BaseModel):
    models: List[ModelMetadataItemDTO]
    total_models: int
    active_model_version: Optional[str] = None


class StatisticalMetricsDTO(BaseModel):
    sample_count: int = Field(description="Total valid prediction-actual pairs evaluated")
    mae_mpa: Optional[float] = Field(None, description="Mean Absolute Error (MPa): mean(|predicted - actual|)")
    mse_mpa2: Optional[float] = Field(None, description="Mean Squared Error (MPa²): mean((predicted - actual)²)")
    rmse_mpa: Optional[float] = Field(None, description="Root Mean Squared Error (MPa): sqrt(MSE)")
    r2_score: Optional[float] = Field(None, description="Coefficient of Determination: 1 - SSE/SST (null if SST=0 or N<2)")
    mean_residual_mpa: Optional[float] = Field(None, description="Mean Residual / Bias (MPa): mean(predicted - actual)")
    residual_std_dev_mpa: Optional[float] = Field(None, description="Sample Standard Deviation of residuals (null if N<2)")
    min_residual_mpa: Optional[float] = Field(None, description="Minimum residual (maximum under-prediction)")
    max_residual_mpa: Optional[float] = Field(None, description="Maximum residual (maximum over-prediction)")
    mean_actual_strength_mpa: Optional[float] = Field(None, description="Mean ground truth 28-day break strength")
    mean_predicted_strength_mpa: Optional[float] = Field(None, description="Mean predicted strength")


class PredictionSourceBreakdownDTO(BaseModel):
    total_evaluated: int = Field(default=0, description="Total predictions evaluated")
    model_predictions_count: int = Field(default=0, description="Genuine model inferences (N_model)")
    fallback_predictions_count: int = Field(default=0, description="Heuristic fallback estimates (N_fallback)")
    fallback_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count of fallback instances by root cause")


class ModelMonitoringScopeDTO(BaseModel):
    evaluation_type: str = Field(description="PRODUCTION_STORED or RETROSPECTIVE_BACKTEST")
    plant_code: Optional[str] = None
    recipe_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    date_filter_applied_to: str = "production_date"
    model_version: Optional[str] = None
    status: str = Field(description="OK, NO_STORED_PREDICTIONS_IN_RANGE, NO_ELIGIBLE_BATCHES_IN_RANGE, etc.")
    disclaimer: Optional[str] = None
    eligible_count: int = 0
    total_predictions_count: Optional[int] = None
    model_predictions_count: Optional[int] = None
    fallback_predictions_count: Optional[int] = None
    excluded_records_count: int = 0
    cache_token_version: int = 1
    generated_at: str


class PredictionSummaryDTO(BaseModel):
    scope: ModelMonitoringScopeDTO
    metrics: StatisticalMetricsDTO
    active_model: Optional[ModelMetadataItemDTO] = None
    selected_model: Optional[ModelMetadataItemDTO] = None
    disaggregated_summary: Optional[PredictionSourceBreakdownDTO] = None
    fallback_metrics: Optional[StatisticalMetricsDTO] = None


class ActualVsPredictedItemDTO(BaseModel):
    batch_id: str
    batch_number: str
    plant_code: str
    recipe_code: str
    grade: Optional[str] = None
    production_timestamp: str
    testing_date: Optional[str] = None
    actual_strength_mpa: float
    predicted_strength_mpa: float
    residual_mpa: float = Field(description="predicted - actual (positive = over-predicted, negative = under-predicted)")
    abs_error_mpa: float = Field(description="|predicted - actual|")
    model_version: str
    prediction_source: str = Field(default="ML_MODEL", description="ML_MODEL or HEURISTIC")
    fallback_reason: Optional[str] = None


class ActualVsPredictedResponseDTO(BaseModel):
    scope: ModelMonitoringScopeDTO
    summary_metrics: StatisticalMetricsDTO
    items: List[ActualVsPredictedItemDTO]
    total_items: int


class PredictionErrorTrendItemDTO(BaseModel):
    batch_number: str
    production_timestamp: str
    testing_date: Optional[str] = None
    actual_strength_mpa: float
    predicted_strength_mpa: float
    residual_mpa: float
    abs_error_mpa: float
    rolling_mae_mpa: Optional[float] = Field(None, description="Moving average MAE over preceding sliding window")


class PredictionErrorTrendResponseDTO(BaseModel):
    scope: ModelMonitoringScopeDTO
    items: List[PredictionErrorTrendItemDTO]
    total_items: int
    rolling_window_size: int = 10
    operational_monitoring_threshold_mpa: float = 3.0
    threshold_description: str = "Operational monitoring threshold for alert triggering (not an IS 456 material limit)"


class FeatureImportanceItemDTO(BaseModel):
    feature_name: str
    display_name: str
    importance_weight: float = Field(description="Relative importance weight (normalized 0.0 to 1.0 or raw weight)")
    raw_value: Optional[float] = None
    unit: str


class ModelFeatureImportanceResponseDTO(BaseModel):
    model_version: str
    algorithm: str
    feature_importance_available: bool
    status_code: str  # OK, FEATURE_IMPORTANCE_NOT_AVAILABLE, MODEL_NOT_FOUND
    message: str
    features: List[FeatureImportanceItemDTO]


# Canonical Feature Display Mappings
CANONICAL_FEATURE_METADATA: Dict[str, Dict[str, str]] = {
    "cement_kg_m3": {"display_name": "Cement Content", "unit": "kg/m³"},
    "flyash_kg_m3": {"display_name": "Fly Ash (PFA)", "unit": "kg/m³"},
    "ggbs_kg_m3": {"display_name": "GGBS Slag", "unit": "kg/m³"},
    "water_kg_m3": {"display_name": "Batch Water", "unit": "kg/m³"},
    "admixture_kg_m3": {"display_name": "Chemical Admixture", "unit": "kg/m³"},
    "fine_aggregate_kg_m3": {"display_name": "Fine Aggregate (Sand)", "unit": "kg/m³"},
    "coarse_aggregate_kg_m3": {"display_name": "Coarse Aggregate", "unit": "kg/m³"},
    "total_binder_kg_m3": {"display_name": "Total Cementitious Binder", "unit": "kg/m³"},
    "water_binder_ratio": {"display_name": "Water-to-Binder Ratio (W/B)", "unit": "ratio"},
    "water_cement_ratio": {"display_name": "Water-to-Cement Ratio (W/C)", "unit": "ratio"},
    "plant_code": {"display_name": "Production Plant Origin", "unit": "categorical"},
    "recipe_code": {"display_name": "Mix Design / Recipe", "unit": "categorical"},
}

ORDERED_CANONICAL_FEATURES = [
    "cement_kg_m3",
    "flyash_kg_m3",
    "ggbs_kg_m3",
    "water_kg_m3",
    "admixture_kg_m3",
    "fine_aggregate_kg_m3",
    "coarse_aggregate_kg_m3",
    "total_binder_kg_m3",
    "water_binder_ratio",
    "water_cement_ratio",
    "plant_code",
    "recipe_code",
]


# =========================================================================
# CORE STATISTICAL CALCULATION ENGINE
# =========================================================================

class StatisticalMathEngine:
    """Rigorous server-side statistical computations for model evaluation."""

    @staticmethod
    def calculate_metrics(
        pairs: List[Tuple[float, float]],  # List of (actual, predicted)
    ) -> Tuple[StatisticalMetricsDTO, int]:
        """Compute MAE, MSE, RMSE, R², Mean Residual, and Residual Std Dev with strict edge-case handling.
        
        Residual convention: e_i = predicted_i - actual_i
        Positive residual = model over-predicted
        Negative residual = model under-predicted
        """
        valid_pairs: List[Tuple[float, float]] = []
        excluded_count = 0

        for y, y_hat in pairs:
            if y is None or y_hat is None:
                excluded_count += 1
                continue
            try:
                y_f = float(y)
                y_hat_f = float(y_hat)
                if not (math.isfinite(y_f) and math.isfinite(y_hat_f)) or math.isnan(y_f) or math.isnan(y_hat_f):
                    excluded_count += 1
                    continue
                valid_pairs.append((y_f, y_hat_f))
            except (ValueError, TypeError):
                excluded_count += 1
                continue

        n = len(valid_pairs)
        if n == 0:
            return StatisticalMetricsDTO(
                sample_count=0,
                mae_mpa=None,
                mse_mpa2=None,
                rmse_mpa=None,
                r2_score=None,
                mean_residual_mpa=None,
                residual_std_dev_mpa=None,
                min_residual_mpa=None,
                max_residual_mpa=None,
                mean_actual_strength_mpa=None,
                mean_predicted_strength_mpa=None,
            ), excluded_count

        actuals = np.array([p[0] for p in valid_pairs], dtype=np.float64)
        predicteds = np.array([p[1] for p in valid_pairs], dtype=np.float64)
        residuals = predicteds - actuals  # Sign convention: predicted - actual
        abs_errors = np.abs(residuals)
        sq_errors = residuals ** 2

        mae = float(np.mean(abs_errors))
        mse = float(np.mean(sq_errors))
        rmse = float(math.sqrt(mse))
        mean_res = float(np.mean(residuals))
        min_res = float(np.min(residuals))
        max_res = float(np.max(residuals))
        mean_act = float(np.mean(actuals))
        mean_pred = float(np.mean(predicteds))

        # R² Calculation: 1 - SSE / SST
        # SSE = sum((actual - predicted)^2)
        # SST = sum((actual - mean_actual)^2)
        sse = float(np.sum(sq_errors))
        sst = float(np.sum((actuals - mean_act) ** 2))

        if n < 2 or sst <= 1e-9:
            # Undefined variance or single sample
            r2_val = None
            res_std = None
        else:
            r2_val = float(1.0 - (sse / sst))
            # Sample standard deviation (ddof=1)
            res_std = float(np.std(residuals, ddof=1))

        if n == 1:
            # Special case N=1
            mae = float(abs_errors[0])
            mse = float(sq_errors[0])
            rmse = float(abs_errors[0])
            mean_res = float(residuals[0])
            res_std = None
            r2_val = None

        return StatisticalMetricsDTO(
            sample_count=n,
            mae_mpa=round(mae, 3) if mae is not None else None,
            mse_mpa2=round(mse, 3) if mse is not None else None,
            rmse_mpa=round(rmse, 3) if rmse is not None else None,
            r2_score=round(r2_val, 4) if r2_val is not None else None,
            mean_residual_mpa=round(mean_res, 3) if mean_res is not None else None,
            residual_std_dev_mpa=round(res_std, 3) if res_std is not None else None,
            min_residual_mpa=round(min_res, 2) if min_res is not None else None,
            max_residual_mpa=round(max_res, 2) if max_res is not None else None,
            mean_actual_strength_mpa=round(mean_act, 2) if mean_act is not None else None,
            mean_predicted_strength_mpa=round(mean_pred, 2) if mean_pred is not None else None,
        ), excluded_count


# =========================================================================
# MODEL MONITORING SERVICE
# =========================================================================

class ModelMonitoringService:
    """Authoritative service providing Mode A (Production Stored) and Mode B (Retrospective Backtest) evaluations."""

    @classmethod
    def get_registered_models(cls, db: Session) -> ModelRegistryListDTO:
        """Fetch all models in ai_model_registry with deployment statuses and metadata."""
        models = db.query(ModelRegistry).filter(ModelRegistry.is_deleted == False).order_by(ModelRegistry.deployment_timestamp.desc()).all()

        active_ver = None
        items: List[ModelMetadataItemDTO] = []
        for m in models:
            if m.deployment_status == "ACTIVE":
                active_ver = m.model_version
            items.append(
                ModelMetadataItemDTO(
                    model_registry_id=str(m.id),
                    model_name=m.model_name,
                    model_version=m.model_version,
                    framework=m.framework,
                    algorithm=m.algorithm,
                    feature_schema_version=m.feature_schema_version,
                    training_dataset_version=m.training_dataset_version,
                    artifact_location=m.artifact_location,
                    checksum=m.checksum,
                    deployment_status=m.deployment_status,
                    deployment_timestamp=m.deployment_timestamp.isoformat() if m.deployment_timestamp else "",
                )
            )

        return ModelRegistryListDTO(
            models=items,
            total_models=len(items),
            active_model_version=active_ver,
        )

    @classmethod
    def _resolve_model(cls, db: Session, model_version: Optional[str] = None) -> Tuple[Optional[ModelRegistry], Optional[ModelMetadataItemDTO]]:
        """Resolve specific model or active model from registry."""
        if model_version:
            model_orm = db.query(ModelRegistry).filter(
                ModelRegistry.model_version == model_version,
                ModelRegistry.is_deleted == False
            ).first()
        else:
            model_orm = db.query(ModelRegistry).filter(
                ModelRegistry.deployment_status == "ACTIVE",
                ModelRegistry.is_deleted == False
            ).first()

        if not model_orm:
            return None, None

        dto = ModelMetadataItemDTO(
            model_registry_id=str(model_orm.id),
            model_name=model_orm.model_name,
            model_version=model_orm.model_version,
            framework=model_orm.framework,
            algorithm=model_orm.algorithm,
            feature_schema_version=model_orm.feature_schema_version,
            training_dataset_version=model_orm.training_dataset_version,
            artifact_location=model_orm.artifact_location,
            checksum=model_orm.checksum,
            deployment_status=model_orm.deployment_status,
            deployment_timestamp=model_orm.deployment_timestamp.isoformat() if model_orm.deployment_timestamp else "",
        )
        return model_orm, dto

    # ---------------------------------------------------------------------
    # MODE A: PRODUCTION STORED PREDICTION MONITORING
    # ---------------------------------------------------------------------

    @classmethod
    def _query_stored_prediction_pairs(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        model_version: Optional[str] = None,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Join genuine stored predictions in ai_predictions with authoritative 28-day break tests.
        
        Join: ai_predictions -> ai_feature_vectors -> prd_batches -> lab_samples -> lab_cube_sets -> lab_cube_tests (28d)
        """
        from src.database.models.ai import PredictionAudit
        q = (
            db.query(
                Batch.id.label("batch_id"),
                Batch.batch_number,
                Plant.plant_code,
                Recipe.recipe_code,
                Recipe.grade,
                Batch.created_at.label("production_timestamp"),
                CubeTest.test_timestamp.label("testing_date"),
                CubeTest.compressive_strength_mpa.label("actual_strength_mpa"),
                Prediction.predicted_strength_mpa,
                Prediction.model_version,
                Prediction.prediction_source,
                Prediction.fallback_reason,
                PredictionAudit.metadata_json.label("audit_metadata"),
            )
            .join(FeatureVector, Prediction.feature_vector_id == FeatureVector.id)
            .join(Batch, FeatureVector.batch_id == Batch.id)
            .join(Plant, Batch.plant_id == Plant.id)
            .join(Recipe, Batch.recipe_id == Recipe.id)
            .join(ConcreteSample, ConcreteSample.batch_id == Batch.id)
            .join(CubeSet, CubeSet.sample_id == ConcreteSample.id)
            .join(CubeTest, CubeTest.cube_set_id == CubeSet.id)
            .outerjoin(PredictionAudit, PredictionAudit.prediction_id == Prediction.id)
            .filter(
                Batch.is_deleted == False,
                Prediction.is_deleted == False,
                Prediction.prediction_type == "STRENGTH_28D",
                CubeTest.age_days == 28,
            )
        )

        if plant_code:
            q = q.filter(Plant.plant_code == plant_code)
        if recipe_code:
            q = q.filter(Recipe.recipe_code == recipe_code)
        if model_version:
            q = q.filter(Prediction.model_version == model_version)
        if date_from:
            start_dt = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
            q = q.filter(Batch.created_at >= start_dt)
        if date_to:
            end_dt = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
            q = q.filter(Batch.created_at <= end_dt)

        # Order chronologically by production date
        q = q.order_by(Batch.created_at.asc())
        rows = q.all()

        results: List[Dict[str, Any]] = []
        for r in rows:
            src = getattr(r, "prediction_source", None)
            fb_reason = getattr(r, "fallback_reason", None)
            if not src or src not in ["ML_MODEL", "HEURISTIC", "MODEL"]:
                audit_meta = getattr(r, "audit_metadata", None) or {}
                if isinstance(audit_meta, dict):
                    src = audit_meta.get("prediction_source", "HEURISTIC" if float(r.predicted_strength_mpa) == 17.7 else "ML_MODEL")
                    fb_reason = fb_reason or audit_meta.get("fallback_reason")
                else:
                    src = "HEURISTIC" if float(r.predicted_strength_mpa) == 17.7 else "ML_MODEL"
            elif src == "MODEL":
                src = "ML_MODEL"

            if source_filter and src != source_filter:
                continue

            results.append({
                "batch_id": str(r.batch_id),
                "batch_number": r.batch_number,
                "plant_code": r.plant_code,
                "recipe_code": r.recipe_code,
                "grade": r.grade,
                "production_timestamp": r.production_timestamp.isoformat() if r.production_timestamp else "",
                "testing_date": r.testing_date.isoformat() if r.testing_date else None,
                "actual_strength_mpa": float(r.actual_strength_mpa),
                "predicted_strength_mpa": float(r.predicted_strength_mpa),
                "model_version": r.model_version,
                "prediction_source": src,
                "fallback_reason": fb_reason,
            })
        return results

    @classmethod
    def get_prediction_summary(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        model_version: Optional[str] = None,
    ) -> PredictionSummaryDTO:
        """Mode A: Prediction Accuracy Summary for Genuine Stored Production Predictions (Excluding Heuristic Fallbacks)."""
        _, active_dto = cls._resolve_model(db, None)
        _, selected_dto = cls._resolve_model(db, model_version) if model_version else (None, None)

        all_rows = cls._query_stored_prediction_pairs(
            db,
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            model_version=model_version,
            source_filter=None,
        )

        model_rows = [r for r in all_rows if r["prediction_source"] == "ML_MODEL"]
        fallback_rows = [r for r in all_rows if r["prediction_source"] != "ML_MODEL"]

        # Calculate metrics strictly on genuine ML_MODEL predictions
        model_pairs = [(r["actual_strength_mpa"], r["predicted_strength_mpa"]) for r in model_rows]
        model_metrics, excluded_cnt = StatisticalMathEngine.calculate_metrics(model_pairs)

        # Fallback metrics calculated separately
        fallback_pairs = [(r["actual_strength_mpa"], r["predicted_strength_mpa"]) for r in fallback_rows]
        fallback_metrics, _ = StatisticalMathEngine.calculate_metrics(fallback_pairs)

        fb_breakdown: Dict[str, int] = {}
        for r in fallback_rows:
            reason = r.get("fallback_reason") or "INCOMPLETE_INPUT_FEATURES"
            if "cement" in reason:
                clean_r = "MISSING_CEMENT_WEIGHT"
            elif "aggregate" in reason or "fine" in reason or "coarse" in reason:
                clean_r = "MISSING_AGGREGATE_WEIGHT"
            else:
                clean_r = "UNSPECIFIED_FEATURE_OMISSION"
            fb_breakdown[clean_r] = fb_breakdown.get(clean_r, 0) + 1

        disaggregated = PredictionSourceBreakdownDTO(
            total_evaluated=len(all_rows),
            model_predictions_count=len(model_rows),
            fallback_predictions_count=len(fallback_rows),
            fallback_breakdown=fb_breakdown,
        )

        status = "OK" if model_metrics.sample_count > 0 else "NO_STORED_PREDICTIONS_IN_RANGE"
        token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

        scope = ModelMonitoringScopeDTO(
            evaluation_type="PRODUCTION_STORED",
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            date_filter_applied_to="production_date",
            model_version=model_version or (active_dto.model_version if active_dto else None),
            status=status,
            disclaimer="Evaluates genuine online production predictions stored in ai_predictions. Heuristic fallbacks are disaggregated.",
            eligible_count=len(model_rows),
            total_predictions_count=len(all_rows),
            model_predictions_count=len(model_rows),
            fallback_predictions_count=len(fallback_rows),
            excluded_records_count=excluded_cnt,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return PredictionSummaryDTO(
            scope=scope,
            metrics=model_metrics,
            active_model=active_dto,
            selected_model=selected_dto,
            disaggregated_summary=disaggregated,
            fallback_metrics=fallback_metrics,
        )

    @classmethod
    def get_actual_vs_predicted(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        model_version: Optional[str] = None,
        limit: int = 500,
    ) -> ActualVsPredictedResponseDTO:
        """Mode A: Actual vs Predicted Scatter Pairs for Stored Production Telemetry."""
        all_rows = cls._query_stored_prediction_pairs(
            db,
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            model_version=model_version,
            source_filter=None,
        )

        model_rows = [r for r in all_rows if r["prediction_source"] == "ML_MODEL"]
        fallback_rows = [r for r in all_rows if r["prediction_source"] != "ML_MODEL"]

        # Calculate metrics strictly on genuine ML_MODEL predictions
        model_pairs = [(r["actual_strength_mpa"], r["predicted_strength_mpa"]) for r in model_rows]
        metrics, excluded_cnt = StatisticalMathEngine.calculate_metrics(model_pairs)

        items: List[ActualVsPredictedItemDTO] = []
        for r in all_rows[:limit]:
            act = r["actual_strength_mpa"]
            pred = r["predicted_strength_mpa"]
            res = round(pred - act, 2)
            abs_err = round(abs(pred - act), 2)
            items.append(
                ActualVsPredictedItemDTO(
                    batch_id=r["batch_id"],
                    batch_number=r["batch_number"],
                    plant_code=r["plant_code"],
                    recipe_code=r["recipe_code"],
                    grade=r["grade"],
                    production_timestamp=r["production_timestamp"],
                    testing_date=r["testing_date"],
                    actual_strength_mpa=act,
                    predicted_strength_mpa=pred,
                    residual_mpa=res,
                    abs_error_mpa=abs_err,
                    model_version=r["model_version"],
                    prediction_source=r["prediction_source"],
                    fallback_reason=r.get("fallback_reason"),
                )
            )

        status = "OK" if metrics.sample_count > 0 else "NO_STORED_PREDICTIONS_IN_RANGE"
        token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

        scope = ModelMonitoringScopeDTO(
            evaluation_type="PRODUCTION_STORED",
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            date_filter_applied_to="production_date",
            model_version=model_version,
            status=status,
            disclaimer="Evaluates genuine online production predictions stored in ai_predictions. Fallback points displayed with operational tags.",
            eligible_count=len(model_rows),
            total_predictions_count=len(all_rows),
            model_predictions_count=len(model_rows),
            fallback_predictions_count=len(fallback_rows),
            excluded_records_count=excluded_cnt,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return ActualVsPredictedResponseDTO(
            scope=scope,
            summary_metrics=metrics,
            items=items,
            total_items=len(items),
        )

    @classmethod
    def get_prediction_error_trend(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        model_version: Optional[str] = None,
        rolling_window: int = 10,
        limit: int = 200,
    ) -> PredictionErrorTrendResponseDTO:
        """Mode A: Chronological Prediction Error Sequence and Rolling MAE for Genuine Stored Predictions."""
        rows = cls._query_stored_prediction_pairs(
            db,
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            model_version=model_version,
            source_filter="ML_MODEL",
        )

        items: List[PredictionErrorTrendItemDTO] = []
        recent_rows = rows[:limit]
        abs_err_history: List[float] = []

        for r in recent_rows:
            act = r["actual_strength_mpa"]
            pred = r["predicted_strength_mpa"]
            res = round(pred - act, 2)
            abs_err = round(abs(pred - act), 2)
            abs_err_history.append(abs_err)

            # Compute rolling MAE over window
            window_slice = abs_err_history[-rolling_window:]
            rolling_mae = round(float(np.mean(window_slice)), 2) if window_slice else None

            items.append(
                PredictionErrorTrendItemDTO(
                    batch_number=r["batch_number"],
                    production_timestamp=r["production_timestamp"],
                    testing_date=r["testing_date"],
                    actual_strength_mpa=act,
                    predicted_strength_mpa=pred,
                    residual_mpa=res,
                    abs_error_mpa=abs_err,
                    rolling_mae_mpa=rolling_mae,
                )
            )

        status = "OK" if len(items) > 0 else "NO_STORED_PREDICTIONS_IN_RANGE"
        token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

        scope = ModelMonitoringScopeDTO(
            evaluation_type="PRODUCTION_STORED",
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            date_filter_applied_to="production_date",
            model_version=model_version,
            status=status,
            disclaimer="Evaluates genuine online production predictions stored in ai_predictions.",
            eligible_count=len(items),
            excluded_records_count=0,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return PredictionErrorTrendResponseDTO(
            scope=scope,
            items=items,
            total_items=len(items),
            rolling_window_size=rolling_window,
            operational_monitoring_threshold_mpa=3.0,
            threshold_description="Operational monitoring threshold for alert triggering (not an IS 456 material limit)",
        )

    # ---------------------------------------------------------------------
    # MODE B: RETROSPECTIVE MODEL BACKTEST
    # ---------------------------------------------------------------------

    @classmethod
    def _extract_backtest_observations(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[MLBatchObservation], int]:
        """Extract all batches with material consumption and 28-day break tests for retrospective backtesting.
        
        Evaluates the full ground-truth population of 28d-tested concrete batches.
        """
        query = db.query(Batch).filter(Batch.is_deleted == False)

        if plant_code:
            query = query.join(Plant, Batch.plant_id == Plant.id).filter(Plant.plant_code == plant_code)

        if recipe_code:
            query = query.join(Recipe, Batch.recipe_id == Recipe.id).filter(Recipe.recipe_code == recipe_code)

        if date_from:
            start_dt = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
            query = query.filter(Batch.production_start_time >= start_dt)

        if date_to:
            end_dt = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
            query = query.filter(Batch.production_start_time <= end_dt)

        batches = query.all()
        extracted: List[MLBatchObservation] = []
        excluded_count = 0

        for b in batches:
            vol = float(b.actual_quantity_m3 or b.planned_quantity_m3 or 0.0)
            if vol <= 0.0:
                excluded_count += 1
                continue

            plant_cd = b.plant.plant_code if getattr(b, "plant", None) else "UNKNOWN_PLANT"
            recipe_cd = b.recipe.recipe_code if getattr(b, "recipe", None) else "UNKNOWN_RECIPE"

            mat_dict: Dict[str, float] = {
                "cement": 0.0,
                "flyash": 0.0,
                "ggbs": 0.0,
                "water": 0.0,
                "admixture": 0.0,
                "fine_aggregate": 0.0,
                "coarse_aggregate": 0.0,
            }

            for mc in b.consumptions:
                qty_raw = float(mc.actual_quantity or mc.planned_quantity or 0.0)
                qty_kg_m3 = float(mc.quantity_kg_per_m3) if mc.quantity_kg_per_m3 is not None else (qty_raw / vol)
                mat_obj = getattr(mc, "material", None)
                src_code = mc.source_material_code or (mat_obj.material_code if mat_obj else "")
                mat_name = mat_obj.material_name if mat_obj else ""
                cat = TrainingEligibilityService.classify_material_code(src_code, mat_name)
                if cat and cat in mat_dict:
                    mat_dict[cat] += qty_kg_m3

            cement = mat_dict["cement"]
            flyash = mat_dict["flyash"]
            ggbs = mat_dict["ggbs"]
            water = mat_dict["water"]
            admixture = mat_dict["admixture"]
            fine_agg = mat_dict["fine_aggregate"]
            coarse_agg = mat_dict["coarse_aggregate"]

            total_binder = cement + flyash + ggbs
            if total_binder <= 0.0:
                excluded_count += 1
                continue

            if water <= 0.0:
                if total_binder > 0:
                    water = round(total_binder * 0.45, 2)
                else:
                    excluded_count += 1
                    continue

            if fine_agg <= 0.0 or coarse_agg <= 0.0:
                excluded_count += 1
                continue

            wb_ratio = round(water / total_binder, 4)
            wc_ratio = round(water / cement, 4) if cement > 0.0 else wb_ratio

            cube_tests_28d: List[CubeTest] = []
            sample_records = db.query(ConcreteSample).filter(
                ConcreteSample.batch_id == b.id,
                ConcreteSample.is_deleted == False,
            ).all()

            for s in sample_records:
                for cset in s.cube_sets:
                    for ct in cset.cube_tests:
                        if ct.age_days == 28 and ct.compressive_strength_mpa is not None:
                            val = float(ct.compressive_strength_mpa)
                            if val > 0.0 and (ct.failure_mode != "REJECTED_SPECIMEN"):
                                cube_tests_28d.append(ct)

            if not cube_tests_28d:
                excluded_count += 1
                continue

            strengths_list = [float(ct.compressive_strength_mpa) for ct in cube_tests_28d]
            authoritative_target = round(sum(strengths_list) / len(strengths_list), 2)

            obs = MLBatchObservation(
                batch_id=str(b.id),
                batch_number=b.batch_number,
                dataset_origin=b.dataset_origin,
                plant_code=plant_cd,
                recipe_code=recipe_cd,
                batch_volume_m3=round(vol, 2),
                cement_kg_m3=round(cement, 2),
                flyash_kg_m3=round(flyash, 2),
                ggbs_kg_m3=round(ggbs, 2),
                water_kg_m3=round(water, 2),
                admixture_kg_m3=round(admixture, 2),
                fine_aggregate_kg_m3=round(fine_agg, 2),
                coarse_aggregate_kg_m3=round(coarse_agg, 2),
                total_binder_kg_m3=round(total_binder, 2),
                water_binder_ratio=wb_ratio,
                water_cement_ratio=wc_ratio,
                target_28d_strength_mpa=authoritative_target,
                specimen_count_28d=len(strengths_list),
                specimen_strengths_28d=tuple(strengths_list),
                production_timestamp=b.production_start_time,
            )
            extracted.append(obs)

        return extracted, excluded_count

    @classmethod
    def get_model_backtest(
        cls,
        db: Session,
        model_version: Optional[str] = None,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 500,
    ) -> ActualVsPredictedResponseDTO:
        """Mode B: Retrospective Model Backtest against historical 28-day tested batches.
        
        Evaluates the selected (or active) registered model artifact retrospectively.
        DOES NOT INSERT RECORDS INTO ai_predictions.
        """
        model_orm, model_dto = cls._resolve_model(db, model_version)
        token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

        if not model_orm or not model_orm.artifact_location or not os.path.exists(model_orm.artifact_location):
            scope = ModelMonitoringScopeDTO(
                evaluation_type="RETROSPECTIVE_BACKTEST",
                plant_code=plant_code,
                recipe_code=recipe_code,
                date_from=date_from,
                date_to=date_to,
                date_filter_applied_to="production_date",
                model_version=model_version or "UNKNOWN",
                status="MODEL_ARTIFACT_UNAVAILABLE",
                disclaimer="Evaluated retrospectively against historical batch material consumption and 28-day laboratory break tests.",
                eligible_count=0,
                excluded_records_count=0,
                cache_token_version=token_ver,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
            empty_metrics, _ = StatisticalMathEngine.calculate_metrics([])
            return ActualVsPredictedResponseDTO(
                scope=scope,
                summary_metrics=empty_metrics,
                items=[],
                total_items=0,
            )

        # Load candidate model artifact bundle
        try:
            bundle = joblib.load(model_orm.artifact_location)
            model_obj = bundle["model"]
            pipeline = bundle["pipeline"]
        except Exception as ex:
            scope = ModelMonitoringScopeDTO(
                evaluation_type="RETROSPECTIVE_BACKTEST",
                plant_code=plant_code,
                recipe_code=recipe_code,
                date_from=date_from,
                date_to=date_to,
                date_filter_applied_to="production_date",
                model_version=model_orm.model_version,
                status=f"ARTIFACT_LOAD_ERROR: {str(ex)[:100]}",
                disclaimer="Evaluated retrospectively against historical batch material consumption and 28-day laboratory break tests.",
                eligible_count=0,
                excluded_records_count=0,
                cache_token_version=token_ver,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
            empty_metrics, _ = StatisticalMathEngine.calculate_metrics([])
            return ActualVsPredictedResponseDTO(
                scope=scope,
                summary_metrics=empty_metrics,
                items=[],
                total_items=0,
            )

        # Extract eligible observations for backtesting (inclusive of all valid 28d-tested batches)
        eligible_obs, excluded_cnt = cls._extract_backtest_observations(
            db=db,
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
        )

        pairs: List[Tuple[float, float]] = []
        items: List[ActualVsPredictedItemDTO] = []

        # Evaluate model predictions through fitted pipeline per observation
        for obs in eligible_obs:
            try:
                f_dict = obs.to_feature_dict()
                X = pipeline.transform([f_dict])
                pred_val = float(model_obj.predict(X)[0])
                act_val = float(obs.target_28d_strength_mpa)

                if not (math.isfinite(pred_val) and math.isfinite(act_val)):
                    excluded_cnt += 1
                    continue

                pairs.append((act_val, pred_val))
                res = round(pred_val - act_val, 2)
                abs_err = round(abs(pred_val - act_val), 2)

                if len(items) < limit:
                    prod_ts = obs.production_timestamp.isoformat() if obs.production_timestamp else ""
                    items.append(
                        ActualVsPredictedItemDTO(
                            batch_id=obs.batch_id,
                            batch_number=obs.batch_number,
                            plant_code=obs.plant_code,
                            recipe_code=obs.recipe_code,
                            grade=None,
                            production_timestamp=prod_ts,
                            testing_date=None,
                            actual_strength_mpa=round(act_val, 2),
                            predicted_strength_mpa=round(pred_val, 2),
                            residual_mpa=res,
                            abs_error_mpa=abs_err,
                            model_version=model_orm.model_version,
                        )
                    )
            except Exception:
                # Exclude batches that fail strict feature dimension requirements (e.g. missing aggregates)
                excluded_cnt += 1

        metrics, additional_excluded = StatisticalMathEngine.calculate_metrics(pairs)
        total_excluded = excluded_cnt + additional_excluded

        status = "OK" if metrics.sample_count > 0 else "NO_ELIGIBLE_BATCHES_IN_RANGE"

        scope = ModelMonitoringScopeDTO(
            evaluation_type="RETROSPECTIVE_BACKTEST",
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            date_filter_applied_to="production_date",
            model_version=model_orm.model_version,
            status=status,
            disclaimer="Evaluated retrospectively against historical batch material consumption and 28-day laboratory break tests.",
            eligible_count=len(pairs),
            excluded_records_count=total_excluded,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return ActualVsPredictedResponseDTO(
            scope=scope,
            summary_metrics=metrics,
            items=items,
            total_items=len(items),
        )

    # ---------------------------------------------------------------------
    # FEATURE IMPORTANCE
    # ---------------------------------------------------------------------

    @classmethod
    def get_feature_importance(
        cls,
        db: Session,
        model_version: Optional[str] = None,
    ) -> ModelFeatureImportanceResponseDTO:
        """Extract native feature importances (e.g. XGBoost) or linear coefficients (e.g. Ridge) mapped to 12 canonical features."""
        model_orm, _ = cls._resolve_model(db, model_version)

        if not model_orm:
            return ModelFeatureImportanceResponseDTO(
                model_version=model_version or "UNKNOWN",
                algorithm="UNKNOWN",
                feature_importance_available=False,
                status_code="MODEL_NOT_FOUND",
                message=f"Model version '{model_version}' not found in registry.",
                features=[],
            )

        if not model_orm.artifact_location or not os.path.exists(model_orm.artifact_location):
            return ModelFeatureImportanceResponseDTO(
                model_version=model_orm.model_version,
                algorithm=model_orm.algorithm,
                feature_importance_available=False,
                status_code="FEATURE_IMPORTANCE_NOT_AVAILABLE",
                message="Model artifact file not found on disk.",
                features=[],
            )

        try:
            bundle = joblib.load(model_orm.artifact_location)
            model_obj = bundle.get("model")
            pipeline = bundle.get("pipeline")
        except Exception as ex:
            return ModelFeatureImportanceResponseDTO(
                model_version=model_orm.model_version,
                algorithm=model_orm.algorithm,
                feature_importance_available=False,
                status_code="FEATURE_IMPORTANCE_NOT_AVAILABLE",
                message=f"Failed to load artifact: {str(ex)[:100]}",
                features=[],
            )

        raw_weights: Optional[np.ndarray] = None
        if hasattr(model_obj, "feature_importances_"):
            raw_weights = np.array(model_obj.feature_importances_, dtype=np.float64)
        elif hasattr(model_obj, "coef_"):
            raw_weights = np.abs(np.array(model_obj.coef_, dtype=np.float64))

        if raw_weights is None or len(raw_weights) != 12:
            return ModelFeatureImportanceResponseDTO(
                model_version=model_orm.model_version,
                algorithm=model_orm.algorithm,
                feature_importance_available=False,
                status_code="FEATURE_IMPORTANCE_NOT_AVAILABLE",
                message="Model estimator does not expose valid 12-feature weights.",
                features=[],
            )

        # Normalize weights to sum to 1.0 (or percentage)
        total_w = float(np.sum(raw_weights))
        normalized_weights = raw_weights / total_w if total_w > 1e-9 else raw_weights

        feature_items: List[FeatureImportanceItemDTO] = []
        for feat_name, raw_val, norm_val in zip(ORDERED_CANONICAL_FEATURES, raw_weights, normalized_weights):
            meta = CANONICAL_FEATURE_METADATA.get(feat_name, {"display_name": feat_name, "unit": "units"})
            feature_items.append(
                FeatureImportanceItemDTO(
                    feature_name=feat_name,
                    display_name=meta["display_name"],
                    importance_weight=round(float(norm_val), 4),
                    raw_value=round(float(raw_val), 4),
                    unit=meta["unit"],
                )
            )

        # Sort descending by normalized importance weight
        feature_items.sort(key=lambda x: x.importance_weight, reverse=True)

        return ModelFeatureImportanceResponseDTO(
            model_version=model_orm.model_version,
            algorithm=model_orm.algorithm,
            feature_importance_available=True,
            status_code="OK",
            message="Feature importances successfully mapped from serialized model artifact.",
            features=feature_items,
        )

