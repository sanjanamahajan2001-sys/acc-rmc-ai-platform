"""Isolated Python CLI Training Worker Entrypoint (Phase 13C, 13G).

Certified Rules:
- Standalone execution entrypoint invoked exclusively as an isolated child subprocess.
- Supports both simulation dummy test mode and actual Phase 13C multi-candidate training.
- Emits real stage transitions and sanitized execution milestones to durable job telemetry.
- Records candidate artifacts in ai_model_registry strictly as CANDIDATE (never active).
- Preserves currently active production inference models with zero disruption.
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from src.database.engine import get_database_engine
from src.database.models.ai import MLTrainingJob, ModelRegistry
from src.ml.training.eligibility import TrainingEligibilityService
from src.ml.training.trainer import ModelTrainerService
from src.ml.training.job_service import MLTrainingJobService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MLWorker] %(message)s",
)
logger = logging.getLogger("acc_rmc.ml.worker")


def execute_actual_training(job_id: str) -> int:
    """Execute real multi-candidate training workflow, recording real execution milestones."""
    engine = get_database_engine()
    logger.info(f"Initiating production ML training for job '{job_id}'...")

    with Session(engine) as db:
        job = db.get(MLTrainingJob, job_id)
        if not job:
            logger.error(f"Job '{job_id}' not found in database.")
            return 1

        # STAGE 1: PRECHECKING & RESOURCE VERIFICATION
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="PRECHECKING",
            milestone_message="Worker initialized. Verifying system environment.",
        )

        # STAGE 2: DATA EXTRACTION & ELIGIBILITY VALIDATION
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="DATA_EXTRACTION",
            milestone_message="Querying certified eligible production observations.",
        )

        report = TrainingEligibilityService.extract_with_report(db)
        observations = report.eligible_observations
        if not observations or len(observations) < 2:
            scanned = report.total_batches_scanned
            missing_28d = report.exclusion_breakdown.get("EXCLUDED_MISSING_28D_TARGET", 0)
            missing_binder = report.exclusion_breakdown.get("EXCLUDED_ZERO_OR_NEGATIVE_BINDER", 0)
            missing_water = report.exclusion_breakdown.get("EXCLUDED_ZERO_WATER", 0)
            
            reasons = []
            if missing_28d > 0:
                reasons.append(f"{missing_28d} batches missing 28-day lab test results")
            if missing_binder > 0:
                reasons.append(f"{missing_binder} batches missing binder/cement quantities")
            if missing_water > 0:
                reasons.append(f"{missing_water} batches missing water quantities")
            
            reasons_str = "; ".join(reasons) if reasons else "No qualified batches found"
            
            detailed_msg = (
                f"Insufficient eligible production observations (0 found out of {scanned} scanned). "
                f"Issues detected: {reasons_str}. "
                f"Required to train: Historical batches with recorded mix materials (Cement, Water, Aggregates) AND corresponding 28-day compressive strength laboratory test breaks (MPa)."
            )
            
            logger.error(detailed_msg)
            MLTrainingJobService.record_failure(
                db=db,
                job_id=job_id,
                failure_reason=detailed_msg,
                failure_code="INSUFFICIENT_DATA",
            )
            return 1

        obs_count = len(observations)
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="DATA_EXTRACTION",
            records_processed=obs_count,
            milestone_message=f"Extracted {obs_count} eligible batch records with 28D specimen outcomes.",
        )

        # STAGE 3: MODEL FITTING & MULTI-CANDIDATE TRAINING
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="MODEL_FITTING",
            records_processed=obs_count,
            milestone_message="Fitting candidate models (Baseline Ridge, Random Forest, XGBoost).",
        )

        try:
            train_results = ModelTrainerService.train_and_evaluate_candidates(
                observations=observations,
                dataset_fingerprint=job.dataset_fingerprint,
                artifacts_dir=os.environ.get("ML_MODELS_DIR", os.path.join("/opt/apps/acc-rmc-ai-platform" if os.path.exists("/opt/apps/acc-rmc-ai-platform") else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")), "trained_models")),
            )
        except Exception as ex:
            logger.error(f"Candidate model training failed: {ex}")
            MLTrainingJobService.record_failure(
                db=db,
                job_id=job_id,
                failure_reason=f"Model fitting exception: {str(ex)[:200]}",
                failure_code="TRAINING_ERROR",
            )
            return 1

        # STAGE 4: CANDIDATE EVALUATION & ARTIFACT REGISTRATION
        best_algo = train_results["best_candidate"]
        best_metrics = train_results["reports"][best_algo]["test_metrics"]
        
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="REGISTRATION",
            records_processed=obs_count,
            milestone_message=f"Candidate evaluated. Best algorithm: {best_algo} (MAE: {best_metrics['mae_mpa']} MPa). Registering artifact.",
        )

        # Register Candidate Model strictly as 'CANDIDATE' (NEVER ACTIVE)
        candidate_model_entry = ModelRegistry(
            model_name="acc_concrete_28d_strength",
            model_version=f"{best_algo.lower()}-{job_id[:8]}",
            framework="xgboost" if best_algo == "XGBoost" else "scikit-learn",
            algorithm=best_algo,
            feature_schema_version=job.feature_schema_version,
            training_dataset_version=job.dataset_fingerprint,
            artifact_location=train_results["artifact_path"],
            checksum=train_results["artifact_checksum"],
            deployment_status="CANDIDATE",
            deployment_timestamp=datetime.now(timezone.utc),
        )
        db.add(candidate_model_entry)
        db.flush()

        # STAGE 5: COMPLETED
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="COMPLETED",
            records_processed=obs_count,
            milestone_message="Training workflow complete. Candidate model available for quality review.",
            metadata={
                "training_results": train_results,
                "candidate_registered_id": str(candidate_model_entry.id),
                "candidate_model_version": candidate_model_entry.model_version,
            },
        )
        db.commit()
        logger.info(f"Training for job '{job_id}' completed successfully. Best candidate: {best_algo}.")
        return 0


def execute_dummy_training(job_id: str, fail_mode: bool = False, duration_seconds: float = 0.5) -> int:
    """Simulate isolated training worker with real stage transitions for fast infrastructure testing."""
    engine = get_database_engine()
    logger.info(f"Starting dummy worker for job '{job_id}'. PID: {os.getpid()}")

    with Session(engine) as db:
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="PRECHECKING",
            milestone_message="Simulation test worker initializing.",
        )

    time.sleep(duration_seconds / 3.0)

    if fail_mode:
        with Session(engine) as db:
            MLTrainingJobService.record_failure(
                db=db,
                job_id=job_id,
                failure_reason="Simulated intentional worker crash for failure testing.",
                failure_code="SIMULATED_CRASH",
            )
        logger.error(f"Simulated intentional worker crash for job '{job_id}'.")
        return 1

    with Session(engine) as db:
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="MODEL_FITTING",
            records_processed=50,
            milestone_message="Simulation test fitting dummy models.",
        )

    time.sleep(duration_seconds / 3.0)

    with Session(engine) as db:
        MLTrainingJobService.record_stage_transition(
            db=db,
            job_id=job_id,
            stage="COMPLETED",
            records_processed=50,
            milestone_message="Simulation worker completed successfully.",
        )

    logger.info(f"Dummy worker simulation for job '{job_id}' completed successfully.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="ACC RMC Isolated ML Training Worker")
    parser.add_argument("--job-id", type=str, required=True, help="Durable ML Training Job UUID")
    parser.add_argument("--dummy-test", action="store_true", help="Execute dummy verification worker")
    parser.add_argument("--actual-train", action="store_true", help="Execute real Phase 13C model training")
    parser.add_argument("--fail-test", action="store_true", help="Simulate worker crash for failure testing")
    parser.add_argument("--sleep-seconds", type=float, default=0.2, help="Execution duration")
    args = parser.parse_args()

    if args.actual_train:
        exit_code = execute_actual_training(job_id=args.job_id)
    else:
        exit_code = execute_dummy_training(
            job_id=args.job_id,
            fail_mode=args.fail_test,
            duration_seconds=args.sleep_seconds,
        )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
