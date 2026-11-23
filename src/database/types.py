"""Enterprise Data Types and Unit Definitions.

This module defines standard engineering units, data type categories, source systems,
and reusable type definitions for the ACC RMC AI Platform.
"""

from enum import Enum
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field


class EngineeringUnit(str, Enum):
    """Standardized RMC Engineering Units."""

    MPA = "MPa"
    KG = "kg"
    CUBIC_METER = "m³"
    LITRES = "L"
    MILLIMETER = "mm"
    PERCENTAGE = "%"
    CELSIUS = "°C"
    MINUTES = "min"
    HOURS = "hr"
    KM = "km"
    KM_PER_HOUR = "km/h"
    INR = "INR"
    COUNT = "count"


class DataTypeCategory(str, Enum):
    """Enterprise Data Type Categories."""

    IDENTIFIER = "IDENTIFIER"
    CODE = "CODE"
    NAME = "NAME"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    QUANTITY = "QUANTITY"
    PERCENTAGE = "PERCENTAGE"
    CURRENCY = "CURRENCY"
    GPS = "GPS"
    STRENGTH = "STRENGTH"
    DENSITY = "DENSITY"
    TEMPERATURE = "TEMPERATURE"
    DURATION = "DURATION"
    JSON_PAYLOAD = "JSON_PAYLOAD"


class SourceSystem(str, Enum):
    """Enterprise Originating Source Systems."""

    ERP = "ERP"
    SCADA = "SCADA"
    FT7 = "FT7"
    QA = "QA"
    AI = "AI"
    REST_API = "REST_API"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class UnitDefinition(BaseModel):
    """Metadata contract for an engineering unit."""

    unit: EngineeringUnit = Field(description="Engineering unit enum.")
    symbol: str = Field(description="Unit display symbol.")
    description: str = Field(description="Human readable unit description.")
    default_precision: int = Field(default=2, description="Recommended decimal storage precision.")


UNIT_REGISTRY: Dict[EngineeringUnit, UnitDefinition] = {
    EngineeringUnit.MPA: UnitDefinition(unit=EngineeringUnit.MPA, symbol="MPa", description="Megapascals (Compressive Strength)", default_precision=2),
    EngineeringUnit.KG: UnitDefinition(unit=EngineeringUnit.KG, symbol="kg", description="Kilograms (Batch Weight)", default_precision=2),
    EngineeringUnit.CUBIC_METER: UnitDefinition(unit=EngineeringUnit.CUBIC_METER, symbol="m³", description="Cubic Meters (Concrete Volume)", default_precision=2),
    EngineeringUnit.LITRES: UnitDefinition(unit=EngineeringUnit.LITRES, symbol="L", description="Litres (Liquid Admixture Volume)", default_precision=2),
    EngineeringUnit.MILLIMETER: UnitDefinition(unit=EngineeringUnit.MILLIMETER, symbol="mm", description="Millimeters (Slump Workability)", default_precision=0),
    EngineeringUnit.PERCENTAGE: UnitDefinition(unit=EngineeringUnit.PERCENTAGE, symbol="%", description="Percentage (Moisture Content)", default_precision=2),
    EngineeringUnit.CELSIUS: UnitDefinition(unit=EngineeringUnit.CELSIUS, symbol="°C", description="Degrees Celsius (Concrete Temperature)", default_precision=1),
    EngineeringUnit.MINUTES: UnitDefinition(unit=EngineeringUnit.MINUTES, symbol="min", description="Minutes (Mixing / Transit Duration)", default_precision=0),
    EngineeringUnit.HOURS: UnitDefinition(unit=EngineeringUnit.HOURS, symbol="hr", description="Hours (Operation Duration)", default_precision=2),
    EngineeringUnit.KM: UnitDefinition(unit=EngineeringUnit.KM, symbol="km", description="Kilometers (Haul Distance)", default_precision=2),
    EngineeringUnit.KM_PER_HOUR: UnitDefinition(unit=EngineeringUnit.KM_PER_HOUR, symbol="km/h", description="Kilometers per Hour (Transit Speed)", default_precision=1),
    EngineeringUnit.INR: UnitDefinition(unit=EngineeringUnit.INR, symbol="₹", description="Indian Rupees (Cost / Pricing)", default_precision=2),
    EngineeringUnit.COUNT: UnitDefinition(unit=EngineeringUnit.COUNT, symbol="qty", description="Unit Count / Discrete Quantity", default_precision=0),
}
