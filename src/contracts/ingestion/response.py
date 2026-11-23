"""Ingestion Response, Diagnostic, and Result DTO Contracts."""

from typing import List, Optional
from pydantic import Field
from src.contracts.ingestion.base import BaseIngestionModel, CONTRACT_VERSION


class ValidationDiagnosticDTO(BaseIngestionModel):
    """Row/Field Validation Diagnostic Message Contract."""

    field_name: str = Field(..., description="Target property or column header name.")
    error_code: str = Field(..., description="Unique technical error classification code.")
    message: str = Field(..., description="Human-readable diagnostic explanation.")
    severity: str = Field(default="CRITICAL", description="Diagnostic severity level (CRITICAL, WARNING, INFO).")
    row_index: Optional[int] = Field(None, description="0-indexed row number for bulk dataset imports.")


class IngestionResultResponseDTO(BaseIngestionModel):
    """Unified Ingestion Transaction Result Contract."""

    ingestion_status: str = Field(..., description="Result status (SUCCESS, QUARANTINED, FAILED).")
    batch_number: Optional[str] = Field(None, description="Persisted batch identification number.")
    records_processed: int = Field(..., ge=0, description="Total batch/record count processed.")
    diagnostics: List[ValidationDiagnosticDTO] = Field(default_factory=list, description="List of diagnostic validation messages.")
    feature_vector_id: Optional[str] = Field(None, description="Generated canonical AI feature vector UUID if registered.")
    processing_time_ms: Optional[float] = Field(None, ge=0.0, description="Total ingestion transaction processing duration in milliseconds.")
    contract_version: str = Field(default=CONTRACT_VERSION, description="Active ingestion contract schema version.")
    correlation_id: Optional[str] = Field(None, description="System-wide correlation tracking identifier.")
    trace_id: Optional[str] = Field(None, description="Distributed telemetry trace identifier.")
