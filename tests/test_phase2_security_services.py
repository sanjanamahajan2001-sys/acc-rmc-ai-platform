"""Phase 2: Security Utilities & Cryptographic Services Test Suite.

Rigorously verifies:
1. Password hashing (bcrypt) and constant-time verification.
2. Enterprise password policy validation and structured error reporting.
3. Cryptographically random temporary credential generation and policy conformance.
4. Temporary password expiration calculations.
5. JWT token generation, claims preservation, and signature verification.
6. JWT negative security scenarios (expired, tampered signature, missing claims).
7. Session version invalidation (revocation enforcement).
8. Forced-password-change token isolation and scope enforcement.
9. Centralized secret and token redaction across dictionaries and strings.
10. Secure Super Admin bootstrap execution, safe idempotency, and audit logging.
"""

import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
import jwt

from src.database.engine import get_database_engine
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
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
    TokenExpiredError,
    InvalidTokenError,
    SessionVersionMismatchError,
    ForcedPasswordChangeRequiredError,
)
from src.security.redaction import redact_sensitive_dict, redact_sensitive_string
from src.security.bootstrap_admin import bootstrap_super_admin
from src.security.config import config


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session
        session.rollback()


# ==============================================================================
# 1. PASSWORD HASHING & VERIFICATION TESTS
# ==============================================================================

def test_password_hashing_and_verification():
    """Verify that bcrypt hashing produces non-plaintext output and verifies correctly."""
    plain = "AccSecurePass#2026"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword#999", hashed) is False
    assert verify_password("", hashed) is False


def test_password_hashing_empty_fails():
    """Verify that empty or non-string password throws ValueError."""
    with pytest.raises(ValueError):
        hash_password("")
    with pytest.raises(ValueError):
        hash_password(None)  # type: ignore


# ==============================================================================
# 2. PASSWORD POLICY TESTS
# ==============================================================================

def test_password_policy_valid():
    """Verify that a compliant password passes policy check."""
    is_valid, errors = validate_password_policy("StrongPass@2026")
    assert is_valid is True
    assert len(errors) == 0


@pytest.mark.parametrize(
    "bad_password,expected_error_keyword",
    [
        ("Short1!", "at least 10 characters"),
        ("nouppercase123!", "uppercase"),
        ("NOLOWERCASE123!", "lowercase"),
        ("NoDigitsHere!!", "numeric"),
        ("NoSpecialChar123", "special character"),
        (" LeadingSpace@123", "whitespace"),
        ("TrailingSpace@123 ", "whitespace"),
        ("", "empty"),
    ],
)
def test_password_policy_invalid_cases(bad_password: str, expected_error_keyword: str):
    """Verify that policy violations are caught with informative structured errors."""
    is_valid, errors = validate_password_policy(bad_password)
    assert is_valid is False
    assert any(expected_error_keyword.lower() in err.lower() for err in errors)


# ==============================================================================
# 3. TEMPORARY PASSWORD GENERATION TESTS
# ==============================================================================

def test_temporary_password_generation():
    """Verify that generated temporary credentials meet entropy, length, and policy."""
    passwords = set()
    for _ in range(25):
        temp_pw = generate_temporary_password(14)
        assert len(temp_pw) == 14
        is_valid, errors = validate_password_policy(temp_pw)
        assert is_valid is True, f"Generated password failed policy: {errors}"
        passwords.add(temp_pw)

    # Cryptographic randomness check: All 25 passwords must be unique
    assert len(passwords) == 25


def test_temporary_password_expiry():
    """Verify temporary password expiration calculations."""
    now = datetime.now(timezone.utc)
    recent_created = now - timedelta(hours=10)
    old_created = now - timedelta(hours=80)

    # Within 72h window
    assert is_temporary_password_expired(recent_created, max_valid_hours=72) is False
    # Exceeded 72h window
    assert is_temporary_password_expired(old_created, max_valid_hours=72) is True

    # Explicit expires_at
    future_expire = now + timedelta(minutes=30)
    past_expire = now - timedelta(minutes=5)
    assert is_temporary_password_expired(recent_created, expires_at=future_expire) is False
    assert is_temporary_password_expired(recent_created, expires_at=past_expire) is True


# ==============================================================================
# 4. JWT CREATION & VALIDATION TESTS
# ==============================================================================

def test_jwt_token_lifecycle():
    """Verify standard access token creation and decoding with claims."""
    user_id = str(uuid.uuid4())
    token = create_access_token(
        user_id=user_id,
        username="suresh.qa",
        email="suresh@acc-rmc.in",
        roles=["QUALITY_HEAD", "LAB_TECHNICIAN"],
        session_version=2,
        must_change_password=False,
    )

    payload = decode_and_validate_token(token, expected_session_version=2)
    assert payload["sub"] == user_id
    assert payload["username"] == "suresh.qa"
    assert payload["email"] == "suresh@acc-rmc.in"
    assert payload["roles"] == ["QUALITY_HEAD", "LAB_TECHNICIAN"]
    assert payload["session_version"] == 2
    assert payload["must_change_password"] is False
    assert payload["scope"] == "AUTHENTICATED_ACCESS"
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


