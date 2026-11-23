"""FastAPI Security Dependencies for Authentication and Authorization.

Provides reusable dependency injectors for extracting current active users,
validating token claims, enforcing session versioning, and verifying RBAC roles.
"""

from typing import Callable, Generator, List, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.models.user import User, SecurityAuditLog
from src.database.session import get_session_factory
from src.security.jwt import (
    decode_and_validate_token,
    InvalidTokenError,
    TokenExpiredError,
)

security_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing scoped transactional database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _extract_client_ip(request: Optional[Request]) -> Optional[str]:
    if not request:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user_from_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
    require_full_access: bool = True,
) -> User:
    """Validate bearer token and resolve corresponding active database user."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent") if request else None

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or malformed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Decode token (signature, expiration, required claims)
        payload = decode_and_validate_token(token, require_full_access=False)
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except (InvalidTokenError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Database-authoritative user lookup
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account status
    if user.account_status != "ACTIVE":
        # Audit access attempt by inactive/deactivated account
        try:
            db.add(
                SecurityAuditLog(
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    event_type="ACCESS_DENIED_ACCOUNT_INACTIVE",
                    resource_name="AUTHENTICATION",
                    details={"account_status": user.account_status},
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled or locked. Contact your administrator.",
        )

    # Enforce session versioning FIRST (instant token invalidation on password change, role change, or logout)
    token_session_version = payload.get("session_version", 0)
    if user.session_version != token_session_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has been invalidated (password changed, role updated, or logged out). Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If full access is required, enforce that must_change_password is False
    if require_full_access and (payload.get("must_change_password") or user.must_change_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required before accessing platform features.",
        )

    return user


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Standard dependency for authenticated operational endpoints (blocks must_change_password=True)."""
    return get_current_user_from_token(request=request, credentials=credentials, db=db, require_full_access=True)


def get_current_user_any_scope(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency allowing temporary forced-change tokens (used for /change-password and /logout)."""
    return get_current_user_from_token(request=request, credentials=credentials, db=db, require_full_access=False)


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency factory checking database-authoritative role assignments."""
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_roles = {r.role_id for r in current_user.role_assignments}
        # SUPER_ADMIN has access to every operational role function
        if "SUPER_ADMIN" in user_roles:
            return current_user

        if not any(role in user_roles for role in allowed_roles):
            client_ip = _extract_client_ip(request)
            user_agent = request.headers.get("user-agent") if request else None
            # Audit authorization failure
            try:
                db.add(
                    SecurityAuditLog(
                        actor_user_id=current_user.id,
                        target_user_id=None,
                        event_type="ACCESS_DENIED",
                        resource_name="RBAC_AUTHORIZATION",
                        details={
                            "user_roles": list(user_roles),
                            "required_roles": list(allowed_roles),
                            "path": request.url.path if request else "unknown",
                            "method": request.method if request else "unknown",
                        },
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )
                )
                db.commit()
            except Exception:
                db.rollback()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role permissions to perform this action.",
            )
        return current_user

    return role_checker
