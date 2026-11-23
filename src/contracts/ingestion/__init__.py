"""Ingestion Contracts Package Init File."""

from src.contracts.ingestion.base import (
    CONTRACT_AUTHOR,
    CONTRACT_COMPATIBILITY,
    CONTRACT_CREATED_AT,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    BaseIngestionModel,
)
from src.contracts.ingestion.batch import BatchIngestionDTO, ProductionEventIngestionDTO
from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO, WeighingLogIngestionDTO
from src.contracts.ingestion.payload import IngestionBatchPayloadDTO, SingleIngestionPayloadDTO
from src.contracts.ingestion.quality import (
    CubeTestIngestionDTO,
    FT7CertificateIngestionDTO,
    SlumpTestIngestionDTO,
)
from src.contracts.ingestion.response import IngestionResultResponseDTO, ValidationDiagnosticDTO

__all__ = [
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CONTRACT_CREATED_AT",
    "CONTRACT_AUTHOR",
    "CONTRACT_COMPATIBILITY",
    "BaseIngestionModel",
    "BatchIngestionDTO",
    "ProductionEventIngestionDTO",
    "MaterialConsumptionIngestionDTO",
    "WeighingLogIngestionDTO",
    "SlumpTestIngestionDTO",
    "CubeTestIngestionDTO",
    "FT7CertificateIngestionDTO",
    "SingleIngestionPayloadDTO",
    "IngestionBatchPayloadDTO",
    "ValidationDiagnosticDTO",
    "IngestionResultResponseDTO",
]
