"""Technical and Subsystem Exception Hierarchy.

This module defines technical, subsystem, and infrastructure exception classes
isolating validation, infrastructure (database, ingestion, connectors, scheduler, cache),
AI/ML inference, and security failures across the platform.
"""

from typing import Any, Dict, List, Optional
from src.exceptions.base import ACCRMCBaseException


class ValidationException(ACCRMCBaseException):
    """Raised when input payload or contract validation fails."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_SYS_VALIDATION_FAILED",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class InfrastructureException(ACCRMCBaseException):
    """Base class for all technical infrastructure failures (Database, Storage, Ingestion, Scheduler)."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_INFRA_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class ConfigurationException(InfrastructureException):
    """Base exception for all platform configuration failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_CONFIG_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class InvalidConfigurationException(ConfigurationException):
    """Raised when configuration parameter validation fails."""

    def __init__(
        self,
        parameter_name: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadata = {"parameter_name": parameter_name}
        super().__init__(
            message=message,
            error_code="ACC_CONFIG_INVALID",
            details=details,
            metadata=metadata,
        )


class MissingEnvironmentVariableException(ConfigurationException):
    """Raised when a mandatory environment variable is missing."""

    def __init__(
        self,
        env_var_name: str,
        message: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        msg = message if message else f"Mandatory environment variable '{env_var_name}' is missing."
        metadata = {"env_var_name": env_var_name}
        super().__init__(
            message=msg,
            error_code="ACC_CONFIG_MISSING_ENV",
            details=details,
            metadata=metadata,
        )


class DatabaseException(InfrastructureException):
    """Base class for data access and SQL persistence failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_DB_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class DatabaseConnectionException(DatabaseException):
    """Raised when database connection pool is exhausted or server is unreachable."""

    def __init__(
        self,
        message: str = "Database connection unavailable.",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="ACC_DB_CONNECTION_FAILED",
            details=details,
            metadata=metadata,
        )


class DataConstraintViolationException(DatabaseException):
    """Raised when a database foreign key, unique, or check constraint is violated."""

    def __init__(
        self,
        constraint_name: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadata = {"constraint_name": constraint_name}
        super().__init__(
            message=message,
            error_code="ACC_DB_CONSTRAINT_VIOLATION",
            details=details,
            metadata=metadata,
        )


class IngestionException(InfrastructureException):
    """Base class for Excel parsing and SCADA ingestion failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_INGEST_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class TemplateAnchorNotFoundException(IngestionException):
    """Raised when FT7 certificate template anchor cell header is missing."""

    def __init__(
        self,
        anchor_text: str,
        sheet_name: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"Template anchor '{anchor_text}' not found in sheet '{sheet_name}'."
        )
        metadata = {"anchor_text": anchor_text, "sheet_name": sheet_name}
        super().__init__(
            message=message,
            error_code="ACC_INGEST_ANCHOR_MISSING",
            details=details,
            metadata=metadata,
        )


class CellDeunificationException(IngestionException):
    """Raised when cell un-merging or range extraction fails."""

    def __init__(
        self,
        cell_range: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadata = {"cell_range": cell_range}
        super().__init__(
            message=message,
            error_code="ACC_INGEST_DEUNIFY_FAILED",
            details=details,
            metadata=metadata,
        )


class AIInferenceException(ACCRMCBaseException):
    """Base class for machine learning prediction and mix optimization failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_AI_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class ModelNotLoadedException(AIInferenceException):
    """Raised when ML model weights file is missing from model registry."""

    def __init__(
        self,
        model_name: str,
        version: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"ML model '{model_name}' version '{version}' not found in registry."
        )
        metadata = {"model_name": model_name, "version": version}
        super().__init__(
            message=message,
            error_code="ACC_AI_MODEL_NOT_FOUND",
            details=details,
            metadata=metadata,
        )


class OptimizationDivergenceException(AIInferenceException):
    """Raised when SLSQP linear programming mix optimizer fails to converge."""

    def __init__(
        self,
        target_strength_mpa: float,
        reason: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"Mix optimizer diverged for target strength {target_strength_mpa:.2f} MPa: {reason}"
        )
        metadata = {
            "target_strength_mpa": target_strength_mpa,
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="ACC_AI_OPTIMIZER_DIVERGED",
            details=details,
            metadata=metadata,
        )


class SecurityException(ACCRMCBaseException):
    """Base class for authentication and authorization security violations."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_SEC_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class AuthenticationRequiredException(SecurityException):
    """Raised when an unauthenticated request attempts access to a protected resource."""

    def __init__(
        self,
        message: str = "Authentication token missing or expired.",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="ACC_SEC_AUTHENTICATION_REQUIRED",
            details=details,
        )


class PermissionDeniedException(SecurityException):
    """Raised when an authenticated user lacks required RBAC permission."""

    def __init__(
        self,
        required_role: str,
        message: str = "Insufficient permissions.",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadata = {"required_role": required_role}
        super().__init__(
            message=message,
            error_code="ACC_SEC_PERMISSION_DENIED",
            details=details,
            metadata=metadata,
        )


class SchedulerException(InfrastructureException):
    """Raised when background task scheduling or job orchestration fails."""

    def __init__(
        self,
        job_id: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        metadata = {"job_id": job_id}
        super().__init__(
            message=message,
            error_code="ACC_SCHEDULER_FAILURE",
            details=details,
            metadata=metadata,
        )
