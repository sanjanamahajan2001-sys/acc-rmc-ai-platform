"""Production Master Data Management REST API Router.

Provides database-backed CRUD endpoints for Target Plants, Dataset Types, Import Profiles, Recipes, and Customers.
Zero auto-seeding. Zero hardcoded array fallbacks.
Secured with centralized server-side RBAC dependencies.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from src.database.models.master import Plant, Customer, Recipe
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import CubeTest
from src.master_data.models import DatasetTypeModel
from src.mapping.models import ImportProfile
from src.security.dependencies import (
    get_db,
    get_current_user,
    require_roles,
)
from src.database.models.user import User


router = APIRouter(prefix="/api/v1/master-data", tags=["Master Data Management"])


# --- DTO Models ---
class TargetPlantDTO(BaseModel):
    id: str
    plant_code: str
    plant_name: str
    region: str
    timezone: str

    model_config = ConfigDict(from_attributes=True)


class CreateTargetPlantDTO(BaseModel):
    plant_name: str
    plant_code: str
    region: str = "Western Region"
    timezone: str = "Asia/Kolkata"


class DatasetTypeDTO(BaseModel):
    id: str
    type_code: str
    type_name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class CreateDatasetTypeDTO(BaseModel):
    type_name: str
    type_code: str
    description: str = ""


class ImportProfileDTO(BaseModel):
    id: str
    profile_code: str
    name: str
    version: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class CreateImportProfileDTO(BaseModel):
    name: str
    profile_code: str
    version: str = "v1.0"
    description: str = ""


class RecipeDTO(BaseModel):
    id: str
    recipe_code: str
    recipe_name: str
    mix_design_code: str
    grade: str

    model_config = ConfigDict(from_attributes=True)


class CreateRecipeDTO(BaseModel):
    recipe_code: str
    recipe_name: str
    grade: str = "M30"


class CustomerDTO(BaseModel):
    id: str
    customer_code: str
    legal_name: str

    model_config = ConfigDict(from_attributes=True)


class CreateCustomerDTO(BaseModel):
    customer_code: str
    legal_name: str


class DashboardMetricsDTO(BaseModel):
    active_plants_count: int
    total_ingested_batches: int
    total_volume_m3: float
    total_cube_tests: int
    quality_compliance_rate_pct: float
    operational_batches_count: int
    historical_qc_batches_count: int
    forecast_design_batches_count: int
    material_consumptions_count: int


# --- Target Plants Endpoints ---
@router.get("/plants", response_model=List[TargetPlantDTO])
def get_target_plants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plants = db.query(Plant).filter(Plant.is_deleted == False).all()
    return [
        TargetPlantDTO(
            id=p.id,
            plant_code=p.plant_code,
            plant_name=p.plant_name,
            region=p.location or "Default Region",
            timezone=p.timezone or "Asia/Kolkata",
        )
        for p in plants
    ]


@router.post("/plants", response_model=TargetPlantDTO)
def create_target_plant(
    payload: CreateTargetPlantDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(Plant).filter(Plant.plant_code == payload.plant_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Plant code '{payload.plant_code}' already exists")

    plant = Plant(
        id=str(uuid.uuid4()),
        plant_code=payload.plant_code,
        plant_name=payload.plant_name,
        location=payload.region,
        timezone=payload.timezone,
    )
    try:
        db.add(plant)
        db.commit()
        db.refresh(plant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database integrity constraint violated: Plant code '{payload.plant_code}' already exists")

    return TargetPlantDTO(
        id=plant.id,
        plant_code=plant.plant_code,
        plant_name=plant.plant_name,
        region=plant.location or "Default Region",
        timezone=plant.timezone or "Asia/Kolkata",
    )


# --- Dataset Types Endpoints ---
@router.get("/dataset-types", response_model=List[DatasetTypeDTO])
def get_dataset_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    types = db.query(DatasetTypeModel).all()
    return [
        DatasetTypeDTO(
            id=dt.id,
            type_code=dt.type_code,
            type_name=dt.type_name,
            description=dt.description or "",
        )
        for dt in types
    ]


@router.post("/dataset-types", response_model=DatasetTypeDTO)
def create_dataset_type(
    payload: CreateDatasetTypeDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")),
):
    existing = db.query(DatasetTypeModel).filter(DatasetTypeModel.type_code == payload.type_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dataset type code '{payload.type_code}' already exists")

    dt = DatasetTypeModel(
        id=str(uuid.uuid4()),
        type_code=payload.type_code,
        type_name=payload.type_name,
        description=payload.description,
    )
    db.add(dt)
    db.commit()
    db.refresh(dt)

    return DatasetTypeDTO(
        id=dt.id,
        type_code=dt.type_code,
        type_name=dt.type_name,
        description=dt.description or "",
    )


# --- Import Profiles Endpoints ---
@router.get("/import-profiles", response_model=List[ImportProfileDTO])
def get_import_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profiles = db.query(ImportProfile).all()
    return [
        ImportProfileDTO(
            id=p.id,
            profile_code=p.vendor_code or f"PROF-{p.id[:6]}",
            name=p.profile_name,
            version=p.profile_version,
            description=p.description or "",
        )
        for p in profiles
    ]


@router.post("/import-profiles", response_model=ImportProfileDTO)
def create_import_profile(
    payload: CreateImportProfileDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")),
):
    existing = db.query(ImportProfile).filter(ImportProfile.profile_name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Import profile name '{payload.name}' already exists")

    profile = ImportProfile(
        id=str(uuid.uuid4()),
        profile_name=payload.name,
        vendor_code=payload.profile_code,
        profile_version=payload.version,
        description=payload.description,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ImportProfileDTO(
        id=profile.id,
        profile_code=profile.vendor_code,
        name=profile.profile_name,
        version=profile.profile_version,
        description=profile.description or "",
    )


# --- Recipes / Mix Designs Endpoints ---
@router.get("/recipes", response_model=List[RecipeDTO])
def get_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipes = db.query(Recipe).filter(Recipe.is_deleted == False).all()
    return [
        RecipeDTO(
            id=r.id,
            recipe_code=r.recipe_code,
            recipe_name=r.recipe_name,
            mix_design_code=r.recipe_code,
            grade=f"M{int(r.target_strength_mpa)}" if r.target_strength_mpa else "M30",
        )
        for r in recipes
    ]


@router.post("/recipes", response_model=RecipeDTO)
def create_recipe(
    payload: CreateRecipeDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")),
):
    existing = db.query(Recipe).filter(Recipe.recipe_code == payload.recipe_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Recipe code '{payload.recipe_code}' already exists")

    # Extract numeric strength target from grade (e.g. M30 -> 30.0, M40 -> 40.0)
    target_strength = 30.0
    if payload.grade and payload.grade.upper().startswith("M"):
        try:
            target_strength = float(payload.grade.upper().replace("M", ""))
        except ValueError:
            target_strength = 30.0

    rec = Recipe(
        id=str(uuid.uuid4()),
        recipe_code=payload.recipe_code,
        recipe_name=payload.recipe_name,
        target_strength_mpa=target_strength,
    )
    try:
        db.add(rec)
        db.commit()
        db.refresh(rec)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database integrity constraint violated: Recipe code '{payload.recipe_code}' already exists")

    return RecipeDTO(
        id=rec.id,
        recipe_code=rec.recipe_code,
        recipe_name=rec.recipe_name,
        mix_design_code=rec.recipe_code,
        grade=f"M{int(rec.target_strength_mpa)}" if rec.target_strength_mpa else "M30",
    )


# --- Customers Endpoints ---
@router.get("/customers", response_model=List[CustomerDTO])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customers = db.query(Customer).filter(Customer.is_deleted == False).all()
    return [
        CustomerDTO(
            id=c.id,
            customer_code=c.customer_code,
            legal_name=c.legal_name,
        )
        for c in customers
    ]


@router.post("/customers", response_model=CustomerDTO)
def create_customer(
    payload: CreateCustomerDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")),
):
    existing = db.query(Customer).filter(Customer.customer_code == payload.customer_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Customer code '{payload.customer_code}' already exists")

    cust = Customer(
        id=str(uuid.uuid4()),
        customer_code=payload.customer_code,
        legal_name=payload.legal_name,
    )
    try:
        db.add(cust)
        db.commit()
        db.refresh(cust)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database integrity constraint violated: Customer code '{payload.customer_code}' already exists")

    return CustomerDTO(
        id=cust.id,
        customer_code=cust.customer_code,
        legal_name=cust.legal_name,
    )


# --- Dashboard Real-Time Metrics ---
@router.get("/dashboard/metrics", response_model=DashboardMetricsDTO)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authoritative real-time operational dashboard metrics derived directly from production database tables."""
    plants_count = db.query(Plant).filter(Plant.is_deleted == False).count()
    total_batches = db.query(Batch).filter(Batch.is_deleted == False).count()

    op_count = db.query(Batch).filter(Batch.dataset_origin == "OPERATIONAL_ACTUAL", Batch.is_deleted == False).count()
    hist_count = db.query(Batch).filter(Batch.dataset_origin == "HISTORICAL_QC", Batch.is_deleted == False).count()
    forecast_count = db.query(Batch).filter(Batch.dataset_origin == "LAB_FORECAST_DESIGN", Batch.is_deleted == False).count()

    vol_res = db.query(func.sum(func.coalesce(Batch.planned_quantity_m3, 0.0))).filter(Batch.is_deleted == False).scalar() or 0.0

    cube_tests_total = db.query(CubeTest).count()
    cube_tests_pass = db.query(CubeTest).filter(CubeTest.compressive_strength_mpa >= 25.0).count()
    compliance_rate = round((cube_tests_pass / cube_tests_total * 100.0), 1) if cube_tests_total > 0 else 100.0

    mat_count = db.query(BatchMaterialConsumption).count()

    return DashboardMetricsDTO(
        active_plants_count=plants_count,
        total_ingested_batches=total_batches,
        total_volume_m3=round(float(vol_res), 2),
        total_cube_tests=cube_tests_total,
        quality_compliance_rate_pct=compliance_rate,
        operational_batches_count=op_count,
        historical_qc_batches_count=hist_count,
        forecast_design_batches_count=forecast_count,
        material_consumptions_count=mat_count
    )
