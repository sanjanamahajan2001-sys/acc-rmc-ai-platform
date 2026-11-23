"""ML Training Foundation Package Exports for ACC RMC AI Platform."""

from src.ml.training.contracts import (
    CANONICAL_FEATURE_NAMES,
    PLAUSIBILITY_BOUNDS,
    DatasetOriginEnum,
    MLBatchObservation,
    TrainingExclusionReason,
)
from src.ml.training.eligibility import (
    CANONICAL_MATERIAL_MAP,
    ObservationExtractionReport,
    TrainingEligibilityService,
)
from src.ml.training.features import FeaturePipeline
from src.ml.training.resource_guard import (
    DatasetFingerprintService,
    DatasetLineageDescriptor,
    ResourcePreflightReport,
    TrainingResourceGuardService,
)
from src.ml.training.splits import DatasetSplitter, DatasetSplits
from src.ml.training.validation import (
    QualityGateConfig,
    QualityGateResult,
    TrainingQualityGateService,
)

__all__ = [
    "MLBatchObservation",
    "DatasetOriginEnum",
    "TrainingExclusionReason",
    "CANONICAL_FEATURE_NAMES",
    "PLAUSIBILITY_BOUNDS",
    "CANONICAL_MATERIAL_MAP",
    "ObservationExtractionReport",
    "TrainingEligibilityService",
    "FeaturePipeline",
    "DatasetSplitter",
    "DatasetSplits",
    "QualityGateConfig",
    "QualityGateResult",
    "TrainingQualityGateService",
    "DatasetFingerprintService",
    "DatasetLineageDescriptor",
    "TrainingResourceGuardService",
    "ResourcePreflightReport",
]
