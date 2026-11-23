"""Validation Rule Metadata.

This module provides immutable metadata descriptor contracts for validation rules.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier


class RuleMetadata(BaseModel):
    """Immutable metadata descriptor for a validation rule."""

    rule_id: str = Field(..., description="Unique rule identifier code (e.g. ACC_VAL_001).")
    rule_name: str = Field(..., description="Human-readable rule name.")
    description: str = Field(..., description="Detailed rule description and business purpose.")
    tier: ValidationTier = Field(..., description="Pipeline execution tier.")
    category: ValidationCategory = Field(..., description="Domain categorization tag.")
    severity: ValidationSeverity = Field(..., description="Failure severity level.")
    version: str = Field(default="1.0.0", description="Semantic version string (e.g. 1.0.0).")
    author: str = Field(default="System", description="Author or team owning the rule.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC creation timestamp.")
    enabled: bool = Field(default=True, description="True if rule is active for execution.")
    execution_priority: int = Field(default=100, ge=1, le=1000, description="Execution priority (lower values execute earlier).")
    tags: List[str] = Field(default_factory=list, description="Metadata taxonomy tags for group filtering.")

    model_config = ConfigDict(frozen=True, extra="forbid")
