"""Enterprise Laboratory & Quality Assurance ORM Models.

This module provides normalized ORM entities for concrete sampling, slump tests,
cube testing, FT7 quality certificates, and quality observations with sequence constraints.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import (
    AuditMetadataMixin,
    BaseModel,
    CreatedAtMixin,
    GUID,
    OptimisticLockMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
)


class ConcreteSample(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "lab_samples"

    sample_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False, index=True)
    sampling_location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    sampling_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(64), default="FRESH_CONCRETE", nullable=False)
    collected_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    slump_tests: Mapped[List["SlumpTest"]] = relationship("SlumpTest", back_populates="sample", cascade="all, delete-orphan")
    cube_sets: Mapped[List["CubeSet"]] = relationship("CubeSet", back_populates="sample", cascade="all, delete-orphan")


class SlumpTest(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "lab_slump_tests"

    sample_id: Mapped[str] = mapped_column(GUID, ForeignKey("lab_samples.id"), nullable=False, index=True)
    slump_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    test_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    mould_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    saturated_mass_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    mass_in_water_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    calculated_volume_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)
    failure_load_kn: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    specimen_condition: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tester_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ambient_temp_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    concrete_temp_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    sample: Mapped["ConcreteSample"] = relationship("ConcreteSample", back_populates="slump_tests")


class CubeSet(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "lab_cube_sets"

    cube_set_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    sample_id: Mapped[str] = mapped_column(GUID, ForeignKey("lab_samples.id"), nullable=False, index=True)
    casting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    number_of_cubes: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    target_schedule: Mapped[Optional[str]] = mapped_column(String(64), default="7_28_DAYS", nullable=True)

    sample: Mapped["ConcreteSample"] = relationship("ConcreteSample", back_populates="cube_sets")
    cube_tests: Mapped[List["CubeTest"]] = relationship("CubeTest", back_populates="cube_set", cascade="all, delete-orphan")


class CubeTest(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "lab_cube_tests"

    cube_set_id: Mapped[str] = mapped_column(GUID, ForeignKey("lab_cube_sets.id"), nullable=False, index=True)
    age_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 3, 7, 28, 56, 90
    compressive_strength_mpa: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    failure_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    test_machine_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tested_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    test_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    mould_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    saturated_mass_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    mass_in_water_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    calculated_volume_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)
    failure_load_kn: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    specimen_condition: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    cube_set: Mapped["CubeSet"] = relationship("CubeSet", back_populates="cube_tests")


class FT7Certificate(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "lab_ft7_certificates"

    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False, index=True)
    generated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    certificate_status: Mapped[str] = mapped_column(String(64), default="ISSUED", nullable=False)
    certificate_metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class QualityObservation(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "lab_quality_observations"

    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False, index=True)
    observation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    raised_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    observation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(64), default="OPEN", nullable=False)
