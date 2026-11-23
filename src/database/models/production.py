"""Enterprise Production & Batch Execution ORM Models.

This module provides normalized ORM entities for concrete batching execution, material usage,
weighing logs, and production event telemetry with sequence constraints.
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


class Batch(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "prd_batches"

    batch_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    order_id: Mapped[str] = mapped_column(GUID, ForeignKey("ord_orders.id"), nullable=False)
    dispatch_schedule_id: Mapped[str] = mapped_column(GUID, ForeignKey("dsp_schedules.id"), nullable=False)
    recipe_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_recipes.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_plants.id"), nullable=False)
    production_status: Mapped[str] = mapped_column(String(64), default="PLANNED", nullable=False, index=True)
    planned_quantity_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_quantity_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    dataset_origin: Mapped[str] = mapped_column(String(64), default="OPERATIONAL_ACTUAL", nullable=False, index=True)
    delivery_challan_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    truck_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    production_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    production_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    mixer_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operator_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    consumptions: Mapped[List["BatchMaterialConsumption"]] = relationship("BatchMaterialConsumption", back_populates="batch", cascade="all, delete-orphan")
    weighing_logs: Mapped[List["WeighingLog"]] = relationship("WeighingLog", back_populates="batch", cascade="all, delete-orphan")
    events: Mapped[List["ProductionEvent"]] = relationship("ProductionEvent", back_populates="batch", cascade="all, delete-orphan")


class BatchMaterialConsumption(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "prd_batch_material_consumptions"

    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False)
    material_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_materials.id"), nullable=False)
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    engineering_unit: Mapped[str] = mapped_column(String(32), default="kg", nullable=False)
    variance_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    variance_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    source_material_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Explicit Unit Semantics & Mass Normalization
    quantity_kg_per_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    actual_quantity_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    planned_quantity_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    source_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    source_unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_quantity_semantics: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    moisture_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    absorption_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    moisture_correction_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="consumptions")
    material: Mapped[Optional["Material"]] = relationship("Material", lazy="joined")


class WeighingLog(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "prd_weighing_logs"

    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False)
    material_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_materials.id"), nullable=False)
    target_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tolerance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    weighing_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    weighing_device_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="weighing_logs")


class ProductionEvent(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "prd_production_events"
    __table_args__ = (
        UniqueConstraint("batch_id", "event_sequence", name="uq_batch_event_sequence"),
    )

    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    event_sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="events")
