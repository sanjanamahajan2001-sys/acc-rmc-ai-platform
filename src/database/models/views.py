"""Enterprise Database Read Models & Analytical Views.

This module provides read-only ORM mappings for database analytical views supporting batch summaries,
material consumption summaries, quality summaries, prediction summaries, and audit activities.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import DateTime, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import BaseModel


class BatchSummaryView(BaseModel):
    """Read-only model for vw_batch_summary."""

    __tablename__ = "vw_batch_summary"
    __table_args__ = {"info": {"is_view": True}}

    batch_number: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_number: Mapped[str] = mapped_column(String(64))
    plant_code: Mapped[str] = mapped_column(String(32))
    recipe_code: Mapped[str] = mapped_column(String(64))
    production_status: Mapped[str] = mapped_column(String(64))
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    actual_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    production_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    production_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MaterialConsumptionSummaryView(BaseModel):
    """Read-only model for vw_material_consumption_summary."""

    __tablename__ = "vw_material_consumption_summary"
    __table_args__ = {"info": {"is_view": True}}

    batch_number: Mapped[str] = mapped_column(String(64), primary_key=True)
    material_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    variance_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    variance_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2))


class QualitySummaryView(BaseModel):
    """Read-only model for vw_quality_summary."""

    __tablename__ = "vw_quality_summary"
    __table_args__ = {"info": {"is_view": True}}

    sample_number: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(64))
    slump_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    cube_strength_7d: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    cube_strength_28d: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    ft7_certificate_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class MLStrengthFeatureView(BaseModel):
    """Read-only model for vw_ml_strength_features (Canonical ML Feature Store View)."""

    __tablename__ = "vw_ml_strength_features"
    __table_args__ = {"info": {"is_view": True}}

    batch_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(64))
    recipe_code: Mapped[str] = mapped_column(String(64))
    plant_code: Mapped[str] = mapped_column(String(32))
    dataset_origin: Mapped[str] = mapped_column(String(64))
    batch_volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cement_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ggbs_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    flyash_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_binder_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    water_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    admixture_kg_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fine_aggregate_kg_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    coarse_aggregate_kg_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    water_binder_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    water_cement_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    age_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compressive_strength_mpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)


class PredictionSummaryView(BaseModel):
    """Read-only model for vw_prediction_summary."""

    __tablename__ = "vw_prediction_summary"
    __table_args__ = {"info": {"is_view": True}}

    prediction_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64))
    predicted_strength: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    actual_strength: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditActivityView(BaseModel):
    """Read-only model for vw_audit_activity."""

    __tablename__ = "vw_audit_activity"
    __table_args__ = {"info": {"is_view": True}}

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32))
    performed_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    severity: Mapped[str] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(32))
