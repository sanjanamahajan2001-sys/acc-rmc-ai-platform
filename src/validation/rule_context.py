"""Validation Rule Execution Context.

This module provides the shared context container passed to rules during execution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.contracts import ValidationContext


class RuleExecutionContext(BaseModel):
    """Shared execution container carrying row, dataset, and runtime context."""

    row: Optional[Any] = Field(None, description="Target CanonicalRow or raw object being validated.")
    dataset: Optional[Any] = Field(None, description="Enclosing CanonicalDataset or raw collection.")
    context: ValidationContext = Field(..., description="Ingestion runtime context.")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Rule override configuration settings.")
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")
