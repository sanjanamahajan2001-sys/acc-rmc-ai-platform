"""Strongly Typed Service Container Engine.

This module provides a thread-safe dependency injection container supporting singleton
and factory service registrations, circular dependency detection, lazy initialization,
and missing service detection.
"""

import threading
from typing import Any, Callable, Dict, List, Set, Type, TypeVar
from src.exceptions.technical import ConfigurationException, InvalidConfigurationException

T = TypeVar("T")


class ServiceNotRegisteredException(InvalidConfigurationException):
    """Raised when an unregistered service type is requested from container."""

    def __init__(self, service_name: str) -> None:
        super().__init__(
            parameter_name="service_type",
            message=f"Service '{service_name}' is not registered in container.",
        )


class ServiceContainer:
    """Thread-safe Dependency Injection Container."""

    def __init__(self) -> None:
        self._singletons: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[..., Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}
        self._resolving_stack: List[Type[Any]] = []
        self._lock: threading.Lock = threading.Lock()

    def register_singleton(self, service_type: Type[T], instance_or_factory: T | Callable[..., T]) -> None:
        """Register a singleton service instance or lazy factory function.

        Raises:
            InvalidConfigurationException: If duplicate registration is attempted.
        """
        with self._lock:
            if service_type in self._singletons or service_type in self._factories:
                raise InvalidConfigurationException(
                    parameter_name="service_type",
                    message=f"Duplicate registration for service '{service_type.__name__}'.",
                )
            if callable(instance_or_factory) and not isinstance(instance_or_factory, type):
                self._singletons[service_type] = instance_or_factory
            else:
                self._singletons[service_type] = instance_or_factory
                self._instances[service_type] = instance_or_factory

    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for transient service creation.

        Raises:
            InvalidConfigurationException: If duplicate registration is attempted or factory is not callable.
        """
        with self._lock:
            if service_type in self._singletons or service_type in self._factories:
                raise InvalidConfigurationException(
                    parameter_name="service_type",
                    message=f"Duplicate registration for service '{service_type.__name__}'.",
                )
            if not callable(factory):
                raise InvalidConfigurationException(
                    parameter_name="factory",
                    message=f"Factory for service '{service_type.__name__}' must be callable.",
                )
            self._factories[service_type] = factory

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance by type.

        Raises:
            ServiceNotRegisteredException: If service is unregistered.
            ConfigurationException: If a circular dependency resolution is detected.
        """
        with self._lock:
            if service_type in self._resolving_stack:
                chain = " -> ".join([t.__name__ for t in self._resolving_stack] + [service_type.__name__])
                raise ConfigurationException(
                    message=f"Circular dependency detected resolving service chain: {chain}",
                    error_code="ACC_CONTAINER_CIRCULAR_DEPENDENCY",
                )

            # Check cached singleton instances first
            if service_type in self._instances:
                return self._instances[service_type]

            # Check singleton factories
            if service_type in self._singletons:
                self._resolving_stack.append(service_type)
                try:
                    target = self._singletons[service_type]
                    if callable(target) and not isinstance(target, type):
                        instance = target()
                    else:
                        instance = target
                    self._instances[service_type] = instance
                    return instance
                finally:
                    self._resolving_stack.pop()

            # Check transient factories
            if service_type in self._factories:
                self._resolving_stack.append(service_type)
                try:
                    factory = self._factories[service_type]
                    return factory()
                finally:
                    self._resolving_stack.pop()

            raise ServiceNotRegisteredException(service_type.__name__)

    def has(self, service_type: Type[Any]) -> bool:
        """Check whether a service type is registered."""
        with self._lock:
            return service_type in self._singletons or service_type in self._factories

    def remove(self, service_type: Type[Any]) -> None:
        """Remove a service registration from the container."""
        with self._lock:
            self._singletons.pop(service_type, None)
            self._factories.pop(service_type, None)
            self._instances.pop(service_type, None)

    def clear(self) -> None:
        """Clear all registered services and cached instances."""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
            self._instances.clear()
            self._resolving_stack.clear()
