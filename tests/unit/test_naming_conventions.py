"""Unit tests for WS-01.2A Python Style Guide & Domain Naming Conventions."""

from src.shared.naming import (
    is_kebab_case,
    is_pascal_case,
    is_snake_case,
    is_upper_snake_case,
    is_valid_db_table_name,
)


def test_snake_case_validation() -> None:
    assert is_snake_case("batch_twin_service") is True
    assert is_snake_case("actual_cement_kg") is True
    assert is_snake_case("BatchTwinService") is False
    assert is_snake_case("batch-twin-service") is False


def test_pascal_case_validation() -> None:
    assert is_pascal_case("BatchCycleAggregate") is True
    assert is_pascal_case("InvalidBatchStateException") is True
    assert is_pascal_case("batch_cycle_aggregate") is False


def test_upper_snake_case_validation() -> None:
    assert is_upper_snake_case("MAX_WATER_BINDER_RATIO") is True
    assert is_upper_snake_case("STANDARD_CUBE_AREA_MM2") is True
    assert is_upper_snake_case("max_water_binder_ratio") is False


def test_kebab_case_validation() -> None:
    assert is_kebab_case("delivery-challans") is True
    assert is_kebab_case("slump-compliance") is True
    assert is_kebab_case("delivery_challans") is False


def test_db_table_name_validation() -> None:
    assert is_valid_db_table_name("tbl_delivery_challans") is True
    assert is_valid_db_table_name("tbl_cube_specimens") is True
    assert is_valid_db_table_name("delivery_challans") is False
