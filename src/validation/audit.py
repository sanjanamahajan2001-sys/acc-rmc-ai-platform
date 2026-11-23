"""Validation Execution Telemetry & Diagnostics Report.

This module provides operational diagnostics descriptors consumed by WS-03.10 Telemetry & Audit without modifying core validation logic.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ValidationExecutionReport(BaseModel):
    """Operational diagnostics report capturing execution metrics across validation tiers."""

    dataset_id: str = Field(..., description="Unique dataset evaluation tracking code.")
    execution_time_ms: float = Field(..., ge=0.0, description="Total validation execution time in milliseconds.")
    total_rows_processed: int = Field(..., ge=0, description="Total count of rows processed.")
    rows_passed_tier1: int = Field(..., ge=0, description="Count of rows passing Tier 1 structural validation.")
    rows_passed_tier2: int = Field(..., ge=0, description="Count of rows passing Tier 2 primitive validation.")
    rows_passed_tier3: int = Field(..., ge=0, description="Count of rows passing Tier 3 range/enum validation.")
    rows_passed_tier4: int = Field(..., ge=0, description="Count of rows passing Tier 4 cross-field validation.")
    rows_passed_tier5: int = Field(..., ge=0, description="Count of rows passing Tier 5 dataset validation.")
    rows_quarantined: int = Field(..., ge=0, description="Count of rows routed to quarantine due to critical errors.")
    avg_validation_time_per_row_ms: float = Field(..., ge=0.0, description="Average validation processing speed per row in milliseconds.")
    peak_memory_mb: Optional[float] = Field(None, ge=0.0, description="Peak memory usage during validation run in megabytes.")
    rule_execution_counts: Dict[str, int] = Field(default_factory=dict, description="Execution frequency per rule ID.")
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")
