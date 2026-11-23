"""Isolated Subprocess Launcher & Lifecycle Manager for ML Training (Phase 13B).

Certified Rules:
- Training jobs NEVER run in-process or inside Uvicorn worker event loops.
- Executes detached Python subprocess with strict hard timeout management.
- Handles clean termination, SIGTERM/SIGKILL escalation, and mutex cleanup.
- Preserves currently active model registry state on failure or timeout.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from src.database.engine import get_database_engine
from src.database.models.ai import MLTrainingJob
from src.ml.training.contracts import TrainingJobStatus

logger = logging.getLogger("acc_rmc.ml.launcher")


class MLTrainingWorkerLauncher:
    """Manages spawning, timeout enforcement, and status transitions for training worker processes."""

    @staticmethod
    def run_worker_process(
        job_id: str,
        timeout_seconds: int = 600,
        is_dummy_test: bool = False,
    ) -> bool:
        """Spawn isolated worker subprocess and monitor execution."""
        engine = get_database_engine()

        # 1. Update job to RUNNING
        with Session(engine) as db:
            job = db.get(MLTrainingJob, job_id)
            if not job:
                logger.error(f"Cannot launch worker: Job '{job_id}' not found.")
                return False
            if job.status == TrainingJobStatus.RESOURCE_REJECTED.value:
                logger.warning(f"Cannot launch worker for rejected job '{job_id}'.")
                return False

            job.status = TrainingJobStatus.RUNNING.value
            job.started_at = datetime.now(timezone.utc)
            db.commit()

        # 2. Build isolated subprocess command
        python_executable = sys.executable
        cmd = [
            python_executable,
            "-m",
            "src.ml.training.worker",
            "--job-id",
            job_id,
        ]
        if is_dummy_test:
            cmd.append("--dummy-test")
        else:
            cmd.append("--actual-train")

        # Determine repository root dynamically
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_file_dir, "../../.."))

        env = dict(os.environ)
        # Add repo_root and standard production paths to PYTHONPATH
        env["PYTHONPATH"] = f"{repo_root}:/opt/apps/acc-rmc-ai-platform:" + env.get("PYTHONPATH", "")

        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            # Record child PID
            with Session(engine) as db:
                job = db.get(MLTrainingJob, job_id)
                if job:
                    job.worker_pid = proc.pid
                    db.commit()

            stdout, stderr = proc.communicate(timeout=timeout_seconds)

            now = datetime.now(timezone.utc)
            with Session(engine) as db:
                job = db.get(MLTrainingJob, job_id)
                if not job:
                    return False

                job.completed_at = now
                if proc.returncode == 0:
                    job.status = TrainingJobStatus.SUCCEEDED.value
                    job.execution_metadata_json = {
                        **job.execution_metadata_json,
                        "exit_code": 0,
                        "stdout_snippet": stdout[-500:] if stdout else "",
                    }
                    db.commit()
                    return True
                else:
                    job.status = TrainingJobStatus.FAILED.value
                    if not job.failure_reason or job.failure_reason.startswith("Worker exited"):
                        job.failure_reason = f"Worker exited with non-zero code {proc.returncode}."
                    job.execution_metadata_json = {
                        **job.execution_metadata_json,
                        "exit_code": proc.returncode,
                        "stderr_snippet": stderr[-1000:] if stderr else "",
                    }
                    db.commit()
                    return False

        except subprocess.TimeoutExpired:
            logger.warning(f"Training worker for job '{job_id}' exceeded timeout of {timeout_seconds}s. Terminating.")
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

            now = datetime.now(timezone.utc)
            with Session(engine) as db:
                job = db.get(MLTrainingJob, job_id)
                if job:
                    job.status = TrainingJobStatus.TIMED_OUT.value
                    job.completed_at = now
                    job.failure_reason = f"Execution timed out after {timeout_seconds} seconds."
                    db.commit()
            return False

        except Exception as ex:
            logger.error(f"Unexpected launcher exception for job '{job_id}': {ex}")
            now = datetime.now(timezone.utc)
            with Session(engine) as db:
                job = db.get(MLTrainingJob, job_id)
                if job:
                    job.status = TrainingJobStatus.FAILED.value
                    job.completed_at = now
                    job.failure_reason = f"Worker execution failure: {str(ex)[:200]}"
                    db.commit()
            return False

    @staticmethod
    def launch_detached_worker(
        job_id: str,
        timeout_seconds: int = 600,
        is_dummy_test: bool = False,
    ) -> None:
        """Spawn isolated worker subprocess asynchronously via background thread/process."""
        import threading
        t = threading.Thread(
            target=MLTrainingWorkerLauncher.run_worker_process,
            args=(job_id, timeout_seconds, is_dummy_test),
            daemon=True,
        )
        t.start()
