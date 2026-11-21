"""Repository layer for AXIOMATA metadata.

Repositories own all SQL for their domain and return plain dicts so callers do
not depend on sqlite3.Row. They are intentionally small and testable.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from ..sqlite_manager import SQLiteManager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


class ProjectRepository:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db

    def _row_to_project(self, row: Any) -> dict[str, Any]:
        d = _row_to_dict(row)
        assert d is not None
        try:
            d["disciplines"] = json.loads(d.get("disciplines") or "[]")
        except json.JSONDecodeError:
            d["disciplines"] = []
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except json.JSONDecodeError:
            d["metadata"] = {}
        return d

    def create(
        self,
        title: str,
        description: str = "",
        disciplines: list[str] | None = None,
        objectives: str = "",
        hypothesis: str = "",
        directory: str = "",
    ) -> dict[str, Any]:
        pid = _new_id()
        now = _now()
        self.db.execute(
            """INSERT INTO projects
               (id, title, description, disciplines, objectives, hypothesis,
                status, created_at, updated_at, directory, metadata)
               VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, '{}')""",
            (
                pid,
                title,
                description,
                json.dumps(disciplines or []),
                objectives,
                hypothesis,
                now,
                now,
                directory,
            ),
        )
        self.log_activity(pid, "project.created", f"Created project '{title}'")
        project = self.get(pid)
        assert project is not None
        return project

    def update(self, pid: str, **fields: Any) -> dict[str, Any] | None:
        allowed = {
            "title",
            "description",
            "objectives",
            "hypothesis",
            "status",
            "directory",
        }
        sets: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key in allowed:
                sets.append(f"{key} = ?")
                params.append(value)
            elif key == "disciplines" and isinstance(value, list):
                sets.append("disciplines = ?")
                params.append(json.dumps(value))
            elif key == "metadata" and isinstance(value, dict):
                sets.append("metadata = ?")
                params.append(json.dumps(value))
        if not sets:
            return self.get(pid)
        sets.append("updated_at = ?")
        params.append(_now())
        params.append(pid)
        self.db.execute(
            f"UPDATE projects SET {', '.join(sets)} WHERE id = ?", params
        )
        self.log_activity(pid, "project.updated", "Updated project metadata")
        return self.get(pid)

    def get(self, pid: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM projects WHERE id = ?", (pid,))
        return self._row_to_project(row) if row else None

    def list_all(self, include_archived: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT * FROM projects"
        if not include_archived:
            sql += " WHERE status = 'active'"
        sql += " ORDER BY updated_at DESC"
        rows = self.db.query(sql)
        return [self._row_to_project(r) for r in rows]

    def archive(self, pid: str) -> None:
        self.db.execute(
            "UPDATE projects SET status = 'archived', updated_at = ? WHERE id = ?",
            (_now(), pid),
        )
        self.log_activity(pid, "project.archived", "Archived project")

    def unarchive(self, pid: str) -> None:
        self.db.execute(
            "UPDATE projects SET status = 'active', updated_at = ? WHERE id = ?",
            (_now(), pid),
        )

    def duplicate(self, pid: str, new_title: str | None = None) -> dict[str, Any] | None:
        src = self.get(pid)
        if not src:
            return None
        title = new_title or f"{src['title']} (copy)"
        return self.create(
            title=title,
            description=src.get("description", ""),
            disciplines=src.get("disciplines", []),
            objectives=src.get("objectives", ""),
            hypothesis=src.get("hypothesis", ""),
        )

    def delete(self, pid: str) -> None:
        self.db.execute("DELETE FROM projects WHERE id = ?", (pid,))
        self.log_activity(None, "project.deleted", "Deleted project")

    def save_version(self, pid: str, label: str = "") -> None:
        project = self.get(pid)
        if not project:
            return
        self.db.execute(
            "INSERT INTO project_versions (project_id, snapshot, label, created_at)"
            " VALUES (?, ?, ?, ?)",
            (pid, json.dumps(project), label, _now()),
        )

    def list_versions(self, pid: str) -> list[dict[str, Any]]:
        rows = self.db.query(
            "SELECT id, label, created_at FROM project_versions"
            " WHERE project_id = ? ORDER BY id DESC",
            (pid,),
        )
        return [_row_to_dict(r) or {} for r in rows]

    def log_activity(
        self, pid: str | None, kind: str, description: str
    ) -> None:
        self.db.execute(
            "INSERT INTO activity (project_id, kind, description, created_at)"
            " VALUES (?, ?, ?, ?)",
            (pid, kind, description, _now()),
        )


class ExperimentRepository:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db

    def _decode(self, row: Any) -> dict[str, Any]:
        d = _row_to_dict(row)
        assert d is not None
        for key in ("parameters", "results"):
            try:
                d[key] = json.loads(d.get(key) or "{}")
            except json.JSONDecodeError:
                d[key] = {}
        return d

    def create(
        self,
        project_id: str,
        name: str,
        discipline: str = "",
        kind: str = "generic",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        eid = _new_id()
        now = _now()
        self.db.execute(
            """INSERT INTO experiments
               (id, project_id, name, discipline, kind, parameters, results,
                notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, '{}', '', ?, ?)""",
            (
                eid,
                project_id,
                name,
                discipline,
                kind,
                json.dumps(parameters or {}),
                now,
                now,
            ),
        )
        self.db.execute(
            "INSERT INTO activity (project_id, kind, description, created_at)"
            " VALUES (?, 'experiment.created', ?, ?)",
            (project_id, f"Created experiment '{name}'", now),
        )
        exp = self.get(eid)
        assert exp is not None
        return exp

    def update(self, eid: str, **fields: Any) -> dict[str, Any] | None:
        allowed = {"name", "notes", "discipline", "kind"}
        sets, params = [], []
        for key, value in fields.items():
            if key in allowed:
                sets.append(f"{key} = ?")
                params.append(value)
            elif key in ("parameters", "results") and isinstance(value, dict):
                sets.append(f"{key} = ?")
                params.append(json.dumps(value))
        if sets:
            sets.append("updated_at = ?")
            params.append(_now())
            params.append(eid)
            self.db.execute(
                f"UPDATE experiments SET {', '.join(sets)} WHERE id = ?", params
            )
        return self.get(eid)

    def get(self, eid: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM experiments WHERE id = ?", (eid,))
        return self._decode(row) if row else None

    def list_for_project(self, pid: str) -> list[dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM experiments WHERE project_id = ? ORDER BY created_at DESC",
            (pid,),
        )
        return [self._decode(r) for r in rows]

    def delete(self, eid: str) -> None:
        self.db.execute("DELETE FROM experiments WHERE id = ?", (eid,))


class NoteRepository:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db

    def create(
        self, project_id: str | None, title: str = "", body: str = ""
    ) -> dict[str, Any]:
        nid = _new_id()
        now = _now()
        self.db.execute(
            """INSERT INTO notes (id, project_id, title, body, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nid, project_id, title, body, now, now),
        )
        note = self.get(nid)
        assert note is not None
        return note

    def update(self, nid: str, **fields: Any) -> dict[str, Any] | None:
        allowed = {"title", "body"}
        sets, params = [], []
        for key, value in fields.items():
            if key in allowed:
                sets.append(f"{key} = ?")
                params.append(value)
        if sets:
            sets.append("updated_at = ?")
            params.append(_now())
            params.append(nid)
            self.db.execute(
                f"UPDATE notes SET {', '.join(sets)} WHERE id = ?", params
            )
        return self.get(nid)

    def get(self, nid: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM notes WHERE id = ?", (nid,))
        return _row_to_dict(row)

    def list_for_project(self, pid: str) -> list[dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM notes WHERE project_id = ? ORDER BY updated_at DESC",
            (pid,),
        )
        return [_row_to_dict(r) or {} for r in rows]

    def delete(self, nid: str) -> None:
        self.db.execute("DELETE FROM notes WHERE id = ?", (nid,))


class DatasetRepository:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db

    def register(
        self,
        name: str,
        fmt: str,
        path: str,
        row_count: int = 0,
        column_count: int = 0,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        did = _new_id()
        self.db.execute(
            """INSERT INTO datasets
               (id, project_id, name, format, path, row_count, column_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (did, project_id, name, fmt, path, row_count, column_count, _now()),
        )
        row = self.get(did)
        assert row is not None
        return row

    def get(self, did: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM datasets WHERE id = ?", (did,))
        return _row_to_dict(row)

    def list_for_project(self, pid: str) -> list[dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM datasets WHERE project_id = ? ORDER BY created_at DESC",
            (pid,),
        )
        return [_row_to_dict(r) or {} for r in rows]

    def list_all(self) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM datasets ORDER BY created_at DESC")
        return [_row_to_dict(r) or {} for r in rows]


class ActivityRepository:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db

    def recent(self, limit: int = 30) -> list[dict[str, Any]]:
        rows = self.db.query(
            "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [_row_to_dict(r) or {} for r in rows]