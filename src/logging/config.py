from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
"""Structlog Configuration and Initialization Module.

This module provides centralized, idempotent logger initialization for development
(colored console) and production (ISO 8601 UTC JSON) environments, creating
segregated runtime logging directories, rotating log handlers, and structlog processor pipelines.
"""

import logging
from logging.handlers import RotatingFileHandler

def _get_default_base_dir() -> str:
    env_dir = os.environ.get("BASE_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir
    # Auto-detect from file location (src/logging/... -> root)
    detected = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.exists(detected):
        return detected
    return "/opt/apps/acc-rmc-ai-platform" if os.path.exists("/opt/apps/acc-rmc-ai-platform") else "/home/sanjana/acc-rmc-ai-platform"

import os
import sys
from typing import Any, List
import structlog
from src.logging.processors import redact_sensitive_data_processor


# Standardized Platform Component Taxonomy
VALID_COMPONENTS = {
    "api",
    "services",
    "domain",
    "database",
    "repositories",
    "connectors",
    "parsers",
    "ingestion",
    "dashboard",
    "reporting",
    "scheduler",
    "events",
    "authentication",
    "authorization",
    "ai",
    "ml",
    "training",
    "optimizer",
    "utilities",
    "configuration",
    "logging",
}

_INITIALIZED: bool = False


def ensure_runtime_log_directories(base_dir: Optional[str] = None) -> None:
    """Idempotently create segregated runtime logging directories if missing."""
    if not base_dir:
        base_dir = _get_default_base_dir()
    log_dirs = [
        os.path.join(base_dir, "runtime", "logs"),
        os.path.join(base_dir, "runtime", "logs", "app"),
        os.path.join(base_dir, "runtime", "logs", "audit"),
        os.path.join(base_dir, "runtime", "logs", "ai"),
        os.path.join(base_dir, "runtime", "logs", "ingestion"),
        os.path.join(base_dir, "runtime", "logs", "archive"),
    ]
    for d in log_dirs:
        os.makedirs(d, exist_ok=True)


def configure_logging(
    environment: str = "development",
    log_level: str = "INFO",
    base_dir: Optional[str] = None,
) -> None:
    if not base_dir:
        base_dir = _get_default_base_dir()
    """Initialize central structlog configuration and rotating log file handlers."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    ensure_runtime_log_directories(base_dir=base_dir)

    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 2. Segregated Rotating File Handlers (20 MB max, 10 backups, UTF-8)
    max_bytes = 20 * 1024 * 1024  # 20 MB
    backup_count = 10

    app_log_path = os.path.join(base_dir, "runtime", "logs", "app", "app.log")
    ai_log_path = os.path.join(base_dir, "runtime", "logs", "ai", "ai.log")
    ingestion_log_path = os.path.join(base_dir, "runtime", "logs", "ingestion", "ingestion.log")

    app_file_handler = RotatingFileHandler(
        app_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    ai_file_handler = RotatingFileHandler(
        ai_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    ingestion_file_handler = RotatingFileHandler(
        ingestion_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )

    shared_processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        redact_sensitive_data_processor,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment.lower() == "production":
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    for handler in [console_handler, app_file_handler, ai_file_handler, ingestion_file_handler]:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    _INITIALIZED = True


def is_logging_initialized() -> bool:
    """Check whether logging has been initialized."""
    return _INITIALIZED
