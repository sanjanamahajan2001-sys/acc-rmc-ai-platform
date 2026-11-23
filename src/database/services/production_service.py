"""Production & Batch Execution Orchestration Service.

This module provides business services for batch creation, production start/completion telemetry,
material consumption, and weighing log persistence.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from src.database.models.master import Material, Plant, Recipe
from src.database.models.orders import DispatchSchedule, Order
from src.database.models.production import (
    Batch,
    BatchMaterialConsumption,
    ProductionEvent,
    WeighingLog,
)
from src.database.repositories.master_repository import MasterRepository
from src.database.repositories.order_repository import OrderRepository
from src.database.repositories.production_repository import ProductionRepository
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.services.production", component="database")


class ProductionService:
    """Production & Batch Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._prod_repo = ProductionRepository(session)
        self._order_repo = OrderRepository(session)
        self._plant_repo = MasterRepository(Plant, session)
        self._recipe_repo = MasterRepository(Recipe, session)
        self._material_repo = MasterRepository(Material, session)

    def create_batch(
        self,
        batch_number: str,
        order_id: str,
        dispatch_schedule_id: str,
        recipe_id: str,
        plant_id: str,
        planned_quantity_m3: Decimal,
        mixer_identifier: str = "MIXER-01",
        operator_identifier: str = "OPERATOR-01",
    ) -> Batch:
        """Create concrete batch execution record, validating order, schedule, recipe, and plant existence."""
        if self._prod_repo.exists_batch_number(batch_number):
            raise InvalidConfigurationException(
                parameter_name="batch_number",
                message=f"Batch with batch_number '{batch_number}' already exists.",
            )

        # Validate master and order foreign keys
        self._order_repo.get_by_id(order_id)
        self._recipe_repo.get_by_id(recipe_id)
        self._plant_repo.get_by_id(plant_id)

        batch = Batch(
            batch_number=batch_number,
            order_id=order_id,
            dispatch_schedule_id=dispatch_schedule_id,
            recipe_id=recipe_id,
            plant_id=plant_id,
            production_status="PLANNED",
            planned_quantity_m3=planned_quantity_m3,
            mixer_identifier=mixer_identifier,
            operator_identifier=operator_identifier,
        )
        self._prod_repo.create_batch(batch)

        # Record BATCH_CREATED production event
        event = ProductionEvent(
            batch_id=batch.id,
            event_type="BATCH_CREATED",
            event_sequence=1,
            metadata_json={"planned_quantity_m3": str(planned_quantity_m3)},
        )
        self._prod_repo.create_event(event)

        logger.info("Batch created successfully", batch_number=batch_number, planned_quantity_m3=str(planned_quantity_m3))
        return batch

    def start_production(self, batch_id: str) -> Batch:
        """Transition batch status to BATCHING and record start timestamp."""
        batch = self._prod_repo.get_by_id(batch_id)
        batch.production_status = "BATCHING"
        batch.production_start_time = datetime.now(timezone.utc)
        self._prod_repo.update_batch(batch)

        event = ProductionEvent(
            batch_id=batch.id,
            event_type="BATCH_STARTED",
            event_sequence=2,
            metadata_json={"start_time": batch.production_start_time.isoformat()},
        )
        self._prod_repo.create_event(event)

        logger.info("Production started for batch", batch_number=batch.batch_number)
        return batch

    def record_weighing_log(
        self,
        batch_id: str,
        material_id: str,
        target_weight: Decimal,
        actual_weight: Decimal,
        tolerance: Decimal = Decimal("1.00"),
        device_id: str = "SCALE-01",
    ) -> WeighingLog:
        """Record actual scale weighing log during batching execution."""
        batch = self._prod_repo.get_by_id(batch_id)
        self._material_repo.get_by_id(material_id)

        log = WeighingLog(
            batch_id=batch.id,
            material_id=material_id,
            target_weight=target_weight,
            actual_weight=actual_weight,
            tolerance=tolerance,
            weighing_device_identifier=device_id,
        )
        self._prod_repo.create_weighing_log(log)
        logger.info("Weighing log recorded", batch_id=batch_id, material_id=material_id, actual_weight=str(actual_weight))
        return log

    def complete_production(self, batch_id: str, actual_quantity_m3: Decimal) -> Batch:
        """Transition batch status to COMPLETED and record completion timestamp."""
        batch = self._prod_repo.get_by_id(batch_id)
        batch.production_status = "COMPLETED"
        batch.actual_quantity_m3 = actual_quantity_m3
        batch.production_end_time = datetime.now(timezone.utc)
        self._prod_repo.update_batch(batch)

        event = ProductionEvent(
            batch_id=batch.id,
            event_type="BATCH_COMPLETED",
            event_sequence=99,
            metadata_json={"actual_quantity_m3": str(actual_quantity_m3)},
        )
        self._prod_repo.create_event(event)

        logger.info("Production completed for batch", batch_number=batch.batch_number, actual_quantity_m3=str(actual_quantity_m3))
        return batch
