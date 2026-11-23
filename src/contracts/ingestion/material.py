"""Material Consumption & Weighing Log Ingestion DTO Contracts."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field, field_validator
from src.contracts.ingestion.base import BaseIngestionModel


class MaterialConsumptionIngestionDTO(BaseIngestionModel):
    """Raw Material Consumption Ingestion DTO Contract with Explicit Quantity Semantics."""

    material_code: str = Field(..., min_length=1, max_length=64, description="Master material code or category code.")
    source_material_code: Optional[str] = Field(None, max_length=64, description="Raw plant constituent code before master mapping (e.g. CEMENT 1, SAND 1).")
    planned_quantity: Decimal = Field(..., ge=Decimal("0.00"), max_digits=10, decimal_places=2, description="Planned target material mass.")
    actual_quantity: Decimal = Field(..., ge=Decimal("0.00"), max_digits=10, decimal_places=2, description="Actual batched material mass.")
    quantity_semantics: str = Field(default="KG_PER_M3", max_length=32, description="Quantity unit semantics: TOTAL_BATCH_KG, KG_PER_M3, UNKNOWN.")
    source_unit: str = Field(default="KG/M3", max_length=32, description="Source unit of measure (e.g. KG, KG/M3, L).")
    source_quantity: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2, description="Raw source quantity before conversion.")
    moisture_percentage: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"), max_digits=5, decimal_places=2, description="RAW aggregate surface moisture percentage (%).")
    absorption_percentage: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), le=Decimal("100.00"), max_digits=5, decimal_places=2, description="RAW aggregate water absorption percentage (%).")
    moisture_correction_kg: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2, description="DERIVED moisture correction adjustment mass (kg).")

    @property
    def variance_quantity(self) -> Decimal:
        """Calculate exact variance quantity (actual - planned)."""
        return self.actual_quantity - self.planned_quantity

    @property
    def variance_percentage(self) -> Decimal:
        """Calculate variance percentage relative to planned quantity."""
        if self.planned_quantity == Decimal("0.00"):
            return Decimal("0.00")
        return ((self.actual_quantity - self.planned_quantity) / self.planned_quantity) * Decimal("100.00")


class WeighingLogIngestionDTO(BaseIngestionModel):
    """SCADA Weighing Scale Log DTO Contract."""

    material_code: str = Field(..., min_length=1, max_length=64, description="Raw material master code.")
    target_weight_kg: Decimal = Field(..., ge=Decimal("0.00"), max_digits=10, decimal_places=2)
    actual_weight_kg: Decimal = Field(..., ge=Decimal("0.00"), max_digits=10, decimal_places=2)
    scale_device_id: Optional[str] = Field(None, max_length=64, description="Physical scale / bin identifier.")
    weighing_timestamp: datetime = Field(..., description="UTC scale reading timestamp.")
