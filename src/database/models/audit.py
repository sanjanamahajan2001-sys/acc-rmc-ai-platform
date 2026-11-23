"""Enterprise Audit Persistence & Operational History ORM Models.

This module provides normalized ORM entities for immutable audit events, entity field changes,
import execution history, and system operation logs with comprehensive indexing.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import (
    AuditMetadataMixin,
    BaseModel,
    CreatedAtMixin,
    GUID,
    OptimisticLockMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
)


class AuditEvent(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "audit_events"

    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(64), default="BUSINESS", nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    performed_by_user: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    plant_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("mst_plants.id"), nullable=True, index=True)
    batch_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=True, index=True)
    prediction_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("ai_predictions.id"), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), default="INFO", nullable=False)
    result: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    changes: Mapped[List["EntityChange"]] = relationship("EntityChange", back_populates="audit_event", cascade="all, delete-orphan")


class EntityChange(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "audit_entity_changes"

    audit_event_id: Mapped[str] = mapped_column(GUID, ForeignKey("audit_events.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    change_type: Mapped[str] = mapped_column(String(32), default="UPDATE", nullable=False)

    audit_event: Mapped["AuditEvent"] = relationship("AuditEvent", back_populates="changes")


class ImportHistory(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "audit_import_history"

    source_system: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    imported_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class SystemOperation(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "audit_system_operations"

    operation_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    component: Mapped[str] = mapped_column(String(64), default="SYSTEM", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
