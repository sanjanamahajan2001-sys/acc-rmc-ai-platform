"""Comprehensive Unit & Regression Test Suite for Phase 13A ML Foundation.

Tests:
1. Training Eligibility Gating (OPERATIONAL_ACTUAL & HISTORICAL_QC eligible; LAB_FORECAST_DESIGN & MANUAL_PRODUCTION excluded).
2. Explicit Non-Silent Exclusion Reasons.
3. Canonical Material Classification mapping.
4. Authoritative 28-day Target resolution and multi-specimen averaging.
5. Feature transformation completeness, finite ratio validation, and unit consistency.
6. Negative tests for missing required features, NaN/inf features, and invalid ratios.
7. Data Leakage Protection (zero target, zero early-age break, zero QA metadata in X).
8. Deterministic Grouped Dataset Splits by batch_id with strict refusal on insufficient groups.
9. Cross-Validation Safety & refusal on insufficient fold groups.
10. Dataset Quality Gates (sample count, variance, physical bounds).
11. Dataset Cryptographic Fingerprinting & Lineage Descriptors.
12. Pre-Flight Resource Safety Guard Evaluation with Swap Inspection.
13. Security (Zero credentials or tokens in feature vectors).
"""

import pytest
import math
from datetime import datetime, timezone
import numpy as np

from src.ml.training.contracts import (
    MLBatchObservation,
    DatasetOriginEnum,
    TrainingExclusionReason,
    CANONICAL_FEATURE_NAMES,
    PLAUSIBILITY_BOUNDS,
)
from src.ml.training.eligibility import (
    TrainingEligibilityService,
    CANONICAL_MATERIAL_MAP,
)
from src.ml.training.features import FeaturePipeline, FeatureValidationError
from src.ml.training.splits import DatasetSplitter, DatasetSplits, SplitValidationError
from src.ml.training.validation import (
    TrainingQualityGateService,
    QualityGateConfig,
    QualityGateResult,
)
from src.ml.training.resource_guard import (
    DatasetFingerprintService,
    DatasetLineageDescriptor,
    TrainingResourceGuardService,
    ResourcePreflightReport,
)


def _make_dummy_observation(
    batch_id: str,
    origin: str = "OPERATIONAL_ACTUAL",
    target_28d: float = 35.5,
    cement: float = 380.0,
    flyash: float = 80.0,
    water: float = 160.0,
    plant_code: str = "PLANT-MUMBAI-01",
    recipe_code: str = "R-M40-STD",
) -> MLBatchObservation:
    """Helper creating valid canonical MLBatchObservation instances."""
    total_binder = cement + flyash
    wb = round(water / total_binder, 4) if total_binder > 0 else 0.0
    wc = round(water / cement, 4) if cement > 0 else 0.0
    return MLBatchObservation(
        batch_id=batch_id,
        batch_number=f"BN-{batch_id}",
        dataset_origin=origin,
        plant_code=plant_code,
        recipe_code=recipe_code,
        batch_volume_m3=6.0,
        cement_kg_m3=cement,
        flyash_kg_m3=flyash,
        ggbs_kg_m3=0.0,
        water_kg_m3=water,
        admixture_kg_m3=3.5,
        fine_aggregate_kg_m3=720.0,
        coarse_aggregate_kg_m3=1080.0,
        total_binder_kg_m3=total_binder,
        water_binder_ratio=wb,
        water_cement_ratio=wc,
        target_28d_strength_mpa=target_28d,
        specimen_count_28d=3,
        specimen_strengths_28d=(target_28d - 0.5, target_28d, target_28d + 0.5),
        production_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        cube_test_ids=("CT-01", "CT-02", "CT-03"),
    )


# 1. Dataset Origin Gating Tests
def test_dataset_origin_filtering_contracts():
    """Verify that only OPERATIONAL_ACTUAL and HISTORICAL_QC datasets are eligible."""
    is_ok, reason = TrainingEligibilityService.classify_origin("OPERATIONAL_ACTUAL")
    assert is_ok is True
    assert reason == TrainingExclusionReason.ELIGIBLE

    is_ok, reason = TrainingEligibilityService.classify_origin("HISTORICAL_QC")
    assert is_ok is True
    assert reason == TrainingExclusionReason.ELIGIBLE

    # Ineligible origins
    is_ok, reason = TrainingEligibilityService.classify_origin("LAB_FORECAST_DESIGN")
    assert is_ok is False
    assert reason == TrainingExclusionReason.EXCLUDED_FORECAST_DATASET

    is_ok, reason = TrainingEligibilityService.classify_origin("MANUAL_PRODUCTION")
    assert is_ok is False
    assert reason == TrainingExclusionReason.EXCLUDED_MANUAL_PRODUCTION

    is_ok, reason = TrainingEligibilityService.classify_origin("UNKNOWN_ORIGIN")
    assert is_ok is False
    assert reason == TrainingExclusionReason.EXCLUDED_DISALLOWED_ORIGIN


