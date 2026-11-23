"""Unit test suite for WS-01.6 ServiceContainer, Bootstrap Engine & Lifecycle Manager."""

import pytest
from src.bootstrap import (
    HealthDiagnosticService,
    LifecycleManager,
    LifecycleState,
    PlatformBootstrapEngine,
    bootstrap_platform,
)
from src.configuration import FeatureFlagsSettings, PlatformPaths, PlatformSettings
from src.container import ServiceContainer, ServiceNotRegisteredException
from src.exceptions import ConfigurationException, InvalidConfigurationException


def test_service_container_singleton_and_factory() -> None:
    container = ServiceContainer()

    class DummyService:
        pass

    container.register_singleton(DummyService, DummyService())
    assert container.has(DummyService) is True
    assert isinstance(container.resolve(DummyService), DummyService)

    with pytest.raises(InvalidConfigurationException):
        container.register_singleton(DummyService, DummyService())


def test_missing_service_registration_rejection() -> None:
    container = ServiceContainer()

    class UnregisteredService:
        pass

    with pytest.raises(ServiceNotRegisteredException) as exc_info:
        container.resolve(UnregisteredService)
    assert "UnregisteredService" in str(exc_info.value)


def test_service_container_lazy_singleton_caching() -> None:
    container = ServiceContainer()
    calls = 0

    class LazyService:
        def __init__(self) -> None:
            nonlocal calls
            calls += 1

    container.register_singleton(LazyService, LazyService)
    assert calls == 0

    inst1 = container.resolve(LazyService)
    assert calls == 1

    inst2 = container.resolve(LazyService)
    assert calls == 1
    assert inst1 is inst2


def test_service_container_transient_factory_creation() -> None:
    container = ServiceContainer()

    class TransientService:
        pass

    container.register_factory(TransientService, TransientService)
    inst1 = container.resolve(TransientService)
    inst2 = container.resolve(TransientService)
    assert inst1 is not inst2


def test_service_container_circular_dependency_detection() -> None:
    container = ServiceContainer()

    class ServiceA:
        pass

    class ServiceB:
        pass

    def create_a() -> ServiceA:
        container.resolve(ServiceB)
        return ServiceA()

    def create_b() -> ServiceB:
        container.resolve(ServiceA)
        return ServiceB()

    container.register_factory(ServiceA, create_a)
    container.register_factory(ServiceB, create_b)

    with pytest.raises(ConfigurationException) as exc_info:
        container.resolve(ServiceA)
    assert exc_info.value.error_code == "ACC_CONTAINER_CIRCULAR_DEPENDENCY"
    assert "ServiceA -> ServiceB -> ServiceA" in str(exc_info.value)


def test_platform_bootstrap_sequence() -> None:
    container = bootstrap_platform()
    assert isinstance(container, ServiceContainer)
    assert container.has(PlatformSettings) is True
    assert container.has(PlatformPaths) is True
    assert container.has(FeatureFlagsSettings) is True
    assert container.has(HealthDiagnosticService) is True

    lifecycle = container.resolve(LifecycleManager)
    assert lifecycle.state == LifecycleState.RUNNING


def test_lifecycle_manager_transitions() -> None:
    lm = LifecycleManager()
    assert lm.state == LifecycleState.CREATED

    lm.set_state(LifecycleState.INITIALIZING)
    assert lm.state == LifecycleState.INITIALIZING

    lm.transition_to_running()
    assert lm.state == LifecycleState.RUNNING

    lm.shutdown()
    assert lm.state == LifecycleState.STOPPED
