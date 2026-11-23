"""Application Lifecycle Manager and Platform Health Diagnostic Service.

This module manages platform lifecycle state transitions (CREATED, INITIALIZING, RUNNING,
SHUTTING_DOWN, STOPPED, FAILED) and provides integrated health diagnostic services.
"""

from enum import Enum
import threading
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.configuration import ComponentHealthStatus, PlatformHealthReport, run_platform_self_health_check
from src.container.service_container import ServiceContainer
from src.database import dispose_database_engine, get_database_health_status, validate_connection
from src.exceptions.technical import ConfigurationException, InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.bootstrap.lifecycle", component="services")


class LifecycleState(str, Enum):
    """Platform Application Lifecycle State Taxonomy."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class HealthDiagnosticService:
    """Integrated Platform Health Diagnostic Service."""

    def get_health_report(self, container: Optional[ServiceContainer] = None) -> PlatformHealthReport:
        """Run health check and return structured report including container and database readiness."""
        report = run_platform_self_health_check()

        # Database Engine Connection Probe
        db_healthy = validate_connection()
        report.components.append(
            ComponentHealthStatus(
                component="database_engine",
                status="OK" if db_healthy else "ERROR",
                details=get_database_health_status(),
            )
        )

        if container is not None:
            report.components.append(
                ComponentHealthStatus(
                    component="dependency_container",
                    status="OK",
                    details={"services_registered": True},
                )
            )

        if not db_healthy:
            report.overall_status = "UNHEALTHY"

        return report


class LifecycleManager:
    """Thread-safe Application Lifecycle Manager."""

    def __init__(self) -> None:
        self._state: LifecycleState = LifecycleState.CREATED
        self._lock: threading.Lock = threading.Lock()

    @property
    def state(self) -> LifecycleState:
        with self._lock:
            return self._state

    def set_state(self, new_state: LifecycleState) -> None:
        """Update lifecycle state and emit structured log."""
        with self._lock:
            old_state = self._state
            self._state = new_state
            logger.info("Lifecycle state transition", from_state=old_state.value, to_state=new_state.value)

    def transition_to_running(self) -> None:
        """Transition application lifecycle state to RUNNING."""
        self.set_state(LifecycleState.RUNNING)

    def transition_to_failed(self, error_message: str) -> None:
        """Transition application lifecycle state to FAILED."""
        with self._lock:
            self._state = LifecycleState.FAILED
            logger.error("Application lifecycle failure", error=error_message)

    def shutdown(self) -> None:
        """Perform graceful application shutdown and resource cleanup."""
        with self._lock:
            if self._state == LifecycleState.STOPPED:
                return
            logger.info("Initiating graceful shutdown and resource cleanup")
            self._state = LifecycleState.SHUTTING_DOWN

        # Graceful cleanup operations (disposing database connection pools)
        logger.info("Flushing log handlers and disposing registered container resources")
        dispose_database_engine()

        with self._lock:
            self._state = LifecycleState.STOPPED
            logger.info("Application shutdown complete")
