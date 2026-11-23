"""Database Model for Engineering & Calculation Calibre Settings (sys_engineering_settings).

Provides persistent storage for design codes, statistical safety factors (Z-multiplier),
IS 456 Table 5 durability constraints, physical volumetric parameters, and SCM bounds.
"""

from typing import Any, Dict
from sqlalchemy import Boolean, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import (
    BaseModel,
    CreatedAtMixin,
    OptimisticLockMixin,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
)


class EngineeringSettingsModel(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    OptimisticLockMixin,
):
    """Production Database Entity for Engineering & Solver Settings (sys_engineering_settings)."""

    __tablename__ = "sys_engineering_settings"

    standard_code: Mapped[str] = mapped_column(String(64), default="IS_456_IS_10262", nullable=False)
    standard_name: Mapped[str] = mapped_column(
        String(128),
        default="IS 456:2000 & IS 10262:2019 (Indian Standards)",
        nullable=False,
    )
    confidence_multiplier_z: Mapped[float] = mapped_column(Float, default=1.65, nullable=False)
    target_strength_formula: Mapped[str] = mapped_column(
        String(128),
        default="f_ck_prime = fck + Z * sigma",
        nullable=False,
    )
    air_volume_fraction: Mapped[float] = mapped_column(Float, default=0.010, nullable=False)
    exposure_constraints_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    scm_substitution_bounds_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    specific_gravities_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by_username: Mapped[str] = mapped_column(String(64), default="admin", nullable=True)
