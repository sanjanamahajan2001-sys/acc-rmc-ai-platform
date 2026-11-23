"""Canonical ML Training Observation, Eligibility Reasons & Contract Definitions.

Certified Rules:
- MLBatchObservation: Strongly-typed canonical unit of observation (1 Production Batch = 1 Observation).
- TrainingEligibilityReason: Explicit structured exclusion and eligibility classifications.
- CANONICAL_FEATURE_NAMES: Immutable 12-feature predictor ordering.
- PLAUSIBILITY_BOUNDS: IS 456 / IS 10262 domain physical constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DatasetOriginEnum(str, Enum):
    """Allowed and disallowed dataset origin classifications."""
    OPERATIONAL_ACTUAL = "OPERATIONAL_ACTUAL"
    HISTORICAL_QC = "HISTORICAL_QC"
    LAB_FORECAST_DESIGN = "LAB_FORECAST_DESIGN"
    MANUAL_PRODUCTION = "MANUAL_PRODUCTION"


class TrainingExclusionReason(str, Enum):
    """Explicit, non-silent exclusion reasons for batch observations."""
    ELIGIBLE = "ELIGIBLE"
    EXCLUDED_FORECAST_DATASET = "EXCLUDED_FORECAST_DATASET"
    EXCLUDED_MANUAL_PRODUCTION = "EXCLUDED_MANUAL_PRODUCTION"
    EXCLUDED_DISALLOWED_ORIGIN = "EXCLUDED_DISALLOWED_ORIGIN"
    EXCLUDED_MISSING_28D_TARGET = "EXCLUDED_MISSING_28D_TARGET"
    EXCLUDED_INVALID_VOLUME = "EXCLUDED_INVALID_VOLUME"
    EXCLUDED_ZERO_OR_NEGATIVE_BINDER = "EXCLUDED_ZERO_OR_NEGATIVE_BINDER"
    EXCLUDED_ZERO_WATER = "EXCLUDED_ZERO_WATER"
    EXCLUDED_ZERO_AGGREGATE = "EXCLUDED_ZERO_AGGREGATE"
    EXCLUDED_IMPLAUSIBLE_TARGET_RANGE = "EXCLUDED_IMPLAUSIBLE_TARGET_RANGE"
    EXCLUDED_UNLINKED_QA = "EXCLUDED_UNLINKED_QA"


# Certified canonical feature column names in deterministic order
CANONICAL_FEATURE_NAMES: List[str] = [
    "cement_kg_m3",
    "flyash_kg_m3",
    "ggbs_kg_m3",
    "water_kg_m3",
    "admixture_kg_m3",
    "fine_aggregate_kg_m3",
    "coarse_aggregate_kg_m3",
    "total_binder_kg_m3",
    "water_binder_ratio",
    "water_cement_ratio",
    "plant_code",
    "recipe_code",
]

# Physical plausibility domain bounds for cementitious concrete (IS 456 / IS 10262)
PLAUSIBILITY_BOUNDS = {
    "cement_kg_m3": (100.0, 700.0),
    "flyash_kg_m3": (0.0, 350.0),
    "ggbs_kg_m3": (0.0, 450.0),
    "water_kg_m3": (50.0, 300.0),
    "admixture_kg_m3": (0.0, 25.0),
    "fine_aggregate_kg_m3": (300.0, 1400.0),
    "coarse_aggregate_kg_m3": (400.0, 1600.0),
    "total_binder_kg_m3": (150.0, 850.0),
    "water_binder_ratio": (0.20, 0.90),
    "target_strength_mpa": (5.0, 120.0),
}


@dataclass(frozen=True)
class MLBatchObservation:
    """Canonical single-batch observation unit for supervised strength modeling."""
    batch_id: str
    batch_number: str
    dataset_origin: str
    plant_code: str
    recipe_code: str
    batch_volume_m3: float
    
    # Material features (kg/m3 normalized)
    cement_kg_m3: float
    flyash_kg_m3: float
    ggbs_kg_m3: float
    water_kg_m3: float
    admixture_kg_m3: float
    fine_aggregate_kg_m3: float
    coarse_aggregate_kg_m3: float
    
    # Derived physical ratios
    total_binder_kg_m3: float
    water_binder_ratio: float
    water_cement_ratio: float
    
    # Authoritative 28-day Target
    target_28d_strength_mpa: float
    specimen_count_28d: int
    specimen_strengths_28d: Tuple[float, ...]
    
    # Lineage & Audit Metadata
    production_timestamp: Optional[datetime] = None
    cube_test_ids: Tuple[str, ...] = field(default_factory=tuple)

    def to_feature_dict(self) -> Dict[str, Any]:
        """Produce dictionary containing only predictors (zero target leakage)."""
        return {
            "cement_kg_m3": self.cement_kg_m3,
            "flyash_kg_m3": self.flyash_kg_m3,
            "ggbs_kg_m3": self.ggbs_kg_m3,
            "water_kg_m3": self.water_kg_m3,
            "admixture_kg_m3": self.admixture_kg_m3,
            "fine_aggregate_kg_m3": self.fine_aggregate_kg_m3,
            "coarse_aggregate_kg_m3": self.coarse_aggregate_kg_m3,
            "total_binder_kg_m3": self.total_binder_kg_m3,
            "water_binder_ratio": self.water_binder_ratio,
            "water_cement_ratio": self.water_cement_ratio,
            "plant_code": self.plant_code,
            "recipe_code": self.recipe_code,
        }


class TrainingJobStatus(str, Enum):
    """Authoritative lifecycle states for ML Training Jobs (Phase 13B)."""
    QUEUED = "QUEUED"
    PRECHECKING = "PRECHECKING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    RESOURCE_REJECTED = "RESOURCE_REJECTED"
