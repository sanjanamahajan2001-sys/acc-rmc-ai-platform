"""WS-03.4 Excel Dataset Import Subsystem - Phase 1, 2, 3 & 4 Package Exports.

This package exports all Phase 1-4 public classes, DTO contracts, enums, configuration models, scanner, reader, mapping service, validation service, and session managers.
"""

from src.ingestion.excel.checksum import DuplicateDetector, calculate_bytes_sha256, calculate_stream_sha256
from src.ingestion.excel.config import IngestionConfig, get_default_ingestion_config
from src.ingestion.excel.contracts import (
    FileIngestionLifecycle,
    FileUploadTask,
    RawRow,
    RawWorksheetChunk,
    UploadSession,
    UploadSessionLifecycle,
    UploadSessionSummaryContract,
)
from src.ingestion.excel.mapping_contracts import (
    MappedWorksheetChunk,
    MappingExecutionSummary,
    MappingStatistics,
)
from src.ingestion.excel.mapping_service import ExcelMappingService
from src.ingestion.excel.reader import StreamingExcelReader
from src.ingestion.excel.scanner import WorkbookMetadata, WorkbookScanner
from src.ingestion.excel.session_manager import UploadSessionManager
from src.ingestion.excel.validation_contracts import (
    PreviewStatistics,
    ValidatedWorksheetChunk,
    ValidationPreview,
    ValidationPreviewRow,
    ValidationSessionSummary,
    ValidationSummary,
)
from src.ingestion.excel.validation_service import ExcelValidationService

__all__ = [
    # Configuration
    "IngestionConfig",
    "get_default_ingestion_config",

    # Contracts & Enums
    "UploadSessionLifecycle",
    "FileIngestionLifecycle",
    "FileUploadTask",
    "UploadSession",
    "UploadSessionSummaryContract",
    "RawRow",
    "RawWorksheetChunk",

    # Phase 2 Scanner & Streaming Reader
    "WorkbookMetadata",
    "WorkbookScanner",
    "StreamingExcelReader",

    # Phase 3 Mapping Integration & Service
    "MappedWorksheetChunk",
    "MappingStatistics",
    "MappingExecutionSummary",
    "ExcelMappingService",

    # Phase 4 Validation Integration & Service
    "ValidatedWorksheetChunk",
    "ValidationPreviewRow",
    "PreviewStatistics",
    "ValidationSummary",
    "ValidationPreview",
    "ValidationSessionSummary",
    "ExcelValidationService",

    # Infrastructural Managers & Helpers
    "UploadSessionManager",
    "calculate_bytes_sha256",
    "calculate_stream_sha256",
    "DuplicateDetector",
]
