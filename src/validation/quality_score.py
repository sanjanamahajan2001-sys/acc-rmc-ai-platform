"""Deterministic Quality Score Calculator.

This module provides deterministic Quality Score mathematical calculation using Phase 1 penalty weights.
"""

from typing import List
from src.validation.constants import (
    WEIGHT_CRITICAL_PENALTY,
    WEIGHT_ERROR_PENALTY,
    WEIGHT_INFO_PENALTY,
    WEIGHT_WARNING_PENALTY,
)
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationSeverity


class QualityScoreCalculator:
    """Purely deterministic mathematical Quality Score Calculator (0.0 to 100.0).

    Does strictly NOT use machine learning or AI algorithms.
    """

    @staticmethod
    def calculate_score(total_records: int, errors: List[FieldErrorDetail]) -> float:
        """Calculate deterministic dataset Quality Score (0.0 to 100.0)."""
        if total_records <= 0:
            return 100.0

        total_penalty = 0.0
        for err in errors:
            if err.severity == ValidationSeverity.CRITICAL:
                total_penalty += WEIGHT_CRITICAL_PENALTY
            elif err.severity == ValidationSeverity.ERROR:
                total_penalty += WEIGHT_ERROR_PENALTY
            elif err.severity == ValidationSeverity.WARNING:
                total_penalty += WEIGHT_WARNING_PENALTY
            elif err.severity == ValidationSeverity.INFO:
                total_penalty += WEIGHT_INFO_PENALTY

        # Maximum possible score is 100.0
        # Normalization over record count to prevent single error from tanking huge datasets completely
        normalized_penalty = (total_penalty / float(total_records))
        score = max(0.0, 100.0 - normalized_penalty)
        return round(score, 2)
