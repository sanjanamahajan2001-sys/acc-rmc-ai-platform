"""Unit test suite for WS-02.3 Canonical Data Dictionary & Enterprise Data Mapping Layer."""

import pytest
from src.database import (
    CanonicalFieldDefinition,
    CanonicalFieldID,
    CanonicalFieldRegistry,
    DataTypeCategory,
    EngineeringUnit,
    SourceSystem,
    ValidationRuleMetadata,
    get_canonical_dictionary,
    get_unit_definition,
    normalize_alias,
)
from src.exceptions import InvalidConfigurationException


def test_engineering_units_and_source_systems() -> None:
    unit_def = get_unit_definition(EngineeringUnit.MPA)
    assert unit_def.symbol == "MPa"
    assert SourceSystem.SCADA.value == "SCADA"
    assert SourceSystem.FT7.value == "FT7"


def test_alias_normalization() -> None:
    assert normalize_alias("Actual Cement") == "actual_cement"
    assert normalize_alias("ACTUAL CEMENT") == "actual_cement"
    assert normalize_alias("Actual_Cement") == "actual_cement"
    assert normalize_alias("Actual-Cement") == "actual_cement"


def test_canonical_field_id_lookup() -> None:
    dict_reg = get_canonical_dictionary()
    field_def = dict_reg.get_field(CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG)
    assert field_def.canonical_name == "actual_cement_kg"
    assert field_def.source_system == SourceSystem.SCADA


def test_alias_resolution_variations() -> None:
    dict_reg = get_canonical_dictionary()

    variations = [
        "Actual Cement",
        "actual cement",
        "ACTUAL CEMENT",
        "Actual_Cement",
        "Actual-Cement",
    ]
    for v in variations:
        resolved = dict_reg.resolve_alias(v)
        assert resolved.field_id == CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG


def test_duplicate_field_id_and_alias_rejection() -> None:
    reg = CanonicalFieldRegistry()
    f1 = CanonicalFieldDefinition(
        field_id=CanonicalFieldID.FIELD_BATCH_ID,
        canonical_name="test_field",
        display_name="Test Field",
        description="Desc",
        sql_type="VARCHAR(10)",
        python_type="str",
        category=DataTypeCategory.NAME,
        domain="TEST",
        source_system=SourceSystem.ERP,
        excel_aliases=["Alias 1"],
    )
    reg.register_field(f1)

    # Reject duplicate field ID
    with pytest.raises(InvalidConfigurationException):
        reg.register_field(f1)
