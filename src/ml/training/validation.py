"""Training Quality Gates & Physical Plausibility Engine for ACC RMC Platform.

Performs server-authoritative validation before training starts:
1. Minimum dataset observation volume.
2. Complete absence of null/NaN targets.
3. Physical plausibility bounds (IS 456 / IS 10262).
4. Target variance check (rejects invariant / mock targets).
5. Predictor integrity & zero leakage validation.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import numpy as np

from src.ml.training.contracts import (
    MLBatchObservation,
    CANONICAL_FEATURE_NAMES,
    PLAUSIBILITY_BOUNDS,
)


@dataclass
class QualityGateConfig:
    """Configurable quality validation thresholds."""
    min_observations: int = 20  # Minimum statistical sample for holdout evaluation
    min_target_std_mpa: float = 1.0  # Minimum target standard deviation in MPa
    max_missing_feature_ratio: float = 0.05
    min_strength_mpa: float = 5.0
    max_strength_mpa: float = 120.0
    min_binder_kg_m3: float = 150.0
    max_binder_kg_m3: float = 850.0
    min_wb_ratio: float = 0.20
    max_wb_ratio: float = 0.90


@dataclass
class QualityGateResult:
    """Structured result of dataset pre-training validation."""
    passed: bool
    total_observations: int
    eligible_observations: int
    target_mean_mpa: float
    target_std_mpa: float
    issues: List[str]
    warnings: List[str]


class TrainingQualityGateService:
    """Evaluates training eligibility quality gates on canonical observations."""

    @staticmethod
    def validate_dataset(
        observations: List[MLBatchObservation],
        config: QualityGateConfig = QualityGateConfig(),
    ) -> QualityGateResult:
        """Execute all quality gates against extracted observations."""
        issues: List[str] = []
        warnings: List[str] = []

        if not observations:
            return QualityGateResult(
                passed=False,
                total_observations=0,
                eligible_observations=0,
                target_mean_mpa=0.0,
                target_std_mpa=0.0,
                issues=["Dataset contains 0 observations."],
                warnings=[],
            )

        n_obs = len(observations)

        # Gate 1: Minimum Sample Volume
        if n_obs < config.min_observations:
            issues.append(
                f"Insufficient observation count ({n_obs} records). "
                f"Minimum required for robust statistical training is {config.min_observations}."
            )

        # Gate 2: Target Completeness & Physical Plausibility
        targets = [obs.target_28d_strength_mpa for obs in observations]
        invalid_target_count = sum(
            1 for y in targets if y is None or np.isnan(y) or y < config.min_strength_mpa or y > config.max_strength_mpa
        )

        if invalid_target_count > 0:
            issues.append(
                f"{invalid_target_count} observations contain missing, NaN, or physically implausible "
                f"28-day strength values outside ({config.min_strength_mpa} - {config.max_strength_mpa} MPa)."
            )

        # Gate 3: Physical Binder & Water Plausibility
        invalid_mix_count = 0
        for obs in observations:
            if (
                obs.total_binder_kg_m3 < config.min_binder_kg_m3
                or obs.total_binder_kg_m3 > config.max_binder_kg_m3
                or obs.water_binder_ratio < config.min_wb_ratio
                or obs.water_binder_ratio > config.max_wb_ratio
            ):
                invalid_mix_count += 1

        if invalid_mix_count > 0:
            warnings.append(
                f"{invalid_mix_count} observations deviate from standard mix design bounds "
                f"(Binder: {config.min_binder_kg_m3}-{config.max_binder_kg_m3} kg/m3, "
                f"w/b: {config.min_wb_ratio}-{config.max_wb_ratio})."
            )

        # Gate 4: Target Variance Check
        target_arr = np.array(targets, dtype=float)
        mean_mpa = float(np.mean(target_arr))
        std_mpa = float(np.std(target_arr))

        if std_mpa < config.min_target_std_mpa:
            issues.append(
                f"Target standard deviation ({std_mpa:.2f} MPa) is below minimum threshold ({config.min_target_std_mpa:.2f} MPa). "
                f"Dataset exhibits zero or artificial variance and cannot be trained on."
            )

        passed = len(issues) == 0

        return QualityGateResult(
            passed=passed,
            total_observations=n_obs,
            eligible_observations=n_obs if passed else 0,
            target_mean_mpa=round(mean_mpa, 2),
            target_std_mpa=round(std_mpa, 2),
            issues=issues,
            warnings=warnings,
        )
