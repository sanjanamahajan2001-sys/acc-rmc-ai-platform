"""Administrative User Management REST Router.

Provides endpoints for user provisioning, role governance, optimistic concurrency,
one-time temporary credential disclosures, and Super Admin protection rules.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.schemas.admin_user import (
    UserAdminCreateRequestDTO,
    UserAdminCreateResponseDTO,
    UserAdminListResponseDTO,
    UserAdminMetricsDTO,
    UserAdminResponseDTO,
    UserAdminUpdateRequestDTO,
    PasswordResetResponseDTO,
)
from src.schemas.auth import MessageResponseDTO
from src.security.config import config
from src.security.crypto import (
    generate_temporary_password,
    hash_password,
)
from src.security.dependencies import (
    get_db,
    get_current_user,
    require_roles,
)

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin User Management"])


def _extract_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _build_admin_user_dto(user: User) -> UserAdminResponseDTO:
    role_ids = [r.role_id for r in user.role_assignments]
    return UserAdminResponseDTO(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=role_ids,
        account_status=user.account_status,
        password_status=user.password_status,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        version=user.version,
    )


def _validate_role_ids(requested_roles: List[str], db: Session) -> List[Role]:
    """Validate that all requested roles exist in the database."""
    roles = db.scalars(select(Role).where(Role.id.in_(requested_roles))).all()
    found_ids = {r.id for r in roles}
    for r_id in requested_roles:
        if r_id not in found_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role identifier '{r_id}'. Role does not exist.",
            )
    return roles


def _count_other_active_super_admins(target_user_id: str, db: Session) -> int:
    """Count how many other active Super Administrators exist in the system."""
    return db.scalars(
        select(func.count(User.id))
        .join(UserRole, UserRole.user_id == User.id)
        .where(
            (UserRole.role_id == "SUPER_ADMIN")
            & (User.account_status == "ACTIVE")
            & (User.id != target_user_id)
        )
    ).first() or 0


@router.get("", response_model=UserAdminListResponseDTO)
def list_users(
    q: Optional[str] = Query(None, description="Search query matching username, email, or full name"),
    account_status: Optional[str] = Query(None, description="Filter by account status"),
    role_id: Optional[str] = Query(None, description="Filter by role ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminListResponseDTO:
    """List and search platform users with filtering and top-level governance metrics."""
    query = select(User)

    if q:
        search_pattern = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(User.username).like(search_pattern),
                func.lower(User.email).like(search_pattern),
                func.lower(User.full_name).like(search_pattern),
            )
        )

    if account_status:
        query = query.where(User.account_status == account_status.upper())

    if role_id:
        query = query.join(UserRole, UserRole.user_id == User.id).where(UserRole.role_id == role_id.upper())

    # Total matching count
    total_matching = db.scalars(select(func.count()).select_from(query.subquery())).first() or 0

    # Paginated items
    offset = (page - 1) * page_size
    users = db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(page_size)).all()

    # Compute global metrics
    all_users = db.scalars(select(User)).all()
    total_users = len(all_users)
    active_users = sum(1 for u in all_users if u.account_status == "ACTIVE")
    admin_count = sum(
        1 for u in all_users
        if u.account_status == "ACTIVE" and any(r.role_id in ("SUPER_ADMIN", "ADMIN") for r in u.role_assignments)
    )
    password_pending = sum(
        1 for u in all_users if u.must_change_password or u.password_status == "CHANGE_REQUIRED"
    )

    metrics = UserAdminMetricsDTO(
        total_users=total_users,
        active_users=active_users,
        administrators=admin_count,
        password_pending=password_pending,
    )

    return UserAdminListResponseDTO(
        items=[_build_admin_user_dto(u) for u in users],
        total=total_matching,
        page=page,
        page_size=page_size,
        metrics=metrics,
    )


@router.get("/{user_id}", response_model=UserAdminResponseDTO)
def get_user_detail(
    user_id: str,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminResponseDTO:
    """Retrieve detailed user profile for administrative inspection."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )
    return _build_admin_user_dto(user)


