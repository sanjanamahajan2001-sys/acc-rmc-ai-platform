"""Import Profile and Column Mapping Database Models.

This module provides the ORM models for versioned import profiles (mst_import_profiles)
and column mappings (mst_import_column_mappings).
"""

from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import BaseModel, GUID, UUIDPrimaryKeyMixin


class ImportProfile(BaseModel, UUIDPrimaryKeyMixin):
    """Version-controlled vendor import profile entity."""

    __tablename__ = "mst_import_profiles"

    profile_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    profile_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", index=True)  # ACTIVE, DEPRECATED, ARCHIVED
    created_from_profile_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("mst_import_profiles.id"), nullable=True)
    header_row_offset: Mapped[int] = mapped_column(default=0, nullable=False)
    signature_keywords_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    mappings: Mapped[List["ImportColumnMapping"]] = relationship(
        "ImportColumnMapping",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class ImportColumnMapping(BaseModel, UUIDPrimaryKeyMixin):
    """External column title to target CanonicalFieldID mapping rule entity."""

    __tablename__ = "mst_import_column_mappings"

    profile_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_import_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    external_header: Mapped[str] = mapped_column(String(128), nullable=False)
    target_canonical_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    transformation_rule: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    default_value: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    unit_override: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    profile: Mapped[ImportProfile] = relationship("ImportProfile", back_populates="mappings")
