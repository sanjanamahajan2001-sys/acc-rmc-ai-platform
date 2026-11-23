"""Mapping Persistence Model Definition."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from src.database.base import BaseModel, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, OptimisticLockMixin


class SessionMappingModel(BaseModel, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, OptimisticLockMixin):
    """Production Database Entity for Session Mapping Execution Results (sys_session_mappings)."""

    __tablename__ = "sys_session_mappings"

    session_id: Column = Column(String(64), nullable=False, index=True)
    dataset_id: Column = Column(String(64), nullable=False)
    import_profile_id: Column = Column(String(64), nullable=False)
    mapping_execution_id: Column = Column(String(64), nullable=False, unique=True, index=True)
    mapping_engine_version: Column = Column(String(32), default="1.0.0", nullable=False)
    summary_json: Column = Column(Text, nullable=False)


class IngestionJobModel(BaseModel, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, OptimisticLockMixin):
    """Production Database Entity for Ingestion Execution Jobs (sys_ingestion_jobs)."""

    __tablename__ = "sys_ingestion_jobs"

    job_id: Column = Column(String(64), nullable=False, unique=True, index=True)
    session_id: Column = Column(String(64), nullable=False, index=True)
    dataset_id: Column = Column(String(64), nullable=False)
    mapping_execution_id: Column = Column(String(64), nullable=False)
    status: Column = Column(String(32), default="PENDING", nullable=False, index=True)
    current_stage: Column = Column(String(64), default="Upload / Input Verification", nullable=False)
    progress_percent: Column = Column(String(16), default="0%", nullable=False)
    files_total: Column = Column(String(16), default="0", nullable=False)
    files_processed: Column = Column(String(16), default="0", nullable=False)
    worksheets_discovered: Column = Column(String(16), default="0", nullable=False)
    worksheets_processed: Column = Column(String(16), default="0", nullable=False)
    operational_records_detected: Column = Column(String(16), default="0", nullable=False)
    records_persisted: Column = Column(String(16), default="0", nullable=False)
    records_rejected: Column = Column(String(16), default="0", nullable=False)
    excluded_records: Column = Column(String(16), default="0", nullable=False)
    logs_json: Column = Column(Text, default="[]", nullable=False)
    failure_reason: Column = Column(Text, nullable=True)
    completed_at: Column = Column(DateTime, nullable=True)

