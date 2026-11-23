"""Logging Constants Module.

This module defines central logging constants, default sensitive key registries,
and component taxonomies shared across the platform.
"""

from typing import Set

DEFAULT_SENSITIVE_KEYS: Set[str] = {
    "password",
    "passwd",
    "secret",
    "token",
    "jwt",
    "access_token",
    "refresh_token",
    "authorization",
    "auth_header",
    "cookie",
    "api_key",
    "client_secret",
    "private_key",
    "connection_string",
    "db_uri",
    "database_url",
    "smtp_password",
    "aws_secret_access_key",
    "azure_client_secret",
    "gcp_credentials",
}
