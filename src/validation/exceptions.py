"""Validation Registry Exceptions.

This module provides dedicated technical exceptions for validation rule registration, lookup, and configuration.
"""

from src.exceptions.technical import ConfigurationException


class ValidationRegistryException(ConfigurationException):
    """Base exception for validation registry operations."""

    pass


class DuplicateRuleException(ValidationRegistryException):
    """Raised when attempting to register a rule with an already registered rule_id and version."""

    def __init__(self, rule_id: str, version: str) -> None:
        super().__init__(
            message=f"Validation rule '{rule_id}' with version '{version}' is already registered in the registry.",
            error_code="ACC_VAL_DUPLICATE_RULE",
        )


class UnknownRuleException(ValidationRegistryException):
    """Raised when attempting to retrieve an unregistered rule."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(
            message=f"Validation rule '{rule_id}' was not found in the registry.",
            error_code="ACC_VAL_UNKNOWN_RULE",
        )


class InvalidRuleConfigurationException(ValidationRegistryException):
    """Raised when a rule configuration or priority specification is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=f"Invalid validation rule configuration: {message}",
            error_code="ACC_VAL_INVALID_RULE_CONFIG",
        )


class RuleRegistrationException(ValidationRegistryException):
    """Raised when rule registration fails due to missing attributes or invalid structure."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=f"Rule registration failed: {message}",
            error_code="ACC_VAL_REGISTRATION_FAILED",
        )
