"""Database Models Package Init Module."""

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

from src.database.models.mapping_persistence import (
    SessionMappingModel,
    IngestionJobModel,
)
from src.master_data.models import DatasetTypeModel, TargetPlantModel
from src.mapping.models import ImportProfile, ImportColumnMapping
from src.database.models.user import (
    User,
    Role,
    UserRole,
    SecurityAuditLog,
)

__all__ = [
    "SessionMappingModel",
    "IngestionJobModel",
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
    "User",
    "OptimizationRun",
    "OptimizationCandidate",
    "Role",
    "UserRole",
    "SecurityAuditLog",
]

from src.database.models.cache import CacheToken, EventJournal

from src.database.models.optimization import OptimizationRun, OptimizationCandidate

from src.database.models.engineering_settings import EngineeringSettingsModel
__all__.append("EngineeringSettingsModel")
