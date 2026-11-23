"""Canonical Authentication & Identity REST Router.

Provides endpoints for login, session inspection (/me), password change,
and server-authoritative session revocation (/logout).
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.schemas.auth import (
    LoginRequestDTO,
    LoginResponseDTO,
    UserDTO,
    ChangePasswordRequestDTO,
    ChangePasswordResponseDTO,
    MessageResponseDTO,
)
from src.security.config import config
from src.security.crypto import (
    hash_password,
    verify_password,
    validate_password_policy,
    is_temporary_password_expired,
)
from src.security.jwt import create_access_token
from src.security.dependencies import (
    get_db,
    get_current_user,
    get_current_user_any_scope,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Identity"])


def _extract_client_ip(request: Request) -> Optional[str]:
    """Extract client IP respecting standard reverse-proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime object is timezone-aware in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _build_user_dto(user: User) -> UserDTO:
    """Transform User ORM entity into safe UserDTO."""
    role_ids = [r.role_id for r in user.role_assignments]
    return UserDTO(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=role_ids,
        account_status=user.account_status,
        password_status=user.password_status,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=LoginResponseDTO)
def login(
    payload: LoginRequestDTO,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponseDTO:
    """Authenticate user credentials and issue signed JWT session token."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    clean_identifier = payload.username_or_email.strip().lower()

    # Database lookup by username or email
    user = db.scalars(
        select(User).where((User.username == clean_identifier) | (User.email == clean_identifier))
    ).first()

    # Constant time error check to prevent enumeration
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # Check lockout
    user_lockout = _ensure_utc(user.lockout_until)
    if user_lockout and user_lockout > now:
        db.add(
            SecurityAuditLog(
                actor_user_id=user.id,
                target_user_id=user.id,
                event_type="LOGIN_LOCKED",
                resource_name="AUTH",
                details={"reason": "Account temporarily locked due to repeated failed logins."},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked. Please try again later or contact your administrator.",
        )

    # Check account status
    if user.account_status != "ACTIVE":
        db.add(
            SecurityAuditLog(
                actor_user_id=user.id,
                target_user_id=user.id,
                event_type="LOGIN_FAILED",
                resource_name="AUTH",
                details={"reason": f"Account status is {user.account_status}"},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # Verify password hash
    is_valid_pw = verify_password(payload.password, user.password_hash)

    if not is_valid_pw:
        user.failed_login_attempts += 1
        # If 5 consecutive failed attempts, lock for 15 minutes
        if user.failed_login_attempts >= 5:
            user.lockout_until = now + timedelta(minutes=15)
            event_type = "LOGIN_LOCKED"
            details = {"attempts": user.failed_login_attempts, "locked_until": user.lockout_until.isoformat()}
        else:
            event_type = "LOGIN_FAILED"
            details = {"attempts": user.failed_login_attempts}

        db.add(
            SecurityAuditLog(
                actor_user_id=user.id,
                target_user_id=user.id,
                event_type=event_type,
                resource_name="AUTH",
                details=details,
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # Password is valid — check temporary password state and expiration
    role_ids = [r.role_id for r in user.role_assignments]

    if user.must_change_password:
        if is_temporary_password_expired(user.temporary_password_created_at, user.temporary_password_expires_at):
            user.password_status = "EXPIRED"
            db.add(
                SecurityAuditLog(
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    event_type="EXPIRED_TEMPORARY_PASSWORD",
                    resource_name="AUTH",
                    details={"reason": "Temporary password has expired."},
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Temporary password has expired. Contact your administrator to request a reset.",
            )

        # Issue restricted scope token for forced password change
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=role_ids,
            session_version=user.session_version,
            must_change_password=True,
            scope="FORCE_PASSWORD_CHANGE_ONLY",
            expires_delta=timedelta(minutes=config.FORCED_CHANGE_TOKEN_EXPIRE_MINUTES),
        )
        expires_in = config.FORCED_CHANGE_TOKEN_EXPIRE_MINUTES * 60
        event_type = "TEMPORARY_PASSWORD_LOGIN"
    else:
        # Issue standard session token
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=role_ids,
            session_version=user.session_version,
            must_change_password=False,
            scope="AUTHENTICATED_ACCESS",
            expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        expires_in = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        event_type = "LOGIN_SUCCESS"

    # Reset failed attempts and update last login metadata
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.last_login_at = now
    user.last_login_ip = client_ip

    # Audit log
    db.add(
        SecurityAuditLog(
            actor_user_id=user.id,
            target_user_id=user.id,
            event_type=event_type,
            resource_name="AUTH",
            details={"roles": role_ids, "must_change_password": user.must_change_password},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return LoginResponseDTO(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=_build_user_dto(user),
    )


@router.post("/change-password", response_model=ChangePasswordResponseDTO)
def change_password(
    payload: ChangePasswordRequestDTO,
    request: Request,
    current_user: User = Depends(get_current_user_any_scope),
    db: Session = Depends(get_db),
) -> ChangePasswordResponseDTO:
    """Change user password (supports both forced initial change and self-initiated update)."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        db.add(
            SecurityAuditLog(
                actor_user_id=current_user.id,
                target_user_id=current_user.id,
                event_type="PASSWORD_CHANGE_FAILED",
                resource_name="AUTH",
                details={"reason": "Incorrect current password."},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    # Verify password confirmation
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match.",
        )

    # Validate against policy
    is_valid, errors = validate_password_policy(payload.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password policy violation: {'; '.join(errors)}",
        )

    # Update credentials
    current_user.password_hash = hash_password(payload.new_password)
    current_user.password_status = "NORMAL"
    current_user.must_change_password = False
    current_user.password_changed_at = now
    current_user.temporary_password_created_at = None
    current_user.temporary_password_expires_at = None

    # Invalidate existing sessions by incrementing session_version
    current_user.session_version += 1

    role_ids = [r.role_id for r in current_user.role_assignments]

    # Generate new full access token
    new_token = create_access_token(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        roles=role_ids,
        session_version=current_user.session_version,
        must_change_password=False,
        scope="AUTHENTICATED_ACCESS",
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Record audit log
    db.add(
        SecurityAuditLog(
            actor_user_id=current_user.id,
            target_user_id=current_user.id,
            event_type="PASSWORD_CHANGED",
            resource_name="AUTH",
            details={"action": "PASSWORD_UPDATED", "session_version": current_user.session_version},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return ChangePasswordResponseDTO(
        message="Password updated successfully.",
        access_token=new_token,
        token_type="bearer",
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_build_user_dto(current_user),
    )


@router.get("/me", response_model=UserDTO)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserDTO:
    """Return authenticated profile information for the active user."""
    return _build_user_dto(current_user)


@router.post("/logout", response_model=MessageResponseDTO)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user_any_scope),
    db: Session = Depends(get_db),
) -> MessageResponseDTO:
    """Invalidate active session server-authoritatively by incrementing session_version."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    current_user.session_version += 1

    db.add(
        SecurityAuditLog(
            actor_user_id=current_user.id,
            target_user_id=current_user.id,
            event_type="LOGOUT",
            resource_name="AUTH",
            details={"action": "SESSION_REVOKED", "new_session_version": current_user.session_version},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return MessageResponseDTO(message="Successfully logged out. Active sessions invalidated.")
