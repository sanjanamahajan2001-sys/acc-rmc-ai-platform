"""Reporting & Analytical Read Models Orchestration Service.

This module provides business services for executing analytical read queries across database views.
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
from src.database.repositories.reporting_repository import ReportingRepository
from src.logging import get_logger

logger = get_logger("src.database.services.reporting", component="database")


class ReportingService:
    """Read Models & Analytical Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._reporting_repo = ReportingRepository(session)

    def get_batch_summary(self, batch_number: str) -> BatchSummaryView:
        """Fetch batch summary read model."""
        return self._reporting_repo.get_batch_summary(batch_number)

    def get_material_consumption_summary(self, batch_number: str) -> List[MaterialConsumptionSummaryView]:
        """Fetch material usage summary read models for a batch."""
        return self._reporting_repo.get_material_summary(batch_number)

    def get_quality_summary(self, sample_number: str) -> QualitySummaryView:
        """Fetch concrete quality summary read model."""
        return self._reporting_repo.get_quality_summary(sample_number)

    def get_prediction_summary(self, prediction_id: str) -> PredictionSummaryView:
        """Fetch AI prediction summary read model."""
        return self._reporting_repo.get_prediction_summary(prediction_id)

    def get_audit_activity(self, event_id: str) -> AuditActivityView:
        """Fetch audit activity summary read model."""
        return self._reporting_repo.get_audit_activity(event_id)

    def list_batch_summaries(self, plant_code: Optional[str] = None) -> List[BatchSummaryView]:
        """List batch summaries optionally filtered by plant_code."""
        return self._reporting_repo.list_batches(plant_code=plant_code)

    def list_prediction_summaries(self, model_version: Optional[str] = None) -> List[PredictionSummaryView]:
        """List prediction summaries optionally filtered by model_version."""
        return self._reporting_repo.list_predictions(model_version=model_version)
