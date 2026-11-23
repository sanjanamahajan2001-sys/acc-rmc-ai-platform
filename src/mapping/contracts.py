"""Canonical Row, Canonical Dataset, and Mapping Audit Record Data Contracts.

This module provides the intermediate, decoupled canonical data models output by the Canonical Column Mapping Engine
before handing off to the WS-03.1 DTO Builder and WS-03.3 Validation Engine.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MappingAuditRecord(BaseModel):
    """Detailed audit trace for a mapped column resolution."""

    original_header: str = Field(..., description="Raw column header from external file/source.")
    canonical_field_id: str = Field(..., description="Target CanonicalFieldID code.")
    resolution_strategy: str = Field(..., description="Matching strategy used (EXACT, ALIAS, REGEX, FUZZY, PROFILE).")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Levenshtein similarity score.")
    original_value: Optional[Any] = Field(None, description="Raw un-normalized value.")
    original_unit: Optional[str] = Field(None, description="Raw engineering unit if specified.")
    canonical_value: Optional[Any] = Field(None, description="Normalized canonical value.")
    canonical_unit: Optional[str] = Field(None, description="Standard canonical engineering unit.")
    profile_id: Optional[str] = Field(None, description="Import profile ID used.")
    profile_version: Optional[str] = Field(None, description="Import profile version used.")
    sheet_name: Optional[str] = Field(None, description="Source workbook sheet name.")
    row_index: Optional[int] = Field(None, description="0-indexed row position.")
    column_index: Optional[int] = Field(None, description="0-indexed column position.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC mapping timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class CanonicalRow(BaseModel):
    """Decoupled intermediate canonical representation of an ingested row."""

    row_index: int = Field(default=0, ge=0, description="0-indexed row position.")
    fields: Dict[str, Any] = Field(default_factory=dict, description="Map of CanonicalFieldID to normalized value.")
    audit_records: List[MappingAuditRecord] = Field(default_factory=list, description="Per-field mapping audit entries.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class CanonicalDataset(BaseModel):
    """Container for a collection of CanonicalRow records."""

    profile_id: str = Field(..., description="Import profile ID used for mapping.")
    profile_version: str = Field(..., description="Import profile semantic version.")
    rows: List[CanonicalRow] = Field(default_factory=list, description="List of mapped canonical rows.")

    model_config = ConfigDict(frozen=True, extra="forbid")
