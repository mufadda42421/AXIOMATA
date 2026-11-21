"""Top navigation bar: branding, workspace name, search, project, actions."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
)

from .icons import icon
from .themes.theme import ACCENT, TEXT_SECONDARY


class TopNavigationBar(QFrame):
    """Application top bar with brand, workspace, search, project, actions."""

    new_experiment = Signal()
    open_settings = Signal()
    search_requested = Signal(str)
    project_changed = Signal(int)

    def __init__(self, workspace_name: str = "Scientific Workspace", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(14)

        # Brand
        brand_icon = QLabel()
        brand_icon.setPixmap(icon("atom", color=ACCENT, size=24).pixmap(24, 24))
        lay.addWidget(brand_icon)
        brand = QLabel("AXIOMATA")
        brand.setObjectName("Brand")
        lay.addWidget(brand)

        # Divider
        sep1 = QFrame()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: #24344A;")
        lay.addWidget(sep1)

        # Workspace name
        self.workspace_label = QLabel(workspace_name)
        self.workspace_label.setObjectName("WorkspaceName")
        lay.addWidget(self.workspace_label)

        lay.addStretch(1)

        # Project indicator
        proj_lbl = QLabel("Project")
        proj_lbl.setObjectName("CaptionLabel")
        lay.addWidget(proj_lbl)
        self.project_switcher = QComboBox()
        self.project_switcher.setMinimumWidth(200)
        self.project_switcher.setToolTip("Active project")
        self.project_switcher.activated.connect(self._on_project_activated)
        lay.addWidget(self.project_switcher)

        lay.addSpacing(8)

        # Global search
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Search…")
        self.search.setFixedWidth(220)
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self._on_search)
        search_icon = QLabel()
        search_icon.setPixmap(icon("search", color=TEXT_SECONDARY, size=16).pixmap(16, 16))
        lay.addWidget(search_icon)
        lay.addWidget(self.search)

        lay.addSpacing(8)

        # New experiment
        new_btn = QPushButton("+  New Experiment")
        new_btn.setObjectName("Primary")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setIcon(icon("plus", color="#080D16", size=15))
        new_btn.clicked.connect(self.new_experiment.emit)
        lay.addWidget(new_btn)

        # Notifications
        self.bell_btn = QPushButton()
        self.bell_btn.setObjectName("HeaderButton")
        self.bell_btn.setIcon(icon("bell", color=TEXT_SECONDARY, size=18))
        self.bell_btn.setCursor(Qt.PointingHandCursor)
        self.bell_btn.setToolTip("Notifications")
        lay.addWidget(self.bell_btn)

        # Settings
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("HeaderButton")
        self.settings_btn.setIcon(icon("settings", color=TEXT_SECONDARY, size=18))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.open_settings.emit)
        lay.addWidget(self.settings_btn)

    def _on_search(self) -> None:
        text = self.search.text().strip()
        if text:
            self.search_requested.emit(text)
            self.search.clear()

    def _on_project_activated(self, index: int) -> None:
        self.project_changed.emit(index)

    # -- population --------------------------------------------------------
    def set_projects(self, projects: list[dict], active_id: Optional[str] = None) -> None:
        self.project_switcher.blockSignals(True)
        self.project_switcher.clear()
        self.project_switcher.addItem("(No project)", None)
        select_index = 0
        for i, p in enumerate(projects, start=1):
            self.project_switcher.addItem(p["title"], p["id"])
            if p["id"] == active_id:
                select_index = i
        self.project_switcher.setCurrentIndex(select_index)
        self.project_switcher.blockSignals(False)

    def set_workspace_name(self, name: str) -> None:
        self.workspace_label.setText(name)