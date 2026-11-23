"""Unit test suite for WS-02.9 Laboratory & Quality Schema."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from src.database import (
    Batch,
    ConcreteSample,
    CubeSet,
    Customer,
    FT7Certificate,
    LaboratoryRepository,
    LaboratoryService,
    MasterReferenceService,
    Material,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    Plant,
    ProductionService,
    QualityObservation,
    Recipe,
    SlumpTest,
    dispose_database_engine,
    get_db_session,
    seed_lookup_tables,
)
from src.exceptions import EntityNotFoundException, InvalidConfigurationException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_laboratory_sample_slump_and_cube_testing() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_LAB1", "Lab Test Plant")
        customer = master_srv.create_customer("C_LAB1", "Lab Test Customer")
        project = master_srv.create_project("PR_LAB1", customer.id, "Lab Test Project")

        recipe = Recipe(recipe_code="M35_LAB", recipe_name="M35 Lab", target_strength_mpa=35.0)
        session.add(recipe)
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
        order_srv = OrderService(session)
        req_time = datetime.now(timezone.utc) + timedelta(days=1)

        order = order_srv.create_order(
            order_number="ORD-LAB-001",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=40.0,
        )

        schedule = order_srv.create_dispatch_schedule(
            schedule_number="SCH-LAB-001",
            order_id=order.id,
            planned_dispatch_time=req_time,
            planned_delivery_time=req_time + timedelta(minutes=45),
            planned_quantity_m3=6.0,
        )

        prod_srv = ProductionService(session)
        batch = prod_srv.create_batch(
            batch_number="BAT-LAB-001",
            order_id=order.id,
            dispatch_schedule_id=schedule.id,
            recipe_id=recipe.id,
            plant_id=plant.id,
            planned_quantity_m3=Decimal("6.00"),
        )

        lab_srv = LaboratoryService(session)

        # 1. Create Sample
        sample = lab_srv.create_sample(
            sample_number="SMP-001",
            batch_id=batch.id,
            sampling_location="MIXER_DISCHARGE",
        )
        assert sample.id is not None

        # Duplicate sample number should fail
        with pytest.raises(InvalidConfigurationException):
            lab_srv.create_sample("SMP-001", batch.id)

        # 2. Record Slump Test
        slump = lab_srv.record_slump_test(
            sample_id=sample.id,
            slump_mm=Decimal("120.00"),
            ambient_temp_celsius=Decimal("32.50"),
            concrete_temp_celsius=Decimal("29.00"),
        )
        assert slump.id is not None
        assert slump.slump_mm == Decimal("120.00")

        # 3. Create Cube Set & Record Cube Tests
        cset = lab_srv.create_cube_set(
            cube_set_number="CSET-001",
            sample_id=sample.id,
            number_of_cubes=6,
        )
        assert cset.id is not None

        ctest7 = lab_srv.record_cube_test(
            cube_set_id=cset.id,
            age_days=7,
            compressive_strength_mpa=Decimal("27.50"),
        )
        ctest28 = lab_srv.record_cube_test(
            cube_set_id=cset.id,
            age_days=28,
            compressive_strength_mpa=Decimal("41.20"),
        )
        assert ctest7.id is not None
        assert ctest28.compressive_strength_mpa == Decimal("41.20")

        # 4. Register FT7 Certificate & Quality Observation
        cert = lab_srv.register_ft7_certificate(
            certificate_number="FT7-2026-001",
            batch_id=batch.id,
            approved_by="CHIEF_QA_ENGINEER",
        )
        assert cert.id is not None

        obs = lab_srv.record_quality_observation(
            batch_id=batch.id,
            observation_type="HIGH_WORKABILITY",
            description="Slump exceeded target by 10mm due to ambient temperature",
            severity="LOW",
        )
        assert obs.id is not None

        # Verify repository lookups
        lab_repo = LaboratoryRepository(session)
        sample_tests = lab_repo.list_cube_tests_by_sample(sample.id)
        assert len(sample_tests) == 2

        certs = lab_repo.list_ft7_certificates_by_batch(batch.id)
        assert len(certs) == 1

        observations = lab_repo.list_observations_by_batch(batch.id)
        assert len(observations) == 1
