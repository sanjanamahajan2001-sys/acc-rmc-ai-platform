"""Platform Bootstrap Orchestrator Engine.

This module provides the central `bootstrap_platform()` orchestration function executing the
strict 9-step startup sequence before application boot.
"""

from typing import Optional
from src.bootstrap.lifecycle import HealthDiagnosticService, LifecycleManager, LifecycleState
from src.configuration import (
    BasePlatformSettings,
    FeatureFlagsSettings,
    PlatformPaths,
    PlatformSettings,
    get_base_settings,
    get_feature_flags,
    get_paths,
    get_platform_settings,
    validate_platform_configuration,
)
from src.container import ServiceContainer
from src.database import MigrationService, dispose_database_engine, get_database_engine, get_session_factory
from src.exceptions.technical import ConfigurationException
from src.logging import (
    configure_logging,
    get_audit_logger,
    get_logger,
    is_logging_initialized,
)

logger = get_logger("src.bootstrap.engine", component="services")


class PlatformBootstrapEngine:
    """Platform Bootstrap Orchestrator."""

    def __init__(self, container: Optional[ServiceContainer] = None) -> None:
        self._container = container if container is not None else ServiceContainer()
        self._lifecycle = LifecycleManager()

    @property
    def container(self) -> ServiceContainer:
        return self._container

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

    def bootstrap(self, environment_override: Optional[str] = None) -> ServiceContainer:
        """Execute strict 9-step platform bootstrap sequence.

        Sequence:
            1. Load configuration
            2. Validate configuration
            3. Configure logging
            4. Initialize dependency container
            5. Register services (including DB engine & MigrationService)
            6. Initialize runtime directories
            7. Initialize scheduler configuration
            8. Register health services
            9. Produce startup health report
        """
        try:
            self._lifecycle.set_state(LifecycleState.INITIALIZING)
            logger.info("Bootstrap sequence started")

            # Step 1: Load Configuration
            platform_settings = get_platform_settings()
            paths = get_paths()
            logger.info("Configuration loaded", environment=platform_settings.base.environment.value)

            # Step 2: Validate Configuration
            validate_platform_configuration(platform_settings)

            # Step 3: Configure Logging
            if not is_logging_initialized():
                configure_logging(
                    environment=platform_settings.base.environment.value,
                    log_level=platform_settings.logging.log_level,
                )

            # Step 4 & 5: Initialize Container & Register Core Services
            self._container.clear()
            self._container.register_singleton(PlatformSettings, platform_settings)
            self._container.register_singleton(PlatformPaths, paths)
            self._container.register_singleton(FeatureFlagsSettings, get_feature_flags())
            self._container.register_singleton(HealthDiagnosticService, HealthDiagnosticService())
            self._container.register_singleton(LifecycleManager, self._lifecycle)

            # Register Database Infrastructure & Migration Services in Container
            engine = get_database_engine(settings=platform_settings)
            session_factory = get_session_factory(engine=engine)
            migration_service = MigrationService()

            self._container.register_singleton(type(engine), engine)
            self._container.register_singleton(type(session_factory), session_factory)
            self._container.register_singleton(MigrationService, migration_service)

            logger.info("Core DI container, Database & Migration services registered successfully")

            # Step 6: Initialize Runtime Directories
            paths.ensure_runtime_directories()

            # Step 7 & 8: Scheduler config & Health Services
            health_service = self._container.resolve(HealthDiagnosticService)

            # Step 9: Startup Health Report
            health_report = health_service.get_health_report(container=self._container)
            if health_report.overall_status != "HEALTHY":
                raise ConfigurationException(
                    message="Startup self-health check failed.",
                    error_code="ACC_BOOTSTRAP_HEALTH_FAILED",
                )

            self._lifecycle.transition_to_running()
            logger.info("Bootstrap completed successfully", environment=platform_settings.base.environment.value)
            return self._container
        except Exception as err:
            self._lifecycle.transition_to_failed(str(err))
            logger.error("Bootstrap sequence failed", error=str(err))
            if isinstance(err, ConfigurationException):
                raise
            raise ConfigurationException(
                message=f"Platform bootstrap failed: {err}",
                error_code="ACC_BOOTSTRAP_FAILURE",
            ) from err


def bootstrap_platform(environment_override: Optional[str] = None) -> ServiceContainer:
    """Bootstrap the platform and return initialized ServiceContainer."""
    engine = PlatformBootstrapEngine()
    return engine.bootstrap(environment_override=environment_override)
