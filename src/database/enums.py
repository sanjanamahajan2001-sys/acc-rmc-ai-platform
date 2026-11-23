"""Enterprise Database Enumerations.

This module provides strongly typed Python Enum classes matching database lookup codes
to eliminate magic strings across the ACC RMC AI Platform.
"""

from enum import Enum


class BatchStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    BATCHING = "BATCHING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OrderStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class QualityDispositionEnum(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"


class MaterialTypeEnum(str, Enum):
    CEMENT = "CEMENT"
    AGGREGATE_COARSE = "AGGREGATE_COARSE"
    AGGREGATE_FINE = "AGGREGATE_FINE"
    ADMIXTURE = "ADMIXTURE"
    WATER = "WATER"
    FLY_ASH = "FLY_ASH"
    GGBS = "GGBS"
    SILICA_FUME = "SILICA_FUME"


class VehicleStatusEnum(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class DriverStatusEnum(str, Enum):
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    DRIVING = "DRIVING"
    SUSPENDED = "SUSPENDED"


class ImportStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
