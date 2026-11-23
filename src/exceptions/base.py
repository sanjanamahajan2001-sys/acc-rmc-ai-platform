"""Platform Root Exception Hierarchy.

This module defines the fundamental root exception class `ACCRMCBaseException` for the
entire ACC RMC AI Platform. It is transport-agnostic (containing zero HTTP/REST concepts)
to ensure reusability across domain models, background schedulers, CLI tools, and APIs.
"""

from typing import Any, Dict, List, Optional


class ACCRMCBaseException(Exception):
    """Root base exception for all custom platform exceptions.

    Attributes:
        message: Human-readable error description.
        error_code: Semantic, machine-readable error code (e.g. 'ACC_SYS_INTERNAL_ERROR').
        details: List of field-level or contextual error detail dictionaries.
        metadata: Key-value dictionary containing contextual diagnostic state.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_SYS_INTERNAL_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details if details is not None else []
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception attributes into a structured dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
