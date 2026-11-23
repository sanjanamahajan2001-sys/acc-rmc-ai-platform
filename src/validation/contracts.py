"""Validation Contracts and Data Transfer Objects.

This module provides immutable Pydantic V2 models for field error details, validation results, and execution contexts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier


class FieldErrorDetail(BaseModel):
    """Granular detail for a validation failure or warning on a specific field or row."""

    field_id: str = Field(..., description="Target CanonicalFieldID or header name.")
    original_header: Optional[str] = Field(None, description="Raw column title from external source.")
    rule_id: str = Field(..., description="Unique validation rule code (e.g. ACC_VAL_001).")
    tier: ValidationTier = Field(..., description="Validation pipeline tier.")
    severity: ValidationSeverity = Field(..., description="Failure severity classification.")
    error_code: str = Field(..., description="Standardized error code string.")
    message: str = Field(..., description="Human-readable error or warning explanation.")
    invalid_value: Optional[Any] = Field(None, description="The raw or coerced value that triggered failure.")
    category: Optional[ValidationCategory] = Field(None, description="Domain categorization tag.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationContext(BaseModel):
    """Runtime context passed through validation rules during engine execution."""

    profile_id: Optional[str] = Field(None, description="Active import profile ID.")
    profile_version: Optional[str] = Field(None, description="Active import profile version.")
    plant_id: Optional[str] = Field(None, description="Target plant ID.")
    sheet_name: Optional[str] = Field(None, description="Workbook sheet name.")
    source_channel: str = Field(default="EXCEL", description="Source ingestion channel (EXCEL, MANUAL, REST_API).")
    execution_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp.")
    options: Dict[str, Any] = Field(default_factory=dict, description="Custom execution flags and options.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class RowValidationResult(BaseModel):
    """Validation result for a single canonical row."""

    row_index: int = Field(..., ge=0, description="0-indexed row position.")
    is_valid: bool = Field(..., description="True if no CRITICAL errors exist.")
    has_warnings: bool = Field(default=False, description="True if WARNING/INFO issues exist.")
    errors: List[FieldErrorDetail] = Field(default_factory=list, description="Per-field validation error list.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationSummaryReport(BaseModel):
    """Aggregated summary statistics for a validated dataset."""

    total_records: int = Field(..., ge=0, description="Total records evaluated.")
    valid_records_count: int = Field(..., ge=0, description="Count of records cleared for persistence.")
    critical_errors_count: int = Field(..., ge=0, description="Count of CRITICAL failures.")
    error_count: int = Field(..., ge=0, description="Count of ERROR level failures.")
    warning_count: int = Field(..., ge=0, description="Count of WARNING level issues.")
    info_count: int = Field(..., ge=0, description="Count of INFO level notifications.")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Deterministic quality score (0.0 to 100.0).")

    model_config = ConfigDict(frozen=True, extra="forbid")


class DatasetValidationResult(BaseModel):
    """Validation result for a complete collection of canonical rows."""

    dataset_id: str = Field(..., description="Unique dataset evaluation tracking code.")
    is_valid: bool = Field(..., description="True if all records passed without CRITICAL errors.")
    summary: ValidationSummaryReport = Field(..., description="Aggregated quality summary statistics.")
    row_results: List[RowValidationResult] = Field(default_factory=list, description="Per-row validation results.")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC validation timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


# Alias for backward compatibility and simple validation payloads
ValidationResult = DatasetValidationResult
