"""JSON Web Token (JWT) Lifecycle & Validation Services.

Provides token generation with standard claims, signature validation, session-version
invalidation, and scope separation for forced password change flows.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import jwt

from src.security.config import config


class SecurityException(Exception):
    """Base security exception."""
    pass


class TokenExpiredError(SecurityException):
    """Raised when a JWT has passed its expiration time."""
    pass


class InvalidTokenError(SecurityException):
    """Raised when a JWT is malformed, invalid signature, or missing required claims."""
    pass


class SessionVersionMismatchError(SecurityException):
    """Raised when a token's session version does not match the user's active version."""
    pass


class ForcedPasswordChangeRequiredError(SecurityException):
    """Raised when a user attempts operational access with a forced-change token."""
    pass


def create_access_token(
    user_id: str,
    username: str,
    email: str,
    roles: List[str],
    session_version: int = 1,
    must_change_password: bool = False,
    scope: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token with standard claims.

    Args:
        user_id: The unique user identifier (sub).
        username: The user's login username.
        email: The user's email address.
        roles: List of assigned role machine IDs (e.g. ['SUPER_ADMIN', 'ADMIN']).
        session_version: Current session version of the user for revocation.
        must_change_password: Flag indicating if user is restricted to changing password.
        scope: Optional explicit token scope (e.g. 'FORCE_PASSWORD_CHANGE_ONLY').
        expires_delta: Optional custom token expiration duration.

    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(timezone.utc)

    if must_change_password:
        # Default to shorter expiry for temporary forced password change tokens
        duration = expires_delta or timedelta(minutes=config.FORCED_CHANGE_TOKEN_EXPIRE_MINUTES)
        effective_scope = scope or "FORCE_PASSWORD_CHANGE_ONLY"
    else:
        duration = expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        effective_scope = scope or "AUTHENTICATED_ACCESS"

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": str(username),
        "email": str(email),
        "roles": list(roles),
        "session_version": int(session_version),
        "must_change_password": bool(must_change_password),
        "scope": str(effective_scope),
        "token_type": "bearer",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + duration).timestamp()),
    }

    return jwt.encode(
        payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_and_validate_token(
    token: str,
    secret_key: Optional[str] = None,
    expected_session_version: Optional[int] = None,
    require_full_access: bool = False,
) -> Dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The raw JWT token string.
        secret_key: Optional secret key override (defaults to config.JWT_SECRET_KEY).
        expected_session_version: Optional current user session version to enforce revocation.
        require_full_access: If True, rejects tokens having must_change_password=True.

    Returns:
        The decoded claims payload dictionary.

    Raises:
        TokenExpiredError: If token has expired.
        InvalidTokenError: If token signature is invalid, malformed, or missing required claims.
        SessionVersionMismatchError: If token session version differs from expected.
        ForcedPasswordChangeRequiredError: If require_full_access is True but token has must_change_password=True.
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError("Authentication token is required.")

    key = secret_key or config.JWT_SECRET_KEY

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[config.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "session_version"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError("Authentication session has expired. Please sign in again.") from e
    except jwt.InvalidSignatureError as e:
        raise InvalidTokenError("Invalid token signature.") from e
    except jwt.PyJWTError as e:
        raise InvalidTokenError(f"Malformed or invalid authentication token: {str(e)}") from e

    # Validate required claims presence
    required_claims = ["sub", "username", "roles", "session_version", "must_change_password"]
    for claim in required_claims:
        if claim not in payload:
            raise InvalidTokenError(f"Token is missing required claim: '{claim}'")

    # Validate session version if provided
    if expected_session_version is not None:
        token_version = payload.get("session_version", 0)
        if token_version != expected_session_version:
            raise SessionVersionMismatchError(
                "Your session has been invalidated (password reset or logged out). Please sign in again."
            )

    # Validate forced password change scope if full access is demanded
    if require_full_access and payload.get("must_change_password", False):
        raise ForcedPasswordChangeRequiredError(
            "Password change required before accessing platform features."
        )

    return payload
