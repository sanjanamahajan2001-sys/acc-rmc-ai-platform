"""Generic Master Reference Data Repository.

This module provides standard CRUD data access methods for Master Reference Entities.
"""

from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from src.exceptions.domain import EntityNotFoundException

T = TypeVar("T")


class MasterRepository(Generic[T]):
    """Generic Repository for Master Reference Entities."""

    def __init__(self, model_cls: Type[T], session: Session) -> None:
        self._model_cls = model_cls
        self._session = session

    def get_by_id(self, entity_id: str) -> T:
        """Retrieve record by primary key UUID."""
        record = self._session.query(self._model_cls).filter_by(id=entity_id).first()
        if record is None:
            raise EntityNotFoundException(
                entity_name=self._model_cls.__name__,
                entity_id=entity_id,
            )
        return record

    def get_by_code(self, code_attr: str, code_value: str) -> T:
        """Retrieve record by unique business code field."""
        filter_kwargs = {code_attr: code_value}
        record = self._session.query(self._model_cls).filter_by(**filter_kwargs).first()
        if record is None:
            raise EntityNotFoundException(
                entity_name=self._model_cls.__name__,
                entity_id=code_value,
            )
        return record

    def create(self, entity: T) -> T:
        """Add new entity record to session."""
        self._session.add(entity)
        self._session.flush()
        return entity

    def update(self, entity: T) -> T:
        """Flush session changes for entity."""
        self._session.flush()
        return entity

    def deactivate(self, entity: T) -> T:
        """Deactivate entity if soft delete is supported."""
        if hasattr(entity, "is_deleted"):
            setattr(entity, "is_deleted", True)
            self._session.flush()
        return entity

    def exists_code(self, code_attr: str, code_value: str) -> bool:
        """Check if business code exists."""
        filter_kwargs = {code_attr: code_value}
        return self._session.query(self._model_cls.id).filter_by(**filter_kwargs).first() is not None

    def list_active(self) -> List[T]:
        """List active non-deleted entities."""
        query = self._session.query(self._model_cls)
        if hasattr(self._model_cls, "is_deleted"):
            query = query.filter_by(is_deleted=False)
        return query.all()
