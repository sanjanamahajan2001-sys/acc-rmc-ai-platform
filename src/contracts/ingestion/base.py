"""Base Ingestion DTO Model and Core Configuration.

This module provides the BaseIngestionModel enforcing immutability, Pydantic V2 configuration,
contract metadata header attributes, strict type coercions, and standardized serialization methods.
"""

from decimal import Decimal
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict

CONTRACT_NAME: str = "ACC_RMC_Ingestion_Contracts"
CONTRACT_VERSION: str = "1.0.0"
CONTRACT_CREATED_AT: str = "2026-08-07T21:32:00Z"
CONTRACT_AUTHOR: str = "ACC AI Engineering Team"
CONTRACT_COMPATIBILITY: str = "WS-01, WS-02, WS-03"


class BaseIngestionModel(BaseModel):
    """Base immutable Pydantic V2 model for all ingestion DTOs."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        json_encoders={
            Decimal: lambda v: str(v),
        },
    )

    def model_dump_canonical(self) -> Dict[str, Any]:
        """Dump model dictionary with exact Python native types (Decimals preserved)."""
        return self.model_dump(mode="python")

    def model_dump_json_canonical(self) -> str:
        """Serialize model to canonical JSON string with stringified Decimals."""
        return self.model_dump_json(by_alias=True)
