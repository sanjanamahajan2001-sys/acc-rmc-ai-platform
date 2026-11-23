"""Deterministic Idempotent Seed Data Generator.

This module populates normalized lookup tables with production-grade enterprise reference data.
"""

from typing import Dict, List, Type
from sqlalchemy.orm import Session
from src.database.enums import (
    BatchStatusEnum,
    DriverStatusEnum,
    ImportStatusEnum,
    MaterialTypeEnum,
    OrderStatusEnum,
    QualityDispositionEnum,
    VehicleStatusEnum,
)
from src.database.models.lookups import (
    BaseLookupTable,
    BatchStatusLookup,
    DriverStatusLookup,
    ImportStatusLookup,
    MaterialTypeLookup,
    OrderStatusLookup,
    QualityDispositionLookup,
    VehicleStatusLookup,
)
from src.logging import get_logger

logger = get_logger("src.database.seeds", component="database")


SEED_DATA: Dict[Type[BaseLookupTable], List[Dict[str, str]]] = {
    BatchStatusLookup: [
        {"code": BatchStatusEnum.PLANNED.value, "name": "Planned", "description": "Batch scheduled for production."},
        {"code": BatchStatusEnum.BATCHING.value, "name": "Batching", "description": "Batch actively weighing/mixing."},
        {"code": BatchStatusEnum.COMPLETED.value, "name": "Completed", "description": "Batching finished successfully."},
        {"code": BatchStatusEnum.REJECTED.value, "name": "Rejected", "description": "Batch rejected during QA inspection."},
        {"code": BatchStatusEnum.CANCELLED.value, "name": "Cancelled", "description": "Batch cancelled prior to mixing."},
    ],
    OrderStatusLookup: [
        {"code": OrderStatusEnum.DRAFT.value, "name": "Draft", "description": "Order draft creation."},
        {"code": OrderStatusEnum.CONFIRMED.value, "name": "Confirmed", "description": "Order confirmed by customer."},
        {"code": OrderStatusEnum.IN_PROGRESS.value, "name": "In Progress", "description": "Order actively producing/delivering."},
        {"code": OrderStatusEnum.DELIVERED.value, "name": "Delivered", "description": "Order fully delivered."},
        {"code": OrderStatusEnum.CANCELLED.value, "name": "Cancelled", "description": "Order cancelled."},
    ],
    QualityDispositionLookup: [
        {"code": QualityDispositionEnum.PENDING.value, "name": "Pending", "description": "Awaiting lab strength test results."},
        {"code": QualityDispositionEnum.ACCEPTED.value, "name": "Accepted", "description": "Meets IS 456 target strength criteria."},
        {"code": QualityDispositionEnum.REJECTED.value, "name": "Rejected", "description": "Fails IS 456 minimum strength criteria."},
        {"code": QualityDispositionEnum.CONDITIONAL.value, "name": "Conditional", "description": "Accepted under concession agreement."},
    ],
    MaterialTypeLookup: [
        {"code": MaterialTypeEnum.CEMENT.value, "name": "Cement", "description": "OPC / PPC Cement Binder."},
        {"code": MaterialTypeEnum.AGGREGATE_COARSE.value, "name": "Coarse Aggregate", "description": "20mm / 10mm Coarse Aggregate."},
        {"code": MaterialTypeEnum.AGGREGATE_FINE.value, "name": "Fine Aggregate", "description": "Crushed Sand / River Sand."},
        {"code": MaterialTypeEnum.ADMIXTURE.value, "name": "Chemical Admixture", "description": "Plasticizer / Retarder."},
        {"code": MaterialTypeEnum.WATER.value, "name": "Mixing Water", "description": "Batching Water."},
        {"code": MaterialTypeEnum.FLY_ASH.value, "name": "Fly Ash", "description": "Pozzolanic Cement Substitute."},
    ],
}


def seed_lookup_tables(session: Session) -> None:
    """Seed all enterprise lookup tables idempotently."""
    logger.info("Starting deterministic lookup table seed execution")

    for model_cls, items in SEED_DATA.items():
        for order, item in enumerate(items, start=1):
            code = item["code"]
            existing = session.query(model_cls).filter_by(code=code).first()
            if existing is None:
                record = model_cls(
                    code=code,
                    name=item["name"],
                    description=item.get("description"),
                    display_order=order,
                    is_active=True,
                )
                session.add(record)
                logger.info("Seeded lookup record", model=model_cls.__name__, code=code)

    session.commit()
    logger.info("Lookup table seed execution completed successfully")
