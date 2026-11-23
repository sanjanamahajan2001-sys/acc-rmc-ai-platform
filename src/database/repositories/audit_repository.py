"""Audit Persistence & Operational History Data Access Repository.

This module provides data access methods for Audit Events, Entity Field Changes, Import History,
and System Operation logs.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.audit import (
    AuditEvent,
    EntityChange,
    ImportHistory,
    SystemOperation,
)
from src.exceptions.domain import EntityNotFoundException


class AuditRepository:
    """Data Access Repository for Audit & Operational History Entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_audit_event(self, event_id: str) -> AuditEvent:
        """Retrieve audit event record by UUID."""
        record = self._session.query(AuditEvent).filter_by(id=event_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="AuditEvent", entity_id=event_id)
        return record

    def create_audit_event(self, event: AuditEvent) -> AuditEvent:
        """Add new audit event record."""
        self._session.add(event)
        self._session.flush()
        return event

    def create_entity_change(self, change: EntityChange) -> EntityChange:
        """Add new field-level entity change record."""
        self._session.add(change)
        self._session.flush()
        return change

    def create_import_history(self, history: ImportHistory) -> ImportHistory:
        """Add new import execution history record."""
        self._session.add(history)
        self._session.flush()
        return history

    def create_system_operation(self, operation: SystemOperation) -> SystemOperation:
        """Add new system operation log record."""
        self._session.add(operation)
        self._session.flush()
        return operation

    def list_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[AuditEvent]:
        """List audit events optionally filtered by entity or event type."""
        query = self._session.query(AuditEvent)
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if entity_id:
            query = query.filter_by(entity_id=entity_id)
        if event_type:
            query = query.filter_by(event_type=event_type)
        return query.order_by(AuditEvent.event_timestamp.desc()).all()

    def list_import_history(self, source_system: Optional[str] = None) -> List[ImportHistory]:
        """List import execution records optionally filtered by source system."""
        query = self._session.query(ImportHistory).filter_by(is_deleted=False)
        if source_system:
            query = query.filter_by(source_system=source_system)
        return query.order_by(ImportHistory.started_at.desc()).all()

    def list_operations(self, component: Optional[str] = None) -> List[SystemOperation]:
        """List system operation records optionally filtered by component."""
        query = self._session.query(SystemOperation)
        if component:
            query = query.filter_by(component=component)
        return query.order_by(SystemOperation.started_at.desc()).all()
