"""Canonical Feature Pipeline & Preprocessing Engine for ACC RMC ML Platform.

Enforces:
1. Exact transformation symmetry between Training and Inference.
2. Complete non-silent validation of all 12 canonical predictors.
3. Missing values (None, NaN, Inf, non-finite) are strictly rejected with detailed diagnostics.
4. Legitimately 0.0 supplementary binders (flyash, ggbs, admixture) are preserved.
5. Deterministic categorical encoding without test set data leakage.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from src.ml.training.contracts import CANONICAL_FEATURE_NAMES, MLBatchObservation


class FeatureValidationError(ValueError):
    """Raised when observation feature vectors violate completeness, finitude, or required contracts."""
    pass


class FeaturePipeline:
    """Standardized preprocessor mapping raw batch feature dictionaries into numeric arrays."""

    def __init__(self):
        self.numeric_features = [
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
        ]
        self.non_zero_features = [
            "cement_kg_m3",
            "water_kg_m3",
            "fine_aggregate_kg_m3",
            "coarse_aggregate_kg_m3",
            "total_binder_kg_m3",
            "water_binder_ratio",
            "water_cement_ratio",
        ]
        self.plant_map: Dict[str, int] = {}
        self.recipe_map: Dict[str, int] = {}
        self.fitted = False

    def validate_feature_dict(self, d: Dict[str, Any], obs_index: int = 0) -> None:
        """Rigorously validate that all required features exist, are non-null, finite, and within valid domain bounds."""
        if not isinstance(d, dict):
            raise FeatureValidationError(f"Observation #{obs_index}: feature input must be a dictionary, got {type(d).__name__}")

        # 1. Validate plant_code and recipe_code
        for cat_col in ("plant_code", "recipe_code"):
            if cat_col not in d or d[cat_col] is None or str(d[cat_col]).strip() == "":
                raise FeatureValidationError(
                    f"Observation #{obs_index}: missing or empty required categorical feature '{cat_col}'."
                )

        # 2. Validate numeric features
        for feat in self.numeric_features:
            if feat not in d:
                raise FeatureValidationError(
                    f"Observation #{obs_index}: missing required numeric feature '{feat}'."
                )
            val = d[feat]
            if val is None:
                raise FeatureValidationError(
                    f"Observation #{obs_index}: feature '{feat}' is null/None. Missing values must not silently become zero."
                )
            try:
                val_float = float(val)
            except (ValueError, TypeError):
                raise FeatureValidationError(
                    f"Observation #{obs_index}: feature '{feat}' has invalid non-numeric value '{val}'."
                )

            if not math.isfinite(val_float) or math.isnan(val_float):
                raise FeatureValidationError(
                    f"Observation #{obs_index}: feature '{feat}' has non-finite or NaN value '{val_float}'."
                )

            if feat in self.non_zero_features and val_float <= 0.0:
                raise FeatureValidationError(
                    f"Observation #{obs_index}: feature '{feat}' must be strictly positive (> 0.0), got {val_float}."
                )
            elif val_float < 0.0:
                raise FeatureValidationError(
                    f"Observation #{obs_index}: supplementary material feature '{feat}' cannot be negative, got {val_float}."
                )

    def fit(self, X_dicts: List[Dict[str, Any]]) -> "FeaturePipeline":
        """Learn categorical encodings from training features after strict validation."""
        if not X_dicts:
            raise FeatureValidationError("Cannot fit FeaturePipeline on empty feature set.")

        for idx, d in enumerate(X_dicts):
            self.validate_feature_dict(d, obs_index=idx)

        plants = sorted(list(set(str(d["plant_code"]) for d in X_dicts)))
        recipes = sorted(list(set(str(d["recipe_code"]) for d in X_dicts)))

        self.plant_map = {p: i for i, p in enumerate(plants)}
        self.recipe_map = {r: i for i, r in enumerate(recipes)}
        self.fitted = True
        return self

    def transform(self, X_dicts: List[Dict[str, Any]]) -> np.ndarray:
        """Transform dictionaries into clean 2D numpy float array with strict pre-validation."""
        if not self.fitted:
            raise RuntimeError("FeaturePipeline must be fitted before calling transform().")

        rows: List[List[float]] = []

        for idx, d in enumerate(X_dicts):
            self.validate_feature_dict(d, obs_index=idx)
            row: List[float] = []

            # 1. Numeric features
            for feat in self.numeric_features:
                row.append(float(d[feat]))

            # 2. Plant code categorical index
            p_code = str(d["plant_code"])
            p_idx = self.plant_map.get(p_code, -1)
            row.append(float(p_idx))

            # 3. Recipe code categorical index
            r_code = str(d["recipe_code"])
            r_idx = self.recipe_map.get(r_code, -1)
            row.append(float(r_idx))

            rows.append(row)

        return np.array(rows, dtype=np.float32)

    def fit_transform(self, X_dicts: List[Dict[str, Any]]) -> np.ndarray:
        """Fit and transform in a single pass."""
        return self.fit(X_dicts).transform(X_dicts)
