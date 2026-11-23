"""Unit test suite for WS-02.7 Production & Batch Schema."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from src.database import (
    Batch,
    Customer,
    MasterReferenceService,
    Material,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    Plant,
    ProductionRepository,
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


def test_batch_lifecycle_and_service() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_300", "Turbhe Batch Plant")
        customer = master_srv.create_customer("C_300", "Reliance Infrastructure Ltd")
        project = master_srv.create_project("PR_300", customer.id, "DAICC Complex")

        recipe = Recipe(recipe_code="M40_HIGH_STRENGTH", recipe_name="M40 High Strength", target_strength_mpa=40.0)
        material = Material(material_code="CEM_OPC_53", material_name="Ultratech OPC 53 Grade", engineering_unit="kg")
        session.add_all([recipe, material])
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
        order_srv = OrderService(session)
        req_time = datetime.now(timezone.utc) + timedelta(hours=2)

        order = order_srv.create_order(
            order_number="ORD-3001",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=60.0,
        )

        schedule = order_srv.create_dispatch_schedule(
            schedule_number="SCH-3001",
            order_id=order.id,
            planned_dispatch_time=req_time,
            planned_delivery_time=req_time + timedelta(minutes=45),
            planned_quantity_m3=6.0,
        )

        prod_srv = ProductionService(session)
        batch = prod_srv.create_batch(
            batch_number="BAT-2026-0001",
            order_id=order.id,
            dispatch_schedule_id=schedule.id,
            recipe_id=recipe.id,
            plant_id=plant.id,
            planned_quantity_m3=Decimal("6.00"),
        )
        assert batch.id is not None
        assert batch.production_status == "PLANNED"

        # Start production
        batch = prod_srv.start_production(batch.id)
        assert batch.production_status == "BATCHING"
        assert batch.production_start_time is not None

        # Record weighing log
        w_log = prod_srv.record_weighing_log(
            batch_id=batch.id,
            material_id=material.id,
            target_weight=Decimal("2100.00"),
            actual_weight=Decimal("2098.50"),
            tolerance=Decimal("1.00"),
        )
        assert w_log.id is not None

        # Complete production
        batch = prod_srv.complete_production(batch.id, actual_quantity_m3=Decimal("6.00"))
        assert batch.production_status == "COMPLETED"
        assert batch.production_end_time is not None

        # Verify event log count
        prod_repo = ProductionRepository(session)
        events = prod_repo.list_events(batch.id)
        assert len(events) >= 3
