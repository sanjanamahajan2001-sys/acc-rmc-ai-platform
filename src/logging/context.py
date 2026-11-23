"""Thread-Local and Async Context Propagation Engine.

This module provides utilities to bind, unbind, clear, and inspect structured logging
context across multithreaded and async execution contexts using structlog contextvars.
"""

import json
from typing import Any, Dict
import structlog


def _is_json_serializable(val: Any) -> bool:
    """Check if a value is JSON serializable."""
    try:
        json.dumps(val)
        return True
    except (TypeError, OverflowError):
        return False


def bind_log_context(**kwargs: Any) -> None:
    """Bind key-value pairs to the current thread/async context.

    Args:
        **kwargs: Key-value pairs to bind to logging context.

    Raises:
        TypeError: If a key is not a string.
        ValueError: If a value is not JSON serializable.
    """
    to_bind: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if not isinstance(k, str):
            raise TypeError(f"Log context key must be a string, got {type(k).__name__}")
        if v is not None and not _is_json_serializable(v):
            raise ValueError(f"Log context value for key '{k}' must be JSON serializable, got {type(v).__name__}")
        to_bind[k] = v

    structlog.contextvars.bind_contextvars(**to_bind)


def unbind_log_context(*keys: str) -> None:
    """Remove specified keys from current thread/async logging context."""
    for k in keys:
        if not isinstance(k, str):
            raise TypeError(f"Log context key must be a string, got {type(k).__name__}")
    structlog.contextvars.unbind_contextvars(*keys)


def clear_log_context() -> None:
    """Clear all bound context variables for the current thread/async context."""
    structlog.contextvars.clear_contextvars()


def get_log_context() -> Dict[str, Any]:
    """Retrieve current thread/async active logging context dictionary."""
    return structlog.contextvars.get_contextvars()
