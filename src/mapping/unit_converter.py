"""Engineering Unit & Primitive Type Normalizer.

This module provides unit conversions (preserving original vs canonical values/units)
and primitive type coercion for strings, decimals, and dates.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Tuple
from src.database.dictionary import CanonicalFieldDefinition
from src.database.types import EngineeringUnit
from src.logging import get_logger

logger = get_logger("src.mapping.unit_converter", component="mapping")


class UnitNormalizer:
    """Normalizes raw input units to canonical engineering units."""

    @staticmethod
    def convert(
        value: Any,
        from_unit_str: Optional[str],
        target_unit: Optional[EngineeringUnit],
    ) -> Tuple[Optional[Any], Optional[str], Optional[Any], Optional[str]]:
        """Convert value from input unit string to target canonical unit.

        Returns (original_value, original_unit, canonical_value, canonical_unit)
        """
        if value is None:
            return (None, from_unit_str, None, target_unit.value if target_unit else None)

        orig_val = value
        orig_unit = from_unit_str.strip() if from_unit_str else None
        target_unit_str = target_unit.value if target_unit else None

        if not orig_unit or not target_unit_str or orig_unit.upper() == target_unit_str.upper():
            return (orig_val, orig_unit, orig_val, target_unit_str)

        try:
            num_val = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return (orig_val, orig_unit, orig_val, target_unit_str)

        u_from = orig_unit.lower()
        u_to = target_unit_str.lower()

        # Volume conversions (Yd3 -> m3)
        if u_from in ["yd3", "cu_yd", "cubic_yard"] and u_to == "m3":
            canonical_val = (num_val * Decimal("0.764555")).quantize(Decimal("0.01"))
            return (orig_val, orig_unit, canonical_val, target_unit_str)

        # Mass conversions (lbs -> kg)
        if u_from in ["lbs", "lb", "pound"] and u_to == "kg":
            canonical_val = (num_val * Decimal("0.453592")).quantize(Decimal("0.01"))
            return (orig_val, orig_unit, canonical_val, target_unit_str)

        # Length conversions (in -> mm)
        if u_from in ["in", "inch", "inches"] and u_to == "mm":
            canonical_val = (num_val * Decimal("25.40")).quantize(Decimal("0.01"))
            return (orig_val, orig_unit, canonical_val, target_unit_str)

        return (orig_val, orig_unit, orig_val, target_unit_str)


class PrimitiveTypeNormalizer:
    """Coerces raw input string cell values into standard Python primitive types."""

    @staticmethod
    def normalize_value(value: Any, canonical_def: Optional[CanonicalFieldDefinition]) -> Any:
        """Coerce raw input into primitive type matching canonical field category."""
        if value is None:
            return None

        val_str = str(value).strip()
        if val_str == "":
            return None

        if canonical_def is None:
            return val_str

        cat = canonical_def.category.name if hasattr(canonical_def.category, "name") else str(canonical_def.category)

        if "NUMERIC" in cat or "DECIMAL" in cat or "FLOAT" in cat or "QUANTITY" in cat or "STRENGTH" in cat:
            try:
                return Decimal(val_str)
            except (InvalidOperation, ValueError):
                return val_str

        if "INTEGER" in cat:
            try:
                return int(float(val_str))
            except (ValueError, TypeError):
                return val_str

        if "DATETIME" in cat or "TIMESTAMP" in cat:
            try:
                dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                return val_str

        return val_str
