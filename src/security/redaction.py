"""Centralized Secret & Sensitive Credential Redaction.

Ensures sensitive values (passwords, tokens, hashes, API keys) are scrubbed from
application logs, exception strings, audit entries, and telemetry.
"""

import re
from typing import Any, Dict, List, Union
from src.security.config import config

REDACTED_LABEL = "[REDACTED]"

# Regex pattern for bearer tokens and sensitive URL/header formats
BEARER_PATTERN = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]+", re.IGNORECASE)
JWT_PATTERN = re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*")


def redact_sensitive_dict(data: Any) -> Any:
    """Recursively redact sensitive keys from dictionaries, lists, and primitives.

    Args:
        data: The input structure (dict, list, or primitive).

    Returns:
        A deep copy of the structure with sensitive field values replaced with '[REDACTED]'.
    """
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            key_str = str(key).lower()
            if any(sensitive in key_str for sensitive in config.REDACTION_KEYS):
                cleaned[key] = REDACTED_LABEL
            else:
                cleaned[key] = redact_sensitive_dict(value)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_dict(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_sensitive_dict(item) for item in data)
    elif isinstance(data, str):
        return redact_sensitive_string(data)
    else:
        return data


def redact_sensitive_string(text: str) -> str:
    """Scrub tokens, bearer credentials, and potential secrets from a raw string.

    Args:
        text: The string to scrub.

    Returns:
        The sanitized string.
    """
    if not isinstance(text, str):
        return str(text)

    # Redact Bearer headers
    sanitized = BEARER_PATTERN.sub(r"\1[REDACTED_TOKEN]", text)

    # Redact raw JWT tokens
    sanitized = JWT_PATTERN.sub("[REDACTED_JWT]", sanitized)

    return sanitized
