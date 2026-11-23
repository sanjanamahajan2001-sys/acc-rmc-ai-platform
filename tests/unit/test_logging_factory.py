"""Unit test suite for WS-01.4A Structlog Logger Factory & Directory Initialization."""

import os
import structlog
from src.logging import (
    VALID_COMPONENTS,
    configure_logging,
    ensure_runtime_log_directories,
    get_logger,
    is_logging_initialized,
)


def test_runtime_directory_initialization() -> None:
    ensure_runtime_log_directories()
    base = "/home/sanjana/acc-rmc-ai-platform/runtime/logs"
    assert os.path.exists(os.path.join(base, "app")) is True
    assert os.path.exists(os.path.join(base, "audit")) is True
    assert os.path.exists(os.path.join(base, "ai")) is True
    assert os.path.exists(os.path.join(base, "ingestion")) is True
    assert os.path.exists(os.path.join(base, "archive")) is True


def test_logger_factory_and_singleton() -> None:
    configure_logging(environment="development")
    assert is_logging_initialized() is True

    logger = get_logger("test_module", component="domain")
    assert isinstance(logger, structlog.stdlib.BoundLogger)


def test_component_taxonomy() -> None:
    assert "api" in VALID_COMPONENTS
    assert "domain" in VALID_COMPONENTS
    assert "ai" in VALID_COMPONENTS
    assert "ingestion" in VALID_COMPONENTS


def test_logger_component_tagging() -> None:
    logger = get_logger("batch_service", component="services")
    bound_logger = logger.bind(batch_id="B-999")
    assert bound_logger._context.get("batch_id") == "B-999"
