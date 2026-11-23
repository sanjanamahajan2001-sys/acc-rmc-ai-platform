"""Audit Persistence & Operational History Orchestration Service.

This module provides business services for persisting audit events, field-level entity changes,
import execution history, and system operations while validating optional foreign keys.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from src.database.models.ai import Prediction
from src.database.models.audit import (
    AuditEvent,
    EntityChange,
    ImportHistory,
    SystemOperation,
)
from src.database.models.master import Plant
from src.database.models.production import Batch
from src.database.repositories.audit_repository import AuditRepository
from src.database.repositories.master_repository import MasterRepository
from src.database.repositories.production_repository import ProductionRepository
from src.exceptions.domain import EntityNotFoundException
from src.logging import get_logger

logger = get_logger("src.database.services.audit_persistence", component="database")


class AuditPersistenceService:
    """Audit Persistence & Operational History Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._audit_repo = AuditRepository(session)
        self._plant_repo = MasterRepository(Plant, session)
        self._prod_repo = ProductionRepository(session)

    def log_audit_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        event_category: str = "BUSINESS",
        performed_by_user: Optional[str] = "SYSTEM",
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        prediction_id: Optional[str] = None,
        severity: str = "INFO",
        result: str = "SUCCESS",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Persist immutable audit event, validating optional foreign keys."""
        if plant_id:
            self._plant_repo.get_by_id(plant_id)
        if batch_id:
            self._prod_repo.get_by_id(batch_id)
        if prediction_id:
            pred = self._session.query(Prediction).filter_by(id=prediction_id).first()
            if pred is None:
                raise EntityNotFoundException(entity_name="Prediction", entity_id=prediction_id)

        event = AuditEvent(
            event_type=event_type,
            event_category=event_category,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by_user=performed_by_user,
            correlation_id=correlation_id,
            request_id=request_id,
            plant_id=plant_id,
            batch_id=batch_id,
            prediction_id=prediction_id,
            severity=severity,
            result=result,
            metadata_json=metadata_json,
        )
        self._audit_repo.create_audit_event(event)
        logger.info("Audit event persisted to database", event_type=event_type, entity_type=entity_type, entity_id=entity_id)
        return event

    def log_entity_change(
        self,
        audit_event_id: str,
        field_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        change_type: str = "UPDATE",
    ) -> EntityChange:
        """Persist field-level modification attached to an audit event."""
        event = self._audit_repo.get_audit_event(audit_event_id)

        change = EntityChange(
            audit_event_id=event.id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
        )
        self._audit_repo.create_entity_change(change)
        logger.info("Entity field change recorded", audit_event_id=audit_event_id, field_name=field_name)
        return change

    def record_import_history(
        self,
        source_system: str,
        file_name: str,
        file_checksum: Optional[str] = None,
        imported_by: Optional[str] = "DATA_PIPELINE",
        records_processed: int = 0,
        records_inserted: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
        status: str = "COMPLETED",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> ImportHistory:
        """Persist data import execution metadata."""
        history = ImportHistory(
            source_system=source_system,
            file_name=file_name,
            file_checksum=file_checksum,
            imported_by=imported_by,
            records_processed=records_processed,
            records_inserted=records_inserted,
            records_updated=records_updated,
            records_failed=records_failed,
            status=status,
            completed_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
        )
        self._audit_repo.create_import_history(history)
        logger.info("Import execution history recorded", source_system=source_system, file_name=file_name, status=status)
        return history

    def record_system_operation(
        self,
        operation_name: str,
        component: str = "SYSTEM",
        duration_ms: Optional[int] = None,
        status: str = "SUCCESS",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> SystemOperation:
        """Persist operational activity log."""
        operation = SystemOperation(
            operation_name=operation_name,
            component=component,
            duration_ms=duration_ms,
            status=status,
            completed_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
        )
        self._audit_repo.create_system_operation(operation)
        logger.info("System operation recorded", operation_name=operation_name, component=component, status=status)
        return operation
