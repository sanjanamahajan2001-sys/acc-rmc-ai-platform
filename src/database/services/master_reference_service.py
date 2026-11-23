"""Master Reference Data Orchestration Service.

This module provides business master reference validation and creation services enforcing immutable code uniqueness
and natural key relationship resolution across Plants, Customers, Projects, Materials, and Recipes.
"""

from sqlalchemy.orm import Session
from src.database.models.master import Customer, Material, Plant, Project, Recipe
from src.database.repositories.master_repository import MasterRepository
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.services.master_reference", component="database")


class MasterReferenceService:
    """Master Reference Data Integrity & Orchestration Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._plant_repo = MasterRepository(Plant, session)
        self._customer_repo = MasterRepository(Customer, session)
        self._project_repo = MasterRepository(Project, session)

    def create_plant(self, plant_code: str, plant_name: str, location: str = "") -> Plant:
        """Create new plant master record with duplicate code prevention."""
        if self._plant_repo.exists_code("plant_code", plant_code):
            raise InvalidConfigurationException(
                parameter_name="plant_code",
                message=f"Plant with code '{plant_code}' already exists.",
            )
        plant = Plant(plant_code=plant_code, plant_name=plant_name, location=location)
        self._plant_repo.create(plant)
        logger.info("Master Plant record created", plant_code=plant_code)
        return plant

    def create_customer(self, customer_code: str, legal_name: str, gst_identifier: str = "") -> Customer:
        """Create new customer master record, storing raw GST identifier without format validation."""
        if self._customer_repo.exists_code("customer_code", customer_code):
            raise InvalidConfigurationException(
                parameter_name="customer_code",
                message=f"Customer with code '{customer_code}' already exists.",
            )
        customer = Customer(customer_code=customer_code, legal_name=legal_name, gst_identifier=gst_identifier)
        self._customer_repo.create(customer)
        logger.info("Master Customer record created", customer_code=customer_code)
        return customer

    def create_project_by_customer_code(self, project_code: str, customer_code: str, project_name: str) -> Project:
        """Create new project master record resolving parent customer by natural key (customer_code)."""
        customer = self._customer_repo.get_by_code("customer_code", customer_code)

        if self._project_repo.exists_code("project_code", project_code):
            raise InvalidConfigurationException(
                parameter_name="project_code",
                message=f"Project with code '{project_code}' already exists.",
            )
        project = Project(project_code=project_code, customer_id=customer.id, project_name=project_name)
        self._project_repo.create(project)
        logger.info("Master Project record created using natural customer_code", project_code=project_code, customer_code=customer_code)
        return project

    def create_project(self, project_code: str, customer_id: str, project_name: str) -> Project:
        """Create new project master record, validating foreign customer existence."""
        self._customer_repo.get_by_id(customer_id)

        if self._project_repo.exists_code("project_code", project_code):
            raise InvalidConfigurationException(
                parameter_name="project_code",
                message=f"Project with code '{project_code}' already exists.",
            )
        project = Project(project_code=project_code, customer_id=customer_id, project_name=project_name)
        self._project_repo.create(project)
        logger.info("Master Project record created", project_code=project_code)
        return project
