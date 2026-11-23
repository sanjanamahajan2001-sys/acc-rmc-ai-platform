"""Batch & Production Event Ingestion DTO Contracts."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field, field_validator
from src.contracts.ingestion.base import BaseIngestionModel


class BatchIngestionDTO(BaseIngestionModel):
    """Batch Production Entry DTO Contract."""

    batch_number: str = Field(..., min_length=3, max_length=64, description="Unique batch identifier number.")
    order_number: str = Field(..., min_length=3, max_length=64, description="Commercial order identifier number.")
    delivery_challan: Optional[str] = Field(None, max_length=64, description="RAW delivery challan document identifier.")
    truck_number: Optional[str] = Field(None, max_length=64, description="RAW transit mixer vehicle registration code.")
    plant_code: str = Field(..., min_length=2, max_length=32, description="Target plant operational code.")
    recipe_code: str = Field(..., min_length=3, max_length=64, description="Concrete mix design recipe code.")
    planned_quantity_m3: Decimal = Field(..., gt=Decimal("0.00"), max_digits=10, decimal_places=2, description="Planned volume in m3.")
    actual_quantity_m3: Optional[Decimal] = Field(None, ge=Decimal("0.00"), max_digits=10, decimal_places=2, description="Actual batched volume in m3.")
    dataset_origin: str = Field(default="OPERATIONAL_ACTUAL", max_length=64, description="Dataset provenance: OPERATIONAL_ACTUAL, LAB_FORECAST_DESIGN, HISTORICAL_QC.")
    production_start_time: Optional[datetime] = Field(None, description="UTC batching start timestamp.")
    production_end_time: Optional[datetime] = Field(None, description="UTC batching end timestamp.")
    operator_id: Optional[str] = Field(None, max_length=64, description="Plant operator identifier.")

    @field_validator("actual_quantity_m3")
    @classmethod
    def validate_actual_quantity(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Verify actual quantity does not exceed reasonable limits if present."""
        if v is not None and v <= Decimal("0.00"):
            raise ValueError("actual_quantity_m3 must be greater than zero when specified.")
        return v


class ProductionEventIngestionDTO(BaseIngestionModel):
    """Production Event DTO Contract."""

    event_type: str = Field(..., min_length=2, max_length=64, description="Event classification type.")
    event_timestamp: datetime = Field(..., description="UTC event timestamp.")
    sequence_number: int = Field(..., ge=1, description="Timeline sequence position.")
    device_id: Optional[str] = Field(None, max_length=64, description="Weighing scale / SCADA device ID.")
    remarks: Optional[str] = Field(None, max_length=512, description="Operational remarks.")
