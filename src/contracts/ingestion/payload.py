"""Ingestion Payload DTO Contracts."""

from typing import List, Optional
from pydantic import Field
from src.contracts.ingestion.base import BaseIngestionModel
from src.contracts.ingestion.batch import BatchIngestionDTO, ProductionEventIngestionDTO
from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO, WeighingLogIngestionDTO
from src.contracts.ingestion.quality import CubeTestIngestionDTO, FT7CertificateIngestionDTO, SlumpTestIngestionDTO


class SingleIngestionPayloadDTO(BaseIngestionModel):
    """Complete Single Batch Ingestion Payload DTO Contract shared by Excel and Manual channels."""

    batch: BatchIngestionDTO = Field(..., description="Core production batch header record.")
    material_consumptions: List[MaterialConsumptionIngestionDTO] = Field(default_factory=list, description="Associated raw material consumptions.")
    weighing_logs: List[WeighingLogIngestionDTO] = Field(default_factory=list, description="Associated SCADA weighing scale logs.")
    slump_tests: List[SlumpTestIngestionDTO] = Field(default_factory=list, description="Associated slump quality tests.")
    cube_tests: List[CubeTestIngestionDTO] = Field(default_factory=list, description="Associated 7d/28d compressive strength cube tests.")
    ft7_certificate: Optional[FT7CertificateIngestionDTO] = Field(None, description="Associated FT7 quality certificate.")
    production_events: List[ProductionEventIngestionDTO] = Field(default_factory=list, description="Timeline event sequence.")


class IngestionBatchPayloadDTO(BaseIngestionModel):
    """Bulk Ingestion Package DTO Contract."""

    import_profile_id: Optional[str] = Field(None, max_length=64, description="Configured import column mapping profile ID.")
    source_channel: str = Field(default="MANUAL_ENTRY", description="Ingestion source channel (EXCEL_IMPORT / MANUAL_ENTRY).")
    payloads: List[SingleIngestionPayloadDTO] = Field(..., min_length=1, description="List of single batch ingestion payloads.")
