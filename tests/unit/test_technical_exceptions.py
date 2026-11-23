"""Unit test suite for WS-01.3B Technical & Infrastructure Exceptions."""

from src.exceptions import (
    ACCRMCBaseException,
    AIInferenceException,
    AuthenticationRequiredException,
    CellDeunificationException,
    DataConstraintViolationException,
    DatabaseConnectionException,
    DatabaseException,
    InfrastructureException,
    IngestionException,
    ModelNotLoadedException,
    OptimizationDivergenceException,
    PermissionDeniedException,
    SchedulerException,
    SecurityException,
    TemplateAnchorNotFoundException,
    ValidationException,
)


def test_infrastructure_exception_inheritance() -> None:
    exc = DatabaseConnectionException()
    assert isinstance(exc, DatabaseException)
    assert isinstance(exc, InfrastructureException)
    assert isinstance(exc, ACCRMCBaseException)
    assert exc.error_code == "ACC_DB_CONNECTION_FAILED"


def test_ingestion_exceptions() -> None:
    exc = TemplateAnchorNotFoundException(anchor_text="FT7 CERTIFICATE", sheet_name="Sheet1")
    assert isinstance(exc, IngestionException)
    assert isinstance(exc, InfrastructureException)
    assert exc.error_code == "ACC_INGEST_ANCHOR_MISSING"
    assert exc.metadata["sheet_name"] == "Sheet1"

    exc2 = CellDeunificationException(cell_range="A1:F3", message="Failed to unmerge")
    assert exc2.error_code == "ACC_INGEST_DEUNIFY_FAILED"


def test_ai_inference_exceptions() -> None:
    exc = ModelNotLoadedException(model_name="LinestStrengthModel", version="1.0.0")
    assert isinstance(exc, AIInferenceException)
    assert exc.error_code == "ACC_AI_MODEL_NOT_FOUND"

    exc2 = OptimizationDivergenceException(target_strength_mpa=36.6, reason="Constraint matrix singular")
    assert exc2.error_code == "ACC_AI_OPTIMIZER_DIVERGED"


def test_security_exceptions() -> None:
    exc = AuthenticationRequiredException()
    assert isinstance(exc, SecurityException)
    assert exc.error_code == "ACC_SEC_AUTHENTICATION_REQUIRED"

    exc2 = PermissionDeniedException(required_role="QUALITY_LEAD")
    assert exc2.error_code == "ACC_SEC_PERMISSION_DENIED"
    assert exc2.metadata["required_role"] == "QUALITY_LEAD"


def test_scheduler_exceptions() -> None:
    exc = SchedulerException(job_id="retrain_job_01", message="Cron trigger missed")
    assert isinstance(exc, InfrastructureException)
    assert exc.error_code == "ACC_SCHEDULER_FAILURE"
