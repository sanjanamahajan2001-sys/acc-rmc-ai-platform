"""Unit test suite for WS-02.2 Alembic Migration Framework & Declarative ORM Foundation."""

import os
from pathlib import Path
import pytest
from sqlalchemy.orm import Mapped, mapped_column
from src.database import (
    AuditMetadataMixin,
    BaseModel,
    CreatedAtMixin,
    MigrationService,
    OptimisticLockMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
    dispose_database_engine,
    get_db_session,
)


class SampleTestEntity(
    BaseModel,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    UpdatedAtMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
    AuditMetadataMixin,
):
    __tablename__ = "sample_test_entities"

    name: Mapped[str] = mapped_column(nullable=False)


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_declarative_base_model_mixins() -> None:
    entity = SampleTestEntity(name="Test Concrete Sample")
    assert entity.id is not None
    assert len(entity.id) == 36
    assert entity.name == "Test Concrete Sample"
    assert entity.is_deleted is False
    assert entity.version_id == 1


def test_naming_convention_metadata() -> None:
    metadata = BaseModel.metadata
    assert "ix" in metadata.naming_convention
    assert "fk" in metadata.naming_convention
    assert metadata.naming_convention["ix"] == "ix_%(column_0_label)s"


def test_alembic_migration_service() -> None:
    service = MigrationService()
    cfg = service.get_alembic_config()
    assert cfg.get_main_option("sqlalchemy.url") is not None
    assert "alembic" in cfg.get_main_option("script_location")
