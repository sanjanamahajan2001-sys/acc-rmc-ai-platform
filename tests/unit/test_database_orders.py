"""Unit test suite for WS-02.6 Order & Dispatch Schema."""

from datetime import datetime, timedelta, timezone
import pytest
from src.database import (
    Customer,
    MasterReferenceService,
    Order,
    OrderRepository,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    Plant,
    Project,
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


def test_order_creation_and_repository() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_200", "Bhandup Batch Plant")
        customer = master_srv.create_customer("C_200", "Oberoi Realty Ltd")
        project = master_srv.create_project("PR_200", customer.id, "Oberoi Sky City")

        recipe = Recipe(recipe_code="M30_PUMP", recipe_name="M30 Pump Concrete", target_strength_mpa=30.0)
        session.add(recipe)
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
        assert status_lookup is not None

        order_srv = OrderService(session)
        req_time = datetime.now(timezone.utc) + timedelta(days=1)
        order = order_srv.create_order(
            order_number="ORD-2026-001",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=50.0,
        )
        assert order.id is not None
        assert order.total_quantity_m3 == 50.0
        assert len(order.line_items) == 1

        order_repo = OrderRepository(session)
        retrieved = order_repo.get_by_order_number("ORD-2026-001")
        assert retrieved.id == order.id

        # Duplicate order number should fail
        with pytest.raises(InvalidConfigurationException):
            order_srv.create_order(
                order_number="ORD-2026-001",
                customer_id=customer.id,
                project_id=project.id,
                plant_id=plant.id,
                order_status_id=status_lookup.id,
                requested_delivery_datetime=req_time,
                recipe_id=recipe.id,
                ordered_quantity_m3=20.0,
            )


def test_dispatch_schedule_creation() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_201", "Ghansoli RMC Plant")
        customer = master_srv.create_customer("C_201", "Hiranandani Group")
        project = master_srv.create_project("PR_201", customer.id, "Hiranandani Estate")

        recipe = Recipe(recipe_code="M40_SELF_COMPACT", recipe_name="M40 SCC Concrete", target_strength_mpa=40.0)
        session.add(recipe)
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.IN_PROGRESS.value).first()
        order_srv = OrderService(session)

        req_time = datetime.now(timezone.utc) + timedelta(hours=4)
        order = order_srv.create_order(
            order_number="ORD-2026-002",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=30.0,
        )

        schedule = order_srv.create_dispatch_schedule(
            schedule_number="SCH-001",
            order_id=order.id,
            planned_dispatch_time=req_time,
            planned_delivery_time=req_time + timedelta(minutes=45),
            planned_quantity_m3=6.0,
            sequence_number=1,
        )
        assert schedule.id is not None
        assert schedule.planned_quantity_m3 == 6.0
