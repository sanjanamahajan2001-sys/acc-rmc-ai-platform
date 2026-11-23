"""Canonical Data Dictionary Registry and Alias Resolver.

This module provides the central `CanonicalFieldRegistry` containing strongly typed field
definitions, permanent field IDs (`CanonicalFieldID`), normalized string processing, and alias resolution.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from src.database.types import DataTypeCategory, EngineeringUnit, SourceSystem
from src.database.validators import ValidationRuleMetadata
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.dictionary", component="database")


class CanonicalFieldID(str, Enum):
    """Permanent Internal Canonical Field Identifiers."""

    FIELD_BATCH_ID = "FIELD_BATCH_ID"
    FIELD_DELIVERY_NOTE_ID = "FIELD_DELIVERY_NOTE_ID"
    FIELD_CUSTOMER_NAME = "FIELD_CUSTOMER_NAME"
    FIELD_JOBSITE_CODE = "FIELD_JOBSITE_CODE"
    FIELD_TRUCK_CODE = "FIELD_TRUCK_CODE"
    FIELD_PLANT_CODE = "FIELD_PLANT_CODE"
    FIELD_ACTUAL_CEMENT_KG = "FIELD_ACTUAL_CEMENT_KG"
    FIELD_ACTUAL_WATER_KG = "FIELD_ACTUAL_WATER_KG"
    FIELD_ACTUAL_GGBS_KG = "FIELD_ACTUAL_GGBS_KG"
    FIELD_ACTUAL_FLYASH_KG = "FIELD_ACTUAL_FLYASH_KG"
    FIELD_ACTUAL_ADMIXTURE_KG = "FIELD_ACTUAL_ADMIXTURE_KG"
    FIELD_ACTUAL_SAND_KG = "FIELD_ACTUAL_SAND_KG"
    FIELD_ACTUAL_AGGREGATE_10MM_KG = "FIELD_ACTUAL_AGGREGATE_10MM_KG"
    FIELD_ACTUAL_AGGREGATE_20MM_KG = "FIELD_ACTUAL_AGGREGATE_20MM_KG"
    FIELD_CUBE_STRENGTH_28D_MPA = "FIELD_CUBE_STRENGTH_28D_MPA"
    FIELD_SLUMP_MM = "FIELD_SLUMP_MM"
    FIELD_CASTING_DATE = "FIELD_CASTING_DATE"
    FIELD_MIX_GRADE = "FIELD_MIX_GRADE"
    FIELD_CLIENT_NAME = "FIELD_CLIENT_NAME"
    FIELD_LOAD_SIZE = "FIELD_LOAD_SIZE"
    FIELD_TIME_BATCHED = "FIELD_TIME_BATCHED"


def normalize_alias(alias: str) -> str:
    """Normalize alias or header string (lowercased, stripped, dashes/underscores/spaces collapsed)."""
    clean = alias.lower().strip()
    return re.sub(r"[\s\-_]+", "_", clean)


class CanonicalFieldDefinition(BaseModel):
    """Strongly typed contract for a canonical enterprise field definition."""

    field_id: CanonicalFieldID = Field(description="Permanent internal canonical field enum ID.")
    canonical_name: str = Field(description="Unique canonical snake_case field name.")
    display_name: str = Field(description="Human readable display label.")
    description: str = Field(description="Business description and usage.")
    sql_type: str = Field(description="Target SQL data type string (e.g. VARCHAR(64), NUMERIC(10,2)).")
    python_type: str = Field(description="Target Python data type string (e.g. str, float, int).")
    category: DataTypeCategory = Field(description="Data type classification category.")
    unit: Optional[EngineeringUnit] = Field(default=None, description="Associated engineering unit.")
    nullable: bool = Field(default=True, description="Nullable column flag.")
    unique: bool = Field(default=False, description="Unique constraint flag.")
    indexed: bool = Field(default=False, description="Indexed column flag.")
    default_value: Optional[Any] = Field(default=None, description="Default column value.")
    domain: str = Field(description="Subsystem domain (e.g. ERP, SCADA, QA, AI, Fleet).")
    source_system: SourceSystem = Field(description="Primary originating source system enum.")
    excel_aliases: List[str] = Field(default_factory=list, description="Excel header aliases mapping to field.")
    api_aliases: List[str] = Field(default_factory=list, description="REST API JSON key aliases mapping to field.")
    validation: ValidationRuleMetadata = Field(default_factory=ValidationRuleMetadata, description="Validation rules metadata.")


class CanonicalFieldRegistry:
    """Enterprise Canonical Field Registry and Alias Resolver."""

    def __init__(self) -> None:
        self._fields: Dict[CanonicalFieldID, CanonicalFieldDefinition] = {}
        self._name_map: Dict[str, CanonicalFieldID] = {}
        self._alias_map: Dict[str, CanonicalFieldID] = {}

    def register_field(self, field_def: CanonicalFieldDefinition) -> None:
        """Register a new canonical field definition into the registry.

        Raises:
            InvalidConfigurationException: If duplicate field name or alias conflict is detected.
        """
        fid = field_def.field_id
        if fid in self._fields:
            raise InvalidConfigurationException(
                parameter_name="field_id",
                message=f"Duplicate canonical field ID '{fid.value}' detected.",
            )

        c_name = normalize_alias(field_def.canonical_name)
        if c_name in self._name_map:
            raise InvalidConfigurationException(
                parameter_name="canonical_name",
                message=f"Duplicate canonical field name '{c_name}' detected.",
            )

        # Validate aliases uniqueness with normalization
        all_aliases = [normalize_alias(a) for a in field_def.excel_aliases + field_def.api_aliases]
        all_aliases.append(c_name)

        for alias in all_aliases:
            if alias in self._alias_map:
                existing_fid = self._alias_map[alias]
                raise InvalidConfigurationException(
                    parameter_name="alias",
                    message=f"Alias conflict: Alias '{alias}' already maps to canonical field ID '{existing_fid.value}'.",
                )

        # Store field and register alias lookup
        self._fields[fid] = field_def
        self._name_map[c_name] = fid
        for alias in all_aliases:
            self._alias_map[alias] = fid

        logger.info("Canonical field registered", field_id=fid.value, canonical_name=c_name, domain=field_def.domain)

    def get_field(self, field_id_or_name: CanonicalFieldID | str) -> CanonicalFieldDefinition:
        """Retrieve canonical field definition by field ID or canonical name."""
        if isinstance(field_id_or_name, CanonicalFieldID):
            if field_id_or_name not in self._fields:
                raise InvalidConfigurationException(
                    parameter_name="field_id",
                    message=f"Canonical field ID '{field_id_or_name.value}' is not registered in dictionary.",
                )
            return self._fields[field_id_or_name]

        norm_name = normalize_alias(field_id_or_name)
        if norm_name not in self._name_map:
            raise InvalidConfigurationException(
                parameter_name="canonical_name",
                message=f"Canonical field '{field_id_or_name}' (normalized: '{norm_name}') is not registered.",
            )
        return self._fields[self._name_map[norm_name]]

    def resolve_alias(self, alias_or_name: str) -> CanonicalFieldDefinition:
        """Resolve an Excel header, API key, or alias string (normalized) to its canonical field definition."""
        key = normalize_alias(alias_or_name)
        if key not in self._alias_map:
            raise InvalidConfigurationException(
                parameter_name="alias",
                message=f"Unrecognized field alias or header '{alias_or_name}'. No canonical mapping found.",
            )
        fid = self._alias_map[key]
        return self._fields[fid]

    def has_field(self, field_id_or_name: CanonicalFieldID | str) -> bool:
        """Check if canonical field exists."""
        if isinstance(field_id_or_name, CanonicalFieldID):
            return field_id_or_name in self._fields
        return normalize_alias(field_id_or_name) in self._name_map

    def get_all_fields(self) -> List[CanonicalFieldDefinition]:
        """Return list of all registered canonical field definitions."""
        return list(self._fields.values())


_DICTIONARY_SINGLETON: Optional[CanonicalFieldRegistry] = None


def get_canonical_dictionary() -> CanonicalFieldRegistry:
    """Return singleton instance of CanonicalFieldRegistry loaded with platform fields."""
    global _DICTIONARY_SINGLETON
    if _DICTIONARY_SINGLETON is None:
        registry = CanonicalFieldRegistry()
        _load_master_canonical_dictionary(registry)
        _DICTIONARY_SINGLETON = registry
    return _DICTIONARY_SINGLETON


def _load_master_canonical_dictionary(registry: CanonicalFieldRegistry) -> None:
    """Load enterprise canonical fields covering ERP, SCADA, QA, AI, and Reporting."""
    fields = [
        # Operational / Batching Fields
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_BATCH_ID,
            canonical_name="batch_id",
            display_name="Batch ID",
            description="Unique identifier for a concrete batching execution.",
            sql_type="VARCHAR(64)",
            python_type="str",
            category=DataTypeCategory.IDENTIFIER,
            nullable=False,
            unique=True,
            indexed=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Batch No", "Batch Number", "Batch_ID", "batch-id"],
            api_aliases=["batchId", "batch_no"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG,
            canonical_name="actual_cement_kg",
            display_name="Actual Cement Weight",
            description="Actual weight of cement batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=False,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Actual Cement", "actual cement", "ACTUAL CEMENT", "Actual_Cement", "Actual-Cement", "Cement (kg)", "OPC Quantity", "OPC", "OPC (kg)", "OPC_Quantity", "CEMENT 1", "CEMENT 2"],
            api_aliases=["actualCementKg", "cement_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=2000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_GGBS_KG,
            canonical_name="actual_ggbs_kg",
            display_name="Actual GGBS Weight",
            description="Actual weight of GGBS mineral admixture batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["GGBS Quantity", "GGBS", "GGBS (kg)", "GGBS_Quantity", "GGBS(Cement 1) Brand"],
            api_aliases=["actualGgbsKg", "ggbs_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=2000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_WATER_KG,
            canonical_name="actual_water_kg",
            display_name="Actual Water Weight",
            description="Actual total water batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=False,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Actual Water", "Water (kg)", "Act Water", "Water", "WATER", "Water Quantity", "Total Water", "Water (L)"],
            api_aliases=["actualWaterKg", "water_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=1000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_FLYASH_KG,
            canonical_name="actual_flyash_kg",
            display_name="Actual Fly Ash Weight",
            description="Actual weight of fly ash / pulverized fuel ash batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Flyash", "Fly Ash", "Fly Ash (kg)", "Flyash (kg)", "PFS", "FA (kg)", "Flyash Quantity", "Fly Ash Quantity"],
            api_aliases=["actualFlyashKg", "flyash_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=2000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_ADMIXTURE_KG,
            canonical_name="actual_admixture_kg",
            display_name="Actual Admixture Weight",
            description="Actual weight or volume of chemical admixture batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Admixture", "Admixture (kg)", "Actual Admixture", "ADMIXTURE", "Admix", "Admixture 1", "Admixture 2", "Chemical Admixture"],
            api_aliases=["actualAdmixtureKg", "admixture_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=100.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_SAND_KG,
            canonical_name="actual_sand_kg",
            display_name="Actual Sand / Fine Aggregate Weight",
            description="Actual weight of fine aggregates (sand) batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["SAND 1", "SAND 2", "SAND", "Sand", "Sand (kg)", "Fine Aggregate", "FA Sand", "Sand 1", "Sand 2", "M Sand", "M-Sand", "River Sand", "Crushed Sand"],
            api_aliases=["actualSandKg", "sand_kg", "fine_aggregate_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=5000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_AGGREGATE_10MM_KG,
            canonical_name="actual_aggregate_10mm_kg",
            display_name="Actual 10mm Aggregate Weight",
            description="Actual weight of 10mm coarse aggregates batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["10 MM", "10MM", "10 mm", "Aggregate 10mm", "10mm (kg)", "CA 10mm", "AGG 10MM", "AGG 10 MM", "10mm Aggregate", "10 MM Aggregate", "10mm"],
            api_aliases=["actualAggregate10mmKg", "aggregate_10mm_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=5000.0, precision=10, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_ACTUAL_AGGREGATE_20MM_KG,
            canonical_name="actual_aggregate_20mm_kg",
            display_name="Actual 20mm Aggregate Weight",
            description="Actual weight of 20mm coarse aggregates batched.",
            sql_type="NUMERIC(10,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.KG,
            nullable=True,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["20 MM", "20MM", "20 mm", "Aggregate 20mm", "20mm (kg)", "CA 20mm", "AGG 20MM", "AGG 20 MM", "20mm Aggregate", "20 MM Aggregate", "20mm"],
            api_aliases=["actualAggregate20mmKg", "aggregate_20mm_kg"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=5000.0, precision=10, scale=2),
        ),
        # Laboratory Quality Fields
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_CUBE_STRENGTH_28D_MPA,
            canonical_name="cube_strength_28d_mpa",
            display_name="28-Day Cube Compressive Strength",
            description="Compressive strength result of 150mm cube tested at 28 days.",
            sql_type="NUMERIC(6,2)",
            python_type="float",
            category=DataTypeCategory.STRENGTH,
            unit=EngineeringUnit.MPA,
            nullable=True,
            domain="QA",
            source_system=SourceSystem.FT7,
            excel_aliases=["28 Day Strength", "28 Day Strenght", "28D Strength (MPa)", "FT7 28D Strength"],
            api_aliases=["cubeStrength28dMpa", "strength_28d"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=120.0, precision=6, scale=2),
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_SLUMP_MM,
            canonical_name="slump_mm",
            display_name="Slump (mm)",
            description="Slump workability test outcome in mm.",
            sql_type="NUMERIC(6,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.MILLIMETER,
            nullable=True,
            domain="QA",
            source_system=SourceSystem.FT7,
            excel_aliases=["Slump", "Slump (mm)", "Slump Test", "SLUMP", "Workability Slump"],
            api_aliases=["slumpMm", "slump"],
            validation=ValidationRuleMetadata(min_value=0.0, max_value=300.0, precision=6, scale=2),
        ),
    ]
    # Additional ERP / SCADA Batching Headers
    extra_fields = [
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_PLANT_CODE,
            canonical_name="plant_code",
            display_name="Plant Code",
            description="Unique identifier or code for production batching plant.",
            sql_type="VARCHAR(64)",
            python_type="str",
            category=DataTypeCategory.IDENTIFIER,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Plant Code", "Plant", "Plant Name", "Plant ID", "Plant_Code", "Unit Code", "NS70", "NS 70", "NS-70"],
            api_aliases=["plantCode", "plant_id"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_DELIVERY_NOTE_ID,
            canonical_name="delivery_note_number",
            display_name="Delivery Note Number",
            description="Challan / Delivery note number.",
            sql_type="VARCHAR(64)",
            python_type="str",
            category=DataTypeCategory.IDENTIFIER,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Del. note nr.", "challan no.", "Challan No", "Challan Number", "Del Note No", "Challan no. (Editable)", "Challan no (Editable)", "Challan No (Editable)"],
            api_aliases=["deliveryNoteNr", "challan_no"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_CUSTOMER_NAME,
            canonical_name="customer_name",
            display_name="Customer Name",
            description="Customer name label.",
            sql_type="VARCHAR(128)",
            python_type="str",
            category=DataTypeCategory.NAME,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Customer", "Customer Name", "Customer_Name"],
            api_aliases=["customerName"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_JOBSITE_CODE,
            canonical_name="jobsite_code",
            display_name="Jobsite Code",
            description="Jobsite destination code.",
            sql_type="VARCHAR(64)",
            python_type="str",
            category=DataTypeCategory.IDENTIFIER,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Jobsite code", "Jobsite Code", "Jobsite", "Project site", "Project Site"],
            api_aliases=["jobsiteCode"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_TRUCK_CODE,
            canonical_name="truckmixer_code",
            display_name="Truckmixer Code",
            description="Truck / Transit mixer code.",
            sql_type="VARCHAR(64)",
            python_type="str",
            category=DataTypeCategory.IDENTIFIER,
            domain="ERP",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Truckmixer code", "truck Number", "Truck Code", "Truck No"],
            api_aliases=["truckCode", "truck_number"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_CASTING_DATE,
            canonical_name="date_of_casting",
            display_name="Date of Casting",
            description="Casting date for batch or concrete cube sample.",
            sql_type="DATE",
            python_type="str",
            category=DataTypeCategory.TIMESTAMP,
            domain="QA",
            source_system=SourceSystem.ERP,
            excel_aliases=["Date of casting", "Casting Date", "Date of Casting"],
            api_aliases=["castingDate", "date_of_casting"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_MIX_GRADE,
            canonical_name="mix_grade",
            display_name="Concrete Mix Grade",
            description="Concrete mix strength grade.",
            sql_type="VARCHAR(32)",
            python_type="str",
            category=DataTypeCategory.CODE,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Mix grade", "Grade of Mix", "mix grade", "Mix Code"],
            api_aliases=["mixGrade", "mix_grade"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_CLIENT_NAME,
            canonical_name="client_name",
            display_name="Client Name",
            description="Client name or project owner.",
            sql_type="VARCHAR(128)",
            python_type="str",
            category=DataTypeCategory.NAME,
            domain="ERP",
            source_system=SourceSystem.ERP,
            excel_aliases=["Client", "Client Name", "client"],
            api_aliases=["clientName", "client_name"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_LOAD_SIZE,
            canonical_name="load_size_m3",
            display_name="Load Size (m³)",
            description="Volume of concrete loaded in m3.",
            sql_type="NUMERIC(8,2)",
            python_type="float",
            category=DataTypeCategory.QUANTITY,
            unit=EngineeringUnit.CUBIC_METER,
            domain="ERP",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Load size", "load size", "Load Size"],
            api_aliases=["loadSizeM3", "load_size"],
        ),
        CanonicalFieldDefinition(
            field_id=CanonicalFieldID.FIELD_TIME_BATCHED,
            canonical_name="time_batched",
            display_name="Time Batched",
            description="Time when batching was completed.",
            sql_type="VARCHAR(32)",
            python_type="str",
            category=DataTypeCategory.TIMESTAMP,
            domain="SCADA",
            source_system=SourceSystem.SCADA,
            excel_aliases=["Time batched", "time batched", "Time Batched"],
            api_aliases=["timeBatched", "time_batched"],
        ),
    ]
    for f in fields + extra_fields:
        registry.register_field(f)
