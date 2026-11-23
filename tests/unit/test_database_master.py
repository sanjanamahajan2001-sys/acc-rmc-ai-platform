"""Unit test suite for WS-02.5 Master Reference Data."""

import pytest
from src.database import (
    Customer,
    MasterReferenceService,
    MasterRepository,
    Plant,
    Project,
    Recipe,
    Supplier,
    dispose_database_engine,
    get_db_session,
)
from src.exceptions import EntityNotFoundException, InvalidConfigurationException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_master_repository_operations() -> None:
    with get_db_session() as session:
        plant_repo = MasterRepository(Plant, session)
        plant = Plant(plant_code="PLANT_01", plant_name="Kalyan Batch Plant", location="Kalyan, Mumbai")
        plant_repo.create(plant)

        retrieved = plant_repo.get_by_code("plant_code", "PLANT_01")
        assert retrieved.plant_name == "Kalyan Batch Plant"
        assert retrieved.id == plant.id

        assert plant_repo.exists_code("plant_code", "PLANT_01") is True
        assert plant_repo.exists_code("plant_code", "NON_EXISTENT") is False


def test_master_reference_service_and_foreign_keys() -> None:
    with get_db_session() as session:
        srv = MasterReferenceService(session)

        plant = srv.create_plant("PLANT_02", "Thane Batch Plant")
        assert plant.id is not None

        # Duplicate plant code should be rejected
        with pytest.raises(InvalidConfigurationException):
            srv.create_plant("PLANT_02", "Duplicate Plant")

        customer = srv.create_customer("CUST_100", "L&T Construction Ltd")
        assert customer.id is not None

        project = srv.create_project("PROJ_500", customer.id, "Metro Line 4 Elevated Corridor")
        assert project.customer_id == customer.id

        # Non-existent customer ID should raise EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            srv.create_project("PROJ_501", "non-existent-customer-uuid", "Invalid Project")
