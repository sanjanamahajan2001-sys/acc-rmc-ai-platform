"""AI Metadata Persistence Orchestration Service.

This module provides business services for persisting feature vectors, prediction history,
model registry entries, actual outcome links, prediction audits, and drift snapshots.
"""

from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from src.database.models.ai import (
    ActualOutcome,
    DriftSnapshot,
    FeatureVector,
    ModelRegistry,
    Prediction,
    PredictionAudit,
)
from src.database.models.laboratory import CubeTest
from src.database.repositories.ai_repository import AIRepository
from src.database.repositories.laboratory_repository import LaboratoryRepository
from src.database.repositories.production_repository import ProductionRepository
from src.exceptions.domain import EntityNotFoundException
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.services.ai_metadata", component="database")


class AIMetadataService:
    """AI Feature Store & Prediction Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._ai_repo = AIRepository(session)
        self._prod_repo = ProductionRepository(session)
        self._lab_repo = LaboratoryRepository(session)

    def persist_feature_vector(
        self,
        batch_id: str,
        model_version: str,
        feature_hash: str,
        feature_payload_json: Dict[str, Any],
        sample_id: Optional[str] = None,
        feature_schema_version: str = "1.0.0",
    ) -> FeatureVector:
        """Persist feature vector snapshot, validating batch and sample existence."""
        self._prod_repo.get_by_id(batch_id)
        if sample_id:
            self._lab_repo.get_sample_by_id(sample_id)

        fv = FeatureVector(
            batch_id=batch_id,
            sample_id=sample_id,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
            feature_hash=feature_hash,
            feature_payload_json=feature_payload_json,
        )
        self._ai_repo.create_feature_vector(fv)
        logger.info("Feature vector persisted", batch_id=batch_id, model_version=model_version, feature_hash=feature_hash)
        return fv

    def persist_prediction(
        self,
        feature_vector_id: str,
        model_version: str,
        predicted_strength_mpa: Decimal,
        prediction_type: str = "STRENGTH_28D",
        confidence_score: Optional[Decimal] = None,
        inference_duration_ms: Optional[int] = None,
    ) -> Prediction:
        """Persist model prediction execution record."""
        pred = Prediction(
            feature_vector_id=feature_vector_id,
            prediction_type=prediction_type,
            predicted_strength_mpa=predicted_strength_mpa,
            confidence_score=confidence_score,
            model_version=model_version,
            inference_duration_ms=inference_duration_ms,
        )
        self._ai_repo.create_prediction(pred)
        logger.info("Prediction persisted", prediction_id=pred.id, model_version=model_version, predicted_strength_mpa=str(predicted_strength_mpa))
        return pred

    def register_actual_outcome(
        self,
        prediction_id: str,
        cube_test_id: str,
        actual_strength_mpa: Decimal,
    ) -> ActualOutcome:
        """Link actual measured cube strength outcome to a prediction."""
        pred = self._ai_repo.get_prediction(prediction_id)

        # Validate cube test existence
        cube_test = self._session.query(CubeTest).filter_by(id=cube_test_id).first()
        if cube_test is None:
            raise EntityNotFoundException(entity_name="CubeTest", entity_id=cube_test_id)

        outcome = ActualOutcome(
            prediction_id=pred.id,
            cube_test_id=cube_test.id,
            actual_strength_mpa=actual_strength_mpa,
        )
        self._ai_repo.register_actual_outcome(outcome)
        logger.info("Actual outcome registered", prediction_id=prediction_id, cube_test_id=cube_test_id, actual_strength_mpa=str(actual_strength_mpa))
        return outcome

    def register_model(
        self,
        model_name: str,
        model_version: str,
        framework: str = "scikit-learn",
        algorithm: str = "XGBoostRegressor",
        feature_schema_version: str = "1.0.0",
        training_dataset_version: Optional[str] = None,
        artifact_location: Optional[str] = None,
        checksum: Optional[str] = None,
    ) -> ModelRegistry:
        """Register deployed model metadata, rejecting duplicate version registrations."""
        if self._ai_repo.exists_model_version(model_name, model_version):
            raise InvalidConfigurationException(
                parameter_name="model_version",
                message=f"Model '{model_name}' with version '{model_version}' already exists in registry.",
            )

        model = ModelRegistry(
            model_name=model_name,
            model_version=model_version,
            framework=framework,
            algorithm=algorithm,
            feature_schema_version=feature_schema_version,
            training_dataset_version=training_dataset_version,
            artifact_location=artifact_location,
            checksum=checksum,
        )
        self._ai_repo.register_model(model)
        logger.info("Model registered successfully", model_name=model_name, model_version=model_version, algorithm=algorithm)
        return model

    def record_prediction_audit(
        self,
        prediction_id: str,
        model_version: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        execution_duration_ms: Optional[int] = None,
        status: str = "SUCCESS",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> PredictionAudit:
        """Record prediction audit trail."""
        pred = self._ai_repo.get_prediction(prediction_id)

        audit = PredictionAudit(
            prediction_id=pred.id,
            model_version=model_version,
            request_id=request_id,
            correlation_id=correlation_id,
            execution_duration_ms=execution_duration_ms,
            status=status,
            metadata_json=metadata_json,
        )
        self._ai_repo.create_prediction_audit(audit)
        logger.info("Prediction audit recorded", prediction_id=prediction_id, status=status)
        return audit

    def record_drift_snapshot(
        self,
        monitored_feature: str,
        reference_distribution_json: Dict[str, Any],
        observed_distribution_json: Dict[str, Any],
        drift_metric: Decimal,
        threshold: Decimal = Decimal("0.0500"),
        drift_detected: bool = False,
    ) -> DriftSnapshot:
        """Persist statistical drift metric snapshot."""
        snapshot = DriftSnapshot(
            monitored_feature=monitored_feature,
            reference_distribution_json=reference_distribution_json,
            observed_distribution_json=observed_distribution_json,
            drift_metric=drift_metric,
            threshold=threshold,
            drift_detected=drift_detected,
        )
        self._ai_repo.create_drift_snapshot(snapshot)
        logger.info("Drift snapshot recorded", monitored_feature=monitored_feature, drift_metric=str(drift_metric), drift_detected=drift_detected)
        return snapshot
