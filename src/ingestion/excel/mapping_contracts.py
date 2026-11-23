"""WS-03.4 Phase 3 Canonical Mapping Integration Result Contracts.

This module provides immutable Pydantic V2 models for MappedWorksheetChunk, MappingStatistics, and MappingExecutionSummary.
Strict Pydantic V2 models with ConfigDict(frozen=True, extra="forbid").
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.mapping.contracts import CanonicalRow


class MappingStatistics(BaseModel):
    """Immutable operational metrics compiled during a canonical mapping execution."""

    processed_rows: int = Field(..., ge=0, description="Total raw rows submitted for mapping.")
    mapped_rows: int = Field(..., ge=0, description="Count of successfully mapped CanonicalRow objects.")
    skipped_rows: int = Field(..., ge=0, description="Count of skipped or empty rows.")
    rows_fully_mapped: int = Field(default=0, ge=0, description="Rows where all non-empty cells were successfully mapped.")
    rows_with_partial_mapping: int = Field(default=0, ge=0, description="Rows with a mix of mapped and unmapped headers.")
    rows_failed_mapping: int = Field(default=0, ge=0, description="Rows encountering unrecoverable or mapping failures.")
    unmapped_columns_count: int = Field(..., ge=0, description="Count of unmapped raw headers.")
    unknown_header_count: int = Field(default=0, ge=0, description="Count of unrecognized headers.")
    direct_matches_used: int = Field(default=0, ge=0, description="Count of exact/alias/profile header resolutions.")
    fuzzy_matches_used: int = Field(default=0, ge=0, description="Count of fuzzy header resolutions.")
    mapping_error_count: int = Field(..., ge=0, description="Count of recoverable mapping errors.")
    elapsed_time_ms: float = Field(..., ge=0.0, description="Total mapping latency in milliseconds.")
    rows_per_second: float = Field(..., ge=0.0, description="Mapping throughput rate in rows/sec.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class MappedWorksheetChunk(BaseModel):
    """Immutable contract carrying mapped CanonicalRow objects for a worksheet chunk."""

    worksheet_name: str = Field(..., description="Source worksheet tab name.")
    chunk_index: int = Field(..., ge=0, description="0-indexed chunk position in stream.")
    starting_row: int = Field(..., ge=0, description="First row index in chunk.")
    ending_row: int = Field(..., ge=0, description="Last row index in chunk.")
    canonical_rows: List[CanonicalRow] = Field(default_factory=list, description="Mapped intermediate CanonicalRow objects.")
    unmapped_headers: List[str] = Field(default_factory=list, description="Headers that could not be mapped to dictionary fields.")
    mapping_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Recoverable row-level mapping error details.")
    mapping_version: str = Field(default="1.0.0", description="Canonical mapping engine version.")
    dictionary_version: str = Field(default="1.0.0", description="Canonical data dictionary version.")
    worksheet_checksum: Optional[str] = Field(None, description="SHA-256 hash reference for raw worksheet content.")
    mapping_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp when chunk was mapped.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class MappingExecutionSummary(BaseModel):
    """Immutable execution summary compiling mapping results across an entire workbook or multi-file mapping session."""

    session_id: Optional[str] = Field(None, description="Parent upload session code.")
    file_id: Optional[str] = Field(None, description="Parent file task code.")
    filename: str = Field(..., description="Source file name.")
    profile_id: Optional[str] = Field(None, description="Matched WS-03.2 import profile code.")
    profile_version: Optional[str] = Field(None, description="Matched WS-03.2 import profile version.")
    worksheet_chunks: List[MappedWorksheetChunk] = Field(default_factory=list, description="Chunked mapping outputs.")
    statistics: MappingStatistics = Field(..., description="Aggregated mapping statistics.")
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")
