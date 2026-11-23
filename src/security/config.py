"""Security & Cryptographic Runtime Configuration.

Centralizes environment configuration for JWT signing, token lifetimes,
password policies, and credential security.
"""

import os
import secrets
from typing import Set


class SecurityConfig:
    """Security settings loaded from environment with secure defaults."""

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("ACC_RMC_JWT_SECRET_KEY", "acc-rmc-dev-insecure-jwt-secret-key-2026-replace-in-prod")
    JWT_ALGORITHM: str = os.getenv("ACC_RMC_JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACC_RMC_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours
    FORCED_CHANGE_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACC_RMC_FORCED_CHANGE_TOKEN_EXPIRE_MINUTES", "60"))  # 1 hour

    # Password Policy Configuration
    PASSWORD_MIN_LENGTH: int = int(os.getenv("ACC_RMC_PASSWORD_MIN_LENGTH", "10"))
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    SPECIAL_CHARACTERS: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Temporary Credential Configuration
    TEMP_PASSWORD_LENGTH: int = int(os.getenv("ACC_RMC_TEMP_PASSWORD_LENGTH", "14"))
    TEMP_PASSWORD_EXPIRE_HOURS: int = int(os.getenv("ACC_RMC_TEMP_PASSWORD_EXPIRE_HOURS", "72"))  # 3 days

    # Sensitive Keys for Redaction
    REDACTION_KEYS: Set[str] = {
        "password",
        "current_password",
        "new_password",
        "confirm_new_password",
        "temporary_password",
        "temp_password",
        "temp_pass",
        "password_hash",
        "access_token",
        "refresh_token",
        "token",
        "authorization",
        "secret",
        "api_key",
        "cookie",
        "raw_password",
        "secret_key",
    }


config = SecurityConfig()
