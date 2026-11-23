"""Laboratory & Quality Assurance Orchestration Service.

This module provides business services for recording concrete samples, slump tests, cube casting,
cube strength tests, FT7 certificates, and quality observations.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from src.database.models.laboratory import (
    ConcreteSample,
    CubeSet,
    CubeTest,
    FT7Certificate,
    QualityObservation,
    SlumpTest,
)
from src.database.repositories.laboratory_repository import LaboratoryRepository
from src.database.repositories.production_repository import ProductionRepository
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.services.laboratory", component="database")


class LaboratoryService:
    """Laboratory & QA Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._lab_repo = LaboratoryRepository(session)
        self._prod_repo = ProductionRepository(session)

    def create_sample(
        self,
        sample_number: str,
        batch_id: str,
        sampling_location: str = "PLANT_DISCHARGE",
        collected_by: str = "QA_TECHNICIAN_01",
        remarks: str = "",
    ) -> ConcreteSample:
        """Create concrete fresh sample, validating batch existence."""
        if self._lab_repo.exists_sample_number(sample_number):
            raise InvalidConfigurationException(
                parameter_name="sample_number",
                message=f"Sample with sample_number '{sample_number}' already exists.",
            )

        # Validate parent batch existence
        self._prod_repo.get_by_id(batch_id)

        sample = ConcreteSample(
            sample_number=sample_number,
            batch_id=batch_id,
            sampling_location=sampling_location,
            collected_by=collected_by,
            remarks=remarks,
        )
        self._lab_repo.create_sample(sample)
        logger.info("Concrete sample created", sample_number=sample_number, batch_id=batch_id)
        return sample

    def record_slump_test(
        self,
        sample_id: str,
        slump_mm: Decimal,
        tester_name: str = "QA_TECHNICIAN_01",
        ambient_temp_celsius: Optional[Decimal] = None,
        concrete_temp_celsius: Optional[Decimal] = None,
    ) -> SlumpTest:
        """Record slump test workability measurement for a sample."""
        sample = self._lab_repo.get_sample_by_id(sample_id)

        slump_test = SlumpTest(
            sample_id=sample.id,
            slump_mm=slump_mm,
            tester_name=tester_name,
            ambient_temp_celsius=ambient_temp_celsius,
            concrete_temp_celsius=concrete_temp_celsius,
        )
        self._lab_repo.create_slump_test(slump_test)
        logger.info("Slump test recorded", sample_id=sample_id, slump_mm=str(slump_mm))
        return slump_test

    def create_cube_set(
        self,
        cube_set_number: str,
        sample_id: str,
        number_of_cubes: int = 6,
        target_schedule: str = "7_28_DAYS",
    ) -> CubeSet:
        """Record cube set casting for a sample."""
        if self._lab_repo.exists_cube_set_number(cube_set_number):
            raise InvalidConfigurationException(
                parameter_name="cube_set_number",
                message=f"Cube set with number '{cube_set_number}' already exists.",
            )

        sample = self._lab_repo.get_sample_by_id(sample_id)

        cube_set = CubeSet(
            cube_set_number=cube_set_number,
            sample_id=sample.id,
            number_of_cubes=number_of_cubes,
            target_schedule=target_schedule,
        )
        self._lab_repo.create_cube_set(cube_set)
        logger.info("Cube set cast", cube_set_number=cube_set_number, sample_id=sample_id)
        return cube_set

    def record_cube_test(
        self,
        cube_set_id: str,
        age_days: int,
        compressive_strength_mpa: Decimal,
        failure_mode: str = "NORMAL_PYRAMIDAL",
        tested_by: str = "LAB_TESTER_01",
        test_machine_id: str = "CTM-01",
    ) -> CubeTest:
        """Record compressive strength test result for a cube."""
        cube_test = CubeTest(
            cube_set_id=cube_set_id,
            age_days=age_days,
            compressive_strength_mpa=compressive_strength_mpa,
            failure_mode=failure_mode,
            tested_by=tested_by,
            test_machine_identifier=test_machine_id,
        )
        self._lab_repo.create_cube_test(cube_test)
        logger.info("Cube test recorded", cube_set_id=cube_set_id, age_days=age_days, strength_mpa=str(compressive_strength_mpa))
        return cube_test

    def register_ft7_certificate(
        self,
        certificate_number: str,
        batch_id: str,
        approved_by: str = "QA_MANAGER",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> FT7Certificate:
        """Register FT7 quality certificate for a batch."""
        if self._lab_repo.exists_certificate_number(certificate_number):
            raise InvalidConfigurationException(
                parameter_name="certificate_number",
                message=f"Certificate '{certificate_number}' already exists.",
            )

        self._prod_repo.get_by_id(batch_id)

        cert = FT7Certificate(
            certificate_number=certificate_number,
            batch_id=batch_id,
            approved_by=approved_by,
            certificate_metadata_json=metadata_json,
        )
        self._lab_repo.create_ft7_certificate(cert)
        logger.info("FT7 certificate registered", certificate_number=certificate_number, batch_id=batch_id)
        return cert

    def record_quality_observation(
        self,
        batch_id: str,
        observation_type: str,
        description: str,
        severity: str = "MEDIUM",
        raised_by: str = "QA_INSPECTOR",
    ) -> QualityObservation:
        """Record quality observation or non-conformance flag for a batch."""
        self._prod_repo.get_by_id(batch_id)

        obs = QualityObservation(
            batch_id=batch_id,
            observation_type=observation_type,
            severity=severity,
            description=description,
            raised_by=raised_by,
        )
        self._lab_repo.create_quality_observation(obs)
        logger.info("Quality observation recorded", batch_id=batch_id, type=observation_type, severity=severity)
        return obs
