"""Database Package Export Init File."""

from src.database.base import (
    GUID,
    AuditMetadataMixin,
    BaseModel,
    CreatedAtMixin,
    OptimisticLockMixin,
    SoftDeleteMixin,
    UUIDPrimaryKeyMixin,
    UpdatedAtMixin,
)
from src.database.dictionary import (
    CanonicalFieldDefinition,
    CanonicalFieldID,
    CanonicalFieldRegistry,
    get_canonical_dictionary,
    normalize_alias,
)
from src.database.engine import (
    create_database_engine,
    dispose_database_engine,
    get_database_engine,
)
from src.database.enums import (
    BatchStatusEnum,
    DriverStatusEnum,
    ImportStatusEnum,
    MaterialTypeEnum,
    OrderStatusEnum,
    QualityDispositionEnum,
    VehicleStatusEnum,
)
from src.database.health import get_database_health_status, validate_connection
from src.database.migration import MigrationService
from src.database.models.ai import (
    ActualOutcome,
    DriftSnapshot,
    FeatureVector,
    ModelRegistry,
    Prediction,
    PredictionAudit,
)
from src.database.models.audit import (
    AuditEvent,
    EntityChange,
    ImportHistory,
    SystemOperation,
)
from src.database.models.laboratory import (
    ConcreteSample,
    CubeSet,
    CubeTest,
    FT7Certificate,
    QualityObservation,
    SlumpTest,
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
from src.database.models.master import (
    Customer,
    DriverCategory,
    Material,
    MaterialCategory,
    Plant,
    Project,
    Recipe,
    RecipeMaterial,
    Supplier,
    VehicleType,
)
from src.database.models.orders import (
    DispatchAllocation,
    DispatchSchedule,
    Order,
    OrderLineItem,
)
from src.database.models.production import (
    Batch,
    BatchMaterialConsumption,
    ProductionEvent,
    WeighingLog,
)
from src.database.models.views import (
    AuditActivityView,
    BatchSummaryView,
    MaterialConsumptionSummaryView,
    PredictionSummaryView,
    QualitySummaryView,
)
from src.database.repositories.ai_repository import AIRepository
from src.database.repositories.audit_repository import AuditRepository
from src.database.repositories.database_validation_repository import DatabaseValidationRepository
from src.database.repositories.laboratory_repository import LaboratoryRepository
from src.database.repositories.lookup_repository import LookupRepository
from src.database.repositories.master_repository import MasterRepository
from src.database.repositories.order_repository import OrderRepository
from src.database.repositories.production_repository import ProductionRepository
from src.database.repositories.reporting_repository import ReportingRepository
from src.database.seeds import seed_lookup_tables
from src.database.services.ai_metadata_service import AIMetadataService
from src.database.services.audit_persistence_service import AuditPersistenceService
from src.database.services.database_validation_service import DatabaseValidationService
from src.database.services.laboratory_service import LaboratoryService
from src.database.services.master_reference_service import MasterReferenceService
from src.database.services.order_service import OrderService
from src.database.services.production_service import ProductionService
from src.database.services.reporting_service import ReportingService
from src.database.session import (
    get_db_session,
    get_read_only_session,
    get_session_factory,
)
from src.database.types import DataTypeCategory, EngineeringUnit, SourceSystem, UnitDefinition
from src.database.units import get_unit_definition
from src.database.validation import (
    DatabaseValidationReport,
    validate_database_constraints,
    validate_database_indexes,
    validate_database_integrity,
    validate_database_schema,
    validate_database_seed_data,
    validate_database_views,
)
from src.database.validators import ValidationRuleMetadata

__all__ = [
    "BaseModel",
    "GUID",
    "UUIDPrimaryKeyMixin",
    "CreatedAtMixin",
    "UpdatedAtMixin",
    "SoftDeleteMixin",
    "OptimisticLockMixin",
    "AuditMetadataMixin",
    "create_database_engine",
    "get_database_engine",
    "dispose_database_engine",
    "get_session_factory",
    "get_db_session",
    "get_read_only_session",
    "validate_connection",
    "get_database_health_status",
    "MigrationService",
    "EngineeringUnit",
    "DataTypeCategory",
    "SourceSystem",
    "UnitDefinition",
    "get_unit_definition",
    "ValidationRuleMetadata",
    "CanonicalFieldID",
    "CanonicalFieldDefinition",
    "CanonicalFieldRegistry",
    "get_canonical_dictionary",
    "normalize_alias",
    "BatchStatusEnum",
    "OrderStatusEnum",
    "QualityDispositionEnum",
    "MaterialTypeEnum",
    "VehicleStatusEnum",
    "DriverStatusEnum",
    "ImportStatusEnum",
    "BaseLookupTable",
    "BatchStatusLookup",
    "OrderStatusLookup",
    "QualityDispositionLookup",
    "MaterialTypeLookup",
    "VehicleStatusLookup",
    "DriverStatusLookup",
    "ImportStatusLookup",
    "Plant",
    "Customer",
    "Project",
    "Supplier",
    "MaterialCategory",
    "Material",
    "Recipe",
    "RecipeMaterial",
    "VehicleType",
    "DriverCategory",
    "Order",
    "OrderLineItem",
    "DispatchSchedule",
    "DispatchAllocation",
    "Batch",
    "BatchMaterialConsumption",
    "WeighingLog",
    "ProductionEvent",
    "ConcreteSample",
    "SlumpTest",
    "CubeSet",
    "CubeTest",
    "FT7Certificate",
    "QualityObservation",
    "FeatureVector",
    "Prediction",
    "ActualOutcome",
    "ModelRegistry",
    "PredictionAudit",
    "DriftSnapshot",
    "AuditEvent",
    "EntityChange",
    "ImportHistory",
    "SystemOperation",
    "BatchSummaryView",
    "MaterialConsumptionSummaryView",
    "QualitySummaryView",
    "PredictionSummaryView",
    "AuditActivityView",
    "seed_lookup_tables",
    "LookupRepository",
    "MasterRepository",
    "OrderRepository",
    "ProductionRepository",
    "LaboratoryRepository",
    "AIRepository",
    "AuditRepository",
    "ReportingRepository",
    "DatabaseValidationRepository",
    "MasterReferenceService",
    "OrderService",
    "ProductionService",
    "LaboratoryService",
    "AIMetadataService",
    "AuditPersistenceService",
    "ReportingService",
    "DatabaseValidationService",
    "DatabaseValidationReport",
    "validate_database_schema",
    "validate_database_indexes",
    "validate_database_constraints",
    "validate_database_views",
    "validate_database_seed_data",
    "validate_database_integrity",
]
