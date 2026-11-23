"""Structlog Secret Redaction and Sensitive Data Masking Processor.

This module provides a robust, recursive processor for masking sensitive credentials,
tokens, passwords, and connection URIs in structlog event dictionaries.
"""

from typing import Any, Dict, List, Set, Union, Tuple
from src.shared.logging_constants import DEFAULT_SENSITIVE_KEYS


def _mask_value(val: Any, sensitive_keys: Set[str]) -> Any:
    """Recursively mask sensitive values in nested data structures."""
    try:
        if isinstance(val, dict):
            masked_dict: Dict[str, Any] = {}
            for k, v in val.items():
                if isinstance(k, str) and k.lower() in sensitive_keys:
                    masked_dict[k] = "[REDACTED]"
                else:
                    masked_dict[k] = _mask_value(v, sensitive_keys)
            return masked_dict
        elif isinstance(val, list):
            return [_mask_value(item, sensitive_keys) for item in val]
        elif isinstance(val, tuple):
            return tuple(_mask_value(item, sensitive_keys) for item in val)
        elif isinstance(val, set):
            return {_mask_value(item, sensitive_keys) for item in val}
        return val
    except Exception:
        # Guarantee logging safety: return original value if error occurs
        return val


def redact_sensitive_data_processor(
    logger: Any,
    method_name: str,
    event_dict: Dict[str, Any],
    custom_sensitive_keys: Union[Set[str], List[str], Tuple[str, ...], None] = None,
) -> Dict[str, Any]:
    """Structlog processor that recursively redacts sensitive fields in event_dict.

    Args:
        logger: Structlog logger instance.
        method_name: Log method name ('info', 'error', etc.).
        event_dict: Event context dictionary.
        custom_sensitive_keys: Optional set of additional sensitive keys to redact.

    Returns:
        Dict[str, Any]: Redacted event dictionary.
    """
    sensitive_keys = set(DEFAULT_SENSITIVE_KEYS)
    if custom_sensitive_keys:
        sensitive_keys.update({k.lower() for k in custom_sensitive_keys if isinstance(k, str)})

    return _mask_value(event_dict, sensitive_keys)
