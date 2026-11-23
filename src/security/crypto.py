"""Cryptographic & Password Security Services.

Provides bcrypt password hashing, constant-time verification, password policy
enforcement, and cryptographically secure temporary password generation.
"""

import string
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
import bcrypt

from src.security.config import config


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with standard salt rounds.

    Args:
        password: The plaintext password string.

    Returns:
        The encoded bcrypt hash string.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash in constant time.

    Args:
        plain_password: The plaintext password to check.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if password matches the hash, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        plain_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_policy(password: str) -> Tuple[bool, List[str]]:
    """Validate a password against the ACC RMC enterprise password policy.

    Rules:
    - Minimum length 10 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 numeric digit
    - At least 1 special character

    Args:
        password: The candidate password.

    Returns:
        A tuple (is_valid: bool, errors: List[str]).
    """
    errors: List[str] = []

    if not password or not isinstance(password, str):
        return False, ["Password cannot be empty."]

    if password.strip() != password:
        errors.append("Password cannot have leading or trailing whitespace.")

    if len(password) < config.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters long.")

    if config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")

    if config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")

    if config.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one numeric digit.")

    if config.PASSWORD_REQUIRE_SPECIAL and not any(c in config.SPECIAL_CHARACTERS for c in password):
        errors.append(f"Password must contain at least one special character ({config.SPECIAL_CHARACTERS}).")

    return len(errors) == 0, errors


def generate_temporary_password(length: Optional[int] = None) -> str:
    """Generate a cryptographically secure, high-entropy temporary password that satisfies policy.

    Args:
        length: Desired length (defaults to config.TEMP_PASSWORD_LENGTH, min 12).

    Returns:
        A randomly generated, policy-compliant temporary password string.
    """
    target_length = max(length or config.TEMP_PASSWORD_LENGTH, 12)

    # Ensure at least 2 of each required character category
    uppers = [secrets.choice(string.ascii_uppercase) for _ in range(3)]
    lowers = [secrets.choice(string.ascii_lowercase) for _ in range(3)]
    digits = [secrets.choice(string.digits) for _ in range(3)]
    specials = [secrets.choice(config.SPECIAL_CHARACTERS) for _ in range(3)]

    # Fill the remaining characters from combined pool
    all_chars = string.ascii_letters + string.digits + config.SPECIAL_CHARACTERS
    remaining_count = target_length - len(uppers + lowers + digits + specials)
    extra = [secrets.choice(all_chars) for _ in range(max(0, remaining_count))]

    password_list = uppers + lowers + digits + specials + extra
    # Securely shuffle in place using SystemRandom
    secrets.SystemRandom().shuffle(password_list)

    temp_password = "".join(password_list)

    # Sanity check against policy validator
    is_valid, _ = validate_password_policy(temp_password)
    if not is_valid:
        # Fallback to regenerate if edge case occurs
        return generate_temporary_password(length)

    return temp_password


def is_temporary_password_expired(
    created_at: Optional[datetime],
    expires_at: Optional[datetime] = None,
    max_valid_hours: Optional[int] = None,
) -> bool:
    """Check if a temporary password has passed its expiration window.

    Args:
        created_at: When the temporary password was generated.
        expires_at: Optional explicit expiration timestamp.
        max_valid_hours: Optional fallback hours from creation (defaults to config.TEMP_PASSWORD_EXPIRE_HOURS).

    Returns:
        True if expired or invalid, False if still valid.
    """
    now = datetime.now(timezone.utc)

    # If explicit expires_at is present, compare directly
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now >= expires_at

    # If only created_at is present, calculate from window
    if created_at is not None:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        hours = max_valid_hours or config.TEMP_PASSWORD_EXPIRE_HOURS
        expiry_limit = created_at + timedelta(hours=hours)
        return now >= expiry_limit

    # If no timestamps exist, consider expired
    return True
