"""WS-03.3 Shared Validation Engine Integration & Preview Generation Orchestrator for WS-03.4 Phase 4.

This module provides ExcelValidationService bridging Phase 3 MappedWorksheetChunk objects with WS-03.3 SharedValidationEngine.
Executes Tier 1–Tier 5 validation, computes row quality scores, and generates immutable ValidationPreview objects.
Advances task lifecycle strictly: MAPPING -> VALIDATING -> GENERATING_PREVIEW -> STOP.
Zero database writes, zero REST APIs, zero frontend UI, zero persistence.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
from src.ingestion.excel.contracts import FileIngestionLifecycle
from src.ingestion.excel.mapping_contracts import MappedWorksheetChunk, MappingExecutionSummary
from src.ingestion.excel.session_manager import UploadSessionManager
from src.ingestion.excel.validation_contracts import (
    PreviewStatistics,
    ValidatedWorksheetChunk,
    ValidationPreview,
    ValidationPreviewRow,
    ValidationSessionSummary,
    ValidationSummary,
)
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.contracts import ValidationContext
from src.validation.enums import ValidationSeverity
from src.validation.shared_validation_engine import SharedValidationEngine


class ExcelValidationService:
    """Enterprise validation & preview generator service bridging mapped Excel data with WS-03.3 SharedValidationEngine."""

    def __init__(self, session_manager: Optional[UploadSessionManager] = None) -> None:
        self._validation_engine = SharedValidationEngine(enable_profiling=True)
        self._session_manager = session_manager

    def validate_chunk(
        self,
        mapped_chunk: MappedWorksheetChunk,
        profile_id: Optional[str] = None,
        profile_version: Optional[str] = None,
    ) -> ValidatedWorksheetChunk:
        """Validate a single MappedWorksheetChunk through WS-03.3 Tiers 1-4 and generate ValidatedWorksheetChunk."""
        preview_rows: List[ValidationPreviewRow] = []
        valid_count = 0
        quarantine_count = 0

        context = ValidationContext(
            profile_id=profile_id,
            profile_version=profile_version,
            source_channel="EXCEL_INGESTION_CHUNK",
        )

        for crow in mapped_chunk.canonical_rows:
            # 1-indexed physical Excel spreadsheet row number (Header is row 1, data starts row 2+)
            excel_row_num = crow.row_index + 2

            # Execute WS-03.3 Tiers 1-4
            r_res = self._validation_engine.validate_row(crow, context=context)

            is_valid = r_res.is_valid
            # Compute row quality score (100.0 minus error penalties)
            penalty = sum(15.0 if e.severity == ValidationSeverity.CRITICAL else (5.0 if e.severity == ValidationSeverity.ERROR else 2.0) for e in r_res.errors)
            quality_score = max(0.0, 100.0 - penalty)
            quarantine = not is_valid

            if is_valid:
                valid_count += 1
            else:
                quarantine_count += 1

            # Categorize warnings and critical errors
            warnings: List[Dict[str, Any]] = [
                {"field_id": e.field_id, "rule_id": e.rule_id, "message": e.message, "severity": e.severity.value}
                for e in r_res.errors
                if e.severity != ValidationSeverity.CRITICAL
            ]
            errors: List[Dict[str, Any]] = [
                {"field_id": e.field_id, "rule_id": e.rule_id, "message": e.message, "severity": e.severity.value}
                for e in r_res.errors
                if e.severity == ValidationSeverity.CRITICAL
            ]

            max_severity = "NONE"
            if r_res.errors:
                severities = [e.severity for e in r_res.errors]
                if ValidationSeverity.CRITICAL in severities:
                    max_severity = "CRITICAL"
                elif ValidationSeverity.ERROR in severities:
                    max_severity = "ERROR"
                elif ValidationSeverity.WARNING in severities:
                    max_severity = "WARNING"
                else:
                    max_severity = "INFO"

            val_status = "PASSED" if is_valid else ("WARNING" if max_severity == "WARNING" else "QUARANTINED")

            preview_row = ValidationPreviewRow(
                worksheet_name=mapped_chunk.worksheet_name,
                excel_row_number=excel_row_num,
                canonical_row=crow,
                validation_status=val_status,
                is_valid=is_valid,
                quality_score=quality_score,
                severity=max_severity,
                quarantine_recommended=quarantine,
                warnings=warnings,
                errors=errors,
            )
            preview_rows.append(preview_row)

        return ValidatedWorksheetChunk(
            worksheet_name=mapped_chunk.worksheet_name,
            chunk_index=mapped_chunk.chunk_index,
            starting_row=mapped_chunk.starting_row,
            ending_row=mapped_chunk.ending_row,
            total_rows=len(mapped_chunk.canonical_rows),
            valid_rows_count=valid_count,
            quarantined_rows_count=quarantine_count,
            preview_rows=preview_rows,
            tier5_dataset_errors=[],
        )

    def validate_summary(
        self,
        mapping_summary: MappingExecutionSummary,
    ) -> ValidationPreview:
        """Execute Tiers 1-5 validation across an entire MappingExecutionSummary, generating ValidationPreview."""
        t0 = time.perf_counter()

        session_id = mapping_summary.session_id
        file_id = mapping_summary.file_id

        # 1. Lifecycle transition: MAPPING -> VALIDATING
        if self._session_manager and session_id and file_id:
            self._session_manager.update_task_status(
                session_id=session_id,
                file_id=file_id,
                new_status=FileIngestionLifecycle.VALIDATING,
                step_description="Executing WS-03.3 Shared Validation Engine (Tiers 1-5)",
            )

        validated_chunks: List[ValidatedWorksheetChunk] = []
        all_canonical_rows: List[CanonicalRow] = []

        for m_chunk in mapping_summary.worksheet_chunks:
            val_chunk = self.validate_chunk(
                mapped_chunk=m_chunk,
                profile_id=mapping_summary.profile_id,
                profile_version=mapping_summary.profile_version,
            )
            validated_chunks.append(val_chunk)
            all_canonical_rows.extend(m_chunk.canonical_rows)

        # 2. Execute Tier 5 Dataset-level validation using WS-03.3 SharedValidationEngine
        canon_dataset = CanonicalDataset(
            profile_id=mapping_summary.profile_id or "DEFAULT_PROFILE",
            profile_version=mapping_summary.profile_version or "1.0.0",
            rows=all_canonical_rows,
        )
        ds_val_result, _ = self._validation_engine.validate_dataset(canon_dataset)

        t1 = time.perf_counter()
        val_duration_ms = (t1 - t0) * 1000.0

        # 3. Generate Preview & Lifecycle transition: VALIDATING -> GENERATING_PREVIEW
        if self._session_manager and session_id and file_id:
            self._session_manager.update_task_status(
                session_id=session_id,
                file_id=file_id,
                new_status=FileIngestionLifecycle.GENERATING_PREVIEW,
                step_description="Compiling Immutable Validation Preview Contracts",
            )

        t2 = time.perf_counter()
        flattened_previews: List[ValidationPreviewRow] = [
            p_row for v_chunk in validated_chunks for p_row in v_chunk.preview_rows
        ]

        tot_eval = len(flattened_previews)
        val_cnt = sum(1 for p in flattened_previews if p.is_valid)
        warn_cnt = sum(1 for p in flattened_previews if p.severity == "WARNING")
        quar_cnt = sum(1 for p in flattened_previews if p.quarantine_recommended)

        avg_score = ds_val_result.summary.quality_score
        preview_duration_ms = (time.perf_counter() - t2) * 1000.0
        throughput = (tot_eval / (val_duration_ms / 1000.0)) if val_duration_ms > 0 else 0.0

        stats = PreviewStatistics(
            total_rows_evaluated=tot_eval,
            valid_rows_count=val_cnt,
            warning_rows_count=warn_cnt,
            quarantined_rows_count=quar_cnt,
            overall_quality_score=avg_score,
            validation_duration_ms=val_duration_ms,
            preview_generation_duration_ms=preview_duration_ms,
            rows_per_second=throughput,
        )

        val_summary = ValidationSummary(
            session_id=session_id,
            file_id=file_id,
            filename=mapping_summary.filename,
            profile_id=mapping_summary.profile_id,
            statistics=stats,
            validated_chunks=validated_chunks,
            validated_at=datetime.now(timezone.utc),
        )

        return ValidationPreview(
            session_id=session_id,
            file_id=file_id,
            filename=mapping_summary.filename,
            summary=val_summary,
            preview_rows=flattened_previews,
            created_at=datetime.now(timezone.utc),
        )
