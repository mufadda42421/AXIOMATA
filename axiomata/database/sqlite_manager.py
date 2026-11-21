"""SQLite database management for AXIOMATA metadata.

Handles connection lifecycle, schema migrations, foreign-key enforcement, and
transactional writes. Large scientific binaries never live here; only metadata
and references to files on disk are stored.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable


_SCHEMA_V1 = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT DEFAULT '',
    disciplines   TEXT DEFAULT '[]',     -- JSON array of discipline keys
    objectives    TEXT DEFAULT '',
    hypothesis    TEXT DEFAULT '',
    status        TEXT DEFAULT 'active', -- active | archived
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    directory     TEXT DEFAULT '',
    metadata      TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS experiments (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL,
    name          TEXT NOT NULL,
    discipline    TEXT DEFAULT '',
    kind          TEXT DEFAULT 'generic', -- generic | simulation | measurement
    parameters    TEXT DEFAULT '{}',
    results       TEXT DEFAULT '{}',
    notes         TEXT DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notes (
    id            TEXT PRIMARY KEY,
    project_id    TEXT,
    title         TEXT NOT NULL DEFAULT '',
    body          TEXT DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS datasets (
    id            TEXT PRIMARY KEY,
    project_id    TEXT,
    name          TEXT NOT NULL,
    format        TEXT DEFAULT '',
    path          TEXT DEFAULT '',
    row_count     INTEGER DEFAULT 0,
    column_count  INTEGER DEFAULT 0,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    TEXT,
    kind          TEXT DEFAULT '',
    description   TEXT DEFAULT '',
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_versions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    TEXT NOT NULL,
    snapshot      TEXT NOT NULL,         -- JSON snapshot of project state
    label         TEXT DEFAULT '',
    created_at    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_experiments_project ON experiments(project_id);
CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project_id);
CREATE INDEX IF NOT EXISTS idx_datasets_project ON datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity(created_at);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
"""


class SQLiteManager:
    """Thread-safe wrapper around a single SQLite connection.

    Qt UI runs on the main thread; background workers may also touch the DB.
    A re-entrant lock serialises access and SQLite is opened with
    ``check_same_thread=False`` so a single connection can be shared safely.
    """

    def __init__(self, db_path: Path) -> None:
        self._path = Path(db_path)
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None
        self.open()

    def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._path), check_same_thread=False, timeout=30.0
        )
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._conn.execute("PRAGMA busy_timeout = 30000;")
        self._migrate()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.commit()
                finally:
                    self._conn.close()
                    self._conn = None

    # -- low level ---------------------------------------------------------
    def _migrate(self) -> None:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.executescript(_SCHEMA_V1)
            self._conn.commit()
            del cur
            row = self._conn.execute("SELECT version FROM schema_version").fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO schema_version (version) VALUES (1)"
                )
                self._conn.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SQLite connection is not open")
        return self._conn

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self.connection.execute(sql, tuple(params))
            self.connection.commit()
            return cur

    def executemany(self, sql: str, seq: Iterable[Iterable[Any]]) -> None:
        with self._lock:
            self.connection.executemany(sql, [tuple(p) for p in seq])
            self.connection.commit()

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self.connection.execute(sql, tuple(params)).fetchall()

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        with self._lock:
            return self.connection.execute(sql, tuple(params)).fetchone()

    def transaction(self):
        """Context manager exposing the connection inside a transaction."""
        return _Transaction(self)

    def vacuum(self) -> None:
        with self._lock:
            self.connection.execute("VACUUM")


class _Transaction:
    def __init__(self, manager: SQLiteManager) -> None:
        self._m = manager

    def __enter__(self) -> sqlite3.Connection:
        self._m._lock.acquire()
        return self._m.connection

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None:
                self._m.connection.commit()
            else:
                self._m.connection.rollback()
        finally:
            self._m._lock.release()
        return False