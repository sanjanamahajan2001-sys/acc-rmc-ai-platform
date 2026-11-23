"""Laboratory Data Access Repository.

This module provides data access methods for Laboratory & Quality entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.laboratory import (
    ConcreteSample,
    CubeSet,
    CubeTest,
    FT7Certificate,
    QualityObservation,
    SlumpTest,
)
from src.exceptions.domain import EntityNotFoundException


class LaboratoryRepository:
    """Data Access Repository for Laboratory & QA Entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_sample_by_id(self, sample_id: str) -> ConcreteSample:
        """Retrieve sample record by UUID."""
        record = self._session.query(ConcreteSample).filter_by(id=sample_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="ConcreteSample", entity_id=sample_id)
        return record

    def get_sample_by_number(self, sample_number: str) -> ConcreteSample:
        """Retrieve sample record by unique sample_number."""
        record = self._session.query(ConcreteSample).filter_by(sample_number=sample_number).first()
        if record is None:
            raise EntityNotFoundException(entity_name="ConcreteSample", entity_id=sample_number)
        return record

    def get_samples_by_batch(self, batch_id: str) -> List[ConcreteSample]:
        """List samples collected for a batch."""
        return self._session.query(ConcreteSample).filter_by(batch_id=batch_id, is_deleted=False).all()

    def create_sample(self, sample: ConcreteSample) -> ConcreteSample:
        """Add new concrete sample record."""
        self._session.add(sample)
        self._session.flush()
        return sample

    def create_slump_test(self, slump_test: SlumpTest) -> SlumpTest:
        """Add new slump test record."""
        self._session.add(slump_test)
        self._session.flush()
        return slump_test

    def create_cube_set(self, cube_set: CubeSet) -> CubeSet:
        """Add new cube set record."""
        self._session.add(cube_set)
        self._session.flush()
        return cube_set

    def create_cube_test(self, cube_test: CubeTest) -> CubeTest:
        """Add new cube strength test record."""
        self._session.add(cube_test)
        self._session.flush()
        return cube_test

    def create_ft7_certificate(self, cert: FT7Certificate) -> FT7Certificate:
        """Add new FT7 quality certificate record."""
        self._session.add(cert)
        self._session.flush()
        return cert

    def create_quality_observation(self, obs: QualityObservation) -> QualityObservation:
        """Add new quality observation record."""
        self._session.add(obs)
        self._session.flush()
        return obs

    def list_cube_tests_by_sample(self, sample_id: str) -> List[CubeTest]:
        """List all cube tests for a sample across its cube sets."""
        return (
            self._session.query(CubeTest)
            .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
            .filter(CubeSet.sample_id == sample_id)
            .all()
        )

    def list_ft7_certificates_by_batch(self, batch_id: str) -> List[FT7Certificate]:
        """List FT7 certificates for a batch."""
        return self._session.query(FT7Certificate).filter_by(batch_id=batch_id, is_deleted=False).all()

    def list_observations_by_batch(self, batch_id: str) -> List[QualityObservation]:
        """List quality observations for a batch."""
        return self._session.query(QualityObservation).filter_by(batch_id=batch_id, is_deleted=False).all()

    def exists_sample_number(self, sample_number: str) -> bool:
        """Check if sample_number exists."""
        return self._session.query(ConcreteSample.id).filter_by(sample_number=sample_number).first() is not None

    def exists_cube_set_number(self, cube_set_number: str) -> bool:
        """Check if cube_set_number exists."""
        return self._session.query(CubeSet.id).filter_by(cube_set_number=cube_set_number).first() is not None

    def exists_certificate_number(self, certificate_number: str) -> bool:
        """Check if certificate_number exists."""
        return self._session.query(FT7Certificate.id).filter_by(certificate_number=certificate_number).first() is not None
