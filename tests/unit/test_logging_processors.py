"""Unit test suite for WS-01.4C Secret Redaction Processor & Log Rotation Handlers."""

import logging
from logging.handlers import RotatingFileHandler
import os
from src.logging import (
    DEFAULT_SENSITIVE_KEYS,
    configure_logging,
    get_logger,
    is_logging_initialized,
    redact_sensitive_data_processor,
)


def test_sensitive_keys_registry() -> None:
    assert "password" in DEFAULT_SENSITIVE_KEYS
    assert "token" in DEFAULT_SENSITIVE_KEYS
    assert "jwt" in DEFAULT_SENSITIVE_KEYS
    assert "db_uri" in DEFAULT_SENSITIVE_KEYS
    assert "api_key" in DEFAULT_SENSITIVE_KEYS


def test_redact_sensitive_data_processor() -> None:
    event_dict = {
        "user": "sanjana",
        "PASSWORD": "SuperSecretPassword123",
        "token": "bearer-xyz",
        "nested": {
            "db_uri": "postgresql://user:pass@localhost/db",
            "safe_field": "keep_this",
        },
        "list_data": [{"api_key": "key-123", "normal": 42}],
        "tuple_data": ({"client_secret": "sec-456"}, "item"),
    }

    res = redact_sensitive_data_processor(None, "info", event_dict)

    assert res["user"] == "sanjana"
    assert res["PASSWORD"] == "[REDACTED]"
    assert res["token"] == "[REDACTED]"
    assert res["nested"]["db_uri"] == "[REDACTED]"
    assert res["nested"]["safe_field"] == "keep_this"
    assert res["list_data"][0]["api_key"] == "[REDACTED]"
    assert res["list_data"][0]["normal"] == 42
    assert res["tuple_data"][0]["client_secret"] == "[REDACTED]"


def test_rotating_file_handlers_configuration() -> None:
    root_logger = logging.getLogger()
    handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(handlers) >= 3

    for h in handlers:
        assert h.maxBytes == 20 * 1024 * 1024
        assert h.backupCount == 10
        assert h.encoding == "utf-8"
