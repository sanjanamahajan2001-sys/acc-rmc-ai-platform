"""Domain Business Exception Hierarchy.

This module defines pure, transport-agnostic domain business exceptions representing
violations of RMC business rules, state transitions, quality dispositions, and natural keys.
"""

from typing import Any, Dict, List, Optional
from src.exceptions.base import ACCRMCBaseException


class DomainException(ACCRMCBaseException):
    """Base class for all business domain rule violations."""

    def __init__(
        self,
        message: str,
        error_code: str = "ACC_DOMAIN_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            metadata=metadata,
        )


class InvalidBatchStateException(DomainException):
    """Raised when an invalid batch lifecycle state transition is attempted."""

    def __init__(
        self,
        current_state: str,
        target_state: str,
        batch_id: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"Invalid batch state transition from '{current_state}' to '{target_state}'."
        )
        metadata = {
            "current_state": current_state,
            "target_state": target_state,
            "batch_id": batch_id,
        }
        super().__init__(
            message=message,
            error_code="ACC_BATCH_INVALID_STATE",
            details=details,
            metadata=metadata,
        )


class QualityDispositionException(DomainException):
    """Raised when a concrete specimen fails IS 456 quality compliance rules."""

    def __init__(
        self,
        characteristic_strength_mpa: float,
        actual_strength_mpa: float,
        specimen_ref: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"Quality disposition rejected: Compressive strength {actual_strength_mpa:.2f} MPa "
            f"failed characteristic target {characteristic_strength_mpa:.2f} MPa."
        )
        metadata = {
            "characteristic_strength_mpa": characteristic_strength_mpa,
            "actual_strength_mpa": actual_strength_mpa,
            "specimen_ref": specimen_ref,
        }
        super().__init__(
            message=message,
            error_code="ACC_QA_DISPOSITION_REJECTED",
            details=details,
            metadata=metadata,
        )


class RecipeComplianceException(DomainException):
    """Raised when actual material dosing exceeds IS 4926 tolerance bounds."""

    def __init__(
        self,
        material_type: str,
        target_kg: float,
        actual_kg: float,
        tolerance_pct: float,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = (
            f"Recipe compliance failure for '{material_type}': Actual {actual_kg:.2f} kg "
            f"exceeds target {target_kg:.2f} kg by more than allowable ±{tolerance_pct:.1f}%."
        )
        metadata = {
            "material_type": material_type,
            "target_kg": target_kg,
            "actual_kg": actual_kg,
            "tolerance_pct": tolerance_pct,
        }
        super().__init__(
            message=message,
            error_code="ACC_BATCH_DOSING_VARIANCE_EXCEEDED",
            details=details,
            metadata=metadata,
        )


class DuplicateEntityException(DomainException):
    """Raised on natural key or unique field collision (e.g., Duplicate Challan No)."""

    def __init__(
        self,
        entity_name: str,
        key_name: str,
        key_value: Any,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = f"Duplicate {entity_name} collision on {key_name}='{key_value}'."
        metadata = {
            "entity_name": entity_name,
            "key_name": key_name,
            "key_value": str(key_value),
        }
        super().__init__(
            message=message,
            error_code="ACC_BATCH_DUPLICATE_CHALLAN",
            details=details,
            metadata=metadata,
        )


class EntityNotFoundException(DomainException):
    """Raised when a requested entity or master record does not exist."""

    def __init__(
        self,
        entity_name: str,
        identifier: Any,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        message = f"{entity_name} with identifier '{identifier}' was not found."
        metadata = {
            "entity_name": entity_name,
            "identifier": str(identifier),
        }
        super().__init__(
            message=message,
            error_code="ACC_BATCH_NOT_FOUND",
            details=details,
            metadata=metadata,
        )
