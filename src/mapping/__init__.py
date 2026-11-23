"""Mapping Subsystem Package Exports."""

from src.mapping.audit import log_mapping_telemetry
from src.mapping.contracts import CanonicalDataset, CanonicalRow, MappingAuditRecord
from src.mapping.engine import CanonicalColumnMappingEngine, HeaderResolution, HeaderResolver
from src.mapping.models import ImportColumnMapping, ImportProfile
from src.mapping.repository import ImportProfileRepository
from src.mapping.service import ImportProfileService
from src.mapping.unit_converter import PrimitiveTypeNormalizer, UnitNormalizer

__all__ = [
    "CanonicalRow",
    "CanonicalDataset",
    "MappingAuditRecord",
    "ImportProfile",
    "ImportColumnMapping",
    "ImportProfileRepository",
    "ImportProfileService",
    "HeaderResolution",
    "HeaderResolver",
    "CanonicalColumnMappingEngine",
    "UnitNormalizer",
    "PrimitiveTypeNormalizer",
    "log_mapping_telemetry",
]
