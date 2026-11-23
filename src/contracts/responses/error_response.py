"""REST API Error Response Contracts.

This module defines the transport response contracts (ErrorDetail and ErrorResponse)
used by REST API gateways, CLI applications, and payload serializers to output
structured JSON error contracts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Field-level or granular contextual error detail."""

    field: Optional[str] = Field(
        default=None, description="Field or parameter name associated with error."
    )
    issue: str = Field(description="Human-readable description of specific issue.")


class ErrorResponse(BaseModel):
    """Standardized platform REST API error response payload contract."""

    error_code: str = Field(
        description="Machine-readable semantic error code (e.g. 'ACC_BATCH_INVALID_STATE')."
    )
    message: str = Field(description="User-friendly error description.")
    http_status: int = Field(description="Corresponding HTTP status code (e.g. 400, 404, 422).")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when error occurred.",
    )
    correlation_id: Optional[str] = Field(
        default=None, description="Thread-local tracing request identifier."
    )
    details: List[ErrorDetail] = Field(
        default_factory=list, description="List of granular error details."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Contextual diagnostic state parameters."
    )
