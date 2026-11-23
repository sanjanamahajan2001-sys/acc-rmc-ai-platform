"""Production Data Access Repository.

This module provides data access methods for Batch entities, material consumption,
weighing logs, and production events.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.production import (
    Batch,
    BatchMaterialConsumption,
    ProductionEvent,
    WeighingLog,
)
from src.exceptions.domain import EntityNotFoundException


class ProductionRepository:
    """Data Access Repository for Production & Batch Entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_batch_number(self, batch_number: str) -> Batch:
        """Retrieve batch record by unique batch_number."""
        record = self._session.query(Batch).filter_by(batch_number=batch_number).first()
        if record is None:
            raise EntityNotFoundException(entity_name="Batch", entity_id=batch_number)
        return record

    def get_by_id(self, batch_id: str) -> Batch:
        """Retrieve batch record by primary key UUID."""
        record = self._session.query(Batch).filter_by(id=batch_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="Batch", entity_id=batch_id)
        return record

    def create_batch(self, batch: Batch) -> Batch:
        """Add new batch record to session."""
        self._session.add(batch)
        self._session.flush()
        return batch

    def update_batch(self, batch: Batch) -> Batch:
        """Flush session changes for batch."""
        self._session.flush()
        return batch

    def list_by_order(self, order_id: str) -> List[Batch]:
        """List batches for an order."""
        return self._session.query(Batch).filter_by(order_id=order_id, is_deleted=False).all()

    def list_by_schedule(self, schedule_id: str) -> List[Batch]:
        """List batches for a dispatch schedule."""
        return self._session.query(Batch).filter_by(dispatch_schedule_id=schedule_id, is_deleted=False).all()

    def list_by_status(self, production_status: str) -> List[Batch]:
        """List batches by production status."""
        return self._session.query(Batch).filter_by(production_status=production_status, is_deleted=False).all()

    def create_weighing_log(self, weighing_log: WeighingLog) -> WeighingLog:
        """Add new weighing log record."""
        self._session.add(weighing_log)
        self._session.flush()
        return weighing_log

    def create_material_consumption(self, consumption: BatchMaterialConsumption) -> BatchMaterialConsumption:
        """Add new material consumption record."""
        self._session.add(consumption)
        self._session.flush()
        return consumption

    def create_event(self, event: ProductionEvent) -> ProductionEvent:
        """Add new production event record."""
        self._session.add(event)
        self._session.flush()
        return event

    def list_events(self, batch_id: str) -> List[ProductionEvent]:
        """List chronological production events for a batch."""
        return (
            self._session.query(ProductionEvent)
            .filter_by(batch_id=batch_id)
            .order_by(ProductionEvent.event_sequence.asc())
            .all()
        )

    def exists_batch_number(self, batch_number: str) -> bool:
        """Check if batch_number exists."""
        return self._session.query(Batch.id).filter_by(batch_number=batch_number).first() is not None
