"""Unit test suite for WS-02.4 Lookup Tables & Enumerations."""

import pytest
from src.database import (
    BatchStatusEnum,
    BatchStatusLookup,
    LookupRepository,
    MaterialTypeEnum,
    MaterialTypeLookup,
    OrderStatusEnum,
    OrderStatusLookup,
    dispose_database_engine,
    get_db_session,
    seed_lookup_tables,
)
from src.exceptions import EntityNotFoundException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_idempotent_lookup_seed() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)

    # Second seed run should be idempotent with 0 duplicate errors
    with get_db_session() as session:
        seed_lookup_tables(session)


def test_lookup_repository_operations() -> None:
    with get_db_session() as session:
        seed_lookup_tables(session)
        repo = LookupRepository(BatchStatusLookup, session)

        assert repo.exists(BatchStatusEnum.PLANNED.value) is True

        batch_status = repo.get_by_code(BatchStatusEnum.PLANNED.value)
        assert batch_status.name == "Planned"

        active_list = repo.list_active()
        assert len(active_list) >= 5

        with pytest.raises(EntityNotFoundException):
            repo.get_by_code("NON_EXISTENT_CODE")
