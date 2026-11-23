"""Thread-Safe Upload Session & File Queue Infrastructure Manager.

This module provides UploadSessionManager responsible for creating sessions, enqueueing files, enforcing configuration limits,
validating state machine transitions, tracking SHA-256 duplicates, and generating session summary contracts.
Zero persistence, zero Excel parsing, zero mapping, zero validation.
"""

from datetime import datetime, timezone

import os
import threading
from typing import Dict, List, Optional, Tuple
from src.ingestion.excel.checksum import DuplicateDetector, calculate_bytes_sha256
from src.ingestion.excel.config import IngestionConfig, get_default_ingestion_config
from src.ingestion.excel.contracts import (
    FileIngestionLifecycle,
    FileUploadTask,
    UploadSession,
    UploadSessionLifecycle,
    UploadSessionSummaryContract,
)


class UploadSessionManager:
    """Thread-safe manager for upload sessions, file queues, duplicate detection, and lifecycle state transitions."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or get_default_ingestion_config()
        self._sessions: Dict[str, UploadSession] = {}
        self._duplicate_detector = DuplicateDetector()
        self._lock = threading.RLock()

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> UploadSession:
        """Create and initialize a new multi-file UploadSession."""
        if not user_id or not user_id.strip():
            raise ValueError("user_id must be a non-empty string.")

        with self._lock:
            sid = session_id or f"SES-{datetime.now(timezone.utc).strftime('%Y%m%m%H%M%S')}-{os.urandom(3).hex().upper()}"
            if sid in self._sessions:
                raise ValueError(f"Session with ID '{sid}' already exists.")

            session = UploadSession(
                session_id=sid,
                user_id=user_id,
                status=UploadSessionLifecycle.CREATED,
                files=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self._sessions[sid] = session
            return session

    def get_session(self, session_id: str) -> Optional[UploadSession]:
        """Retrieve active UploadSession by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def enqueue_file(
        self,
        session_id: str,
        filename: str,
        file_size_bytes: int,
        file_bytes: Optional[bytes] = None,
        file_id: Optional[str] = None,
    ) -> FileUploadTask:
        """Enqueue a file upload task into an active UploadSession, enforcing configuration limits and duplicate checks."""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"UploadSession '{session_id}' not found.")

            if session.status in (UploadSessionLifecycle.COMPLETED, UploadSessionLifecycle.FAILED, UploadSessionLifecycle.CANCELLED):
                raise ValueError(f"Cannot enqueue files into session in terminal state '{session.status}'.")

            # 1. Enforce max files per session limit
            if len(session.files) >= self.config.max_files_per_session:
                raise ValueError(
                    f"Session limit exceeded: maximum {self.config.max_files_per_session} files allowed per upload session."
                )

            # 2. Enforce file size limit
            if file_size_bytes > self.config.max_file_size_bytes:
                raise ValueError(
                    f"File size limit exceeded: {file_size_bytes} bytes exceeds maximum allowed {self.config.max_file_size_bytes} bytes."
                )

            # 3. Enforce extension check
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.config.allowed_extensions:
                raise ValueError(
                    f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(self.config.allowed_extensions)}"
                )

            # 4. Checksum & Duplicate Detection
            sha256_hash: Optional[str] = None
            status = FileIngestionLifecycle.QUEUED
            step_desc = "Enqueued in queue"

            if file_bytes:
                sha256_hash = calculate_bytes_sha256(file_bytes)
                if self.config.duplicate_hash_check_enabled:
                    if self._duplicate_detector.is_duplicate(sha256_hash):
                        status = FileIngestionLifecycle.DUPLICATE_REJECTED
                        step_desc = "Rejected: Duplicate SHA-256 file checksum detected"
                    else:
                        self._duplicate_detector.register(sha256_hash)

            fid = file_id or f"FILE-{os.urandom(4).hex().upper()}"
            task = FileUploadTask(
                file_id=fid,
                session_id=session_id,
                filename=filename,
                file_size_bytes=file_size_bytes,
                checksum_sha256=sha256_hash,
                status=status,
                progress_percentage=0.0,
                current_step_description=step_desc,
                enqueued_at=datetime.now(timezone.utc),
            )

            # Update session state
            updated_files = list(session.files) + [task]
            new_session_status = UploadSessionLifecycle.ACTIVE if status != FileIngestionLifecycle.DUPLICATE_REJECTED else session.status

            updated_session = UploadSession(
                session_id=session.session_id,
                user_id=session.user_id,
                status=new_session_status,
                files=updated_files,
                created_at=session.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            self._sessions[session_id] = updated_session
            return task

    def update_task_status(
        self,
        session_id: str,
        file_id: str,
        new_status: FileIngestionLifecycle,
        progress: Optional[float] = None,
        step_description: Optional[str] = None,
        error_message: Optional[str] = None,
        rows_found: Optional[int] = None,
        rows_valid: Optional[int] = None,
        rows_invalid: Optional[int] = None,
        quality_score: Optional[float] = None,
    ) -> FileUploadTask:
        """Validate state transition and update FileUploadTask state."""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"UploadSession '{session_id}' not found.")

            task_idx = next((i for i, f in enumerate(session.files) if f.file_id == file_id), -1)
            if task_idx == -1:
                raise ValueError(f"Task '{file_id}' not found in session '{session_id}'.")

            current_task = session.files[task_idx]

            # Validate state transition rules
            self._validate_state_transition(current_task.status, new_status)

            now = datetime.now(timezone.utc)
            started_at = current_task.started_at or (now if new_status not in (FileIngestionLifecycle.QUEUED, FileIngestionLifecycle.CANCELLED) else None)
            completed_at = now if new_status in (FileIngestionLifecycle.COMPLETED, FileIngestionLifecycle.PARTIAL_SUCCESS, FileIngestionLifecycle.FAILED, FileIngestionLifecycle.CANCELLED, FileIngestionLifecycle.DUPLICATE_REJECTED) else None

            updated_task = FileUploadTask(
                file_id=current_task.file_id,
                session_id=current_task.session_id,
                filename=current_task.filename,
                file_size_bytes=current_task.file_size_bytes,
                checksum_sha256=current_task.checksum_sha256,
                status=new_status,
                progress_percentage=progress if progress is not None else current_task.progress_percentage,
                current_step_description=step_description or current_task.current_step_description,
                worksheet_names=current_task.worksheet_names,
                selected_worksheet=current_task.selected_worksheet,
                import_profile_id=current_task.import_profile_id,
                total_rows_found=rows_found if rows_found is not None else current_task.total_rows_found,
                rows_mapped=current_task.rows_mapped,
                rows_valid=rows_valid if rows_valid is not None else current_task.rows_valid,
                rows_invalid=rows_invalid if rows_invalid is not None else current_task.rows_invalid,
                quality_score=quality_score if quality_score is not None else current_task.quality_score,
                error_message=error_message or current_task.error_message,
                enqueued_at=current_task.enqueued_at,
                started_at=started_at,
                completed_at=completed_at,
            )

            files_copy = list(session.files)
            files_copy[task_idx] = updated_task

            # Evaluate overall session status
            session_status = self._evaluate_session_status(files_copy)

            updated_session = UploadSession(
                session_id=session.session_id,
                user_id=session.user_id,
                status=session_status,
                files=files_copy,
                created_at=session.created_at,
                updated_at=now,
                completed_at=now if session_status in (UploadSessionLifecycle.COMPLETED, UploadSessionLifecycle.PARTIAL_SUCCESS, UploadSessionLifecycle.FAILED, UploadSessionLifecycle.CANCELLED) else None,
            )
            self._sessions[session_id] = updated_session
            return updated_task

    def generate_session_summary(self, session_id: str) -> UploadSessionSummaryContract:
        """Compile immutable UploadSessionSummaryContract for session."""
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"UploadSession '{session_id}' not found.")

            total_files = len(session.files)
            completed_files = sum(1 for f in session.files if f.status == FileIngestionLifecycle.COMPLETED)
            failed_files = sum(1 for f in session.files if f.status == FileIngestionLifecycle.FAILED)
            cancelled_files = sum(1 for f in session.files if f.status == FileIngestionLifecycle.CANCELLED)
            duplicate_files = sum(1 for f in session.files if f.status == FileIngestionLifecycle.DUPLICATE_REJECTED)

            total_rows_proc = sum(f.total_rows_found for f in session.files)
            total_valid = sum(f.rows_valid for f in session.files)
            total_invalid = sum(f.rows_invalid for f in session.files)

            scores = [f.quality_score for f in session.files if f.quality_score is not None]
            avg_score = (sum(scores) / len(scores)) if scores else 100.0

            end_time = session.completed_at or datetime.now(timezone.utc)
            duration_ms = (end_time - session.created_at).total_seconds() * 1000.0

            file_summaries = [
                {
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "status": f.status.value,
                    "rows_valid": f.rows_valid,
                    "rows_invalid": f.rows_invalid,
                    "quality_score": f.quality_score,
                }
                for f in session.files
            ]

            return UploadSessionSummaryContract(
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at,
                completed_at=session.completed_at,
                total_files=total_files,
                completed_files=completed_files,
                failed_files=failed_files,
                cancelled_files=cancelled_files,
                duplicate_files=duplicate_files,
                total_rows_processed=total_rows_proc,
                total_rows_valid=total_valid,
                total_rows_invalid=total_invalid,
                overall_quality_score=avg_score,
                processing_duration_ms=duration_ms,
                file_summaries=file_summaries,
            )

    def _validate_state_transition(self, current: FileIngestionLifecycle, target: FileIngestionLifecycle) -> None:
        """Enforce strict 16-state lifecycle transition matrix."""
        if current == target:
            return

        # Terminal state guard
        terminal_states = (FileIngestionLifecycle.COMPLETED, FileIngestionLifecycle.PARTIAL_SUCCESS, FileIngestionLifecycle.CANCELLED, FileIngestionLifecycle.DUPLICATE_REJECTED)
        if current in terminal_states and target != FileIngestionLifecycle.RETRY_PENDING:
            raise ValueError(f"Illegal state transition: cannot transition from terminal state '{current}' to '{target}'.")

        # Allow user cancellation from any non-completed state
        if target == FileIngestionLifecycle.CANCELLED:
            return

        # Explicit state sequence validation
        allowed_transitions = {
            FileIngestionLifecycle.QUEUED: [FileIngestionLifecycle.UPLOADING, FileIngestionLifecycle.CANCELLED],
            FileIngestionLifecycle.UPLOADING: [FileIngestionLifecycle.UPLOAD_COMPLETED, FileIngestionLifecycle.FAILED, FileIngestionLifecycle.CANCELLED],
            FileIngestionLifecycle.UPLOAD_COMPLETED: [FileIngestionLifecycle.CHECKSUM_VERIFICATION, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.CHECKSUM_VERIFICATION: [FileIngestionLifecycle.SCANNING, FileIngestionLifecycle.DUPLICATE_REJECTED, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.SCANNING: [FileIngestionLifecycle.READING_WORKBOOK, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.READING_WORKBOOK: [FileIngestionLifecycle.READING_WORKSHEETS, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.READING_WORKSHEETS: [FileIngestionLifecycle.MAPPING, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.MAPPING: [FileIngestionLifecycle.VALIDATING, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.VALIDATING: [FileIngestionLifecycle.GENERATING_PREVIEW, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.GENERATING_PREVIEW: [FileIngestionLifecycle.COMPLETED, FileIngestionLifecycle.PARTIAL_SUCCESS, FileIngestionLifecycle.FAILED],
            FileIngestionLifecycle.FAILED: [FileIngestionLifecycle.RETRY_PENDING],
            FileIngestionLifecycle.RETRY_PENDING: [FileIngestionLifecycle.QUEUED],
        }

        valid_targets = allowed_transitions.get(current, [])
        if target not in valid_targets:
            raise ValueError(f"Invalid file lifecycle state transition from '{current.value}' to '{target.value}'.")

    def _evaluate_session_status(self, files: List[FileUploadTask]) -> UploadSessionLifecycle:
        """Derive overall UploadSession status from file tasks."""
        if not files:
            return UploadSessionLifecycle.CREATED

        statuses = [f.status for f in files]
        if all(s == FileIngestionLifecycle.COMPLETED for s in statuses):
            return UploadSessionLifecycle.COMPLETED
        if all(s in (FileIngestionLifecycle.COMPLETED, FileIngestionLifecycle.PARTIAL_SUCCESS) for s in statuses):
            return UploadSessionLifecycle.PARTIAL_SUCCESS
        if any(s == FileIngestionLifecycle.FAILED for s in statuses) and all(s in (FileIngestionLifecycle.COMPLETED, FileIngestionLifecycle.PARTIAL_SUCCESS, FileIngestionLifecycle.FAILED, FileIngestionLifecycle.CANCELLED, FileIngestionLifecycle.DUPLICATE_REJECTED) for s in statuses):
            return UploadSessionLifecycle.FAILED
        if all(s == FileIngestionLifecycle.CANCELLED for s in statuses):
            return UploadSessionLifecycle.CANCELLED
        return UploadSessionLifecycle.PROCESSING
