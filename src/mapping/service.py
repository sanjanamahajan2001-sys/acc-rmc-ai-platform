"""Import Profile Service.

This module provides business orchestration for creating, loading, inheriting, and managing versioned import profiles.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.exceptions.domain import EntityNotFoundException
from src.mapping.models import ImportColumnMapping, ImportProfile
from src.mapping.repository import ImportProfileRepository


class ImportProfileService:
    """Orchestrator for managing versioned Import Profile lifecycle and inheritance."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = ImportProfileRepository(session)

    def get_profile(self, profile_id: str) -> ImportProfile:
        """Retrieve active ImportProfile by ID."""
        return self._repository.get_by_id(profile_id)

    def list_active_profiles(self) -> List[ImportProfile]:
        """List all active ImportProfile entities."""
        return self._repository.list_active_profiles()

    def create_profile(
        self,
        name: str,
        vendor_code: str,
        version: str = "1.0.0",
        created_from_profile_id: Optional[str] = None,
        mappings_dict: Optional[dict] = None,
    ) -> ImportProfile:
        """Create new versioned ImportProfile record with inheritance."""
        parent: Optional[ImportProfile] = None
        if created_from_profile_id:
            parent = self._repository.get_by_id(created_from_profile_id)

        profile = ImportProfile(
            profile_name=name,
            vendor_code=vendor_code,
            profile_version=version,
            profile_status="ACTIVE",
            created_from_profile_id=created_from_profile_id,
        )

        # Inherit parent mappings if specified
        if parent and parent.mappings:
            for pm in parent.mappings:
                profile.mappings.append(
                    ImportColumnMapping(
                        external_header=pm.external_header,
                        target_canonical_id=pm.target_canonical_id,
                        transformation_rule=pm.transformation_rule,
                        default_value=pm.default_value,
                        unit_override=pm.unit_override,
                    )
                )

        # Apply custom mapping overrides
        if mappings_dict:
            for ext_header, target_cid in mappings_dict.items():
                profile.mappings.append(
                    ImportColumnMapping(
                        external_header=ext_header,
                        target_canonical_id=target_cid,
                    )
                )

        return self._repository.create_profile(profile)

    def deprecate_profile(self, profile_id: str) -> ImportProfile:
        """Mark ImportProfile status as DEPRECATED."""
        profile = self.get_profile(profile_id)
        profile.profile_status = "DEPRECATED"
        self._session.flush()
        return profile
