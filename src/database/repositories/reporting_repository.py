"""Reporting & Analytical View Data Access Repository.

This module provides read-only data access methods for database analytical views.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.views import (
    AuditActivityView,
    BatchSummaryView,
    MaterialConsumptionSummaryView,
    PredictionSummaryView,
    QualitySummaryView,
)
from src.exceptions.domain import EntityNotFoundException


class ReportingRepository:
    """Read-only Data Access Repository for Analytical Views."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_batch_summary(self, batch_number: str) -> BatchSummaryView:
        """Retrieve batch summary view record by batch_number."""
        record = self._session.query(BatchSummaryView).filter_by(batch_number=batch_number).first()
        if record is None:
            raise EntityNotFoundException(entity_name="BatchSummaryView", identifier=batch_number)
        return record

    def get_material_summary(self, batch_number: str) -> List[MaterialConsumptionSummaryView]:
        """List material consumption summary records for a batch."""
        return self._session.query(MaterialConsumptionSummaryView).filter_by(batch_number=batch_number).all()

    def get_quality_summary(self, sample_number: str) -> QualitySummaryView:
        """Retrieve quality summary view record by sample_number."""
        record = self._session.query(QualitySummaryView).filter_by(sample_number=sample_number).first()
        if record is None:
            raise EntityNotFoundException(entity_name="QualitySummaryView", identifier=sample_number)
        return record

    def get_prediction_summary(self, prediction_id: str) -> PredictionSummaryView:
        """Retrieve prediction summary view record by prediction_id."""
        record = self._session.query(PredictionSummaryView).filter_by(prediction_id=prediction_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="PredictionSummaryView", identifier=prediction_id)
        return record

    def get_audit_activity(self, event_id: str) -> AuditActivityView:
        """Retrieve audit activity view record by event_id."""
        record = self._session.query(AuditActivityView).filter_by(event_id=event_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="AuditActivityView", identifier=event_id)
        return record

    def list_batches(self, plant_code: Optional[str] = None) -> List[BatchSummaryView]:
        """List batch summaries optionally filtered by plant_code."""
        query = self._session.query(BatchSummaryView)
        if plant_code:
            query = query.filter_by(plant_code=plant_code)
        return query.all()

    def list_predictions(self, model_version: Optional[str] = None) -> List[PredictionSummaryView]:
        """List prediction summaries optionally filtered by model_version."""
        query = self._session.query(PredictionSummaryView)
        if model_version:
            query = query.filter_by(model_version=model_version)
        return query.all()
