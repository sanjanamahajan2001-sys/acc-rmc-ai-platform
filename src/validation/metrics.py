"""Validation Metrics Collector.

This module provides in-memory telemetry collection tracking validator calls, tier latencies, and error counters.
"""

from threading import Lock
from typing import Dict


class ValidationMetricsCollector:
    """Thread-safe in-memory metrics collector tracking validation operational statistics."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.tier_execution_counts: Dict[str, int] = {}
        self.validator_execution_counts: Dict[str, int] = {}
        self.severity_error_counts: Dict[str, int] = {}
        self.total_datasets_processed: int = 0
        self.total_rows_processed: int = 0

    def record_tier_execution(self, tier_name: str, count: int = 1) -> None:
        with self._lock:
            self.tier_execution_counts[tier_name] = self.tier_execution_counts.get(tier_name, 0) + count

    def record_validator_execution(self, rule_id: str, count: int = 1) -> None:
        with self._lock:
            self.validator_execution_counts[rule_id] = self.validator_execution_counts.get(rule_id, 0) + count

    def record_error(self, severity: str, count: int = 1) -> None:
        with self._lock:
            self.severity_error_counts[severity] = self.severity_error_counts.get(severity, 0) + count

    def record_dataset_run(self, total_rows: int) -> None:
        with self._lock:
            self.total_datasets_processed += 1
            self.total_rows_processed += total_rows

    def reset(self) -> None:
        with self._lock:
            self.tier_execution_counts.clear()
            self.validator_execution_counts.clear()
            self.severity_error_counts.clear()
            self.total_datasets_processed = 0
            self.total_rows_processed = 0
