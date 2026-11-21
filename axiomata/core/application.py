"""Central application context / service registry.

``AppContext`` is the single object every UI panel and module receives. It owns
the data paths, settings, database connections, the event bus, and repositories.
Keeping this in one place avoids global singletons scattered across the codebase
and makes the whole thing easy to construct in tests with a temp directory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import AppPaths, Settings
from .events import EventBus
from ..database.sqlite_manager import SQLiteManager
from ..database.duckdb_manager import DuckDBManager
from ..database.repositories.repositories import (
    ActivityRepository,
    DatasetRepository,
    ExperimentRepository,
    NoteRepository,
    ProjectRepository,
)


class AppContext:
    def __init__(self, root: Path | None = None) -> None:
        self.paths = AppPaths(root)
        self.paths.ensure()
        self.settings = Settings(self.paths)
        self.events = EventBus()
        self.db = SQLiteManager(self.paths.sqlite_path)
        self.duckdb = DuckDBManager(self.paths.duckdb_path)

        self.projects = ProjectRepository(self.db)
        self.experiments = ExperimentRepository(self.db)
        self.notes = NoteRepository(self.db)
        self.datasets = DatasetRepository(self.db)
        self.activity = ActivityRepository(self.db)

        self._active_project: Optional[dict] = None

    # -- project lifecycle convenience ------------------------------------
    @property
    def active_project(self) -> Optional[dict]:
        return self._active_project

    def open_project(self, project_id: str) -> Optional[dict]:
        project = self.projects.get(project_id)
        if project:
            self._active_project = project
            self.settings.set("active_project_id", project_id)
            self.paths.project_dir(project_id)
        return project

    def shutdown(self) -> None:
        try:
            self.db.close()
        finally:
            self.duckdb.close()