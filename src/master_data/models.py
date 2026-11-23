"""Master Data Entities ORM Models.

Provides ORM models for Dataset Types and Target Plants (mst_dataset_types, mst_target_plants).
"""

from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import BaseModel, UUIDPrimaryKeyMixin


class DatasetTypeModel(BaseModel, UUIDPrimaryKeyMixin):
    """Production Master Data Entity for Dataset Types."""

    __tablename__ = "mst_dataset_types"

    type_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    type_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class TargetPlantModel(BaseModel, UUIDPrimaryKeyMixin):
    """Production Master Data Entity for Target RMC Plants."""

    __tablename__ = "mst_target_plants"

    plant_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    plant_name: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    erp_source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
