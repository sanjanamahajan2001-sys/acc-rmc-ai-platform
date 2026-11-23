"""Deterministic Grouped Dataset Partitioning & Leakage Prevention.

Enforces:
1. Grouped split by batch_id / batch_number so no batch crosses partition boundaries.
2. Complete test set holdout isolation.
3. Explicit refusal when insufficient batch groups exist to form independent train/test or k-fold partitions.
4. Deterministic reproducibility via explicit random seed.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Generator
import numpy as np

from src.ml.training.contracts import MLBatchObservation, CANONICAL_FEATURE_NAMES


class SplitValidationError(ValueError):
    """Raised when dataset cannot be safely partitioned into independent groups."""
    pass


@dataclass
class DatasetSplits:
    """Encapsulates partitioned observation subsets with zero cross-leakage."""
    train_observations: List[MLBatchObservation]
    test_observations: List[MLBatchObservation]
    
    @property
    def train_count(self) -> int:
        return len(self.train_observations)

    @property
    def test_count(self) -> int:
        return len(self.test_observations)

    def get_train_matrix(self) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Extract X_train (dict features) and y_train (float targets)."""
        X = [obs.to_feature_dict() for obs in self.train_observations]
        y = [obs.target_28d_strength_mpa for obs in self.train_observations]
        return X, y

    def get_test_matrix(self) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Extract X_test (dict features) and y_test (float targets)."""
        X = [obs.to_feature_dict() for obs in self.test_observations]
        y = [obs.target_28d_strength_mpa for obs in self.test_observations]
        return X, y


class DatasetSplitter:
    """Performs deterministic grouped partitioning on canonical observations."""

    @staticmethod
    def train_test_split(
        observations: List[MLBatchObservation],
        test_size: float = 0.20,
        random_seed: int = 42,
    ) -> DatasetSplits:
        """Split observations into train and holdout test sets with grouped batch isolation."""
        if not observations:
            raise SplitValidationError("Cannot split an empty observation list.")

        # Group observations by batch_id
        batch_ids = sorted(list(set(obs.batch_id for obs in observations)))
        n_batches = len(batch_ids)

        if n_batches < 2:
            raise SplitValidationError(
                f"Insufficient independent batch groups ({n_batches} batch found). "
                f"A minimum of 2 distinct production batches is required to create independent train and test partitions."
            )

        rng = np.random.RandomState(random_seed)
        shuffled_indices = rng.permutation(n_batches)

        n_test = max(1, int(n_batches * test_size))
        if n_test >= n_batches:
            n_test = n_batches - 1

        test_batch_indices = set(shuffled_indices[:n_test])
        test_batch_ids = set(batch_ids[i] for i in test_batch_indices)
        train_batch_ids = set(batch_ids[i] for i in range(n_batches) if i not in test_batch_indices)

        if not train_batch_ids or not test_batch_ids:
            raise SplitValidationError("Partitioning failed to generate non-empty train and test partitions.")

        train_obs = [obs for obs in observations if obs.batch_id in train_batch_ids]
        test_obs = [obs for obs in observations if obs.batch_id in test_batch_ids]

        # Verify zero overlap
        overlap = set(obs.batch_id for obs in train_obs).intersection(set(obs.batch_id for obs in test_obs))
        if overlap:
            raise SplitValidationError(f"Data leakage detected! Batches found in both train and test: {overlap}")

        return DatasetSplits(
            train_observations=train_obs,
            test_observations=test_obs,
        )

    @staticmethod
    def kfold_grouped_cv(
        train_observations: List[MLBatchObservation],
        n_splits: int = 5,
        random_seed: int = 42,
    ) -> Generator[Tuple[List[MLBatchObservation], List[MLBatchObservation]], None, None]:
        """Generate k-fold cross-validation partitions grouped by batch_id with strict refusal on insufficient groups."""
        if not train_observations:
            raise SplitValidationError("Cannot perform cross-validation on empty observations.")

        batch_ids = sorted(list(set(obs.batch_id for obs in train_observations)))
        n_batches = len(batch_ids)

        if n_batches < n_splits:
            raise SplitValidationError(
                f"Insufficient independent batch groups ({n_batches} batches) for requested {n_splits}-fold cross-validation. "
                f"At least {n_splits} distinct batches are strictly required."
            )

        rng = np.random.RandomState(random_seed)
        shuffled_batches = list(batch_ids)
        rng.shuffle(shuffled_batches)

        folds = np.array_split(shuffled_batches, n_splits)

        for i in range(n_splits):
            val_batch_set = set(folds[i])
            trn_batch_set = set(b for idx, f in enumerate(folds) if idx != i for b in f)

            trn_obs = [obs for obs in train_observations if obs.batch_id in trn_batch_set]
            val_obs = [obs for obs in train_observations if obs.batch_id in val_batch_set]

            if not trn_obs or not val_obs:
                raise SplitValidationError(f"Fold #{i} resulted in empty train or validation set.")

            yield trn_obs, val_obs
