"""Configuration-Driven Enterprise Ingestion Limits for WS-03.4 Excel Dataset Import Subsystem.

This module provides the central IngestionConfig Pydantic V2 model loading server-side ingestion limits.
All limits are strictly configuration-driven and loaded dynamically from environment or defaults.
"""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class IngestionConfig(BaseModel):
    """Configuration-driven enterprise ingestion limits model."""

    max_files_per_session: int = Field(default=20, ge=1, le=100, description="Maximum files allowed per upload session.")
    max_file_size_bytes: int = Field(default=104_857_600, ge=1024, description="Maximum allowed file size in bytes (default: 100 MB).")
    max_worksheets_per_file: int = Field(default=50, ge=1, description="Maximum worksheets allowed per Excel workbook.")
    max_rows_per_worksheet: int = Field(default=100_000, ge=1, description="Maximum rows allowed per worksheet.")
    max_total_session_rows: int = Field(default=500_000, ge=1, description="Maximum total aggregate rows allowed per session.")
    allowed_extensions: List[str] = Field(default_factory=lambda: [".xlsx", ".xls", ".csv"], description="Supported spreadsheet extensions.")
    chunk_size_rows: int = Field(default=1000, ge=100, le=5000, description="Streaming reader row chunk size.")
    duplicate_hash_check_enabled: bool = Field(default=True, description="Flag to enable SHA-256 duplicate checksum checking.")
    worker_pool_max_threads: int = Field(default=4, ge=1, le=16, description="Maximum concurrent background worker threads.")
    backpressure_queue_limit: int = Field(default=50, ge=1, description="Maximum queued tasks before backpressure HTTP 429 response.")
    session_ttl_seconds: int = Field(default=86400, ge=60, description="Upload session state TTL retention in seconds (default: 24h).")

    model_config = ConfigDict(frozen=True, extra="forbid")


def get_default_ingestion_config() -> IngestionConfig:
    """Return default configuration instance."""
    return IngestionConfig()