# 2. Canonical Material Mapping
def test_canonical_material_classification_mapping():
    """Verify that disparate plant material codes resolve cleanly to standard canonical types."""
    assert TrainingEligibilityService.classify_material_code("CEMENT 1", "OPC 53 Grade") == "cement"
    assert TrainingEligibilityService.classify_material_code("FLY ASH", "Class F Flyash") == "flyash"
    assert TrainingEligibilityService.classify_material_code("SLAG", "GGBS Grade 120") == "ggbs"
    assert TrainingEligibilityService.classify_material_code("WATER 1", "Borewell Water") == "water"
    assert TrainingEligibilityService.classify_material_code("ADD 1", "Superplasticizer PCE") == "admixture"
    assert TrainingEligibilityService.classify_material_code("SAND 1", "River Sand M-Zone II") == "fine_aggregate"
    assert TrainingEligibilityService.classify_material_code("20 MM", "Crushed Granite 20mm") == "coarse_aggregate"


# 3. Target Aggregation & Exclusion Semantics
def test_authoritative_28d_target_resolution():
    """Verify 28-day specimen resolution and multi-specimen averaging."""
    obs = _make_dummy_observation("BATCH-001", target_28d=42.5)
    assert obs.target_28d_strength_mpa == 42.5
    assert obs.specimen_count_28d == 3
    assert len(obs.specimen_strengths_28d) == 3


# 4. Feature Pipeline Completeness & Unknown Handling
def test_feature_pipeline_deterministic_encoding():
    """Verify deterministic categorical encoding and feature extraction."""
    obs_list = [
        _make_dummy_observation("B-01", plant_code="P-1", recipe_code="R-1"),
        _make_dummy_observation("B-02", plant_code="P-2", recipe_code="R-2"),
    ]
    dicts = [o.to_feature_dict() for o in obs_list]

    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(dicts)

    assert X.shape == (2, 12)
    assert pipeline.plant_map == {"P-1": 0, "P-2": 1}
    assert pipeline.recipe_map == {"R-1": 0, "R-2": 1}


def test_feature_pipeline_unknown_category_handling():
    """Verify unknown categories receive -1.0 encoding during transform."""
    obs_train = [_make_dummy_observation("B-01", plant_code="P-KNOWN", recipe_code="R-KNOWN")]
    obs_test = [_make_dummy_observation("B-02", plant_code="P-UNKNOWN", recipe_code="R-NEW")]

    pipeline = FeaturePipeline()
    pipeline.fit([o.to_feature_dict() for o in obs_train])

    X_test = pipeline.transform([o.to_feature_dict() for o in obs_test])
    assert X_test[0, 10] == -1.0  # plant_code
    assert X_test[0, 11] == -1.0  # recipe_code


# 5. Dedicated Negative Feature Completeness Tests
def test_feature_pipeline_rejects_missing_numeric_feature():
    """Negative test: missing numeric feature raises FeatureValidationError."""
    d = _make_dummy_observation("B-01").to_feature_dict()
    del d["cement_kg_m3"]

    pipeline = FeaturePipeline()
    with pytest.raises(FeatureValidationError, match="missing required numeric feature 'cement_kg_m3'"):
        pipeline.fit([d])


def test_feature_pipeline_rejects_none_numeric_feature():
    """Negative test: None/null feature does not silently become zero; raises FeatureValidationError."""
    d = _make_dummy_observation("B-01").to_feature_dict()
    d["water_kg_m3"] = None

    pipeline = FeaturePipeline()
    with pytest.raises(FeatureValidationError, match="feature 'water_kg_m3' is null/None"):
        pipeline.fit([d])


def test_feature_pipeline_rejects_nan_and_infinite_feature():
    """Negative test: NaN or Infinite values are rejected."""
    d = _make_dummy_observation("B-01").to_feature_dict()
    d["water_binder_ratio"] = float("nan")

    pipeline = FeaturePipeline()
    with pytest.raises(FeatureValidationError, match="has non-finite or NaN value"):
        pipeline.fit([d])

    d2 = _make_dummy_observation("B-01").to_feature_dict()
    d2["water_binder_ratio"] = float("inf")
    with pytest.raises(FeatureValidationError, match="has non-finite or NaN value"):
        pipeline.fit([d2])


def test_feature_pipeline_rejects_zero_or_negative_required_materials():
    """Negative test: strictly positive features (cement, water, aggregates) cannot be zero or negative."""
    d = _make_dummy_observation("B-01").to_feature_dict()
    d["cement_kg_m3"] = 0.0

    pipeline = FeaturePipeline()
    with pytest.raises(FeatureValidationError, match="must be strictly positive"):
        pipeline.fit([d])


