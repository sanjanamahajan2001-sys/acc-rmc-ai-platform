"""Canonical Identity, Role, and Security Audit ORM Models.

This module establishes the canonical persistence models for users, domain roles,
role assignments, and security audit logs in the ACC RMC platform.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import (
    BaseModel,
    CreatedAtMixin,
    GUID,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
)


class Role(BaseModel):
    """Canonical Domain Role definition for ACC RMC RBAC."""

    __tablename__ = "usr_roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Immutable machine ID, e.g. 'SUPER_ADMIN'
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user_assignments: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class User(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    """Canonical Platform User entity."""

    __tablename__ = "usr_users"

    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    account_status: Mapped[str] = mapped_column(
        String(32),
        default="ACTIVE",
        nullable=False,
        index=True,
    )  # ACTIVE, INACTIVE, LOCKED, SUSPENDED, DEACTIVATED

    password_status: Mapped[str] = mapped_column(
        String(32),
        default="NORMAL",
        nullable=False,
    )  # NORMAL, CHANGE_REQUIRED, EXPIRED

    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    temporary_password_created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    temporary_password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lockout_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    session_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic lock version

    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        GUID,
        ForeignKey("usr_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    role_assignments: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="[UserRole.user_id]",
        cascade="all, delete-orphan",
    )

    audit_logs_as_actor: Mapped[List["SecurityAuditLog"]] = relationship(
        "SecurityAuditLog",
        back_populates="actor",
        foreign_keys="[SecurityAuditLog.actor_user_id]",
    )

    audit_logs_as_target: Mapped[List["SecurityAuditLog"]] = relationship(
        "SecurityAuditLog",
        back_populates="target",
        foreign_keys="[SecurityAuditLog.target_user_id]",
    )


class UserRole(BaseModel):
    """Many-to-Many association mapping Users to Domain Roles."""

    __tablename__ = "usr_user_roles"

    user_id: Mapped[str] = mapped_column(
        GUID,
        ForeignKey("usr_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("usr_roles.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    assigned_by_user_id: Mapped[Optional[str]] = mapped_column(
        GUID,
        ForeignKey("usr_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="role_assignments",
        foreign_keys=[user_id],
    )
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_assignments",
        foreign_keys=[role_id],
    )


class SecurityAuditLog(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
):
    """Immutable Security and Administrative Audit Log."""

    __tablename__ = "usr_audit_logs"

    actor_user_id: Mapped[Optional[str]] = mapped_column(
        GUID,
        ForeignKey("usr_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_user_id: Mapped[Optional[str]] = mapped_column(
        GUID,
        ForeignKey("usr_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_name: Mapped[str] = mapped_column(String(64), default="USER_MANAGEMENT", nullable=False)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[actor_user_id],
        back_populates="audit_logs_as_actor",
    )
    target: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="audit_logs_as_target",
    )
