import logging
logger = logging.getLogger(__name__)
from src.ml.inference.inference_service import (
    MLInferenceService,
    PredictionRequestDTO,
    PredictionResultDTO,
)
"""ML Training Job Management & Model Registry API Router (Phase 13B, 13D, 13E, 13G).

Endpoints:
- POST /api/v1/ml/jobs: Create durable training job, perform preflight, and launch isolated worker.
- GET /api/v1/ml/jobs/{job_id}: Query durable execution status, stage, logs, and resource metrics.
- GET /api/v1/ml/jobs: List historical training jobs.
- GET /api/v1/ml/registry/active: Retrieve current active model.
- GET /api/v1/ml/registry/models: List all registered models.
- GET /api/v1/ml/registry/models/{model_id}: Retrieve single model detail.
- POST /api/v1/ml/registry/models/{model_id}/activate: Explicitly activate candidate model.
- POST /api/v1/ml/registry/rollback: Rollback active model to verified prior candidate.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.security.dependencies import require_roles, get_db
from src.database.models.user import User, SecurityAuditLog
from src.ml.training.job_service import MLTrainingJobService, TrainingConcurrencyError
from src.ml.training.launcher import MLTrainingWorkerLauncher
from src.ml.training.contracts import TrainingJobStatus
from src.ml.registry.registry_service import (
    ModelRegistryService,
    ModelRegistryError,
    ModelValidationError,
    ModelActivationError,
)
from src.database.models.ai import ModelRegistry

router = APIRouter(prefix="/api/v1/ml", tags=["ML Model Training & Registry Operations"])

# Fine-grained Role Authorization:
ML_READ_AUTH = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD", "LAB_TECHNICIAN", "ANALYST_VIEWER"))
ML_TRAIN_AUTH = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD"))
ML_ADMIN_AUTH = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD"))


class CreateTrainingJobRequest(BaseModel):
    dataset_fingerprint: str
    observation_count: int
    dataset_origin_breakdown: Optional[Dict[str, Any]] = None
    feature_schema_version: str = "1.0.0"
    execution_timeout_seconds: int = 600
    is_dummy_test: bool = False


class MLTrainingJobResponse(BaseModel):
    job_id: str
    dataset_fingerprint: str
    feature_schema_version: str
    observation_count: int
    status: str
    current_stage: Optional[str] = "QUEUED"
    records_processed: Optional[int] = 0
    records_total: Optional[int] = 0
    last_heartbeat_at: Optional[str] = None
    execution_logs: List[Dict[str, Any]] = []
    failure_reason: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_metadata: Dict[str, Any]


class ModelRegistryResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    framework: str
    algorithm: str
    feature_schema_version: str
    training_dataset_version: Optional[str] = None
    artifact_location: Optional[str] = None
    checksum: Optional[str] = None
    deployment_status: str
    deployment_timestamp: str
    created_at: str


class ActivateModelRequest(BaseModel):
    reason: Optional[str] = "Explicit production approval"


class RollbackModelRequest(BaseModel):
    target_model_id: Optional[str] = None
    reason: Optional[str] = "Reverting active model to previous verified retired model"


def _build_job_response(job) -> MLTrainingJobResponse:
    """Helper to convert MLTrainingJob ORM model to response with sanitized telemetry."""
    meta = job.execution_metadata_json or {}
    return MLTrainingJobResponse(
        job_id=job.id,
        dataset_fingerprint=job.dataset_fingerprint,
        feature_schema_version=job.feature_schema_version,
        observation_count=job.observation_count,
        status=job.status,
        current_stage=meta.get("current_stage", job.status),
        records_processed=meta.get("records_processed", 0),
        records_total=meta.get("records_total", job.observation_count),
        last_heartbeat_at=meta.get("last_heartbeat_at"),
        execution_logs=meta.get("execution_logs", []),
        failure_reason=job.failure_reason,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        execution_metadata=meta,
    )


# ==========================================================
# 1. TRAINING JOB ENDPOINTS
# ==========================================================

@router.post("/jobs", response_model=MLTrainingJobResponse, status_code=status.HTTP_201_CREATED)
def submit_training_job(
    req: CreateTrainingJobRequest,
    current_user: User = ML_TRAIN_AUTH,
    db: Session = Depends(get_db),
):
    """Create durable ML training job with atomic concurrency check and resource pre-flight."""
    try:
        job, preflight = MLTrainingJobService.create_job(
            db=db,
            dataset_fingerprint=req.dataset_fingerprint,
            observation_count=req.observation_count,
            dataset_origin_breakdown=req.dataset_origin_breakdown,
            feature_schema_version=req.feature_schema_version,
            execution_timeout_seconds=req.execution_timeout_seconds,
        )
    except TrainingConcurrencyError as ex:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ex),
        )

    # Audit Training Job Submission
    try:
        audit = SecurityAuditLog(
            actor_user_id=current_user.id,
            target_user_id=None,
            event_type="ML_TRAINING_JOB_REQUESTED",
            resource_name="ML_TRAINING_JOB",
            correlation_id=job.id,
            details={
                "dataset_fingerprint": req.dataset_fingerprint,
                "observation_count": req.observation_count,
                "preflight_allowed": preflight.allowed,
                "preflight_reason": preflight.reason if not preflight.allowed else None,
            },
        )
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()

    # If resource preflight rejected the job, return rejection immediately without launching worker
    if not preflight.allowed:
        return _build_job_response(job)

    # Launch isolated worker in background
    if req.is_dummy_test:
        MLTrainingWorkerLauncher.run_worker_process(
            job_id=job.id,
            timeout_seconds=req.execution_timeout_seconds,
            is_dummy_test=True,
        )
        job = MLTrainingJobService.get_job(db, job.id)
    else:
        # Asynchronously launch actual training worker subprocess
        MLTrainingWorkerLauncher.launch_detached_worker(
            job_id=job.id,
            timeout_seconds=req.execution_timeout_seconds,
            is_dummy_test=False,
        )

    return _build_job_response(job)


@router.get("/jobs/{job_id}", response_model=MLTrainingJobResponse)
def get_training_job_status(
    job_id: str,
    current_user: User = ML_READ_AUTH,
    db: Session = Depends(get_db),
):
    """Retrieve durable status, stages, logs, and telemetry for a specific ML training job."""
    job = MLTrainingJobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job '{job_id}' not found.",
        )

    return _build_job_response(job)


@router.get("/jobs", response_model=List[MLTrainingJobResponse])
def list_training_jobs(
    limit: int = 50,
    current_user: User = ML_READ_AUTH,
    db: Session = Depends(get_db),
):
    """List historical ML training jobs with telemetry."""
    jobs = MLTrainingJobService.list_jobs(db, limit=limit)
    return [_build_job_response(j) for j in jobs]


# ==========================================================
# 2. MODEL REGISTRY ENDPOINTS
# ==========================================================

@router.get("/registry/active", response_model=Optional[ModelRegistryResponse])
def get_active_model_endpoint(
    current_user: User = ML_READ_AUTH,
    db: Session = Depends(get_db),
):
    """Retrieve the currently ACTIVE production ML model if one exists."""
    active = ModelRegistryService.get_active_model(db)
    if not active:
        return None
    return ModelRegistryResponse(
        id=str(active.id),
        model_name=active.model_name,
        model_version=active.model_version,
        framework=active.framework,
        algorithm=active.algorithm,
        feature_schema_version=active.feature_schema_version,
        training_dataset_version=active.training_dataset_version,
        artifact_location=active.artifact_location,
        checksum=active.checksum,
        deployment_status=active.deployment_status,
        deployment_timestamp=active.deployment_timestamp.isoformat(),
        created_at=active.created_at.isoformat(),
    )


@router.get("/registry/models", response_model=List[ModelRegistryResponse])
def list_registry_models_endpoint(
    current_user: User = ML_READ_AUTH,
    db: Session = Depends(get_db),
):
    """List all registered models (CANDIDATE, ACTIVE, RETIRED) with full lineage."""
    models = ModelRegistryService.list_models(db)
    return [
        ModelRegistryResponse(
            id=str(m.id),
            model_name=m.model_name,
            model_version=m.model_version,
            framework=m.framework,
            algorithm=m.algorithm,
            feature_schema_version=m.feature_schema_version,
            training_dataset_version=m.training_dataset_version,
            artifact_location=m.artifact_location,
            checksum=m.checksum,
            deployment_status=m.deployment_status,
            deployment_timestamp=m.deployment_timestamp.isoformat(),
            created_at=m.created_at.isoformat(),
        )
        for m in models
    ]


@router.get("/registry/models/{model_id}", response_model=ModelRegistryResponse)
def get_registry_model_detail_endpoint(
    model_id: str,
    current_user: User = ML_READ_AUTH,
    db: Session = Depends(get_db),
):
    """Retrieve single registered model detail by UUID or version."""
    model = db.get(ModelRegistry, model_id)
    if not model:
        model = db.query(ModelRegistry).filter(ModelRegistry.model_version == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found in registry.",
        )

    return ModelRegistryResponse(
        id=str(model.id),
        model_name=model.model_name,
        model_version=model.model_version,
        framework=model.framework,
        algorithm=model.algorithm,
        feature_schema_version=model.feature_schema_version,
        training_dataset_version=model.training_dataset_version,
        artifact_location=model.artifact_location,
        checksum=model.checksum,
        deployment_status=model.deployment_status,
        deployment_timestamp=model.deployment_timestamp.isoformat(),
        created_at=model.created_at.isoformat(),
    )


@router.post("/registry/models/{model_id}/activate", response_model=ModelRegistryResponse)
def activate_model_endpoint(
    model_id: str,
    req: ActivateModelRequest,
    current_user: User = ML_ADMIN_AUTH,
    db: Session = Depends(get_db),
):
    """Explicitly activate a candidate model after verifying artifact existence and checksum."""
    try:
        activated, retired = ModelRegistryService.activate_model(
            db=db,
            model_id=model_id,
            actor_user_id=str(current_user.id),
            reason=req.reason,
        )
        try:
            CacheTokenService.bump_token_and_journal(
                db=db,
                token_name="reporting_metrics",
                event_type="MODEL_ACTIVATED",
                scopes=["models", "kpis", "summary"],
                payload={"activated_model_version": activated.model_version, "algorithm": activated.algorithm},
            )
            db.commit()
        except Exception as err:
            logger.warning(f"Could not bump cache token on model activation: {err}")
        return ModelRegistryResponse(
            id=str(activated.id),
            model_name=activated.model_name,
            model_version=activated.model_version,
            framework=activated.framework,
            algorithm=activated.algorithm,
            feature_schema_version=activated.feature_schema_version,
            training_dataset_version=activated.training_dataset_version,
            artifact_location=activated.artifact_location,
            checksum=activated.checksum,
            deployment_status=activated.deployment_status,
            deployment_timestamp=activated.deployment_timestamp.isoformat(),
            created_at=activated.created_at.isoformat(),
        )
    except ModelValidationError as ex:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ex))
    except ModelActivationError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.post("/registry/rollback", response_model=ModelRegistryResponse)
def rollback_model_endpoint(
    req: RollbackModelRequest,
    current_user: User = ML_ADMIN_AUTH,
    db: Session = Depends(get_db),
):
    """Atomically rollback active model to a previous verified retired model (or explicit target model)."""
    try:
        restored, retired = ModelRegistryService.rollback_model(
            db=db,
            target_model_id=req.target_model_id,
            actor_user_id=str(current_user.id),
            reason=req.reason,
        )
        return ModelRegistryResponse(
            id=str(restored.id),
            model_name=restored.model_name,
            model_version=restored.model_version,
            framework=restored.framework,
            algorithm=restored.algorithm,
            feature_schema_version=restored.feature_schema_version,
            training_dataset_version=restored.training_dataset_version,
            artifact_location=restored.artifact_location,
            checksum=restored.checksum,
            deployment_status=restored.deployment_status,
            deployment_timestamp=restored.deployment_timestamp.isoformat(),
            created_at=restored.created_at.isoformat(),
        )
    except ModelValidationError as ex:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ex))
    except ModelActivationError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.post("/inference/predict", response_model=PredictionResultDTO)
def predict_strength_endpoint(
    payload: PredictionRequestDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD", "PLANT_OPERATOR", "DISPATCH_OFFICER")),
):
    """Execute real-time concrete strength prediction using ACTIVE model or fallback heuristic."""
    return MLInferenceService.predict_strength(
        db=db,
        request=payload,
        actor_user_id=current_user.id,
    )