def test_jwt_negative_scenarios():
    """Verify rejection of expired, forged, malformed, and version-mismatched tokens."""
    user_id = str(uuid.uuid4())

    # 1. Expired token
    expired_token = create_access_token(
        user_id=user_id,
        username="expired.user",
        email="exp@acc.in",
        roles=["ANALYST_VIEWER"],
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(TokenExpiredError):
        decode_and_validate_token(expired_token)

    # 2. Forged signature (tampered token)
    valid_token = create_access_token(
        user_id=user_id,
        username="user1",
        email="u1@acc.in",
        roles=["PLANT_OPERATOR"],
    )
    tampered_token = valid_token[:-4] + "abcd"
    with pytest.raises(InvalidTokenError):
        decode_and_validate_token(tampered_token)

    # 3. Wrong secret key (at least 32 bytes to avoid warning)
    with pytest.raises(InvalidTokenError):
        decode_and_validate_token(valid_token, secret_key="wrong-secret-key-999-must-be-very-long-32bytes!")

    # 4. Session version mismatch (revoked token)
    with pytest.raises(SessionVersionMismatchError):
        decode_and_validate_token(valid_token, expected_session_version=99)


# ==============================================================================
# 5. FORCED PASSWORD CHANGE TOKEN TESTS
# ==============================================================================

def test_forced_password_change_token():
    """Verify that forced-change tokens have restricted scope and are isolated from full access."""
    user_id = str(uuid.uuid4())
    temp_token = create_access_token(
        user_id=user_id,
        username="new.operator",
        email="op@acc.in",
        roles=["PLANT_OPERATOR"],
        must_change_password=True,
    )

    # Accepts when validating for password change flow
    payload = decode_and_validate_token(temp_token, require_full_access=False)
    assert payload["must_change_password"] is True
    assert payload["scope"] == "FORCE_PASSWORD_CHANGE_ONLY"

    # Rejects when full platform access is demanded
    with pytest.raises(ForcedPasswordChangeRequiredError):
        decode_and_validate_token(temp_token, require_full_access=True)


# ==============================================================================
# 6. CENTRALIZED REDACTION TESTS
# ==============================================================================

def test_centralized_secret_redaction():
    """Verify that sensitive credential keys and token strings are scrubbed."""
    raw_payload = {
        "username": "acc.operator",
        "password": "SecretPlaintextPassword!99",
        "nested": {
            "temporary_password": "TempSecret#1234",
            "safe_field": "M30_BATCH_001",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy",
        },
        "items": [
            {"password_hash": "$2b$12$hashed...", "id": "123"},
        ],
    }

    sanitized = redact_sensitive_dict(raw_payload)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["nested"]["temporary_password"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "M30_BATCH_001"
    assert sanitized["items"][0]["password_hash"] == "[REDACTED]"

    # Test string redaction
    header_str = "Authorization: Bearer secret_jwt_token_value_abc123"
    sanitized_str = redact_sensitive_string(header_str)
    assert "secret_jwt_token_value_abc123" not in sanitized_str
    assert "[REDACTED_TOKEN]" in sanitized_str


# ==============================================================================
# 7. SECURE SUPER ADMIN BOOTSTRAP TESTS
# ==============================================================================

def test_secure_super_admin_bootstrap(db_session: Session):
    """Verify secure bootstrap provisioning of initial Super Admin account."""
    unique_suffix = uuid.uuid4().hex[:6]
    admin_uname = f"admin_{unique_suffix}"
    admin_email = f"admin_{unique_suffix}@acc-rmc.in"
    bootstrap_pw = "MasterAdminSecure#2026"

    # Initial Provisioning
    result = bootstrap_super_admin(
        session=db_session,
        username=admin_uname,
        email=admin_email,
        full_name="Master Super Admin",
        password=bootstrap_pw,
    )
    assert result["status"] == "SUCCESS"
    assert result["event_type"] == "SUPER_ADMIN_BOOTSTRAPPED"

    # Verify user in database
    admin_user = db_session.get(User, result["user_id"])
    assert admin_user is not None
    assert admin_user.username == admin_uname
    assert admin_user.account_status == "ACTIVE"
    assert verify_password(bootstrap_pw, admin_user.password_hash) is True

    # Verify role assignment
    user_roles = [r.role_id for r in admin_user.role_assignments]
    assert "SUPER_ADMIN" in user_roles

    # Verify audit record
    audit = db_session.scalars(
        select(SecurityAuditLog).where(SecurityAuditLog.actor_user_id == admin_user.id)
    ).first()
    assert audit is not None
    assert audit.event_type == "SUPER_ADMIN_BOOTSTRAPPED"

    # Idempotent execution (do not overwrite without explicit flag)
    second_result = bootstrap_super_admin(
        session=db_session,
        username=admin_uname,
        email=admin_email,
        password="AnotherPassword#999",
        overwrite_existing=False,
    )
    assert second_result["status"] == "ALREADY_EXISTS"
    # Original password remains unchanged
    refreshed_admin = db_session.get(User, result["user_id"])
    assert verify_password(bootstrap_pw, refreshed_admin.password_hash) is True
