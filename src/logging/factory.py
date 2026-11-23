"""Structlog Logger Factory Module.

This module provides the central `get_logger()` factory function returning bound logger
instances pre-tagged with component metadata.
"""

from typing import Optional
import structlog
from src.logging.config import VALID_COMPONENTS, configure_logging, is_logging_initialized


def get_logger(name: Optional[str] = None, component: Optional[str] = None) -> structlog.BoundLogger:
    """Return a structlog BoundLogger instance pre-configured for the platform.

    Args:
        name: Logger name (defaults to 'acc_rmc').
        component: Standardized component taxonomy tag (e.g. 'api', 'domain', 'ai').

    Returns:
        structlog.BoundLogger bound logger instance.
    """
    if not is_logging_initialized():
        configure_logging()

    logger_name = name if name is not None else "acc_rmc"
    logger = structlog.get_logger(logger_name)

    if component:
        comp = component.lower()
        if comp in VALID_COMPONENTS:
            logger = logger.bind(component=comp)
        else:
            logger = logger.bind(component=comp)

    return logger