@router.post("", response_model=UserAdminCreateResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserAdminCreateRequestDTO,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminCreateResponseDTO:
    """Create a new platform user and generate a one-time temporary credential."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    clean_username = payload.username.strip().lower()
    clean_email = payload.email.strip().lower()

    # Uniqueness check
    existing = db.scalars(
        select(User).where((User.username == clean_username) | (User.email == clean_email))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username or email address already exists.",
        )

    # Role validation
    _validate_role_ids(payload.roles, db)

    # Authority check: Only SUPER_ADMIN can assign SUPER_ADMIN role
    admin_roles = {r.role_id for r in current_admin.role_assignments}
    if "SUPER_ADMIN" in payload.roles and "SUPER_ADMIN" not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Master Administrator (SUPER_ADMIN) can assign the SUPER_ADMIN role.",
        )

    # Generate one-time temporary credential
    temp_password = generate_temporary_password(14)
    hashed_pw = hash_password(temp_password)
    expires_at = now + timedelta(hours=config.TEMP_PASSWORD_EXPIRE_HOURS)

    # Create User ORM entity
    new_user = User(
        username=clean_username,
        email=clean_email,
        full_name=payload.full_name.strip(),
        password_hash=hashed_pw,
        account_status="ACTIVE",
        password_status="CHANGE_REQUIRED",
        must_change_password=True,
        temporary_password_created_at=now,
        temporary_password_expires_at=expires_at,
        created_by_user_id=current_admin.id,
        session_version=1,
        version=1,
    )
    db.add(new_user)
    db.flush()

    # Assign roles
    for role_id in set(payload.roles):
        db.add(
            UserRole(
                user_id=new_user.id,
                role_id=role_id,
                assigned_by_user_id=current_admin.id,
                assigned_at=now,
            )
        )

    # Record security audit log (redacting password)
    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=new_user.id,
            event_type="USER_CREATED",
            resource_name="USER_MANAGEMENT",
            details={
                "username": new_user.username,
                "email": new_user.email,
                "roles": payload.roles,
                "created_by": current_admin.username,
            },
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return UserAdminCreateResponseDTO(
        user=_build_admin_user_dto(new_user),
        temporary_password=temp_password,
        expires_at=expires_at,
    )


@router.patch("/{user_id}", response_model=UserAdminResponseDTO)
def update_user(
    user_id: str,
    payload: UserAdminUpdateRequestDTO,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminResponseDTO:
    """Update permitted user profile attributes and role assignments."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    admin_roles = {r.role_id for r in current_admin.role_assignments}
    target_roles = {r.role_id for r in user.role_assignments}

    # Hierarchy guard: ADMIN cannot modify SUPER_ADMIN user
    if "SUPER_ADMIN" in target_roles and "SUPER_ADMIN" not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plant Administrators cannot modify a Master Administrator (SUPER_ADMIN) account.",
        )

    # Optimistic locking check
    if payload.version is not None and user.version != payload.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrency conflict: User profile has been modified by another administrator. Please refresh.",
        )

    changes: Dict[str, Any] = {}

    # Email update
    if payload.email is not None:
        clean_email = payload.email.strip().lower()
        if clean_email != user.email:
            existing_email = db.scalars(
                select(User).where((User.email == clean_email) & (User.id != user.id))
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already in use by another account.",
                )
            changes["email"] = {"old": user.email, "new": clean_email}
            user.email = clean_email

    # Full name update
    if payload.full_name is not None:
        clean_name = payload.full_name.strip()
        if clean_name != user.full_name:
            changes["full_name"] = {"old": user.full_name, "new": clean_name}
            user.full_name = clean_name

    # Roles update
    if payload.roles is not None:
        _validate_role_ids(payload.roles, db)
        new_role_set = set(payload.roles)

        # ADMIN cannot grant SUPER_ADMIN
        if "SUPER_ADMIN" in new_role_set and "SUPER_ADMIN" not in admin_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a Master Administrator (SUPER_ADMIN) can assign the SUPER_ADMIN role.",
            )

        # Last SUPER_ADMIN demotion check
        if "SUPER_ADMIN" in target_roles and "SUPER_ADMIN" not in new_role_set:
            other_super_admins = _count_other_active_super_admins(user.id, db)
            if other_super_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the SUPER_ADMIN role from the last remaining Master Administrator.",
                )

        if new_role_set != target_roles:
            changes["roles"] = {"old": list(target_roles), "new": list(new_role_set)}
            # Clear old and add new
            db.scalars(select(UserRole).where(UserRole.user_id == user.id)).all()
            for assignment in user.role_assignments:
                db.delete(assignment)
            db.flush()

            for role_id in new_role_set:
                db.add(
                    UserRole(
                        user_id=user.id,
                        role_id=role_id,
                        assigned_by_user_id=current_admin.id,
                        assigned_at=now,
                    )
                )
            # Invalidate existing sessions immediately on role modification
            user.session_version += 1

    # Increment optimistic locking version and updated_at
    user.version += 1
    user.updated_at = now

    # Record audit log
    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=user.id,
            event_type="USER_UPDATED",
            resource_name="USER_MANAGEMENT",
            details=changes,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return _build_admin_user_dto(user)


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponseDTO)
def reset_user_password(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> PasswordResetResponseDTO:
    """Reset a user's password, generate a new temporary credential, and revoke active sessions."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    admin_roles = {r.role_id for r in current_admin.role_assignments}
    target_roles = {r.role_id for r in user.role_assignments}

    # Hierarchy guard: ADMIN cannot reset SUPER_ADMIN
    if "SUPER_ADMIN" in target_roles and "SUPER_ADMIN" not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plant Administrators cannot reset passwords for a Master Administrator account.",
        )

    # Generate new temporary password
    temp_password = generate_temporary_password(14)
    hashed_pw = hash_password(temp_password)
    expires_at = now + timedelta(hours=config.TEMP_PASSWORD_EXPIRE_HOURS)

    # Update credential state
    user.password_hash = hashed_pw
    user.password_status = "CHANGE_REQUIRED"
    user.must_change_password = True
    user.temporary_password_created_at = now
    user.temporary_password_expires_at = expires_at
    user.failed_login_attempts = 0
    user.lockout_until = None

    # Revoke all active sessions
    user.session_version += 1
    user.version += 1
    user.updated_at = now

    # Record security audit log
    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=user.id,
            event_type="PASSWORD_RESET",
            resource_name="USER_MANAGEMENT",
            details={
                "action": "ADMIN_PASSWORD_RESET",
                "reset_by": current_admin.username,
                "new_session_version": user.session_version,
            },
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return PasswordResetResponseDTO(
        user_id=user.id,
        username=user.username,
        temporary_password=temp_password,
        expires_at=expires_at,
    )


@router.post("/{user_id}/activate", response_model=UserAdminResponseDTO)
def activate_user(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminResponseDTO:
    """Activate a deactivated, inactive, or locked user account."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.account_status = "ACTIVE"
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.version += 1
    user.updated_at = now

    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=user.id,
            event_type="USER_ACTIVATED",
            resource_name="USER_MANAGEMENT",
            details={"activated_by": current_admin.username},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return _build_admin_user_dto(user)


@router.post("/{user_id}/deactivate", response_model=UserAdminResponseDTO)
def deactivate_user(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
    db: Session = Depends(get_db),
) -> UserAdminResponseDTO:
    """Deactivate user account and immediately invalidate all active sessions."""
    now = datetime.now(timezone.utc)
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Self-deactivation prevention
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-deactivation error: You cannot deactivate your own administrator account.",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    admin_roles = {r.role_id for r in current_admin.role_assignments}
    target_roles = {r.role_id for r in user.role_assignments}

    # Hierarchy guard: ADMIN cannot deactivate SUPER_ADMIN
    if "SUPER_ADMIN" in target_roles and "SUPER_ADMIN" not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plant Administrators cannot deactivate a Master Administrator account.",
        )

    # Last SUPER_ADMIN protection
    if "SUPER_ADMIN" in target_roles:
        other_super_admins = _count_other_active_super_admins(user.id, db)
        if other_super_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last remaining active Master Administrator.",
            )

    user.account_status = "DEACTIVATED"
    user.session_version += 1  # Invalidate all active tokens immediately
    user.version += 1
    user.updated_at = now

    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=user.id,
            event_type="USER_DEACTIVATED",
            resource_name="USER_MANAGEMENT",
            details={"deactivated_by": current_admin.username},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return _build_admin_user_dto(user)


