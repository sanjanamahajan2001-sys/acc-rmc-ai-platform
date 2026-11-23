"""WS-03.4 Phase 4 Multi-Tier Validation Integration Result & Preview Contracts.

This module provides immutable Pydantic V2 models for ValidatedWorksheetChunk, ValidationPreview,
ValidationSummary, PreviewStatistics, and ValidationSessionSummary.
Strict Pydantic V2 models with ConfigDict(frozen=True, extra="forbid").
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.mapping.contracts import CanonicalRow


class ValidationPreviewRow(BaseModel):
    """Immutable preview record for an individual row, combining raw worksheet metadata, Excel row index, CanonicalRow, and validation results."""

    preview_row_id: str = Field(default_factory=lambda: f"PRV-{uuid.uuid4().hex[:12].upper()}", description="Stable unique preview row ID.")
    validation_trace_id: str = Field(default_factory=lambda: f"TRC-{uuid.uuid4().hex[:12].upper()}", description="Unique validation execution trace ID.")
    worksheet_name: str = Field(..., description="Source worksheet tab name.")
    excel_row_number: int = Field(..., ge=1, description="1-indexed physical Excel spreadsheet row number.")
    canonical_row: CanonicalRow = Field(..., description="Mapped intermediate CanonicalRow object.")
    validation_status: str = Field(..., description="Validation outcome status (PASSED, WARNING, CRITICAL, QUARANTINED).")
    is_valid: bool = Field(..., description="Boolean indicating whether row passed all validation rules.")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Row quality score (0.0 to 100.0).")
    severity: str = Field(..., description="Highest severity level encountered (NONE, INFO, WARNING, ERROR, CRITICAL).")
    quarantine_recommended: bool = Field(..., description="Flag indicating if row should be routed to Quarantine payload.")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="List of warning error details.")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of critical validation error details.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidatedWorksheetChunk(BaseModel):
    """Immutable contract carrying validation results for a single worksheet chunk."""

    worksheet_name: str = Field(..., description="Source worksheet tab name.")
    chunk_index: int = Field(..., ge=0, description="0-indexed chunk position in stream.")
    starting_row: int = Field(..., ge=0, description="First row index in chunk.")
    ending_row: int = Field(..., ge=0, description="Last row index in chunk.")
    total_rows: int = Field(..., ge=0, description="Total rows evaluated in chunk.")
    valid_rows_count: int = Field(..., ge=0, description="Count of rows passing validation.")
    quarantined_rows_count: int = Field(..., ge=0, description="Count of rows recommended for quarantine.")
    preview_rows: List[ValidationPreviewRow] = Field(default_factory=list, description="Immutable preview records per row.")
    tier5_dataset_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Dataset-level Tier 5 validation error details.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class PreviewStatistics(BaseModel):
    """Immutable metrics aggregating validation preview results across a file or session."""

    total_rows_evaluated: int = Field(..., ge=0, description="Total rows submitted for validation.")
    valid_rows_count: int = Field(..., ge=0, description="Total valid rows.")
    warning_rows_count: int = Field(..., ge=0, description="Total rows with non-critical warnings.")
    quarantined_rows_count: int = Field(..., ge=0, description="Total quarantined rows.")
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Aggregate quality score.")
    validation_duration_ms: float = Field(..., ge=0.0, description="Total validation latency in milliseconds.")
    preview_generation_duration_ms: float = Field(..., ge=0.0, description="Latency incurred generating preview contracts.")
    rows_per_second: float = Field(..., ge=0.0, description="Validation throughput rate in rows/sec.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationSummary(BaseModel):
    """Immutable summary compiling validation execution outcome for a single file."""

    session_id: Optional[str] = Field(None, description="Parent upload session code.")
    file_id: Optional[str] = Field(None, description="Parent file task code.")
    filename: str = Field(..., description="Source file name.")
    profile_id: Optional[str] = Field(None, description="Matched WS-03.2 import profile code.")
    statistics: PreviewStatistics = Field(..., description="Aggregated validation preview statistics.")
    validated_chunks: List[ValidatedWorksheetChunk] = Field(default_factory=list, description="Validated worksheet chunk contracts.")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC validation timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationPreview(BaseModel):
    """Immutable validation preview payload designed to power frontend visualization in Phase 5."""

    session_id: Optional[str] = Field(None, description="Parent upload session code.")
    file_id: Optional[str] = Field(None, description="Parent file task code.")
    filename: str = Field(..., description="Source file name.")
    summary: ValidationSummary = Field(..., description="Parent validation summary.")
    preview_rows: List[ValidationPreviewRow] = Field(default_factory=list, description="Flattened sample list of row previews.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC creation timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationSessionSummary(BaseModel):
    """Immutable session-level summary aggregating multi-file validation results."""

    session_id: str = Field(..., description="Unique upload session code.")
    user_id: str = Field(..., description="Operator identity code.")
    total_files: int = Field(..., ge=0, description="Total files in session.")
    successful_files: int = Field(default=0, ge=0, description="Count of files completely valid.")
    partially_valid_files: int = Field(default=0, ge=0, description="Count of files with partial warnings/quarantined rows.")
    failed_files: int = Field(default=0, ge=0, description="Count of files failing completely.")
    total_files_evaluated: int = Field(..., ge=0, description="Total files evaluated.")
    total_rows: int = Field(..., ge=0, description="Total aggregate rows evaluated.")
    total_rows_evaluated: int = Field(..., ge=0, description="Total aggregate rows evaluated.")
    total_valid_rows: int = Field(..., ge=0, description="Total aggregate valid rows.")
    total_quarantined_rows: int = Field(..., ge=0, description="Total aggregate quarantined rows.")
    total_quarantined: int = Field(..., ge=0, description="Total aggregate quarantined rows.")
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Weighted average quality score across session.")
    per_file_statistics: List[Dict[str, Any]] = Field(default_factory=list, description="Granular per-file statistics breakdown.")
    file_summaries: List[ValidationSummary] = Field(default_factory=list, description="Per-file validation summaries.")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC evaluation timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")
