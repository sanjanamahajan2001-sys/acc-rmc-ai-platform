"""Lifecycle Enumerations & Immutable Contracts for WS-03.4 Excel Dataset Import Subsystem.

This module provides all production lifecycle state enums, FileUploadTask, UploadSession, UploadSessionSummaryContract,
RawRow, and RawWorksheetChunk DTOs.
Strict Pydantic V2 models with ConfigDict(frozen=True, extra="forbid").
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UploadSessionLifecycle(str, Enum):
    """Lifecycle states for an entire multi-file UploadSession."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PROCESSING = "PROCESSING"
    PREVIEW_READY = "PREVIEW_READY"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class FileIngestionLifecycle(str, Enum):
    """Refined 16-state lifecycle for individual file upload tasks within an UploadSession."""

    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    UPLOAD_COMPLETED = "UPLOAD_COMPLETED"
    CHECKSUM_VERIFICATION = "CHECKSUM_VERIFICATION"
    SCANNING = "SCANNING"
    READING_WORKBOOK = "READING_WORKBOOK"
    READING_WORKSHEETS = "READING_WORKSHEETS"
    MAPPING = "MAPPING"
    VALIDATING = "VALIDATING"
    GENERATING_PREVIEW = "GENERATING_PREVIEW"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRY_PENDING = "RETRY_PENDING"
    DUPLICATE_REJECTED = "DUPLICATE_REJECTED"


class RawRow(BaseModel):
    """Immutable DTO carrying raw cell key-value pairs for a single extracted spreadsheet row."""

    row_index: int = Field(..., ge=0, description="0-indexed row position in worksheet.")
    data: Dict[str, Any] = Field(..., description="Raw column header to cell value mapping.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class RawWorksheetChunk(BaseModel):
    """Immutable chunk contract emitted by StreamingExcelReader carrying structured raw rows for downstream canonical mapping."""

    worksheet_name: str = Field(..., description="Source worksheet tab name.")
    chunk_index: int = Field(..., ge=0, description="0-indexed chunk position in stream.")
    starting_row: int = Field(..., ge=0, description="First row index in chunk.")
    ending_row: int = Field(..., ge=0, description="Last row index in chunk.")
    rows: List[RawRow] = Field(default_factory=list, description="Extracted raw row objects.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class FileUploadTask(BaseModel):
    """Immutable state model tracking an individual file upload task within an UploadSession."""

    file_id: str = Field(..., description="Unique file task code.")
    session_id: str = Field(..., description="Parent upload session code.")
    filename: str = Field(..., description="Original filename with extension.")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes.")
    checksum_sha256: Optional[str] = Field(None, description="Hex SHA-256 hash verified post-upload.")
    status: FileIngestionLifecycle = Field(default=FileIngestionLifecycle.QUEUED, description="Current 16-state lifecycle stage.")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Processing progress percentage.")
    current_step_description: str = Field(default="Enqueued in queue", description="Human-readable operational status text.")
    worksheet_names: List[str] = Field(default_factory=list, description="Discovered worksheet tab names.")
    selected_worksheet: Optional[str] = Field(None, description="Worksheet tab selected for ingestion.")
    import_profile_id: Optional[str] = Field(None, description="Matched WS-03.2 import profile code.")
    total_rows_found: int = Field(default=0, ge=0, description="Total rows scanned in file.")
    rows_mapped: int = Field(default=0, ge=0, description="Rows mapped via WS-03.2.")
    rows_valid: int = Field(default=0, ge=0, description="Rows passing WS-03.3 validation.")
    rows_invalid: int = Field(default=0, ge=0, description="Rows failing validation.")
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="WS-03.3 quality score (0.0 to 100.0).")
    error_message: Optional[str] = Field(None, description="Error message if task failed.")
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp when enqueued.")
    started_at: Optional[datetime] = Field(None, description="UTC timestamp processing started.")
    completed_at: Optional[datetime] = Field(None, description="UTC timestamp processing finished.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class UploadSession(BaseModel):
    """Immutable state model tracking an entire multi-file upload session."""

    session_id: str = Field(..., description="Unique upload session code.")
    user_id: str = Field(..., description="Operator identity code.")
    status: UploadSessionLifecycle = Field(default=UploadSessionLifecycle.CREATED, description="Overall session lifecycle stage.")
    files: List[FileUploadTask] = Field(default_factory=list, description="Ordered list of file upload tasks.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC creation timestamp.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC last update timestamp.")
    completed_at: Optional[datetime] = Field(None, description="UTC completion timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class UploadSessionSummaryContract(BaseModel):
    """Immutable operational summary contract aggregating session ingestion results across all files."""

    session_id: str = Field(..., description="Unique upload session code.")
    user_id: str = Field(..., description="Ingestion operator identity code.")
    created_at: datetime = Field(..., description="Session creation timestamp.")
    completed_at: Optional[datetime] = Field(None, description="Session completion timestamp.")
    total_files: int = Field(..., ge=0, description="Total files submitted in session.")
    completed_files: int = Field(..., ge=0, description="Files successfully processed without critical errors.")
    failed_files: int = Field(..., ge=0, description="Files failing validation with critical errors.")
    cancelled_files: int = Field(..., ge=0, description="Files cancelled by user.")
    duplicate_files: int = Field(..., ge=0, description="Files rejected due to SHA-256 duplicate checksums.")
    total_rows_processed: int = Field(..., ge=0, description="Total aggregate rows processed across all files.")
    total_rows_valid: int = Field(..., ge=0, description="Total rows passing validation.")
    total_rows_invalid: int = Field(..., ge=0, description="Total rows failing validation.")
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Weighted average quality score.")
    processing_duration_ms: float = Field(..., ge=0.0, description="Total session wall-clock processing latency.")
    file_summaries: List[Dict[str, Any]] = Field(default_factory=list, description="Per-file execution breakdown.")

    model_config = ConfigDict(frozen=True, extra="forbid")
