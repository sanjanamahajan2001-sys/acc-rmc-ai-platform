"""WS-03.2 Canonical Mapping Engine Integration Orchestrator for WS-03.4 Phase 3.

This module provides ExcelMappingService bridging Phase 2 StreamingExcelReader with WS-03.2 CanonicalColumnMappingEngine.
Transforms RawWorksheetChunk contracts into MappedWorksheetChunk objects, preserving worksheet metadata and original row indexes.
Advances session state strictly: READING_WORKSHEETS -> MAPPING.
Zero validation, zero database persistence, zero REST APIs, zero frontend UI.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
from src.ingestion.excel.contracts import FileIngestionLifecycle, RawWorksheetChunk
from src.ingestion.excel.mapping_contracts import (
    MappedWorksheetChunk,
    MappingExecutionSummary,
    MappingStatistics,
)
from src.ingestion.excel.reader import StreamingExcelReader
from src.ingestion.excel.session_manager import UploadSessionManager
from src.mapping.contracts import CanonicalRow
from src.mapping.engine import CanonicalColumnMappingEngine
from src.mapping.models import ImportProfile


class ExcelMappingService:
    """Enterprise mapping orchestrator bridging Excel streaming reader with WS-03.2 Canonical Mapping Engine."""

    def __init__(self, session_manager: Optional[UploadSessionManager] = None) -> None:
        self._mapping_engine = CanonicalColumnMappingEngine()
        self._reader = StreamingExcelReader()
        self._session_manager = session_manager

    def map_chunk(
        self,
        raw_chunk: RawWorksheetChunk,
        profile: Optional[ImportProfile] = None,
    ) -> MappedWorksheetChunk:
        """Map a single RawWorksheetChunk into a MappedWorksheetChunk containing CanonicalRow objects."""
        canonical_rows: List[CanonicalRow] = []
        unmapped_headers_set = set()
        mapping_errors: List[Dict[str, Any]] = []

        for raw_row in raw_chunk.rows:
            try:
                mapped_row = self._mapping_engine.map_row(
                    raw_row=raw_row.data,
                    profile=profile,
                    row_index=raw_row.row_index,
                    sheet_name=raw_chunk.worksheet_name,
                )
                canonical_rows.append(mapped_row)

                # Capture unmapped headers by auditing resolved field mapping
                for audit in mapped_row.audit_records:
                    if audit.resolution_strategy == "UNMAPPED":
                        unmapped_headers_set.add(audit.original_header)

                # Check for raw headers that produced zero mapped fields or explicitly returned UNMAPPED
                mapped_orig_headers = {a.original_header for a in mapped_row.audit_records}
                for header_key in raw_row.data.keys():
                    if header_key not in mapped_orig_headers:
                        unmapped_headers_set.add(header_key)

            except Exception as e:
                # Recoverable row-level mapping error handler
                mapping_errors.append(
                    {
                        "row_index": raw_row.row_index,
                        "worksheet_name": raw_chunk.worksheet_name,
                        "error_message": str(e),
                        "raw_data": raw_row.data,
                    }
                )

        return MappedWorksheetChunk(
            worksheet_name=raw_chunk.worksheet_name,
            chunk_index=raw_chunk.chunk_index,
            starting_row=raw_chunk.starting_row,
            ending_row=raw_chunk.ending_row,
            canonical_rows=canonical_rows,
            unmapped_headers=sorted(list(unmapped_headers_set)),
            mapping_errors=mapping_errors,
        )

    def map_file(
        self,
        file_path: str,
        worksheet_name: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        profile: Optional[ImportProfile] = None,
        session_id: Optional[str] = None,
        file_id: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> MappingExecutionSummary:
        """Stream and map an entire Excel/CSV file into MappingExecutionSummary, advancing session state to MAPPING."""
        t0 = time.perf_counter()

        # Lifecycle integration: advance task state to MAPPING if session_manager provided
        if self._session_manager and session_id and file_id:
            self._session_manager.update_task_status(
                session_id=session_id,
                file_id=file_id,
                new_status=FileIngestionLifecycle.MAPPING,
                step_description="Executing WS-03.2 Canonical Column Mapping",
            )

        mapped_chunks: List[MappedWorksheetChunk] = []
        total_raw_rows = 0
        total_mapped_rows = 0
        total_skipped_rows = 0
        total_error_count = 0
        unmapped_headers_all = set()

        raw_chunks_gen = self._reader.stream_worksheet_chunks(
            file_path=file_path,
            worksheet_name=worksheet_name,
            file_bytes=file_bytes,
            chunk_size=chunk_size,
        )

        for raw_chunk in raw_chunks_gen:
            chunk_mapped = self.map_chunk(raw_chunk, profile=profile)
            mapped_chunks.append(chunk_mapped)

            total_raw_rows += len(raw_chunk.rows)
            total_mapped_rows += len(chunk_mapped.canonical_rows)
            total_error_count += len(chunk_mapped.mapping_errors)
            unmapped_headers_all.update(chunk_mapped.unmapped_headers)

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        throughput = (total_raw_rows / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0

        rows_full = 0
        rows_partial = 0
        direct_matches = 0
        fuzzy_matches = 0

        for chunk in mapped_chunks:
            for crow in chunk.canonical_rows:
                unmapped_in_row = sum(1 for a in crow.audit_records if a.resolution_strategy == "UNMAPPED")
                mapped_in_row = len(crow.audit_records) - unmapped_in_row
                if unmapped_in_row == 0:
                    rows_full += 1
                elif mapped_in_row > 0:
                    rows_partial += 1

                for audit in crow.audit_records:
                    if audit.resolution_strategy in ("EXACT", "ALIAS", "REGEX", "PROFILE"):
                        direct_matches += 1
                    elif audit.resolution_strategy == "FUZZY":
                        fuzzy_matches += 1

        stats = MappingStatistics(
            processed_rows=total_raw_rows,
            mapped_rows=total_mapped_rows,
            skipped_rows=total_skipped_rows,
            rows_fully_mapped=rows_full,
            rows_with_partial_mapping=rows_partial,
            rows_failed_mapping=total_error_count,
            unmapped_columns_count=len(unmapped_headers_all),
            unknown_header_count=len(unmapped_headers_all),
            direct_matches_used=direct_matches,
            fuzzy_matches_used=fuzzy_matches,
            mapping_error_count=total_error_count,
            elapsed_time_ms=elapsed_ms,
            rows_per_second=throughput,
        )

        prof_id = profile.id if profile else None
        prof_ver = profile.profile_version if profile else None

        return MappingExecutionSummary(
            session_id=session_id,
            file_id=file_id,
            filename=file_path,
            profile_id=prof_id,
            profile_version=prof_ver,
            worksheet_chunks=mapped_chunks,
            statistics=stats,
            executed_at=datetime.now(timezone.utc),
        )
