"""Subsystem Settings Models.

This module defines strongly typed, immutable (frozen=True) subsystem settings models
for Application, Database, Logging, Security, Scheduler, AI, Import, Reporting,
Dashboard, FeatureFlags, and composed PlatformSettings using pydantic-settings.
"""

from enum import Enum
from pathlib import Path
from typing import ClassVar, List, Set
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from src.configuration.base import BasePlatformSettings, EnvironmentProfile, get_paths
from src.configuration.feature_flags import FeatureFlagsSettings


class DatabaseType(str, Enum):
    """Supported Platform Database Engines."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DuplicatePolicy(str, Enum):
    """Excel / Data Ingestion Duplicate Resolution Policies."""

    SKIP = "skip"
    OVERWRITE = "overwrite"
    QUARANTINE = "quarantine"
    ERROR = "error"


class ApplicationSettings(BaseSettings):
    """Application & Runtime Server Settings."""

    app_name: str = Field(default="ACC RMC AI Platform", description="Platform application name.")
    app_version: str = Field(default="0.1.0", description="Semantic platform version.")
    debug: bool = Field(default=False, description="Enable debug mode.")
    timezone: str = Field(default="UTC", description="System default timezone.")
    host: str = Field(default="0.0.0.0", description="Application bind host.")
    port: int = Field(default=8000, description="Application bind port.")
    workers: int = Field(default=4, description="Uvicorn / Server worker count.")
    default_language: str = Field(default="en", description="Default platform language.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class DatabaseSettings(BaseSettings):
    """Database & Persistence Layer Settings."""

    database_type: DatabaseType = Field(default=DatabaseType.SQLITE, description="Active database engine.")
    sqlite_path: str = Field(default="runtime/acc_rmc_dev.sqlite3", description="Relative SQLite DB file path.")
    postgresql_host: str = Field(default="localhost", description="PostgreSQL host address.")
    postgresql_port: int = Field(default=5432, description="PostgreSQL port.")
    postgresql_database: str = Field(default="acc_rmc_prod", description="PostgreSQL database name.")
    postgresql_username: str = Field(default="acc_user", description="PostgreSQL username.")
    postgresql_password: str = Field(default="change_me_in_prod", description="PostgreSQL password.")
    pool_size: int = Field(default=10, description="Connection pool size.")
    max_overflow: int = Field(default=20, description="Maximum pool overflow connections.")
    pool_timeout: int = Field(default=30, description="Connection pool timeout in seconds.")
    echo: bool = Field(default=False, description="Enable SQL query echo logging.")
    connection_retry_count: int = Field(default=3, description="Connection retry attempts.")
    connection_retry_delay: float = Field(default=2.0, description="Delay between retries in seconds.")

    @property
    def database_url(self) -> str:
        """Construct database DSN dynamically based on active database_type."""
        if self.database_type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.postgresql_username}:{self.postgresql_password}"
                f"@{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"
            )
        paths = get_paths()
        sqlite_file = paths.project_root / self.sqlite_path
        return f"sqlite:///{sqlite_file}"

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class LoggingSettings(BaseSettings):
    """Structured Logging Subsystem Settings."""

    log_level: str = Field(default="INFO", description="Logging output level.")
    console_logging: bool = Field(default=True, description="Enable console log handler.")
    json_logging: bool = Field(default=True, description="Enable JSON formatting.")
    audit_logging: bool = Field(default=True, description="Enable immutable audit log stream.")
    rotation_size_mb: int = Field(default=20, description="Rotating log file max size in MB.")
    backup_count: int = Field(default=10, description="Number of rotated log backups to retain.")
    enable_stack_traces: bool = Field(default=True, description="Render stack traces on exception.")
    enable_structlog: bool = Field(default=True, description="Use structlog processor engine.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class SecuritySettings(BaseSettings):
    """Authentication & Security Subsystem Settings."""

    jwt_secret_key: str = Field(default="CHANGE_ME_PRODUCTION_JWT_SECRET_32_CHARS_MIN", description="JWT HMAC secret key.")
    jwt_algorithm: str = Field(default="HS256", description="JWT signature algorithm.")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration in minutes.")
    refresh_token_expire_minutes: int = Field(default=10080, description="Refresh token expiration in minutes (7 days).")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:8000"], description="Allowed CORS origins.")
    allowed_hosts: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"], description="Allowed HTTP host headers.")
    secure_cookies: bool = Field(default=False, description="Enforce secure HTTPS cookies.")
    csrf_enabled: bool = Field(default=True, description="Enable CSRF protection.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class SchedulerSettings(BaseSettings):
    """Background Task Scheduler Subsystem Settings."""

    max_instances: int = Field(default=3, description="Max concurrent job instances.")
    coalesce: bool = Field(default=True, description="Coalesce missed job executions.")
    misfire_grace_time_sec: int = Field(default=60, description="Misfire grace period in seconds.")
    timezone: str = Field(default="UTC", description="Scheduler execution timezone.")
    scheduler_enabled: bool = Field(default=True, description="Enable background scheduler.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class AISettings(BaseSettings):
    """AI, Machine Learning & Optimization Subsystem Settings."""

    model_registry_dir: str = Field(default="runtime/trained_models", description="Relative ML model weights directory.")
    feature_store_dir: str = Field(default="data/feature_store", description="Relative feature store directory.")
    inference_batch_size: int = Field(default=64, description="ML inference batch size.")
    lp_tolerance: float = Field(default=1e-5, description="SLSQP linear programming optimizer tolerance.")
    drift_ks_alpha: float = Field(default=0.05, description="Kolmogorov-Smirnov data drift significance threshold.")
    default_model_version: str = Field(default="1.0.0", description="Default production ML model version.")
    prediction_timeout_sec: float = Field(default=10.0, description="Prediction calculation timeout in seconds.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class ImportSettings(BaseSettings):
    """Excel & SCADA Data Ingestion Subsystem Settings."""

    max_upload_size_mb: int = Field(default=50, description="Max file upload size in MB.")
    max_rows: int = Field(default=100000, description="Maximum allowed rows per import file.")
    max_columns: int = Field(default=200, description="Maximum allowed columns per import file.")
    chunk_size: int = Field(default=5000, description="Streaming row batch processing size.")
    duplicate_policy: DuplicatePolicy = Field(default=DuplicatePolicy.QUARANTINE, description="Duplicate Challan resolution policy.")
    quarantine_policy: str = Field(default="STRICT", description="Invalid row quarantine policy.")
    header_scan_depth: int = Field(default=15, description="Max top rows to scan for anchor headers.")
    template_detection_mode: str = Field(default="AUTO", description="FT7 template auto-detection mode.")
    allowed_extensions: List[str] = Field(default_factory=lambda: [".xlsx", ".xls", ".csv"], description="Allowed import file extensions.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class ReportingSettings(BaseSettings):
    """Export & PDF/Excel Reporting Subsystem Settings."""

    pdf_template_dir: str = Field(default="templates/pdf", description="Relative PDF template directory.")
    excel_template_dir: str = Field(default="templates/excel", description="Relative Excel template directory.")
    csv_export_encoding: str = Field(default="utf-8", description="Export CSV file encoding.")
    max_export_rows: int = Field(default=50000, description="Maximum allowed rows for report exports.")
    default_page_size: int = Field(default=50, description="Default report table page size.")
    export_timeout_sec: float = Field(default=30.0, description="Report generation timeout in seconds.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class DashboardSettings(BaseSettings):
    """Dashboard UI & Realtime API Settings."""

    refresh_interval_sec: int = Field(default=10, description="Dashboard widget polling interval.")
    cache_ttl_sec: int = Field(default=60, description="Dashboard widget cache TTL.")
    default_page_size: int = Field(default=25, description="Default dashboard grid page size.")
    max_export_rows: int = Field(default=10000, description="Max rows for dashboard grid exports.")
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket real-time updates.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


class PlatformSettings(BaseSettings):
    """Final Imposed Composition Settings Model combining all Subsystems. Immutable (frozen=True)."""

    base: BasePlatformSettings = Field(default_factory=BasePlatformSettings, description="Base platform settings.")
    app: ApplicationSettings = Field(default_factory=ApplicationSettings, description="Application settings.")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings.")
    logging: LoggingSettings = Field(default_factory=LoggingSettings, description="Logging settings.")
    security: SecuritySettings = Field(default_factory=SecuritySettings, description="Security settings.")
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings, description="Scheduler settings.")
    ai: AISettings = Field(default_factory=AISettings, description="AI settings.")
    ingestion: ImportSettings = Field(default_factory=ImportSettings, description="Ingestion settings.")
    reporting: ReportingSettings = Field(default_factory=ReportingSettings, description="Reporting settings.")
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings, description="Dashboard settings.")
    feature_flags: FeatureFlagsSettings = Field(default_factory=FeatureFlagsSettings, description="Feature flags settings.")

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")


_PLATFORM_SETTINGS_SINGLETON: PlatformSettings | None = None


def get_platform_settings() -> PlatformSettings:
    """Return singleton instance of composed PlatformSettings."""
    global _PLATFORM_SETTINGS_SINGLETON
    if _PLATFORM_SETTINGS_SINGLETON is None:
        _PLATFORM_SETTINGS_SINGLETON = PlatformSettings()
    return _PLATFORM_SETTINGS_SINGLETON
