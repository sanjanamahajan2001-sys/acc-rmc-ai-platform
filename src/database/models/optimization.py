"""Enterprise AI Mix Optimization ORM Models.

This module provides normalized ORM entities for mix optimization execution runs,
immutable recipe/model/constraint/pricing context snapshots, candidate mix alternatives,
and human review audit logs.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
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


class OptimizationRun(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "ai_optimization_runs"

    recipe_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_recipes.id"), nullable=False, index=True)
    recipe_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    plant_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    optimization_objective: Mapped[str] = mapped_column(String(64), default="MINIMIZE_COST", nullable=False)
    run_status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False, index=True)
    
    # Immutable context snapshots
    recipe_snapshot_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    model_snapshot_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    target_strength_snapshot_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    constraints_snapshot_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    pricing_snapshot_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    candidates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stage_message: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    triggered_by_user_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("usr_users.id"), nullable=True)

    candidates: Mapped[List["OptimizationCandidate"]] = relationship(
        "OptimizationCandidate", back_populates="run", cascade="all, delete-orphan"
    )


class OptimizationCandidate(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "ai_optimization_candidates"

    run_id: Mapped[str] = mapped_column(GUID, ForeignKey("ai_optimization_runs.id"), nullable=False, index=True)
    candidate_identifier: Mapped[str] = mapped_column(String(32), nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_feasible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    predicted_strength_mpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    prediction_source: Mapped[str] = mapped_column(String(32), default="ML_MODEL", nullable=False)
    cost_per_m3: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    binder_intensity: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    
    constituent_payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    constraint_evaluation_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped["OptimizationRun"] = relationship("OptimizationRun", back_populates="candidates")
