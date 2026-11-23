"""Mapping Audit Telemetry & Logging.

This module provides structured telemetry logging for mapping execution and resolution audit trails.
"""

from typing import List
from src.logging import get_logger
from src.mapping.contracts import MappingAuditRecord

logger = get_logger("src.mapping.audit", component="mapping")


def log_mapping_telemetry(profile_id: str, profile_version: str, audit_records: List[MappingAuditRecord]) -> None:
    """Log structured telemetry stream for column mapping execution audit."""
    mapped_count = len([r for r in audit_records if r.resolution_strategy != "UNMAPPED"])
    unmapped_count = len([r for r in audit_records if r.resolution_strategy == "UNMAPPED"])
    fuzzy_count = len([r for r in audit_records if r.resolution_strategy == "FUZZY"])

    logger.info(
        "Column mapping execution completed",
        profile_id=profile_id,
        profile_version=profile_version,
        mapped_count=mapped_count,
        unmapped_count=unmapped_count,
        fuzzy_count=fuzzy_count,
    )