@router.delete("/{user_id}", response_model=MessageResponseDTO)
def delete_user(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_roles("SUPER_ADMIN")),
    db: Session = Depends(get_db),
) -> MessageResponseDTO:
    """Permanently delete a user account with strict safeguards (SUPER_ADMIN only)."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Self-deletion prevention
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-deletion error: You cannot delete your own administrator account.",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Protected account: The canonical system administrator 'admin' is permanent and cannot be deleted.",
        )

    target_roles = {r.role_id for r in user.role_assignments}

    # Last SUPER_ADMIN protection
    if "SUPER_ADMIN" in target_roles:
        other_super_admins = _count_other_active_super_admins(user.id, db)
        if other_super_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last remaining active Master Administrator.",
            )

    username_cached = user.username

    # Delete User (UserRole is cascaded automatically, audit logs set actor/target to NULL)
    db.delete(user)
    db.flush()

    # Record deletion audit log
    db.add(
        SecurityAuditLog(
            actor_user_id=current_admin.id,
            target_user_id=None,
            event_type="USER_DELETED",
            resource_name="USER_MANAGEMENT",
            details={"deleted_username": username_cached, "deleted_by": current_admin.username},
            ip_address=client_ip,
            user_agent=user_agent,
        )
    )
    db.commit()

    return MessageResponseDTO(message=f"User '{username_cached}' successfully deleted.")
