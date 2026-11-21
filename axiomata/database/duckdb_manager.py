"""DuckDB analytical store for scientific datasets.

DuckDB is used only for analytical queries and large tabular data, never as a
replacement for the SQLite application metadata database. This wrapper is
imported lazily by the data-analysis module so the rest of the app does not
require DuckDB to start.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class DuckDBManager:
    def __init__(self, db_path: Path) -> None:
        self._path = Path(db_path)
        self._conn: Any = None

    def open(self) -> None:
        if self._conn is not None:
            return
        import duckdb  # imported lazily

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self._path))

    @property
    def available(self) -> bool:
        return self._conn is not None

    def register_dataframe(self, name: str, df: Any) -> None:
        """Register a pandas DataFrame as a queryable view ``name``."""
        self.open()
        self._conn.register(name, df)

    def query(self, sql: str) -> Any:
        self.open()
        return self._conn.execute(sql)

    def query_df(self, sql: str) -> Any:
        self.open()
        return self._conn.execute(sql).df()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None