"""Enterprise Lookup Reference ORM Models.

This module provides normalized ORM lookup tables for platform enumerations and reference lookup data.
"""

from typing import Optional
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import BaseModel, CreatedAtMixin, GUID, UUIDPrimaryKeyMixin, UpdatedAtMixin


class BaseLookupTable(BaseModel, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    """Abstract Base Class for normalized Lookup Tables."""

    __abstract__ = True

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class BatchStatusLookup(BaseLookupTable):
    __tablename__ = "lkp_batch_statuses"


class OrderStatusLookup(BaseLookupTable):
    __tablename__ = "lkp_order_statuses"


class QualityDispositionLookup(BaseLookupTable):
    __tablename__ = "lkp_quality_dispositions"


class MaterialTypeLookup(BaseLookupTable):
    __tablename__ = "lkp_material_types"


class VehicleStatusLookup(BaseLookupTable):
    __tablename__ = "lkp_vehicle_statuses"


class DriverStatusLookup(BaseLookupTable):
    __tablename__ = "lkp_driver_statuses"


class ImportStatusLookup(BaseLookupTable):
    __tablename__ = "lkp_import_statuses"
