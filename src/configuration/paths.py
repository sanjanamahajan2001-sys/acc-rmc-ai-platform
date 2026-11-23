"""Dynamic Platform Path Registry.

This module automatically determines the project root directory using pathlib and derives
all repository and runtime paths dynamically. Zero hardcoded paths.
"""

import os
from pathlib import Path
from typing import Dict, List


class PlatformPaths:
    """Dynamic Platform Path Registry.

    All paths derive dynamically from the project root (`Path(__file__).parents[2]`).
    """

    def __init__(self, root_override: Path | None = None) -> None:
        if root_override is not None:
            self._project_root = root_override.resolve()
        else:
            # Derived from src/configuration/paths.py -> 3 levels up to project root
            self._project_root = Path(__file__).resolve().parents[2]

    @property
    def project_root(self) -> Path:
        return self._project_root

    # Repository Source & Metadata Directories
    @property
    def config_dir(self) -> Path:
        return self._project_root / "config"

    @property
    def src_dir(self) -> Path:
        return self._project_root / "src"

    @property
    def tests_dir(self) -> Path:
        return self._project_root / "tests"

    @property
    def docs_dir(self) -> Path:
        return self._project_root / "docs"

    @property
    def scripts_dir(self) -> Path:
        return self._project_root / "scripts"

    @property
    def templates_dir(self) -> Path:
        return self._project_root / "templates"

    @property
    def static_dir(self) -> Path:
        return self._project_root / "static"

    @property
    def data_dir(self) -> Path:
        return self._project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self._project_root / "data" / "raw"

    @property
    def feature_store_dir(self) -> Path:
        return self._project_root / "data" / "feature_store"

    @property
    def datasets_dir(self) -> Path:
        return self._project_root / "data" / "datasets"

    # Runtime Subsystem Directories
    @property
    def runtime_dir(self) -> Path:
        return self._project_root / "runtime"

    @property
    def logs_dir(self) -> Path:
        return self._project_root / "runtime" / "logs"

    @property
    def uploads_dir(self) -> Path:
        return self._project_root / "runtime" / "uploads"

    @property
    def quarantine_dir(self) -> Path:
        return self._project_root / "runtime" / "quarantine"

    @property
    def exports_dir(self) -> Path:
        return self._project_root / "runtime" / "exports"

    @property
    def reports_dir(self) -> Path:
        return self._project_root / "runtime" / "reports"

    @property
    def cache_dir(self) -> Path:
        return self._project_root / "runtime" / "cache"

    @property
    def temp_dir(self) -> Path:
        return self._project_root / "runtime" / "temp"

    @property
    def backups_dir(self) -> Path:
        return self._project_root / "runtime" / "backups"

    @property
    def pid_dir(self) -> Path:
        return self._project_root / "runtime" / "pid"

    @property
    def sockets_dir(self) -> Path:
        return self._project_root / "runtime" / "sockets"

    @property
    def trained_models_dir(self) -> Path:
        return self._project_root / "runtime" / "trained_models"

    def get_all_runtime_directories(self) -> List[Path]:
        """Return list of all runtime directory paths."""
        return [
            self.runtime_dir,
            self.logs_dir,
            self.logs_dir / "app",
            self.logs_dir / "audit",
            self.logs_dir / "ai",
            self.logs_dir / "ingestion",
            self.logs_dir / "archive",
            self.uploads_dir,
            self.quarantine_dir,
            self.exports_dir,
            self.reports_dir,
            self.cache_dir,
            self.temp_dir,
            self.backups_dir,
            self.pid_dir,
            self.sockets_dir,
            self.trained_models_dir,
        ]

    def ensure_runtime_directories(self) -> None:
        """Idempotently create all runtime directories without deleting existing files."""
        for path in self.get_all_runtime_directories():
            os.makedirs(path, exist_ok=True)

    def to_dict(self) -> Dict[str, str]:
        """Return dictionary mapping of all path names to absolute path strings."""
        return {
            "project_root": str(self.project_root),
            "config_dir": str(self.config_dir),
            "src_dir": str(self.src_dir),
            "tests_dir": str(self.tests_dir),
            "docs_dir": str(self.docs_dir),
            "scripts_dir": str(self.scripts_dir),
            "templates_dir": str(self.templates_dir),
            "static_dir": str(self.static_dir),
            "data_dir": str(self.data_dir),
            "raw_data_dir": str(self.raw_data_dir),
            "feature_store_dir": str(self.feature_store_dir),
            "datasets_dir": str(self.datasets_dir),
            "runtime_dir": str(self.runtime_dir),
            "logs_dir": str(self.logs_dir),
            "uploads_dir": str(self.uploads_dir),
            "quarantine_dir": str(self.quarantine_dir),
            "exports_dir": str(self.exports_dir),
            "reports_dir": str(self.reports_dir),
            "cache_dir": str(self.cache_dir),
            "temp_dir": str(self.temp_dir),
            "backups_dir": str(self.backups_dir),
            "pid_dir": str(self.pid_dir),
            "sockets_dir": str(self.sockets_dir),
            "trained_models_dir": str(self.trained_models_dir),
        }
