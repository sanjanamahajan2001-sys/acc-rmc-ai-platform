"""Validation Operational Execution Report & Configuration Snapshot.

This module provides immutable operational execution reporting and configuration snapshot models for WS-03.3 Phase 7.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.validation.version import RULE_REGISTRY_VERSION, VALIDATION_ENGINE_VERSION


class ValidationConfigurationSnapshot(BaseModel):
    """Immutable snapshot of validation engine configuration state at execution time for audit reproducibility."""

    engine_version: str = Field(default=VALIDATION_ENGINE_VERSION, description="Validation Engine version.")
    enabled_tiers: List[str] = Field(default_factory=list, description="List of enabled validation tier identifiers.")
    rule_registry_version: str = Field(default=RULE_REGISTRY_VERSION, description="Validation rule registry version.")
    rule_count: int = Field(..., ge=0, description="Total active rules in registry at runtime.")
    profiling_enabled: bool = Field(default=False, description="Flag indicating whether profiling was enabled.")
    execution_mode: str = Field(default="SINGLE_THREADED", description="Execution mode (SINGLE_THREADED, BATCH, PARALLEL).")
    snapshot_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC snapshot creation timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class ValidationExecutionReport(BaseModel):
    """Immutable operational report carrying performance diagnostics, metrics, and configuration snapshot for a validation run."""

    dataset_id: str = Field(..., description="Unique dataset evaluation identifier.")
    correlation_id: Optional[str] = Field(None, description="Request correlation tracing identifier.")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp.")
    total_rows: int = Field(..., ge=0, description="Total rows submitted for validation.")
    valid_rows: int = Field(..., ge=0, description="Count of valid rows passing validation.")
    invalid_rows: int = Field(..., ge=0, description="Count of invalid rows failing validation.")
    rows_passed_tier1: int = Field(..., ge=0, description="Rows passing Tier 1 structural validation.")
    rows_passed_tier2: int = Field(..., ge=0, description="Rows passing Tier 2 primitive type validation.")
    rows_passed_tier3: int = Field(..., ge=0, description="Rows passing Tier 3 range/enum validation.")
    rows_passed_tier4: int = Field(..., ge=0, description="Rows passing Tier 4 cross-field validation.")
    rows_passed_tier5: int = Field(..., ge=0, description="Rows passing Tier 5 dataset validation.")
    rows_quarantined: int = Field(..., ge=0, description="Count of rows quarantined.")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Calculated dataset quality score.")
    per_tier_duration_ms: Dict[str, float] = Field(default_factory=dict, description="Execution latency breakdown per tier in milliseconds.")
    total_execution_duration_ms: float = Field(..., ge=0.0, description="Total validation execution latency in milliseconds.")
    rows_per_second: float = Field(..., ge=0.0, description="Validation throughput processing rate in rows/sec.")
    peak_memory_mb: Optional[float] = Field(None, ge=0.0, description="Peak memory consumption in MB.")
    config_snapshot: Optional[ValidationConfigurationSnapshot] = Field(None, description="Reproducibility configuration snapshot at runtime.")

    model_config = ConfigDict(frozen=True, extra="forbid")
