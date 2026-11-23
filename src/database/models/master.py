"""Enterprise Master Reference Data ORM Models.

This module provides normalized ORM models for long-lived business master reference entities
(Plant, Customer, Project, Material, MaterialCategory, Recipe, RecipeMaterial, Supplier, VehicleType, DriverCategory)
with Decimal coordinate precision and immutable business codes.
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
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


class Plant(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_plants"

    plant_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    plant_name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    capacity_per_hour_m3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Customer(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_customers"

    customer_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_details: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    billing_information: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    gst_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    default_plant_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("mst_plants.id"), nullable=True)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="customer")


class Project(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_projects"

    project_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_customers.id"), nullable=False)
    project_name: Mapped[str] = mapped_column(String(128), nullable=False)
    project_location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="ACTIVE", nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="projects")


class Supplier(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_suppliers"

    supplier_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    supplier_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_information: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class MaterialCategory(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_material_categories"

    category_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    category_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class Material(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_materials"

    material_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    material_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("mst_material_categories.id"), nullable=True)
    supplier_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("mst_suppliers.id"), nullable=True)
    engineering_unit: Mapped[str] = mapped_column(String(32), default="kg", nullable=False)
    default_density_kg_m3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Recipe(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_recipes"

    recipe_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    recipe_name: Mapped[str] = mapped_column(String(128), nullable=False)
    mix_design_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    target_strength_mpa: Mapped[float] = mapped_column(Float, nullable=False)
    slump_target_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nominal_max_aggregate_size_mm: Mapped[Optional[float]] = mapped_column(Float, default=20.0, nullable=True)
    exposure_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    water_cement_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    items: Mapped[List["RecipeMaterial"]] = relationship("RecipeMaterial", back_populates="recipe", cascade="all, delete-orphan")


class RecipeMaterial(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
):
    __tablename__ = "mst_recipe_materials"
    __table_args__ = (
        UniqueConstraint("recipe_id", "material_id", name="uq_recipe_material"),
    )

    recipe_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_recipes.id"), nullable=False)
    material_id: Mapped[str] = mapped_column(GUID, ForeignKey("mst_materials.id"), nullable=False)
    target_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    engineering_unit: Mapped[str] = mapped_column(String(32), default="kg", nullable=False)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="items")


class VehicleType(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_vehicle_types"

    vehicle_type_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    type_name: Mapped[str] = mapped_column(String(128), nullable=False)
    capacity_m3: Mapped[float] = mapped_column(Float, nullable=False)
    default_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class DriverCategory(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "mst_driver_categories"

    category_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    category_name: Mapped[str] = mapped_column(String(128), nullable=False)
    qualification_level: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
