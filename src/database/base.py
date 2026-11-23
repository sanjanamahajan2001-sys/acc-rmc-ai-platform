"""Declarative Base and Reusable ORM Model Mixins.

This module provides the SQLAlchemy 2.0 DeclarativeBase (`BaseModel`) and 6 production-grade
reusable mixins (UUID primary key, timezone-aware UTC created_at, updated_at, soft delete, optimistic locking, and audit metadata).
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, MetaData, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

NAMING_CONVENTION: Dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)


class GUID(TypeDecorator):
    """Platform Portable GUID type.

    Uses PostgreSQL native UUID if available, falling back to String(36) on SQLite.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            val_str = str(value).strip()
            try:
                # If already valid UUID format, return standard UUID
                return uuid.UUID(val_str)
            except (ValueError, AttributeError):
                # Deterministically convert domain string identifiers (e.g. ORD-1234, PRJ-1234) to valid UUIDs
                return uuid.uuid5(uuid.NAMESPACE_DNS, val_str)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


class BaseModel(DeclarativeBase):
    """Base Declarative Class for all platform database models.

    Infrastructure behavior only — zero business columns defined here.
    """

    metadata = metadata_obj


class UUIDPrimaryKeyMixin:
    """Mixin adding strongly typed UUIDv4 primary key column using portable GUID type."""

    id: Mapped[str] = mapped_column(
        GUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        sort_order=-100,
    )


class CreatedAtMixin:
    """Mixin adding automatic timezone-aware UTC created_at timestamp column."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UpdatedAtMixin:
    """Mixin adding automatic timezone-aware UTC updated_at timestamp column."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin adding soft delete functionality (is_deleted flag & deleted_at timestamp)."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class OptimisticLockMixin:
    """Mixin adding optimistic locking version_id counter column."""

    version_id: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    __mapper_args__ = {
        "version_id_col": version_id,
    }


class AuditMetadataMixin:
    """Mixin adding created_by_user_id and updated_by_user_id audit columns."""

    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
