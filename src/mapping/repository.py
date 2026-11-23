"""Import Profile Repository.

This module provides data access methods for managing versioned Import Profiles and Column Mappings.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.exceptions.domain import EntityNotFoundException
from src.mapping.models import ImportColumnMapping, ImportProfile


class ImportProfileRepository:
    """Repository managing persistence for Import Profiles and Column Mappings."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, profile_id: str) -> ImportProfile:
        """Retrieve active ImportProfile by ID or raise EntityNotFoundException."""
        profile = self._session.query(ImportProfile).filter_by(id=profile_id).first()
        if profile is None:
            raise EntityNotFoundException(entity_name="ImportProfile", identifier=profile_id)
        return profile

    def find_by_vendor_and_version(self, vendor_code: str, version: str) -> Optional[ImportProfile]:
        """Find ImportProfile by vendor code and profile version."""
        return (
            self._session.query(ImportProfile)
            .filter_by(vendor_code=vendor_code, profile_version=version)
            .first()
        )

    def list_active_profiles(self) -> List[ImportProfile]:
        """List all ACTIVE import profiles."""
        return self._session.query(ImportProfile).filter_by(profile_status="ACTIVE").all()

    def create_profile(self, profile: ImportProfile) -> ImportProfile:
        """Persist new ImportProfile record."""
        self._session.add(profile)
        self._session.flush()
        return profile
