"""Quality Testing & FT7 Certificate Ingestion DTO Contracts."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import Field, field_validator
from src.contracts.ingestion.base import BaseIngestionModel


class SlumpTestIngestionDTO(BaseIngestionModel):
    """Slump Test Record DTO Contract."""

    slump_mm: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("300.00"), max_digits=6, decimal_places=2, description="Slump measurement in mm.")
    test_timestamp: datetime = Field(..., description="UTC slump testing timestamp.")
    tester_name: Optional[str] = Field(None, max_length=128, description="Quality technician name.")
    ambient_temperature_c: Optional[Decimal] = Field(None, ge=Decimal("-10.00"), le=Decimal("60.00"), max_digits=5, decimal_places=2)
    concrete_temperature_c: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("60.00"), max_digits=5, decimal_places=2)


class IndividualCubeSpecimenDTO(BaseIngestionModel):
    """Individual Cube Specimen Test Record DTO Contract."""

    mould_identifier: str = Field(..., min_length=1, max_length=64, description="RAW mould or specimen identifier (e.g. MOULD-01-A).")
    casting_timestamp: Optional[datetime] = Field(None, description="RAW specimen casting timestamp.")
    testing_timestamp: datetime = Field(..., description="RAW UTC breaking test timestamp.")
    age_days: int = Field(..., ge=1, le=365, description="RAW specimen testing age in days (e.g. 7 or 28).")
    specimen_condition: Optional[str] = Field(None, max_length=64, description="RAW physical specimen condition (e.g. SATURATED, NORMAL).")
    saturated_mass_kg: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("500.00"), max_digits=8, decimal_places=3, description="RAW saturated specimen mass in kg.")
    mass_in_water_kg: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("500.00"), max_digits=8, decimal_places=3, description="RAW submerged specimen mass in water in kg.")
    calculated_volume_m3: Optional[Decimal] = Field(None, ge=Decimal("0.000000"), le=Decimal("1.000000"), max_digits=8, decimal_places=6, description="DERIVED specimen volume in m³.")
    failure_load_kn: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("2000.00"), max_digits=8, decimal_places=2, description="RAW maximum load at failure in kN.")
    source_compressive_strength_mpa: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("150.00"), max_digits=6, decimal_places=2, description="RAW compressive strength directly reported by client/Excel source in MPa.")
    calculated_compressive_strength_mpa: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("150.00"), max_digits=6, decimal_places=2, description="DERIVED compressive strength calculated from (failure_load_kn / area) in MPa.")
    failure_mode: Optional[str] = Field(None, max_length=64, description="RAW failure mode classification (e.g. NORMAL_FLAT).")
    tested_by_user: Optional[str] = Field(None, max_length=128, description="RAW laboratory technician name.")

    @property
    def compressive_strength_mpa(self) -> Decimal:
        """Convenience property returning RAW source compressive strength for legacy compatibility."""
        return self.source_compressive_strength_mpa



class CubeTestIngestionDTO(BaseIngestionModel):
    """Compressive Strength Cube Test Set DTO Contract."""

    cube_set_number: str = Field(..., min_length=3, max_length=64, description="Cube set identifier.")
    age_days: int = Field(..., ge=1, le=365, description="Testing age in days (e.g., 7 or 28).")
    compressive_strength_mpa: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("150.00"), max_digits=6, decimal_places=2, description="Tested set compressive strength in MPa.")
    testing_timestamp: datetime = Field(..., description="UTC breaking test timestamp.")
    tested_by_user: Optional[str] = Field(None, max_length=128, description="Laboratory technician name.")
    cube_specimens: Optional[List[IndividualCubeSpecimenDTO]] = Field(None, description="Optional array of individual cube specimen test records.")


class FT7CertificateIngestionDTO(BaseIngestionModel):
    """FT7 Quality Compliance Certificate DTO Contract."""

    certificate_number: str = Field(..., min_length=3, max_length=64, description="Unique FT7 certificate number.")
    issued_date: datetime = Field(..., description="UTC issuance timestamp.")
    approval_status: str = Field(default="APPROVED", min_length=2, max_length=32, description="FT7 compliance status.")
    remarks: Optional[str] = Field(None, max_length=512, description="Quality remarks.")
