"""Engineering Units Registry and Converter Utilities.

This module provides unit metadata retrieval and verification helpers.
"""

from typing import Dict, Optional
from src.database.types import UNIT_REGISTRY, EngineeringUnit, UnitDefinition
from src.exceptions.technical import InvalidConfigurationException


def get_unit_definition(unit: EngineeringUnit) -> UnitDefinition:
    """Return UnitDefinition for specified engineering unit."""
    if unit not in UNIT_REGISTRY:
        raise InvalidConfigurationException(
            parameter_name="unit",
            message=f"Engineering unit '{unit}' is not registered in unit registry.",
        )
    return UNIT_REGISTRY[unit]
