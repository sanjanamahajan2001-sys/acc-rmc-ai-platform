"""HTTP Status Code Mapper and Exception Converter.

This module isolates transport-level HTTP status code mapping and Exception-to-ErrorResponse
conversion away from pure domain and core exception classes.
"""

from typing import Dict, Optional, Type
from src.contracts.responses.error_response import ErrorDetail, ErrorResponse
from src.exceptions.base import ACCRMCBaseException
from src.exceptions.domain import (
    DuplicateEntityException,
    EntityNotFoundException,
    InvalidBatchStateException,
    QualityDispositionException,
    RecipeComplianceException,
)
from src.exceptions.technical import (
    AuthenticationRequiredException,
    DataConstraintViolationException,
    DatabaseConnectionException,
    ModelNotLoadedException,
    OptimizationDivergenceException,
    PermissionDeniedException,
    ValidationException,
)

# Clean Architecture Exception-to-HTTP Status Mapping Registry
HTTP_STATUS_MAPPING: Dict[Type[ACCRMCBaseException], int] = {
    InvalidBatchStateException: 400,
    AuthenticationRequiredException: 401,
    PermissionDeniedException: 403,
    EntityNotFoundException: 404,
    DuplicateEntityException: 409,
    DataConstraintViolationException: 409,
    QualityDispositionException: 422,
    RecipeComplianceException: 422,
    ValidationException: 422,
    OptimizationDivergenceException: 422,
    DatabaseConnectionException: 503,
    ModelNotLoadedException: 503,
}


def get_http_status_for_exception(exception: ACCRMCBaseException) -> int:
    """Resolve the corresponding HTTP status code for a platform exception."""
    for exc_type, status_code in HTTP_STATUS_MAPPING.items():
        if isinstance(exception, exc_type):
            return status_code
    return 500


def map_exception_to_error_response(
    exception: Exception, correlation_id: Optional[str] = None
) -> ErrorResponse:
    """Convert any platform or Python exception into a standardized ErrorResponse payload."""
    if isinstance(exception, ACCRMCBaseException):
        status_code = get_http_status_for_exception(exception)
        details = [
            ErrorDetail(field=d.get("field"), issue=d.get("issue", str(d)))
            for d in exception.details
        ]
        return ErrorResponse(
            error_code=exception.error_code,
            message=exception.message,
            http_status=status_code,
            correlation_id=correlation_id,
            details=details,
            metadata=exception.metadata,
        )

    # Fallback for unhandled standard Python exceptions
    return ErrorResponse(
        error_code="ACC_SYS_INTERNAL_ERROR",
        message="An unexpected internal server error occurred.",
        http_status=500,
        correlation_id=correlation_id,
        details=[ErrorDetail(issue=str(exception))],
    )