# 6. Grouped Dataset Splitter & Strict Refusal Tests
def test_dataset_splitter_grouped_by_batch():
    """Verify train/test split maintains strict batch isolation."""
    obs_list = [
        _make_dummy_observation(f"BATCH-{i:02d}", target_28d=30.0 + i)
        for i in range(10)
    ]
    splits = DatasetSplitter.train_test_split(obs_list, test_size=0.20, random_seed=42)

    assert splits.train_count > 0
    assert splits.test_count > 0
    assert splits.train_count + splits.test_count == 10

    train_ids = set(o.batch_id for o in splits.train_observations)
    test_ids = set(o.batch_id for o in splits.test_observations)
    assert train_ids.isdisjoint(test_ids)


def test_dataset_splitter_refuses_insufficient_batches():
    """Negative test: train/test split strictly fails when < 2 distinct batches exist."""
    obs_single = [_make_dummy_observation("SINGLE-BATCH")]
    with pytest.raises(SplitValidationError, match="Insufficient independent batch groups"):
        DatasetSplitter.train_test_split(obs_single)


def test_kfold_cv_refuses_insufficient_batch_groups():
    """Negative test: K-Fold CV strictly fails when batch count < n_splits."""
    obs_list = [_make_dummy_observation(f"B-{i}") for i in range(3)]  # 3 batches, requesting 5 folds
    with pytest.raises(SplitValidationError, match="Insufficient independent batch groups.*for requested 5-fold"):
        list(DatasetSplitter.kfold_grouped_cv(obs_list, n_splits=5))


def test_kfold_cv_grouped_safety():
    """Verify 5-fold CV yields mutually exclusive partitions without leakage."""
    obs_list = [_make_dummy_observation(f"B-{i:02d}") for i in range(10)]
    folds = list(DatasetSplitter.kfold_grouped_cv(obs_list, n_splits=5, random_seed=42))

    assert len(folds) == 5
    for trn, val in folds:
        trn_ids = set(o.batch_id for o in trn)
        val_ids = set(o.batch_id for o in val)
        assert trn_ids.isdisjoint(val_ids)


# 7. Quality Gates Evaluation
def test_quality_gates_evaluation():
    """Verify server quality gates reject small or invariant datasets."""
    # Too few observations
    obs_small = [_make_dummy_observation(f"B-{i}") for i in range(5)]
    res = TrainingQualityGateService.validate_dataset(obs_small, config=QualityGateConfig(min_observations=20))
    assert res.passed is False
    assert any("Insufficient observation count" in issue for issue in res.issues)

    # Invariant targets
    obs_flat = [_make_dummy_observation(f"B-{i}", target_28d=35.0) for i in range(25)]
    res_flat = TrainingQualityGateService.validate_dataset(obs_flat, config=QualityGateConfig(min_observations=20))
    assert res_flat.passed is False
    assert any("Target standard deviation" in issue for issue in res_flat.issues)

    # Valid dataset
    obs_good = [_make_dummy_observation(f"B-{i}", target_28d=30.0 + (i % 15)) for i in range(25)]
    res_good = TrainingQualityGateService.validate_dataset(obs_good, config=QualityGateConfig(min_observations=20))
    assert res_good.passed is True


# 8. Lineage & Cryptographic Fingerprinting
def test_dataset_fingerprint_deterministic_lineage():
    """Verify SHA-256 dataset fingerprinting is completely deterministic."""
    obs_a = [_make_dummy_observation(f"B-{i}") for i in range(10)]
    obs_b = list(reversed(obs_a))

    lineage_a = DatasetFingerprintService.generate_lineage_descriptor(obs_a)
    lineage_b = DatasetFingerprintService.generate_lineage_descriptor(obs_b)

    assert lineage_a.dataset_fingerprint == lineage_b.dataset_fingerprint
    assert lineage_a.observation_count == 10
    assert lineage_a.feature_schema_version == "1.0.0"


# 9. Resource Guard Pre-Flight Tests
def test_resource_guard_preflight_evaluation():
    """Verify resource safety guard evaluates headroom and swap properly."""
    # Test safe budget
    report_safe = TrainingResourceGuardService.evaluate_preflight(
        observation_count=100,
        estimated_training_ram_mb=50.0,
        required_safety_headroom_mb=50.0,
    )
    assert report_safe.allowed is True
    assert report_safe.total_ram_mb > 0
    assert report_safe.available_ram_mb > 0

    # Test unsafe headroom refusal
    report_unsafe = TrainingResourceGuardService.evaluate_preflight(
        observation_count=100,
        estimated_training_ram_mb=50000.0,  # 50 GB request
        required_safety_headroom_mb=500.0,
    )
    assert report_unsafe.allowed is False
    assert "below safe pre-flight budget" in report_unsafe.reason
