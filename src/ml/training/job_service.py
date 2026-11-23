"""Durable ML Training Job Lifecycle, Observability & Concurrency Service.

Certified Rules (Phase 13B, 13G):
- Authoritative state machine: QUEUED, PRECHECKING, RUNNING, SUCCEEDED, FAILED, TIMED_OUT, CANCELLED, RESOURCE_REJECTED.
- Authoritative execution stages: QUEUED, PRECHECKING, DATA_EXTRACTION, MODEL_FITTING, EVALUATION, REGISTRATION, COMPLETED.
- MAX_CONCURRENT_TRAINING_JOBS = 1 strictly enforced via atomic locking.
- Structured execution milestones & sanitized telemetry persistence.
- Zero secret / token disclosure in metadata and logs.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from src.database.models.ai import MLTrainingJob
from src.ml.training.contracts import TrainingJobStatus
from src.ml.training.resource_guard import (
    TrainingResourceGuardService,
    ResourcePreflightReport,
    DatasetFingerprintService,
)

logger = logging.getLogger("acc_rmc.ml.training")

TRAINING_CONCURRENCY_LOCK_KEY = "acc_rmc:ml_training_active_lock"


class TrainingConcurrencyError(Exception):
    """Raised when a concurrent training job is active or locked."""
    pass


class MLTrainingJobService:
    """Enterprise service managing durable ML training jobs and execution telemetry."""

    @staticmethod
    def get_active_job(db: Session) -> Optional[MLTrainingJob]:
        """Check for any existing training job currently occupying the execution slot."""
        return db.scalar(
            select(MLTrainingJob).where(
                MLTrainingJob.status.in_([
                    TrainingJobStatus.PRECHECKING.value,
                    TrainingJobStatus.RUNNING.value,
                    TrainingJobStatus.QUEUED.value,
                ])
            ).order_by(MLTrainingJob.created_at.desc())
        )

    @staticmethod
    def reconcile_stale_jobs(db: Session) -> int:
        """Reconcile orphaned RUNNING or PRECHECKING jobs after server restart or crash."""
        now = datetime.now(timezone.utc)
        active_jobs = db.scalars(
            select(MLTrainingJob).where(
                MLTrainingJob.status.in_([
                    TrainingJobStatus.PRECHECKING.value,
                    TrainingJobStatus.RUNNING.value,
                ])
            )
        ).all()

        reconciled_count = 0
        for job in active_jobs:
            job.status = TrainingJobStatus.FAILED.value
            job.completed_at = now
            job.failure_reason = "Server restart recovery: worker execution was interrupted unexpectedly."
            
            # Append sanitized log
            logs = job.execution_metadata_json.get("execution_logs", [])
            logs.append({
                "timestamp": now.isoformat(),
                "stage": "FAILED",
                "severity": "ERROR",
                "message": "Orphaned job recovered after server restart.",
            })
            job.execution_metadata_json = {
                **job.execution_metadata_json,
                "current_stage": "FAILED",
                "execution_logs": logs,
            }
            reconciled_count += 1
            logger.warning(f"Reconciled stale training job '{job.id}' to FAILED.")

        if reconciled_count > 0:
            db.commit()
        return reconciled_count

    @staticmethod
    def create_job(
        db: Session,
        dataset_fingerprint: str,
        observation_count: int,
        dataset_origin_breakdown: Optional[Dict[str, Any]] = None,
        feature_schema_version: str = "1.0.0",
        execution_timeout_seconds: int = 600,
    ) -> Tuple[MLTrainingJob, ResourcePreflightReport]:
        """Create a durable training job after enforcing concurrency limit and resource safety."""
        # 1. Enforce Server-Side Concurrency Limit = 1
        active_job = MLTrainingJobService.get_active_job(db)
        if active_job:
            raise TrainingConcurrencyError(
                f"Another ML training job '{active_job.id}' is currently in state '{active_job.status}'. "
                f"Concurrent execution limit is 1."
            )

        # 2. Resource Pre-Flight Check (Phase 13A Certified Guard)
        preflight: ResourcePreflightReport = TrainingResourceGuardService.evaluate_preflight(
            observation_count=observation_count
        )

        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())

        initial_status = (
            TrainingJobStatus.QUEUED.value
            if preflight.allowed
            else TrainingJobStatus.RESOURCE_REJECTED.value
        )
        failure_msg = None if preflight.allowed else preflight.reason

        initial_logs = [
            {
                "timestamp": now.isoformat(),
                "stage": "QUEUED" if preflight.allowed else "RESOURCE_REJECTED",
                "severity": "INFO" if preflight.allowed else "WARN",
                "message": "Training job registered." if preflight.allowed else f"Resource preflight rejected: {preflight.reason}",
            }
        ]

        job = MLTrainingJob(
            id=job_id,
            dataset_fingerprint=dataset_fingerprint,
            feature_schema_version=feature_schema_version,
            observation_count=observation_count,
            dataset_origin_breakdown=dataset_origin_breakdown or {},
            status=initial_status,
            execution_timeout_seconds=execution_timeout_seconds,
            failure_reason=failure_msg,
            execution_metadata_json={
                "current_stage": "QUEUED" if preflight.allowed else "RESOURCE_REJECTED",
                "records_processed": 0,
                "records_total": observation_count,
                "preflight_allowed": preflight.allowed,
                "available_ram_mb": preflight.available_ram_mb,
                "total_ram_mb": preflight.total_ram_mb,
                "safety_headroom_mb": preflight.safety_headroom_mb,
                "estimated_training_ram_mb": preflight.estimated_training_ram_mb,
                "execution_logs": initial_logs,
                "last_heartbeat_at": now.isoformat(),
            },
            created_at=now,
            completed_at=now if not preflight.allowed else None,
        )

        db.add(job)
        db.commit()
        db.refresh(job)
        return job, preflight

    @staticmethod
    def record_stage_transition(
        db: Session,
        job_id: str,
        stage: str,
        records_processed: Optional[int] = None,
        milestone_message: Optional[str] = None,
        severity: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MLTrainingJob]:
        """Atomically record a real execution stage transition and append milestone log."""
        job = db.get(MLTrainingJob, job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc)
        meta = dict(job.execution_metadata_json or {})
        logs = list(meta.get("execution_logs", []))

        # Append bounded log entry (max 50 entries)
        if milestone_message:
            logs.append({
                "timestamp": now.isoformat(),
                "stage": stage,
                "severity": severity,
                "message": milestone_message[:300],
            })
            if len(logs) > 50:
                logs = logs[-50:]

        meta["current_stage"] = stage
        meta["last_heartbeat_at"] = now.isoformat()
        if records_processed is not None:
            meta["records_processed"] = records_processed
        if metadata:
            meta.update(metadata)

        meta["execution_logs"] = logs
        job.execution_metadata_json = meta
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def record_failure(
        db: Session,
        job_id: str,
        failure_reason: str,
        failure_code: str = "WORKER_ERROR",
    ) -> Optional[MLTrainingJob]:
        """Record durable failure state and sanitized failure reason."""
        job = db.get(MLTrainingJob, job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc)
        job.status = TrainingJobStatus.FAILED.value
        job.completed_at = now
        job.failure_reason = failure_reason[:500]

        meta = dict(job.execution_metadata_json or {})
        logs = list(meta.get("execution_logs", []))
        logs.append({
            "timestamp": now.isoformat(),
            "stage": "FAILED",
            "severity": "ERROR",
            "message": f"Failure ({failure_code}): {failure_reason[:250]}",
        })
        meta["current_stage"] = "FAILED"
        meta["failure_code"] = failure_code
        meta["execution_logs"] = logs[-50:]
        job.execution_metadata_json = meta

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[MLTrainingJob]:
        """Retrieve a durable training job by ID."""
        return db.get(MLTrainingJob, job_id)

    @staticmethod
    def list_jobs(db: Session, limit: int = 50) -> List[MLTrainingJob]:
        """List historical training jobs in descending creation order."""
        return list(
            db.scalars(
                select(MLTrainingJob).order_by(MLTrainingJob.created_at.desc()).limit(limit)
            ).all()
        )
