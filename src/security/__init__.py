"""Canonical Security Package for ACC RMC.

Exports cryptographic services, password policies, token management,
redaction utilities, and administrator bootstrap mechanisms.
"""

from src.security.config import config, SecurityConfig
from src.security.crypto import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_temporary_password,
    is_temporary_password_expired,
)
from src.security.jwt import (
    create_access_token,
    decode_and_validate_token,
    SecurityException,
    TokenExpiredError,
    InvalidTokenError,
    SessionVersionMismatchError,
    ForcedPasswordChangeRequiredError,
)
from src.security.redaction import (
    redact_sensitive_dict,
    redact_sensitive_string,
    REDACTED_LABEL,
)
from src.security.bootstrap_admin import bootstrap_super_admin

__all__ = [
    "config",
    "SecurityConfig",
    "hash_password",
    "verify_password",
    "validate_password_policy",
    "generate_temporary_password",
    "is_temporary_password_expired",
    "create_access_token",
    "decode_and_validate_token",
    "SecurityException",
    "TokenExpiredError",
    "InvalidTokenError",
    "SessionVersionMismatchError",
    "ForcedPasswordChangeRequiredError",
    "redact_sensitive_dict",
    "redact_sensitive_string",
    "REDACTED_LABEL",
    "bootstrap_super_admin",
]
