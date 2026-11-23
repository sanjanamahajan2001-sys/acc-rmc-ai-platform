"""Field Validation Metadata Contracts.

This module provides reusable validation metadata contracts for canonical field definitions.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ValidationRuleMetadata(BaseModel):
    """Reusable validation metadata contract for canonical fields."""

    required: bool = Field(default=False, description="Field mandatory flag.")
    min_value: Optional[float] = Field(default=None, description="Minimum allowed numeric value.")
    max_value: Optional[float] = Field(default=None, description="Maximum allowed numeric value.")
    min_length: Optional[int] = Field(default=None, description="Minimum string length.")
    max_length: Optional[int] = Field(default=None, description="Maximum string length.")
    regex_pattern: Optional[str] = Field(default=None, description="Regex pattern string.")
    allowed_values: Optional[List[Any]] = Field(default=None, description="List of allowed discrete values.")
    precision: Optional[int] = Field(default=None, description="Numeric storage precision.")
    scale: Optional[int] = Field(default=None, description="Numeric storage scale.")
