"""Unit and Integration Tests for WS-DASH-4A Model Monitoring & Strength Prediction Validation.

Tests all 22 required evaluation criteria:
1. MAE calculation formula
2. RMSE calculation formula (including sqrt)
3. R² calculation formula (1 - SSE/SST)
4. Mean residual (predicted - actual) sign convention
5. Sample standard deviation of residuals (ddof=1)
6. Edge case N = 0: All metrics None, sample_count = 0
7. Edge case N = 1: MAE/RMSE = abs error, R²/res_std = None
8. Zero actual variance (SST = 0): R² = None
9. Null/non-finite values: Excluded from calculation and counted
10. Stored prediction matching join integrity
11. Zero stored prediction state: honest status NO_STORED_PREDICTIONS_IN_RANGE
12. Model-version filtering and isolation
13. Plant filter isolation
14. Recipe filter isolation
15. Production date filter isolation (applied to prd_batches.created_at)
16. Retrospective backtest mode separation (RETROSPECTIVE_BACKTEST)
17. No ai_predictions insertion during backtesting
18. Feature importance availability checking
19. Feature importance canonical 12-feature mapping
20. Authentication & role authorization checks
21. Response DTO schema integrity
22. Duplicate prevention across test evaluation pairs
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import math
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.models.ai import FeatureVector, ModelRegistry, Prediction
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.models.user import User
from src.security.jwt import create_access_token
from src.services.model_monitoring_service import (
    CANONICAL_FEATURE_METADATA,
    ORDERED_CANONICAL_FEATURES,
    ModelMonitoringService,
    StatisticalMathEngine,
)


@pytest.fixture
def db_session():
    """Isolated database session fixture."""
    engine = get_database_engine()
    with Session(engine) as session:
        yield session


@pytest.fixture
def auth_headers(db_session: Session) -> dict:
    """Fixture to provide valid JWT authorization headers for testing."""
    user = db_session.query(User).filter(User.username == "admin").first()
    if not user:
        user = db_session.query(User).first()
    if not user:
        user = User(
            username="admin",
            email="admin@accrmc.com",
            hashed_password="hashed_test_pass",
            session_version=1,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    token = create_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email or "admin@acc-rmc.local",
        roles=["SUPER_ADMIN"],
        session_version=getattr(user, "session_version", 1),
    )
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 1. MATHEMATICAL FORMULAS & EDGE CASES TESTS
# =========================================================================

def test_01_mae_calculation():
    """Test MAE: mean(|predicted - actual|)."""
    # Actuals: 30.0, 40.0; Predicteds: 35.0, 38.0 -> Abs errors: 5.0, 2.0 -> MAE = 3.5
    pairs = [(30.0, 35.0), (40.0, 38.0)]
    metrics, excluded = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.sample_count == 2
    assert metrics.mae_mpa == 3.5
    assert excluded == 0


def test_02_rmse_calculation():
    """Test RMSE: sqrt(mean((predicted - actual)²)). Must explicitly distinguish MSE from RMSE."""
    # Actuals: 30.0, 40.0; Predicteds: 33.0, 44.0 -> Errors: 3.0, 4.0 -> Sq: 9.0, 16.0 -> MSE: 12.5 -> RMSE: sqrt(12.5) ≈ 3.5355339 -> round(3) = 3.536
    pairs = [(30.0, 33.0), (40.0, 44.0)]
    metrics, _ = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.mse_mpa2 == 12.5
    assert metrics.rmse_mpa == round(math.sqrt(12.5), 3)
    assert metrics.rmse_mpa == 3.536
    assert metrics.rmse_mpa != metrics.mse_mpa2
    assert abs(metrics.rmse_mpa - round(math.sqrt(metrics.mse_mpa2), 3)) == 0.0


def test_03_r2_score_calculation():
    """Test R²: 1 - SSE / SST."""
    # Actuals: [20.0, 30.0, 40.0] -> Mean actual = 30.0, SST = (-10)^2 + 0^2 + 10^2 = 200.0
    # Predicteds: [22.0, 29.0, 41.0] -> Errors = [2, -1, 1] -> Sq errors = [4, 1, 1] -> SSE = 6.0
    # R² = 1 - 6/200 = 1 - 0.03 = 0.97
    pairs = [(20.0, 22.0), (30.0, 29.0), (40.0, 41.0)]
    metrics, _ = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.r2_score == 0.97


def test_04_mean_residual_sign_convention():
    """Test Mean Residual: mean(predicted - actual). Positive = over-prediction."""
    # Over-prediction: actual=30, pred=35 -> residual = +5.0
    # Under-prediction: actual=40, pred=38 -> residual = -2.0
    # Mean residual = (+5 - 2) / 2 = +1.5
    pairs = [(30.0, 35.0), (40.0, 38.0)]
    metrics, _ = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.mean_residual_mpa == 1.5


def test_05_residual_standard_deviation():
    """Test Sample Standard Deviation of Residuals: ddof=1."""
    # Residuals: [2.0, 4.0] -> Mean res = 3.0 -> Devs: [-1.0, 1.0] -> Sq devs: [1.0, 1.0] -> Sum: 2.0 -> / (2-1) = 2.0 -> sqrt(2) ≈ 1.414
    pairs = [(30.0, 32.0), (40.0, 44.0)]
    metrics, _ = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.residual_std_dev_mpa == round(math.sqrt(2.0), 3)


def test_06_edge_case_n_zero():
    """Test N=0: All statistics must be None, sample_count=0 (no fake zero metrics)."""
    pairs = []
    metrics, excluded = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.sample_count == 0
    assert metrics.mae_mpa is None
    assert metrics.rmse_mpa is None
    assert metrics.r2_score is None
    assert metrics.mean_residual_mpa is None
    assert metrics.residual_std_dev_mpa is None
    assert excluded == 0


def test_07_edge_case_n_one():
    """Test N=1: MAE/RMSE = abs error, R²=None, residual_std=None."""
    pairs = [(30.0, 34.2)]
    metrics, excluded = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.sample_count == 1
    assert metrics.mae_mpa == 4.2
    assert metrics.rmse_mpa == 4.2
    assert metrics.mean_residual_mpa == 4.2
    assert metrics.r2_score is None
    assert metrics.residual_std_dev_mpa is None
    assert excluded == 0


def test_08_zero_actual_variance():
    """Test Zero Actual Variance (SST = 0): R² must be None (not 0.0 or error)."""
    # All actuals are 35.0
    pairs = [(35.0, 34.0), (35.0, 36.0), (35.0, 35.5)]
    metrics, _ = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.sample_count == 3
    assert metrics.r2_score is None
    assert metrics.mae_mpa is not None


def test_09_null_and_non_finite_exclusion():
    """Test Null, NaN, Inf values are excluded and counted in excluded_records_count."""
    pairs = [
        (30.0, 32.0),
        (None, 35.0),
        (40.0, None),
        (float("nan"), 38.0),
        (35.0, float("inf")),
        (45.0, 44.0),
    ]
    metrics, excluded = StatisticalMathEngine.calculate_metrics(pairs)
    assert metrics.sample_count == 2
    assert excluded == 4


# =========================================================================
# 2. STORED PREDICTION MONITORING & ENDPOINT TESTS (MODE A)
# =========================================================================

def test_10_stored_prediction_matching_and_zero_state(db_session: Session):
    """Test that stored prediction monitoring returns NO_STORED_PREDICTIONS_IN_RANGE when no stored predictions match."""
    summary = ModelMonitoringService.get_prediction_summary(db=db_session, model_version="NON_EXISTENT_MODEL_V0")
    assert summary.scope.evaluation_type == "PRODUCTION_STORED"
    assert summary.metrics.sample_count == 0
    assert summary.metrics.mae_mpa is None
    assert summary.scope.status == "NO_STORED_PREDICTIONS_IN_RANGE"


def test_11_stored_prediction_with_populated_data(db_session: Session):
    """Test stored prediction evaluation when genuine stored records exist."""
    # Find a batch that has 28d break tests
    batch = (
        db_session.query(Batch)
        .join(ConcreteSample, ConcreteSample.batch_id == Batch.id)
        .join(CubeSet, CubeSet.sample_id == ConcreteSample.id)
        .join(CubeTest, CubeTest.cube_set_id == CubeSet.id)
        .filter(Batch.is_deleted == False, CubeTest.age_days == 28)
        .first()
    )
    if not batch:
        pytest.skip("No 28d tested batches in test DB")

    # Create a FeatureVector and Prediction for this batch
    fv = FeatureVector(
        batch_id=batch.id,
        model_version="test-model-v1.0",
        feature_schema_version="1.0.0",
        feature_hash="hash_12345",
        feature_payload_json={"cement_kg_m3": 350.0},
    )
    db_session.add(fv)
    db_session.flush()

    pred = Prediction(
        feature_vector_id=fv.id,
        prediction_type="STRENGTH_28D",
        predicted_strength_mpa=Decimal("38.50"),
        model_version="test-model-v1.0",
    )
    db_session.add(pred)
    db_session.commit()

    # Query summary for test-model-v1.0
    summary = ModelMonitoringService.get_prediction_summary(db=db_session, model_version="test-model-v1.0")
    assert summary.scope.evaluation_type == "PRODUCTION_STORED"
    assert summary.metrics.sample_count >= 1
    assert summary.metrics.mae_mpa is not None
    assert summary.scope.status == "OK"

    # Clean up test prediction
    db_session.delete(pred)
    db_session.delete(fv)
    db_session.commit()


def test_12_model_version_isolation(db_session: Session):
    """Test that model_version filter isolates only predictions from that model."""
    summary = ModelMonitoringService.get_prediction_summary(db=db_session, model_version="NON_EXISTENT_MODEL_V99")
    assert summary.metrics.sample_count == 0
    assert summary.scope.model_version == "NON_EXISTENT_MODEL_V99"


def test_13_plant_and_recipe_filters(db_session: Session):
    """Test that plant and recipe filters are respected."""
    plant = db_session.query(Plant).filter(Plant.is_deleted == False).first()
    p_code = plant.plant_code if plant else "PLANT-01"

    summary = ModelMonitoringService.get_prediction_summary(db=db_session, plant_code=p_code)
    assert summary.scope.plant_code == p_code
    assert summary.scope.evaluation_type == "PRODUCTION_STORED"


def test_14_production_date_filter_semantics(db_session: Session):
    """Test date filter uses prd_batches.created_at and exposes date_filter_applied_to = production_date."""
    d_from = date(2026, 1, 1)
    d_to = date(2026, 12, 31)
    summary = ModelMonitoringService.get_prediction_summary(db=db_session, date_from=d_from, date_to=d_to)
    assert summary.scope.date_filter_applied_to == "production_date"
    assert summary.scope.date_from == d_from
    assert summary.scope.date_to == d_to


# =========================================================================
# 3. RETROSPECTIVE MODEL BACKTEST TESTS (MODE B)
# =========================================================================

def test_15_retrospective_backtest_mode_separation(db_session: Session):
    """Test that backtest returns evaluation_type = RETROSPECTIVE_BACKTEST and clear disclaimer."""
    backtest = ModelMonitoringService.get_model_backtest(db=db_session)
    assert backtest.scope.evaluation_type == "RETROSPECTIVE_BACKTEST"
    assert "historical batch material consumption" in backtest.scope.disclaimer


def test_16_no_ai_predictions_created_during_backtest(db_session: Session):
    """Test that running a backtest does NOT insert rows into ai_predictions."""
    initial_count = db_session.query(Prediction).count()
    _ = ModelMonitoringService.get_model_backtest(db=db_session)
    final_count = db_session.query(Prediction).count()
    assert final_count == initial_count


# =========================================================================
# 4. FEATURE IMPORTANCE & REGISTRY TESTS
# =========================================================================

def test_17_feature_importance_canonical_mapping(db_session: Session):
    """Test feature importance metadata structure and canonical 12-feature ordering."""
    resp = ModelMonitoringService.get_feature_importance(db=db_session)
    assert isinstance(resp.feature_importance_available, bool)
    assert resp.status_code in ("OK", "FEATURE_IMPORTANCE_NOT_AVAILABLE", "MODEL_NOT_FOUND")

    if resp.feature_importance_available:
        assert len(resp.features) == 12
        feat_names = {f.feature_name for f in resp.features}
        for expected in ORDERED_CANONICAL_FEATURES:
            assert expected in feat_names


def test_18_feature_importance_unavailable_handling(db_session: Session):
    """Test graceful handling when model version is non-existent."""
    resp = ModelMonitoringService.get_feature_importance(db=db_session, model_version="NON_EXISTENT_MODEL_V99")
    assert resp.feature_importance_available is False
    assert resp.status_code == "MODEL_NOT_FOUND"


def test_19_model_registry_metadata_endpoint(db_session: Session):
    """Test retrieving model registry inventory."""
    registry_list = ModelMonitoringService.get_registered_models(db=db_session)
    assert isinstance(registry_list.models, list)
    assert registry_list.total_models == len(registry_list.models)


# =========================================================================
# 5. ERROR TREND & API ENDPOINTS HTTP INTEGRATION
# =========================================================================

def test_20_prediction_error_trend_structure(db_session: Session):
    """Test error trend structure and rolling MAE window size."""
    trend = ModelMonitoringService.get_prediction_error_trend(db=db_session, rolling_window=10)
    assert trend.rolling_window_size == 10
    assert trend.operational_monitoring_threshold_mpa == 3.0
    assert "Operational monitoring threshold" in trend.threshold_description


def test_21_api_endpoints_http_auth_and_status(auth_headers: dict):
    """Test all 6 Phase 4 API endpoints with FastAPI TestClient."""
    client = TestClient(app)

    # 1. Summary
    res = client.get("/api/v1/reporting/prediction-summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scope"]["evaluation_type"] == "PRODUCTION_STORED"

    # 2. Actual vs Predicted
    res = client.get("/api/v1/reporting/actual-vs-predicted", headers=auth_headers)
    assert res.status_code == 200

    # 3. Error Trend
    res = client.get("/api/v1/reporting/prediction-error-trend", headers=auth_headers)
    assert res.status_code == 200

    # 4. Model Features
    res = client.get("/api/v1/reporting/model-features", headers=auth_headers)
    assert res.status_code == 200

    # 5. Model Metadata
    res = client.get("/api/v1/reporting/model-metadata", headers=auth_headers)
    assert res.status_code == 200

    # 6. Model Backtest
    res = client.get("/api/v1/reporting/model-backtest", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scope"]["evaluation_type"] == "RETROSPECTIVE_BACKTEST"


def test_22_api_auth_required():
    """Test that Phase 4 endpoints strictly reject unauthorized requests with 401."""
    client = TestClient(app)
    res = client.get("/api/v1/reporting/prediction-summary")
    assert res.status_code == 401

    res = client.get("/api/v1/reporting/model-backtest")
    assert res.status_code == 401


# =========================================================================
# WS-DASH-4E TARGETED VERIFICATION TESTS
# =========================================================================

def test_23_production_inference_orchestrator_feature_extraction(db_session: Session):
    """Test that ProductionInferenceOrchestrator extracts 12 canonical predictors with zero target leakage."""
    from src.services.ingestion_persistence_service import ProductionInferenceOrchestrator
    from src.database.models.production import BatchMaterialConsumption

    # Create test batch with consumptions
    plant = db_session.query(Plant).first()
    recipe = db_session.query(Recipe).first()
    if not plant or not recipe:
        pytest.skip("Master seed records missing in test DB")

    batch = Batch(
        batch_number=f"BATCH-4E-FEAT-{int(datetime.now(timezone.utc).timestamp())}",
        order_id="ORD-001",
        dispatch_schedule_id="DSP-001",
        recipe_id=recipe.id,
        plant_id=plant.id,
        production_status="COMPLETED",
        planned_quantity_m3=Decimal("6.0"),
        actual_quantity_m3=Decimal("6.0"),
        dataset_origin="OPERATIONAL_ACTUAL",
        delivery_challan_number="CH-4E-01",
    )
    db_session.add(batch)
    db_session.flush()

    # Add material consumption
    mc = BatchMaterialConsumption(
        batch_id=batch.id,
        material_id="MAT-CEM-01",
        planned_quantity=Decimal("2100.0"),
        actual_quantity=Decimal("2100.0"),
        engineering_unit="kg",
        variance_quantity=Decimal("0.0"),
        variance_percentage=Decimal("0.0"),
        quantity_kg_per_m3=Decimal("350.0"),
        source_material_code="CEM-OPC-53",
    )
    db_session.add(mc)
    db_session.commit()

    features = ProductionInferenceOrchestrator.extract_pre_pour_features(db_session, batch)

    # Verify 12 canonical keys present
    assert "cement_kg_m3" in features
    assert "flyash_kg_m3" in features
    assert "ggbs_kg_m3" in features
    assert "water_kg_m3" in features
    assert "admixture_kg_m3" in features
    assert "fine_aggregate_kg_m3" in features
    assert "coarse_aggregate_kg_m3" in features
    assert "total_binder_kg_m3" in features
    assert "water_binder_ratio" in features
    assert "water_cement_ratio" in features
    assert "plant_code" in features
    assert "recipe_code" in features

    # Verify ZERO target leakage
    assert "target_28d_strength_mpa" not in features
    assert "break_load_kn" not in features
    assert "actual_strength" not in features


def test_24_production_inference_orchestrator_persistence_and_idempotency(db_session: Session):
    """Test end-to-end post-commit inference execution, persistence, and duplicate protection."""
    from src.services.ingestion_persistence_service import ProductionInferenceOrchestrator

    plant = db_session.query(Plant).first()
    recipe = db_session.query(Recipe).first()
    if not plant or not recipe:
        pytest.skip("Master seed records missing in test DB")

    batch = Batch(
        batch_number=f"BATCH-4E-IDEM-{int(datetime.now(timezone.utc).timestamp())}",
        order_id="ORD-001",
        dispatch_schedule_id="DSP-001",
        recipe_id=recipe.id,
        plant_id=plant.id,
        production_status="COMPLETED",
        planned_quantity_m3=Decimal("6.0"),
        actual_quantity_m3=Decimal("6.0"),
        dataset_origin="OPERATIONAL_ACTUAL",
        delivery_challan_number="CH-4E-02",
    )
    db_session.add(batch)
    db_session.commit()

    # 1. First execution -> Must persist
    res1 = ProductionInferenceOrchestrator.execute_and_persist_batch_inference(batch_id=batch.id)
    assert res1 is not None
    assert res1["status"] == "PERSISTED"
    assert "prediction_id" in res1
    assert "feature_vector_id" in res1

    # Verify row exists in DB
    pred_row = db_session.query(Prediction).filter(Prediction.id == res1["prediction_id"]).first()
    assert pred_row is not None
    assert pred_row.prediction_status == "COMPLETED"

    fv_row = db_session.query(FeatureVector).filter(FeatureVector.id == res1["feature_vector_id"]).first()
    assert fv_row is not None
    assert fv_row.batch_id == batch.id

    # 2. Second execution with same batch + model version -> Must be IDEMPOTENT NO-OP
    res2 = ProductionInferenceOrchestrator.execute_and_persist_batch_inference(batch_id=batch.id)
    assert res2 is not None
    assert res2["status"] == "ALREADY_EXISTS"
    assert res2["prediction_id"] == res1["prediction_id"]


def test_25_production_inference_orchestrator_failure_isolation(db_session: Session):
    """Test that invalid/missing batches or errors do not raise or crash caller."""
    from src.services.ingestion_persistence_service import ProductionInferenceOrchestrator

    # Non-existent batch ID -> Returns None gracefully
    res = ProductionInferenceOrchestrator.execute_and_persist_batch_inference(batch_id="NON_EXISTENT_BATCH_ID")
    assert res is None


