"""Database Validation Inspection Repository.

This module provides read-only inspection methods for schema, tables, indexes, constraints, and views.
"""

from typing import List, Optional
from sqlalchemy import Engine, inspect
from src.database.engine import get_database_engine
from src.database.validation import (
    EXPECTED_BUSINESS_TABLES,
    EXPECTED_VIEWS,
    validate_database_constraints,
    validate_database_indexes,
    validate_database_schema,
    validate_database_seed_data,
    validate_database_views,
)


class DatabaseValidationRepository:
    """Read-only Inspection Repository for Database Schema and Structural Metadata."""

    def __init__(self, engine: Optional[Engine] = None) -> None:
        self._engine = engine if engine is not None else get_database_engine()

    def get_table_names(self) -> List[str]:
        """Return list of existing database table names."""
        insp = inspect(self._engine)
        return insp.get_table_names()

    def get_view_names(self) -> List[str]:
        """Return list of existing database view names."""
        insp = inspect(self._engine)
        return insp.get_view_names()

    def inspect_schema(self) -> List[str]:
        """Inspect and return schema validation issues."""
        return validate_database_schema(self._engine)

    def inspect_indexes(self) -> List[str]:
        """Inspect and return index validation issues."""
        return validate_database_indexes(self._engine)

    def inspect_constraints(self) -> List[str]:
        """Inspect and return constraint validation issues."""
        return validate_database_constraints(self._engine)

    def inspect_views(self) -> List[str]:
        """Inspect and return view validation issues."""
        return validate_database_views(self._engine)

    def inspect_seed_data(self) -> List[str]:
        """Inspect and return seed data validation issues."""
        return validate_database_seed_data()
