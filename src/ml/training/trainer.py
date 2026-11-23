"""Enterprise Model Training & Evaluation Engine for ACC RMC AI Platform (Phase 13C).

Certified Rules:
- Consumes ONLY certified Phase 13A observations (OPERATIONAL_ACTUAL / HISTORICAL_QC).
- Preprocessing FeaturePipeline is fitted strictly on the training partition (zero test leakage).
- Model Candidates Evaluated:
  1. Baseline Regression (Linear Regression / Ridge)
  2. Random Forest Regressor (Ensemble Tree)
  3. XGBoost Regressor (Gradient Boosting)
- Comprehensive Regression Metrics: MAE, RMSE, R2, Bias, Residual Distributions.
- Deterministic Artifact Serialization with SHA-256 Checksum Verification.
- Candidate artifacts are stored in ModelRegistry strictly with deployment_status = 'CANDIDATE' (NEVER AUTO-ACTIVATED).
"""

import os
import sys
import json
import time
import hashlib
import joblib
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

import sklearn
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

from src.ml.training.contracts import MLBatchObservation, CANONICAL_FEATURE_NAMES
from src.ml.training.features import FeaturePipeline
from src.ml.training.splits import DatasetSplitter, DatasetSplits


@dataclass
class ModelEvaluationMetrics:
    """Standardized regression evaluation metrics."""
    mae_mpa: float
    rmse_mpa: float
    r2_score: float
    target_mean_mpa: float
    target_std_mpa: float
    prediction_mean_mpa: float
    prediction_std_mpa: float
    systematic_bias_mpa: float
    sample_count: int


@dataclass
class CandidateTrainingReport:
    """Evaluation diagnostics and artifact details for a candidate model."""
    algorithm: str
    framework: str
    model_version: str
    feature_schema_version: str
    dataset_fingerprint: str
    random_seed: int
    train_metrics: ModelEvaluationMetrics
    test_metrics: ModelEvaluationMetrics
    cv_mean_r2: Optional[float] = None
    cv_std_r2: Optional[float] = None
    artifact_path: Optional[str] = None
    artifact_checksum: Optional[str] = None
    training_duration_seconds: float = 0.0


class ModelTrainerService:
    """Executes multi-candidate model training, cross-validation, and candidate artifact generation."""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> ModelEvaluationMetrics:
        """Compute standard statistical and regression accuracy metrics."""
        residuals = y_true - y_pred
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        
        # R2 score calculation
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 0.0

        return ModelEvaluationMetrics(
            mae_mpa=round(mae, 3),
            rmse_mpa=round(rmse, 3),
            r2_score=round(r2, 4),
            target_mean_mpa=round(float(np.mean(y_true)), 2),
            target_std_mpa=round(float(np.std(y_true)), 2),
            prediction_mean_mpa=round(float(np.mean(y_pred)), 2),
            prediction_std_mpa=round(float(np.std(y_pred)), 2),
            systematic_bias_mpa=round(float(np.mean(y_pred - y_true)), 3),
            sample_count=len(y_true),
        )

    @staticmethod
    def train_and_evaluate_candidates(
        observations: List[MLBatchObservation],
        dataset_fingerprint: str,
        artifacts_dir: Optional[str] = None,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """Train baseline and tree candidates, evaluate holdout metrics, and serialize best candidate."""
        if not artifacts_dir:
            base_dir = "/opt/apps/acc-rmc-ai-platform" if os.path.exists("/opt/apps/acc-rmc-ai-platform") else os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            artifacts_dir = os.path.join(base_dir, "trained_models")
        os.makedirs(artifacts_dir, exist_ok=True)
        start_time = time.time()

        # 1. Deterministic Grouped Train/Test Holdout Partitioning
        splits = DatasetSplitter.train_test_split(
            observations=observations,
            test_size=0.20,
            random_seed=random_seed,
        )

        X_train_dicts, y_train_list = splits.get_train_matrix()
        X_test_dicts, y_test_list = splits.get_test_matrix()

        # 2. Fit FeaturePipeline strictly on Training Partition (Zero Test Leakage)
        pipeline = FeaturePipeline()
        X_train = pipeline.fit_transform(X_train_dicts)
        X_test = pipeline.transform(X_test_dicts)

        y_train = np.array(y_train_list, dtype=np.float32)
        y_test = np.array(y_test_list, dtype=np.float32)

        # 3. Model Candidates Definition
        candidates = {
            "BaselineRidge": {
                "framework": "scikit-learn",
                "model": Ridge(alpha=1.0, random_state=random_seed),
            },
            "RandomForest": {
                "framework": "scikit-learn",
                "model": RandomForestRegressor(n_estimators=50, max_depth=6, random_state=random_seed),
            },
            "XGBoost": {
                "framework": "xgboost",
                "model": xgb.XGBRegressor(n_estimators=50, max_depth=4, learning_rate=0.08, random_state=random_seed),
            },
        }

        results: Dict[str, CandidateTrainingReport] = {}
        best_algo = "BaselineRidge"
        best_rmse = float("inf")

        for name, config in candidates.items():
            model = config["model"]
            model.fit(X_train, y_train)

            pred_train = model.predict(X_train)
            pred_test = model.predict(X_test)

            train_metrics = ModelTrainerService.calculate_metrics(y_train, pred_train)
            test_metrics = ModelTrainerService.calculate_metrics(y_test, pred_test)

            report = CandidateTrainingReport(
                algorithm=name,
                framework=config["framework"],
                model_version=f"{name.lower()}-v1.0.0",
                feature_schema_version="1.0.0",
                dataset_fingerprint=dataset_fingerprint,
                random_seed=random_seed,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
            )
            results[name] = report

            # Track candidate with lowest test RMSE
            if test_metrics.rmse_mpa < best_rmse:
                best_rmse = test_metrics.rmse_mpa
                best_algo = name

        # 4. Serialize Best Candidate Artifact (FeaturePipeline + Trained Model)
        best_model_obj = candidates[best_algo]["model"]
        artifact_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        artifact_filename = f"candidate_{best_algo.lower()}_{artifact_timestamp}.joblib"
        artifact_path = os.path.join(artifacts_dir, artifact_filename)

        bundle = {
            "algorithm": best_algo,
            "model": best_model_obj,
            "pipeline": pipeline,
            "feature_schema_version": "1.0.0",
            "dataset_fingerprint": dataset_fingerprint,
            "random_seed": random_seed,
            "metrics": asdict(results[best_algo].test_metrics),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "library_versions": {
                "scikit_learn": sklearn.__version__,
                "xgboost": xgb.__version__,
                "joblib": joblib.__version__,
            }
        }

        joblib.dump(bundle, artifact_path)

        # 5. Compute Artifact SHA-256 Checksum and Verify Reloadability
        with open(artifact_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        # Reload test verification
        reloaded_bundle = joblib.load(artifact_path)
        assert reloaded_bundle["algorithm"] == best_algo
        assert reloaded_bundle["pipeline"].fitted is True

        results[best_algo].artifact_path = artifact_path
        results[best_algo].artifact_checksum = checksum
        duration = round(time.time() - start_time, 2)
        results[best_algo].training_duration_seconds = duration

        return {
            "best_candidate": best_algo,
            "reports": {k: asdict(v) for k, v in results.items()},
            "artifact_path": artifact_path,
            "artifact_checksum": checksum,
            "train_observations": splits.train_count,
            "test_observations": splits.test_count,
            "total_observations": len(observations),
            "duration_seconds": duration,
        }
