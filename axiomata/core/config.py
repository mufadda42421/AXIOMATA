"""Application configuration: paths, data directory layout, and settings access.

The data directory is created outside the installation directory so user data
survives reinstalls and updates. The default location follows the platform
convention (e.g. ``%APPDATA%\\AXIOMATA`` on Windows) and can be overridden via
the ``AXIOMATA_DATA`` environment variable or through Settings in the app.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_NAME = "AXIOMATA"


def _default_data_root() -> Path:
    """Return the platform-appropriate default root for persistent user data."""
    override = os.environ.get("AXIOMATA_DATA")
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    # Linux / other
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


class AppPaths:
    """Resolves and lazily creates the on-disk layout for AXIOMATA data."""

    def __init__(self, root: Path | None = None) -> None:
        self.root: Path = Path(root) if root else _default_data_root()
        self.database = self.root / "database"
        self.backups = self.database / "backups"
        self.sqlite_path = self.database / "axiomata.sqlite"
        self.duckdb_path = self.database / "scientific.duckdb"
        self.projects = self.root / "projects"
        self.library = self.root / "library"
        self.cache = self.root / "cache"
        self.logs = self.root / "logs"
        self.settings_dir = self.root / "settings"

    def ensure(self) -> None:
        """Create all required directories if they do not yet exist."""
        for path in (
            self.root,
            self.database,
            self.backups,
            self.projects,
            self.library,
            self.cache,
            self.logs,
            self.settings_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        """Return (and create) the directory tree for a single project."""
        base = self.projects / project_id
        for sub in (
            "",
            "experiments",
            "datasets",
            "simulations",
            "notebooks",
            "exports",
            "assets",
        ):
            (base / sub).mkdir(parents=True, exist_ok=True)
        return base


class Settings:
    """Lightweight JSON-backed key/value settings store."""

    _DEFAULTS: dict[str, Any] = {
        "profession": None,  # set on first-launch onboarding
        "onboarded": False,
        "theme": "dark",
        "default_units": "SI",
        "autosave_enabled": True,
        "autosave_interval_sec": 60,
        "backup_enabled": True,
        "backup_interval_hours": 24,
        "active_project_id": None,
        "window_geometry": None,
        "window_state": None,
        "sidebar_collapsed": False,
        "data_root": None,  # informational; changing it requires a restart
    }

    def __init__(self, paths: AppPaths) -> None:
        self._paths = paths
        self._path = paths.settings_dir / "settings.json"
        self._data: dict[str, Any] = dict(self._DEFAULTS)
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        if self._path.exists():
            try:
                stored = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                # Corrupt settings should not prevent startup; keep defaults.
                pass

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, self._DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, **kwargs: Any) -> None:
        self._data.update(kwargs)

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)