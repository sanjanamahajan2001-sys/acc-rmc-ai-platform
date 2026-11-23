"""Enterprise Order & Dispatch Planning ORM Models.

This module provides normalized ORM entities for customer demand, orders, line items,
dispatch schedules, and dispatch allocations with Decimal currency fields and sequence constraints.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
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


class Order(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "ord_orders"

    order_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_customers.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_projects.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_plants.id"), nullable=False)
    order_status_id: Mapped[str] = mapped_column(GUID, ForeignKey("lkp_order_statuses.id"), nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    requested_delivery_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    total_quantity_m3: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    line_items: Mapped[List["OrderLineItem"]] = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")
    dispatch_schedules: Mapped[List["DispatchSchedule"]] = relationship("DispatchSchedule", back_populates="order", cascade="all, delete-orphan")


class OrderLineItem(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "ord_order_line_items"

    order_id: Mapped[str] = mapped_column(GUID, ForeignKey("ord_orders.id"), nullable=False)
    recipe_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_recipes.id"), nullable=False)
    ordered_quantity_m3: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="line_items")


class DispatchSchedule(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "dsp_schedules"
    __table_args__ = (
        UniqueConstraint("order_id", "sequence_number", name="uq_order_schedule_sequence"),
    )

    schedule_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    order_id: Mapped[str] = mapped_column(GUID, ForeignKey("ord_orders.id"), nullable=False)
    planned_dispatch_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_delivery_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_quantity_m3: Mapped[float] = mapped_column(Float, nullable=False)
    schedule_status: Mapped[str] = mapped_column(String(64), default="PLANNED", nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="dispatch_schedules")
    allocations: Mapped[List["DispatchAllocation"]] = relationship("DispatchAllocation", back_populates="schedule", cascade="all, delete-orphan")


class DispatchAllocation(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "dsp_allocations"

    dispatch_schedule_id: Mapped[str] = mapped_column(GUID, ForeignKey("dsp_schedules.id"), nullable=False)
    planned_vehicle_type_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_vehicle_types.id"), nullable=False)
    allocated_quantity_m3: Mapped[float] = mapped_column(Float, nullable=False)
    allocation_sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    schedule: Mapped["DispatchSchedule"] = relationship("DispatchSchedule", back_populates="allocations")
