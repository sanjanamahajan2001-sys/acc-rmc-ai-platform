"""Order Data Access Repository.

This module provides data access methods for Order entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models.orders import Order
from src.exceptions.domain import EntityNotFoundException


class OrderRepository:
    """Data Access Repository for Order Entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, order_id: str) -> Order:
        """Retrieve order by UUID."""
        record = self._session.query(Order).filter_by(id=order_id).first()
        if record is None:
            raise EntityNotFoundException(entity_name="Order", entity_id=order_id)
        return record

    def get_by_order_number(self, order_number: str) -> Order:
        """Retrieve order by unique order_number."""
        record = self._session.query(Order).filter_by(order_number=order_number).first()
        if record is None:
            raise EntityNotFoundException(entity_name="Order", entity_id=order_number)
        return record

    def create(self, order: Order) -> Order:
        """Add new order to session."""
        self._session.add(order)
        self._session.flush()
        return order

    def update(self, order: Order) -> Order:
        """Flush order updates."""
        self._session.flush()
        return order

    def cancel(self, order_id: str) -> Order:
        """Soft delete / cancel order."""
        order = self.get_by_id(order_id)
        order.is_deleted = True
        self._session.flush()
        return order

    def list_by_customer(self, customer_id: str) -> List[Order]:
        """List orders by customer ID."""
        return self._session.query(Order).filter_by(customer_id=customer_id, is_deleted=False).all()

    def list_by_project(self, project_id: str) -> List[Order]:
        """List orders by project ID."""
        return self._session.query(Order).filter_by(project_id=project_id, is_deleted=False).all()

    def list_by_status(self, order_status_id: str) -> List[Order]:
        """List orders by status ID."""
        return self._session.query(Order).filter_by(order_status_id=order_status_id, is_deleted=False).all()

    def exists_order_number(self, order_number: str) -> bool:
        """Check if order number exists."""
        return self._session.query(Order.id).filter_by(order_number=order_number).first() is not None
