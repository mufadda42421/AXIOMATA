"""Research Projects page: list, search, open, archive, duplicate, delete."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.application import AppContext
from .panels.base_page import BasePage
from .themes.theme import ACCENT


class ProjectsPage(BasePage):
    new_project = Signal()
    open_project = Signal(str)

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Research Projects", "Manage and organise your scientific research.", parent)
        self.ctx = ctx
        self.setObjectName("ProjectsPage")
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Toolbar: new project + search
        new_btn = QPushButton("+ New Project")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self.new_project.emit)
        self.add_toolbar_widget(new_btn)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search projects…")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self._apply_filter)
        self.add_toolbar_widget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Disciplines", "Status", "Updated", "Actions"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 220)
        self.table.doubleClicked.connect(self._on_row_activated)
        self.add_body_widget(self.table, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("MutedLabel")
        self.add_body_widget(self.status_label)

    def refresh(self) -> None:
        self._all_rows = self.ctx.projects.list_all()
        self._populate(self._all_rows)

    def _populate(self, projects: list[dict]) -> None:
        self.table.setRowCount(0)
        for p in projects:
            row = self.table.rowCount()
            self.table.insertRow(row)

            title_item = QTableWidgetItem(p["title"])
            title_item.setData(Qt.UserRole, p["id"])
            self.table.setItem(row, 0, title_item)

            discs = ", ".join(p.get("disciplines") or []) or "—"
            self.table.setItem(row, 1, QTableWidgetItem(discs))
            self.table.setItem(row, 2, QTableWidgetItem((p.get("status") or "active").title()))
            self.table.setItem(row, 3, QTableWidgetItem(self._fmt_date(p.get("updated_at"))))

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda _=False, pid=p["id"]: self.open_project.emit(pid))
            dup_btn = QPushButton("Duplicate")
            dup_btn.clicked.connect(lambda _=False, pid=p["id"]: self._duplicate(pid))
            arc_btn = QPushButton(
                "Unarchive" if (p.get("status") == "archived") else "Archive"
            )
            arc_btn.clicked.connect(
                lambda _=False, pid=p["id"], st=p.get("status"): self._toggle_archive(pid, st)
            )
            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(lambda _=False, pid=p["id"]: self._delete(pid))
            for b in (open_btn, dup_btn, arc_btn, del_btn):
                b.setFixedHeight(28)
            al.addWidget(open_btn)
            al.addWidget(dup_btn)
            al.addWidget(arc_btn)
            al.addWidget(del_btn)
            actions.setLayout(al)
            self.table.setCellWidget(row, 4, actions)

        self.status_label.setText(f"{len(projects)} project(s)")

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        filtered = [
            p for p in self._all_rows
            if text in p["title"].lower()
            or text in (p.get("description") or "").lower()
            or any(text in d.lower() for d in (p.get("disciplines") or []))
        ]
        self._populate(filtered)

    def _on_row_activated(self, index) -> None:
        item = self.table.item(index.row(), 0)
        if item is not None:
            pid = item.data(Qt.UserRole)
            if pid:
                self.open_project.emit(pid)

    def _duplicate(self, pid: str) -> None:
        copy = self.ctx.projects.duplicate(pid)
        if copy:
            self.refresh()

    def _toggle_archive(self, pid: str, status: str | None) -> None:
        if status == "archived":
            self.ctx.projects.unarchive(pid)
        else:
            self.ctx.projects.archive(pid)
        self.refresh()

    def _delete(self, pid: str) -> None:
        resp = QMessageBox.question(
            self,
            "Delete project",
            "Permanently delete this project and its metadata? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.ctx.projects.delete(pid)
            self.refresh()

    @staticmethod
    def _fmt_date(iso: str | None) -> str:
        if not iso:
            return "—"
        try:
            return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(iso)