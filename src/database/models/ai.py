"""Enterprise AI Feature Store, Prediction History & Model Registry ORM Models.

This module provides normalized ORM entities for feature vector snapshots, model registry metadata,
prediction execution records, actual outcome links, prediction audit trails, and drift metrics.
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


class FeatureVector(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "ai_feature_vectors"

    batch_id: Mapped[str] = mapped_column(GUID, ForeignKey("prd_batches.id"), nullable=False, index=True)
    sample_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("lab_samples.id"), nullable=True, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(64), default="1.0.0", nullable=False)
    feature_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    feature_payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    feature_generation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="feature_vector", cascade="all, delete-orphan")


class Prediction(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "ai_predictions"

    feature_vector_id: Mapped[str] = mapped_column(GUID, ForeignKey("ai_feature_vectors.id"), nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(64), default="STRENGTH_28D", nullable=False)
    predicted_strength_mpa: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    inference_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prediction_status: Mapped[str] = mapped_column(String(64), default="COMPLETED", nullable=False)
    prediction_source: Mapped[str] = mapped_column(String(64), default="MODEL", nullable=False, index=True)
    fallback_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    feature_vector: Mapped["FeatureVector"] = relationship("FeatureVector", back_populates="predictions")
    actual_outcomes: Mapped[List["ActualOutcome"]] = relationship("ActualOutcome", back_populates="prediction", cascade="all, delete-orphan")
    audits: Mapped[List["PredictionAudit"]] = relationship("PredictionAudit", back_populates="prediction", cascade="all, delete-orphan")


class ActualOutcome(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "ai_actual_outcomes"

    prediction_id: Mapped[str] = mapped_column(GUID, ForeignKey("ai_predictions.id"), nullable=False, unique=True, index=True)
    cube_test_id: Mapped[str] = mapped_column(GUID, ForeignKey("lab_cube_tests.id"), nullable=False, index=True)
    actual_strength_mpa: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    outcome_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="actual_outcomes")


class ModelRegistry(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "ai_model_registry"
    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_model_name_version"),
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    framework: Mapped[str] = mapped_column(String(64), default="scikit-learn", nullable=False)
    algorithm: Mapped[str] = mapped_column(String(128), default="XGBoostRegressor", nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(64), default="1.0.0", nullable=False)
    training_dataset_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    artifact_location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    deployment_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    deployment_status: Mapped[str] = mapped_column(String(64), default="ACTIVE", nullable=False)


class PredictionAudit(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "ai_prediction_audit"

    prediction_id: Mapped[str] = mapped_column(GUID, ForeignKey("ai_predictions.id"), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    execution_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    execution_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="SUCCESS", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="audits")


class DriftSnapshot(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "ai_drift_snapshots"

    snapshot_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    monitored_feature: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reference_distribution_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_distribution_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    drift_metric: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0.0500"), nullable=False)
    drift_detected: Mapped[bool] = mapped_column(default=False, nullable=False)


class MLTrainingJob(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    """Authoritative Durable State Entity for ML Training Jobs (Phase 13B)."""
    __tablename__ = "ai_training_jobs"

    dataset_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feature_schema_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dataset_origin_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", nullable=False, index=True)
    worker_pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_timeout_seconds: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    execution_metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
