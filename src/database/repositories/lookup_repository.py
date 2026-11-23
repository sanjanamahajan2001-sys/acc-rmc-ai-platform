"""Generic Lookup Repository with Cache-Friendly Abstraction.

This module provides data access methods (`get_by_code()`, `list_active()`, `list_all()`, `exists()`, `refresh_cache()`)
for normalized lookup tables with cache-friendly design.
"""

from typing import Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from src.database.models.lookups import BaseLookupTable
from src.exceptions.domain import EntityNotFoundException

T = TypeVar("T", bound=BaseLookupTable)


class LookupRepository(Generic[T]):
    """Generic Cache-Friendly Repository for Lookup Entities."""

    def __init__(self, model_cls: Type[T], session: Session) -> None:
        self._model_cls = model_cls
        self._session = session
        self._cache: Dict[str, T] = {}

    def refresh_cache(self) -> None:
        """Populate or refresh local memory cache of active lookup records."""
        active_records = self.list_active()
        self._cache = {record.code: record for record in active_records}

    def get_by_code(self, code: str) -> T:
        """Retrieve lookup record by unique code, checking in-memory cache first.

        Raises:
            EntityNotFoundException: If lookup record is not found.
        """
        if code in self._cache:
            return self._cache[code]

        record = self._session.query(self._model_cls).filter_by(code=code).first()
        if record is None:
            raise EntityNotFoundException(
                entity_name=self._model_cls.__name__,
                entity_id=code,
            )
        self._cache[code] = record
        return record

    def list_active(self) -> List[T]:
        """List all active lookup records sorted by display order."""
        return (
            self._session.query(self._model_cls)
            .filter_by(is_active=True)
            .order_by(self._model_cls.display_order.asc())
            .all()
        )

    def list_all(self) -> List[T]:
        """List all lookup records sorted by display order."""
        return self._session.query(self._model_cls).order_by(self._model_cls.display_order.asc()).all()

    def exists(self, code: str) -> bool:
        """Check whether lookup code exists."""
        if code in self._cache:
            return True
        return (
            self._session.query(self._model_cls.id).filter_by(code=code).first() is not None
        )
