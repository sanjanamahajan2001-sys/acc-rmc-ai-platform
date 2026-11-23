"""Quarantine Payload Contract.

This module provides immutable contract DTOs describing rejected invalid datasets for downstream WS-03.7 processing.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.contracts import DatasetValidationResult, FieldErrorDetail


class QuarantinePayloadContract(BaseModel):
    """Immutable payload contract passed to WS-03.7 Quarantine when a dataset has critical validation failures."""

    dataset_id: str = Field(..., description="Unique dataset evaluation tracking code.")
    import_profile_id: Optional[str] = Field(None, description="Active import profile ID.")
    source_channel: str = Field(..., description="Source ingestion channel (EXCEL, MANUAL, REST_API).")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Original raw ingestion payload.")
    failed_rows: List[CanonicalRow] = Field(default_factory=list, description="Collection of invalid canonical rows.")
    critical_errors: List[FieldErrorDetail] = Field(default_factory=list, description="All CRITICAL severity validation errors.")
    validation_result: DatasetValidationResult = Field(..., description="Complete evaluation result report.")
    quarantined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC quarantine timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")
