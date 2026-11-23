"""Unit test suite for WS-02.11 Audit Persistence & Operational History Schema."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from src.database import (
    AIMetadataService,
    AuditEvent,
    AuditPersistenceService,
    AuditRepository,
    Batch,
    Customer,
    EntityChange,
    ImportHistory,
    MasterReferenceService,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    Plant,
    ProductionService,
    Recipe,
    SystemOperation,
    dispose_database_engine,
    get_db_session,
    seed_lookup_tables,
)
from src.exceptions import EntityNotFoundException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_audit_event_entity_change_import_and_operation_persistence() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        master_srv = MasterReferenceService(session)

        plant = master_srv.create_plant("P_AUD1", "Audit Plant 1")
        customer = master_srv.create_customer("C_AUD1", "Audit Customer 1")
        project = master_srv.create_project("PR_AUD1", customer.id, "Audit Project 1")

        recipe = Recipe(recipe_code="M35_AUD", recipe_name="M35 Audit", target_strength_mpa=35.0)
        session.add(recipe)
        session.flush()

        status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
        order_srv = OrderService(session)
        req_time = datetime.now(timezone.utc) + timedelta(days=1)

        order = order_srv.create_order(
            order_number="ORD-AUD-001",
            customer_id=customer.id,
            project_id=project.id,
            plant_id=plant.id,
            order_status_id=status_lookup.id,
            requested_delivery_datetime=req_time,
            recipe_id=recipe.id,
            ordered_quantity_m3=40.0,
        )

        schedule = order_srv.create_dispatch_schedule(
            schedule_number="SCH-AUD-001",
            order_id=order.id,
            planned_dispatch_time=req_time,
            planned_delivery_time=req_time + timedelta(minutes=45),
            planned_quantity_m3=6.0,
        )

        prod_srv = ProductionService(session)
        batch = prod_srv.create_batch(
            batch_number="BAT-AUD-001",
            order_id=order.id,
            dispatch_schedule_id=schedule.id,
            recipe_id=recipe.id,
            plant_id=plant.id,
            planned_quantity_m3=Decimal("6.00"),
        )

        audit_srv = AuditPersistenceService(session)

        # 1. Log Audit Event
        event = audit_srv.log_audit_event(
            event_type="BATCH_DISPATCH_APPROVED",
            entity_type="Batch",
            entity_id=batch.id,
            action="APPROVE",
            plant_id=plant.id,
            batch_id=batch.id,
            severity="INFO",
            result="SUCCESS",
            metadata_json={"approved_by": "PLANT_MANAGER"},
        )
        assert event.id is not None

        # 2. Log Entity Change
        change = audit_srv.log_entity_change(
            audit_event_id=event.id,
            field_name="production_status",
            old_value="PLANNED",
            new_value="BATCHING",
            change_type="UPDATE",
        )
        assert change.id is not None

        # 3. Record Import History
        imp = audit_srv.record_import_history(
            source_system="SCADA_FT7",
            file_name="scada_batch_logs_20260807.csv",
            file_checksum="md5_a1b2c3d4",
            records_processed=150,
            records_inserted=145,
            records_failed=5,
            status="COMPLETED_WITH_WARNINGS",
        )
        assert imp.id is not None

        # 4. Record System Operation
        op = audit_srv.record_system_operation(
            operation_name="ALEMBIC_SCHEMA_MIGRATION",
            component="MIGRATION_ENGINE",
            duration_ms=250,
            status="SUCCESS",
        )
        assert op.id is not None

        # Verify Repository Queries
        audit_repo = AuditRepository(session)
        events = audit_repo.list_events(entity_type="Batch", entity_id=batch.id)
        assert len(events) == 1
        assert events[0].changes[0].field_name == "production_status"

        imports = audit_repo.list_import_history(source_system="SCADA_FT7")
        assert len(imports) == 1

        ops = audit_repo.list_operations(component="MIGRATION_ENGINE")
        assert len(ops) == 1
