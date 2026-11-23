"""Validation Statistics Service.

This module provides statistical aggregation services over accumulated ValidationExecutionReport metrics.
"""

from typing import Dict, List
import numpy as np
from src.validation.execution_report import ValidationExecutionReport


class ValidationStatisticsService:
    """Computes statistical aggregations (mean, median, P95, P99) over execution reports."""

    @staticmethod
    def calculate_aggregate_statistics(reports: List[ValidationExecutionReport]) -> Dict[str, float]:
        """Calculate mean, median, P95, P99, and average throughput from execution reports."""
        if not reports:
            return {
                "count": 0.0,
                "mean_execution_time_ms": 0.0,
                "median_execution_time_ms": 0.0,
                "p95_execution_time_ms": 0.0,
                "p99_execution_time_ms": 0.0,
                "avg_rows_per_second": 0.0,
                "avg_quality_score": 0.0,
            }

        durations = [r.total_execution_duration_ms for r in reports]
        throughputs = [r.rows_per_second for r in reports]
        scores = [r.quality_score for r in reports]

        return {
            "count": float(len(reports)),
            "mean_execution_time_ms": float(np.mean(durations)),
            "median_execution_time_ms": float(np.median(durations)),
            "p95_execution_time_ms": float(np.percentile(durations, 95)),
            "p99_execution_time_ms": float(np.percentile(durations, 99)),
            "avg_rows_per_second": float(np.mean(throughputs)),
            "avg_quality_score": float(np.mean(scores)),
        }
