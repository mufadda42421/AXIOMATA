"""Home dashboard — a premium scientific command centre.

Sections:
  * Time-based greeting with a profession-aware description.
  * Quick Actions row (New Project, New Experiment, 2D/3D Sandbox, Import).
  * Recent Projects as compact cards (or an elegant empty state).
  * Scientific Workspace — compact department panels.
  * Recent Activity feed.
  * System Information strip (database, storage, simulations, version).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .. import __version__
from ..core.application import AppContext
from ..core.professions import get_profession
from .components import ActionButton, EmptyState, SectionHeader, StatusIndicator
from .icons import icon, icon_pixmap
from .panels.base_page import BasePage
from .themes.theme import (
    ACCENT, ACCENT_2, BORDER_SOFT, PANEL, PANEL_ELEVATED, SUCCESS, TEXT,
    TEXT_DIM, TEXT_SECONDARY,
)

# quick-start id -> (label, icon, nav key or special action)
QUICK_ACTIONS: dict[str, tuple[str, str, str]] = {
    "project": ("New Research Project", "folder_open", "action:new_project"),
    "experiment": ("New Experiment", "flask", "action:new_experiment"),
    "sandbox_2d": ("Open 2D Sandbox", "grid", "sandbox_2d"),
    "sandbox_3d": ("Open 3D Sandbox", "cube", "sandbox_3d"),
    "data_analysis": ("Import Dataset", "upload", "data_analysis"),
}

DEPARTMENTS = [
    ("physics", "Physics", "atom"),
    ("chemistry", "Chemistry", "flask"),
    ("biology", "Biology", "dna"),
    ("astronomy", "Astronomy", "orbit"),
    ("engineering", "Engineering", "settings"),
    ("mathematics", "Mathematics", "calculator"),
]


class _Card(QFrame):
    def __init__(self, object_name: str = "Card"):
        super().__init__()
        self.setObjectName(object_name)
        self.setStyleSheet(
            f"#{object_name} {{ background-color: {PANEL};"
            f" border: 1px solid {BORDER_SOFT}; border-radius: 10px; }}"
        )


class DashboardPage(BasePage):
    navigate = Signal(str)
    new_project = Signal()
    new_experiment = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("", "", "", parent)
        self.ctx = ctx
        self.setObjectName("DashboardPage")
        self._build()
        self.refresh()

    # -- construction -----------------------------------------------------
    def _build(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(22)

        # Greeting header
        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("H1")
        self.description_label = QLabel()
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        greeting_box = QVBoxLayout()
        greeting_box.setSpacing(4)
        greeting_box.addWidget(self.greeting_label)
        greeting_box.addWidget(self.description_label)
        outer.addLayout(greeting_box)

        # Quick actions
        qs_header = SectionHeader("Quick Actions")
        outer.addWidget(qs_header)
        self.quick_row = QHBoxLayout()
        self.quick_row.setSpacing(10)
        outer.addLayout(self.quick_row)

        # Middle two-column: Recent Projects + Recent Activity
        mid = QHBoxLayout()
        mid.setSpacing(18)
        mid.addWidget(self._build_recent_projects(), 1)
        mid.addWidget(self._build_activity(), 1)
        outer.addLayout(mid)

        # Scientific workspace (department panels)
        sw_header = SectionHeader("Scientific Workspace")
        outer.addWidget(sw_header)
        self.dept_grid = QGridLayout()
        self.dept_grid.setSpacing(10)
        outer.addLayout(self.dept_grid)

        # System information
        sys_header = SectionHeader("System Information")
        outer.addWidget(sys_header)
        outer.addWidget(self._build_system_info())

        outer.addStretch(1)
        scroll.setWidget(container)
        self.body_layout.addWidget(scroll, 1)

    def _build_recent_projects(self) -> QWidget:
        card = _Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        header = SectionHeader("Recent Projects", "View all")
        header.action_clicked.connect(lambda: self.navigate.emit("projects"))
        lay.addWidget(header)
        self.recent_projects_container = QWidget()
        self.recent_projects_layout = QVBoxLayout(self.recent_projects_container)
        self.recent_projects_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_projects_layout.setSpacing(8)
        lay.addWidget(self.recent_projects_container)
        return card

    def _build_activity(self) -> QWidget:
        card = _Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        header = SectionHeader("Recent Activity")
        lay.addWidget(header)
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(8)
        lay.addWidget(self.activity_container)
        lay.addStretch(1)
        return card

    def _build_system_info(self) -> QWidget:
        card = _Card()
        lay = QHBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(24)
        self.sys_db = StatusIndicator("Database: checking…", SUCCESS)
        self.sys_storage = StatusIndicator("Storage: —", ACCENT)
        self.sys_sims = StatusIndicator("Simulations: 0", ACCENT_2)
        self.sys_version = StatusIndicator(f"Version {__version__}", TEXT_SECONDARY)
        for w in (self.sys_db, self.sys_storage, self.sys_sims, self.sys_version):
            lay.addWidget(w)
        lay.addStretch(1)
        return card

    # -- data binding -----------------------------------------------------
    def refresh(self) -> None:
        self._refresh_greeting()
        self._refresh_quick_actions()
        self._refresh_recent_projects()
        self._refresh_activity()
        self._refresh_departments()
        self._refresh_system_info()

    def _refresh_greeting(self) -> None:
        hour = datetime.now().hour
        if hour < 12:
            part = "Good morning"
        elif hour < 18:
            part = "Good afternoon"
        else:
            part = "Good evening"
        prof = get_profession(self.ctx.settings.get("profession"))
        who = prof.name if prof else "Scientist"
        self.greeting_label.setText(f"{part}, {who}.")
        if prof:
            self.description_label.setText(prof.welcome)
        else:
            self.description_label.setText(
                "Welcome to AXIOMATA — your scientific research and simulation environment."
            )

    def _refresh_quick_actions(self) -> None:
        while self.quick_row.count():
            item = self.quick_row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        for idx, (aid, (label, icon_name, _target)) in enumerate(QUICK_ACTIONS.items()):
            btn = QPushButton()
            btn.setObjectName("Card")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(64)
            btn.setStyleSheet(
                f"QPushButton#Card {{ background-color: {PANEL};"
                f" border: 1px solid {BORDER_SOFT}; border-radius: 10px; text-align: left;"
                f" padding: 14px; }}"
                f"QPushButton#Card:hover {{ border-color: {ACCENT};"
                f" background-color: {PANEL_ELEVATED}; }}"
            )
            row = QHBoxLayout()
            row.setContentsMargins(14, 12, 14, 12)
            row.setSpacing(12)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pixmap(icon_name, color=ACCENT, size=22))
            row.addWidget(icon_lbl)
            text = QLabel(label)
            text.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 500;")
            row.addWidget(text, 1)
            btn.setLayout(row)
            btn.clicked.connect(lambda _=False, a=aid: self._on_quick_action(a))
            self.quick_row.addWidget(btn, 1)

    def _on_quick_action(self, action_id: str) -> None:
        _label, _icon_name, target = QUICK_ACTIONS[action_id]
        if target.startswith("action:"):
            action = target.split(":", 1)[1]
            if action == "new_project":
                self.new_project.emit()
            elif action == "new_experiment":
                self.new_experiment.emit()
            return
        self.navigate.emit(target)

    def _refresh_recent_projects(self) -> None:
        while self.recent_projects_layout.count():
            item = self.recent_projects_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        projects = self.ctx.projects.list_all()[:5]
        if not projects:
            empty = EmptyState(
                "No projects yet",
                "Create your first research project to begin.",
                icon_name="folder",
                action_text="New Project",
            )
            empty.action_clicked.connect(self.new_project.emit)
            self.recent_projects_layout.addWidget(empty)
            return
        for p in projects:
            self.recent_projects_layout.addWidget(self._project_row(p))

    def _project_row(self, project: dict) -> QWidget:
        row = QFrame()
        row.setObjectName("ProjectRow")
        row.setCursor(Qt.PointingHandCursor)
        row.setMinimumHeight(56)
        row.setStyleSheet(
            f"QFrame#ProjectRow {{ background-color: {PANEL_ELEVATED};"
            f" border: 1px solid {BORDER_SOFT}; border-radius: 8px; }}"
            f"QFrame#ProjectRow:hover {{ border-color: {ACCENT}; }}"
        )
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon_pixmap("folder", color=ACCENT, size=20))
        lay.addWidget(icon_lbl)

        textcol = QVBoxLayout()
        textcol.setSpacing(1)
        title = QLabel(project["title"])
        title.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 13px;")
        discs = project.get("disciplines") or []
        disc_str = ", ".join(d.title() for d in discs) if discs else "Uncategorised"
        meta = QLabel(
            f"{disc_str}  ·  {self._fmt_date(project.get('updated_at'))}"
        )
        meta.setObjectName("CaptionLabel")
        textcol.addWidget(title)
        textcol.addWidget(meta)
        lay.addLayout(textcol, 1)

        status = project.get("status") or "active"
        status_lbl = QLabel(status.title())
        status_lbl.setStyleSheet(
            f"color: {SUCCESS if status == 'active' else TEXT_SECONDARY};"
            f" font-size: 11px; font-weight: 600;"
        )
        lay.addWidget(status_lbl)

        open_btn = QPushButton()
        open_btn.setObjectName("ToolButton")
        open_btn.setIcon(icon("arrow_right", color=ACCENT, size=18))
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setToolTip("Open project")
        pid = project["id"]
        open_btn.clicked.connect(lambda _=False, p=pid: self.navigate.emit(f"open_project:{p}"))
        lay.addWidget(open_btn)

        def _open(e=None, p=pid):
            self.navigate.emit(f"open_project:{p}")
        row.mouseReleaseEvent = _open
        return row

    def _refresh_activity(self) -> None:
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        events = self.ctx.activity.recent(7)
        if not events:
            self.activity_layout.addWidget(
                EmptyState(
                    "No activity recorded",
                    "Experiments and project changes will appear here.",
                    icon_name="activity",
                )
            )
            return
        for ev in events:
            row = QHBoxLayout()
            row.setSpacing(10)
            dot = QLabel()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet(f"background-color: {ACCENT}; border-radius: 4px;")
            dot.setAlignment(Qt.AlignTop)
            desc = QLabel(ev.get("description", ""))
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            ts = QLabel(self._fmt_time(ev.get("created_at")))
            ts.setObjectName("CaptionLabel")
            row.addWidget(dot, 0, Qt.AlignTop)
            row.addWidget(desc, 1)
            row.addWidget(ts, 0, Qt.AlignTop)
            w = QWidget()
            w.setLayout(row)
            self.activity_layout.addWidget(w)

    def _refresh_departments(self) -> None:
        while self.dept_grid.count():
            item = self.dept_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        cols = 3
        for idx, (key, label, icon_name) in enumerate(DEPARTMENTS):
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(52)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {PANEL};"
                f" border: 1px solid {BORDER_SOFT}; border-radius: 10px;"
                f" text-align: left; padding: 12px 14px; }}"
                f"QPushButton:hover {{ border-color: {ACCENT};"
                f" background-color: {PANEL_ELEVATED}; }}"
            )
            row = QHBoxLayout()
            row.setContentsMargins(14, 10, 14, 10)
            row.setSpacing(12)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pixmap(icon_name, color=TEXT_SECONDARY, size=20))
            row.addWidget(icon_lbl)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 500;")
            row.addWidget(lbl, 1)
            btn.setLayout(row)
            btn.clicked.connect(lambda _=False, k=key: self.navigate.emit(k))
            r, c = divmod(idx, cols)
            self.dept_grid.addWidget(btn, r, c)

    def _refresh_system_info(self) -> None:
        # Database status (real check).
        try:
            self.ctx.db.query_one("SELECT 1")
            self.sys_db.set_state("Database: connected", SUCCESS)
        except Exception:  # noqa: BLE001
            self.sys_db.set_state("Database: error", "#F07178")
        # Storage usage (real).
        used = self._dir_size(self.ctx.paths.root)
        self.sys_storage.set_state(f"Storage: {self._human_size(used)}", ACCENT)
        # Active simulations: count non-static bodies in any open sandbox is not
        # tracked globally; report the number of experiment records as a proxy is
        # misleading, so we show the number of recent experiments (real data).
        projects = self.ctx.projects.list_all()
        exp_total = sum(len(self.ctx.experiments.list_for_project(p["id"]))
                        for p in projects)
        self.sys_sims.set_state(f"Experiments: {exp_total}", ACCENT_2)

    @staticmethod
    def _dir_size(path) -> int:
        try:
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        except OSError:
            return 0

    @staticmethod
    def _human_size(num: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if num < 1024:
                return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
            num /= 1024  # type: ignore[assignment]
        return f"{num:.1f} PB"

    @staticmethod
    def _fmt_date(iso: str | None) -> str:
        if not iso:
            return "—"
        try:
            return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(iso)

    @staticmethod
    def _fmt_time(iso: str | None) -> str:
        if not iso:
            return ""
        try:
            return datetime.fromisoformat(iso).strftime("%H:%M")
        except (ValueError, TypeError):
            return ""