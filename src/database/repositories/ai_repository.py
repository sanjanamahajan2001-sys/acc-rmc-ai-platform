"""AI Feature Store & Prediction Data Access Repository.

This module provides data access methods for Feature Vectors, Predictions, Actual Outcomes,
Model Registry, Prediction Audits, and Drift Snapshots.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.ai import (
    ActualOutcome,
    DriftSnapshot,
    FeatureVector,
    ModelRegistry,
    Prediction,
    PredictionAudit,
)
from src.exceptions.domain import EntityNotFoundException


class AIRepository:
    """Data Access Repository for AI Metadata Entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_prediction(self, prediction_id: str) -> Prediction:
        """Retrieve prediction record by UUID."""
        record = self._session.query(Prediction).filter_by(id=prediction_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="Prediction", entity_id=prediction_id)
        return record

    def create_feature_vector(self, feature_vector: FeatureVector) -> FeatureVector:
        """Add new feature vector snapshot."""
        self._session.add(feature_vector)
        self._session.flush()
        return feature_vector

    def create_prediction(self, prediction: Prediction) -> Prediction:
        """Add new prediction record."""
        self._session.add(prediction)
        self._session.flush()
        return prediction

    def register_actual_outcome(self, outcome: ActualOutcome) -> ActualOutcome:
        """Link actual measured cube test outcome to a prediction."""
        self._session.add(outcome)
        self._session.flush()
        return outcome

    def register_model(self, model: ModelRegistry) -> ModelRegistry:
        """Register deployed model metadata."""
        self._session.add(model)
        self._session.flush()
        return model

    def create_prediction_audit(self, audit: PredictionAudit) -> PredictionAudit:
        """Add prediction execution audit record."""
        self._session.add(audit)
        self._session.flush()
        return audit

    def create_drift_snapshot(self, snapshot: DriftSnapshot) -> DriftSnapshot:
        """Add statistical drift metric snapshot."""
        self._session.add(snapshot)
        self._session.flush()
        return snapshot

    def list_predictions(self, model_version: Optional[str] = None) -> List[Prediction]:
        """List predictions optionally filtered by model version."""
        query = self._session.query(Prediction).filter_by(is_deleted=False)
        if model_version:
            query = query.filter_by(model_version=model_version)
        return query.all()

    def get_model_version(self, model_name: str, model_version: str) -> ModelRegistry:
        """Retrieve registered model by name and version."""
        record = (
            self._session.query(ModelRegistry)
            .filter_by(model_name=model_name, model_version=model_version)
            .first()
        )
        if record is None:
            raise EntityNotFoundException(entity_name="ModelRegistry", entity_id=f"{model_name}:{model_version}")
        return record

    def list_models(self) -> List[ModelRegistry]:
        """List all deployed model metadata records."""
        return self._session.query(ModelRegistry).filter_by(is_deleted=False).all()

    def exists_model_version(self, model_name: str, model_version: str) -> bool:
        """Check if model name and version combination exists."""
        return (
            self._session.query(ModelRegistry.id)
            .filter_by(model_name=model_name, model_version=model_version)
            .first()
            is not None
        )
