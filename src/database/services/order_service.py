"""Order & Dispatch Orchestration Service.

This module provides business services for order creation, customer/project/recipe relationship validation,
and dispatch schedule creation.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.database.models.lookups import OrderStatusLookup
from src.database.models.master import Customer, Plant, Project, Recipe
from src.database.models.orders import DispatchSchedule, Order, OrderLineItem
from src.database.repositories.master_repository import MasterRepository
from src.database.repositories.order_repository import OrderRepository
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.database.services.order", component="database")


class OrderService:
    """Order & Dispatch Planning Service."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._order_repo = OrderRepository(session)
        self._customer_repo = MasterRepository(Customer, session)
        self._project_repo = MasterRepository(Project, session)
        self._plant_repo = MasterRepository(Plant, session)
        self._recipe_repo = MasterRepository(Recipe, session)

    def create_order(
        self,
        order_number: str,
        customer_id: str,
        project_id: str,
        plant_id: str,
        order_status_id: str,
        requested_delivery_datetime: datetime,
        recipe_id: str,
        ordered_quantity_m3: float,
        priority: int = 1,
        remarks: str = "",
    ) -> Order:
        """Create new commercial order with line items, validating customer, project, plant, and recipe existence."""
        if self._order_repo.exists_order_number(order_number):
            raise InvalidConfigurationException(
                parameter_name="order_number",
                message=f"Order with order_number '{order_number}' already exists.",
            )

        # Validate master entity existence
        self._customer_repo.get_by_id(customer_id)
        self._project_repo.get_by_id(project_id)
        self._plant_repo.get_by_id(plant_id)
        self._recipe_repo.get_by_id(recipe_id)

        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            project_id=project_id,
            plant_id=plant_id,
            order_status_id=order_status_id,
            requested_delivery_datetime=requested_delivery_datetime,
            priority=priority,
            remarks=remarks,
            total_quantity_m3=ordered_quantity_m3,
        )

        line_item = OrderLineItem(
            recipe_id=recipe_id,
            ordered_quantity_m3=ordered_quantity_m3,
        )
        order.line_items.append(line_item)

        self._order_repo.create(order)
        logger.info("Order created successfully", order_number=order_number, quantity_m3=ordered_quantity_m3)
        return order

    def create_dispatch_schedule(
        self,
        schedule_number: str,
        order_id: str,
        planned_dispatch_time: datetime,
        planned_delivery_time: datetime,
        planned_quantity_m3: float,
        sequence_number: int = 1,
    ) -> DispatchSchedule:
        """Create planned dispatch schedule for an order."""
        order = self._order_repo.get_by_id(order_id)

        schedule = DispatchSchedule(
            schedule_number=schedule_number,
            order_id=order.id,
            planned_dispatch_time=planned_dispatch_time,
            planned_delivery_time=planned_delivery_time,
            planned_quantity_m3=planned_quantity_m3,
            sequence_number=sequence_number,
        )
        self._session.add(schedule)
        self._session.flush()
        logger.info("Dispatch schedule created", schedule_number=schedule_number, order_id=order_id)
        return schedule
