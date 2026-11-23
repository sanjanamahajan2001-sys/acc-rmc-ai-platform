"""Unit test suite for WS-02.10 AI Feature Store & Prediction Schema."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from src.database import (
    AIMetadataService,
    AIRepository,
    Batch,
    Customer,
    LaboratoryService,
    MasterReferenceService,
    Material,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    Plant,
    ProductionService,
    Recipe,
    dispose_database_engine,
    get_db_session,
    seed_lookup_tables,
)
from src.exceptions import EntityNotFoundException, InvalidConfigurationException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_ai_feature_vector_prediction_and_model_registry() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_AI1", "AI Test Plant")
        customer = master_srv.create_customer("C_AI1", "AI Test Customer")
        project = master_srv.create_project("PR_AI1", customer.id, "AI Test Project")

        recipe = Recipe(recipe_code="M40_AI", recipe_name="M40 AI", target_strength_mpa=40.0)
        session.add(recipe)
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
        order_srv = OrderService(session)
        req_time = datetime.now(timezone.utc) + timedelta(days=1)

        order = order_srv.create_order(
            order_number="ORD-AI-001",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=50.0,
        )

        schedule = order_srv.create_dispatch_schedule(
            schedule_number="SCH-AI-001",
            order_id=order.id,
            planned_dispatch_time=req_time,
            planned_delivery_time=req_time + timedelta(minutes=45),
            planned_quantity_m3=6.0,
        )

        prod_srv = ProductionService(session)
        batch = prod_srv.create_batch(
            batch_number="BAT-AI-001",
            order_id=order.id,
            dispatch_schedule_id=schedule.id,
            recipe_id=recipe.id,
            plant_id=plant.id,
            planned_quantity_m3=Decimal("6.00"),
        )

        lab_srv = LaboratoryService(session)
        sample = lab_srv.create_sample("SMP-AI-001", batch.id)
        cset = lab_srv.create_cube_set("CSET-AI-001", sample.id)
        ctest = lab_srv.record_cube_test(cset.id, 28, Decimal("44.50"))

        ai_srv = AIMetadataService(session)

        # 1. Register Deployed Model
        model = ai_srv.register_model(
            model_name="StrengthPredictorXGB",
            model_version="2.1.0",
            framework="xgboost",
            algorithm="XGBoostRegressor",
        )
        assert model.id is not None

        # Duplicate model version registration should fail
        with pytest.raises(InvalidConfigurationException):
            ai_srv.register_model("StrengthPredictorXGB", "2.1.0")

        # 2. Persist Feature Vector Snapshot
        fv = ai_srv.persist_feature_vector(
            batch_id=batch.id,
            sample_id=sample.id,
            model_version="2.1.0",
            feature_hash="hash_a1b2c3d4e5f6",
            feature_payload_json={"cement_kg": 380, "w_c_ratio": 0.42, "slump_mm": 120},
        )
        assert fv.id is not None

        # 3. Persist Model Prediction
        pred = ai_srv.persist_prediction(
            feature_vector_id=fv.id,
            model_version="2.1.0",
            predicted_strength_mpa=Decimal("43.80"),
            confidence_score=Decimal("0.9450"),
            inference_duration_ms=45,
        )
        assert pred.id is not None

        # 4. Link Actual Measured Outcome
        outcome = ai_srv.register_actual_outcome(
            prediction_id=pred.id,
            cube_test_id=ctest.id,
            actual_strength_mpa=Decimal("44.50"),
        )
        assert outcome.id is not None

        # 5. Record Audit & Drift Snapshots
        audit = ai_srv.record_prediction_audit(
            prediction_id=pred.id,
            model_version="2.1.0",
            request_id="REQ-AI-100",
            execution_duration_ms=45,
        )
        assert audit.id is not None

        drift = ai_srv.record_drift_snapshot(
            monitored_feature="cement_kg",
            reference_distribution_json={"mean": 380, "std": 15},
            observed_distribution_json={"mean": 372, "std": 18},
            drift_metric=Decimal("0.0320"),
            threshold=Decimal("0.0500"),
            drift_detected=False,
        )
        assert drift.id is not None

        # Verify repository lookups
        ai_repo = AIRepository(session)
        retrieved_model = ai_repo.get_model_version("StrengthPredictorXGB", "2.1.0")
        assert retrieved_model.id == model.id

        retrieved_pred = ai_repo.get_prediction(pred.id)
        assert retrieved_pred.predicted_strength_mpa == Decimal("43.80")
