"""Abstract Base Validation Rule.

This module provides the abstract base class that all validation rules must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class BaseValidationRule(ABC):
    """Abstract base class for all validation rules."""

    def __init__(self, metadata: RuleMetadata) -> None:
        self._metadata = metadata

    @property
    def rule_id(self) -> str:
        return self._metadata.rule_id

    @property
    def rule_name(self) -> str:
        return self._metadata.rule_name

    @property
    def rule_description(self) -> str:
        return self._metadata.description

    @property
    def validation_tier(self) -> ValidationTier:
        return self._metadata.tier

    @property
    def validation_category(self) -> ValidationCategory:
        return self._metadata.category

    @property
    def severity(self) -> ValidationSeverity:
        return self._metadata.severity

    @property
    def version(self) -> str:
        return self._metadata.version

    @property
    def enabled(self) -> bool:
        return self._metadata.enabled

    @property
    def execution_priority(self) -> int:
        return self._metadata.execution_priority

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    @abstractmethod
    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate input value or row context. Returns FieldErrorDetail if invalid, None if valid."""
        pass

    @abstractmethod
    def supports(self, field_id: str) -> bool:
        """Return True if this rule supports validating target field_id."""
        pass
