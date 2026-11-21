"""Main application window.

Layout::

    ┌───────────────────────────────────────────────────────────────────┐
    │ Menu bar — File · Edit · View · Compute · Data · Tools · Help     │
    │ Tool bar — new · run · export · panel toggles                     │
    │ Brand bar — workspace · project switcher · search                 │
    ├──────────┬──────────────────────────────┬────────────────────────┤
    │ Sidebar  │ Tabbed workspace              │ Inspector              │
    │ (nav)    │ (open destinations as tabs)   │ (contextual)           │
    ├──────────┴──────────────────────────────┴────────────────────────┤
    │ Scientific console (console · results)                             │
    ├───────────────────────────────────────────────────────────────────┤
    │ Status bar — project · units · precision · engine state · clock   │
    └───────────────────────────────────────────────────────────────────┘

The window hosts the onboarding flow, wires navigation to a tabbed workspace
of pages, and manages the active project. Each destination is a page object
keyed by its navigation key; pages register themselves via ``_add_page``.
"""
from __future__ import annotations

import base64
import csv
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QByteArray, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.application import AppContext
from ..core.professions import get_profession
from .coming_soon import ComingSoonPage
from .components import ToastNotification
from .console import ScientificConsole
from .dashboard import DashboardPage
from .dialogs.project_dialog import ProjectDialog
from .icons import icon
from .inspector import Inspector
from .menu_bar import build_menu_bar
from .navigation import NAV_BY_KEY, NAV_ITEMS
from .onboarding import OnboardingDialog
from .projects_page import ProjectsPage
from .settings_page import SettingsPage
from .sidebar import Sidebar
from .themes import theme as theme_mod
from .themes.theme import build_stylesheet
from .tool_bar import build_tool_bar
from .top_bar import TopNavigationBar


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setObjectName("MainWindow")
        self.setWindowTitle("AXIOMATA — Scientific Research & Simulation Environment")
        self.resize(1560, 960)
        self.setMinimumSize(1120, 700)

        self._current_key: str = "home"
        self._pages: dict[str, QWidget] = {}
        self._page_titles: dict[str, str] = {}
        self._zoom: float = 1.0
        self._theme_name: str = ctx.settings.get("theme", "dark")
        self.precision_digits: int = int(ctx.settings.get("precision_digits", 6) or 6)

        self._build_topbar()
        self._build_body()
        self._build_statusbar()
        self._build_actions()
        self._register_pages()
        self._wire_events()

        build_menu_bar(self)
        build_tool_bar(self)

        # Apply theme.
        self.apply_theme(self._theme_name)

        # Decide onboarding vs main UI.
        if not self.ctx.settings.get("onboarded"):
            self._show_onboarding()
        else:
            self._finish_startup()

        # Restore geometry.
        geom = self.ctx.settings.get("window_geometry")
        if isinstance(geom, str) and geom:
            self.restoreGeometry(QByteArray.fromBase64(geom.encode("ascii")))

    # ------------------------------------------------------------------ UI
    def _build_topbar(self) -> None:
        self.topbar = TopNavigationBar()
        self.topbar.new_experiment.connect(self.new_experiment)
        self.topbar.open_settings.connect(lambda: self.navigate("settings"))
        self.topbar.search_requested.connect(self._on_search)
        self.topbar.project_changed.connect(self._on_topbar_project_changed)

    def _build_body(self) -> None:
        central = QWidget()
        central.setObjectName("RootWidget")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.topbar)

        # Main horizontal splitter: sidebar | workspace | inspector
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self.navigate)
        self.sidebar.settings_requested.connect(lambda: self.navigate("settings"))
        self.sidebar.help_requested.connect(self.show_help)
        self.main_splitter.addWidget(self.sidebar)

        # Central workspace: every visited destination becomes a tab.
        self.workspace = QTabWidget()
        self.workspace.setDocumentMode(True)
        self.workspace.setTabsClosable(True)
        self.workspace.setMovable(True)
        self.workspace.setElideMode(Qt.ElideRight)
        self.workspace.tabCloseRequested.connect(self._on_tab_close_requested)
        self.workspace.currentChanged.connect(self._on_tab_changed)
        self.main_splitter.addWidget(self.workspace)
        # Backwards-compatible alias used across the codebase.
        self.stack = self.workspace

        self.inspector = Inspector()
        self.main_splitter.addWidget(self.inspector)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.main_splitter.setSizes([232, 980, 292])

        self.console = ScientificConsole()
        self.console.setMinimumHeight(130)

        # Vertical splitter so the console is resizable against the workspace.
        self.body_splitter = QSplitter(Qt.Vertical)
        self.body_splitter.addWidget(self.main_splitter)
        self.body_splitter.addWidget(self.console)
        self.body_splitter.setStretchFactor(0, 1)
        self.body_splitter.setStretchFactor(1, 0)
        self.body_splitter.setSizes([660, 190])
        outer.addWidget(self.body_splitter, 1)

        # Toast overlay lives on the central widget.
        self.toast = ToastNotification(central)

        self._wire_console_commands()

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        self.save_status = QLabel("Ready")
        sb.addWidget(self.save_status)

        sb.addPermanentWidget(self._status_divider())
        self.status_project = QLabel("No project")
        sb.addPermanentWidget(self.status_project)

        sb.addPermanentWidget(self._status_divider())
        self.status_profession = QLabel("—")
        self.status_profession.setToolTip("Active profession")
        sb.addPermanentWidget(self.status_profession)

        sb.addPermanentWidget(self._status_divider())
        self.status_units = QLabel("SI")
        self.status_units.setToolTip("Active unit system")
        sb.addPermanentWidget(self.status_units)

        sb.addPermanentWidget(self._status_divider())
        self.status_precision = QLabel(f"{self.precision_digits} sig")
        self.status_precision.setToolTip("Displayed significant figures")
        sb.addPermanentWidget(self.status_precision)

        sb.addPermanentWidget(self._status_divider())
        self.status_engine = QLabel("READY")
        self.status_engine.setToolTip("Engine state")
        sb.addPermanentWidget(self.status_engine)

        sb.addPermanentWidget(self._status_divider())
        self.status_clock = QLabel("")
        sb.addPermanentWidget(self.status_clock)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

        self._refresh_profession_status()

    @staticmethod
    def _status_divider() -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet("color: #2C343F;")
        return sep

    def _tick_clock(self) -> None:
        self.status_clock.setText(datetime.now().strftime("%H:%M:%S"))

    def _refresh_profession_status(self) -> None:
        prof = get_profession(self.ctx.settings.get("profession"))
        self.status_project.setText(
            f"Project: {self.ctx.active_project['title']}"
            if self.ctx.active_project else "No project"
        )
        self.status_profession.setText(prof.name if prof else "—")
        self.status_profession.setToolTip(
            f"Active profession — {prof.name}" if prof else "No profession selected"
        )
        self.status_units.setText(str(self.ctx.settings.get("default_units", "SI")))

    # ------------------------------------------------------------- actions
    def _build_actions(self) -> None:
        """Create the shared QActions referenced by the menu bar and tool bar."""
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.cut_action = QAction("Cu&t", self)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.paste_action = QAction("&Paste", self)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.select_all_action = QAction("Select &All", self)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)

        self.toggle_sidebar_action = QAction("Show &Sidebar", self)
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(True)
        self.toggle_sidebar_action.setShortcut(QKeySequence("F1"))
        self.toggle_sidebar_action.triggered.connect(self.toggle_sidebar)

        self.toggle_console_action = QAction("Show Conso&le", self)
        self.toggle_console_action.setCheckable(True)
        self.toggle_console_action.setChecked(True)
        self.toggle_console_action.setShortcut(QKeySequence("F2"))
        self.toggle_console_action.triggered.connect(self.toggle_console)

        self.toggle_inspector_action = QAction("Show &Inspector", self)
        self.toggle_inspector_action.setCheckable(True)
        self.toggle_inspector_action.setChecked(True)
        self.toggle_inspector_action.setShortcut(QKeySequence("F3"))
        self.toggle_inspector_action.triggered.connect(self.toggle_inspector)

        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        self.zoom_in_action.triggered.connect(lambda: self.set_zoom(self._zoom + 0.1))

        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        self.zoom_out_action.triggered.connect(lambda: self.set_zoom(self._zoom - 0.1))

        self.zoom_reset_action = QAction("&Reset Zoom", self)
        self.zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        self.zoom_reset_action.triggered.connect(lambda: self.set_zoom(1.0))

    # -------------------------------------------------------------- pages
    def _register_pages(self) -> None:
        # Home dashboard
        dashboard = DashboardPage(self.ctx)
        dashboard.navigate.connect(self._on_dashboard_nav)
        dashboard.new_project.connect(self.create_project)
        dashboard.new_experiment.connect(self.new_experiment)
        self._add_page("home", dashboard, "Overview")

        # Projects
        projects = ProjectsPage(self.ctx)
        projects.new_project.connect(self.create_project)
        projects.open_project.connect(self.open_project)
        self._add_page("projects", projects, "Research Projects")

        # Settings
        settings = SettingsPage(self.ctx)
        settings.settings_saved.connect(self._on_settings_changed)
        self._add_page("settings", settings, "Settings")

        # Notebook (real)
        from .notebook_page import NotebookPage
        self._add_page("notebook", NotebookPage(self.ctx), "Research Notebook")

        # Departments + tools: real pages where available, placeholders otherwise.
        real_pages = self._real_department_pages()
        real_pages["library"] = _make_library_page
        real_pages["experiments"] = _make_experiments_page
        real_pages["data_analysis"] = _make_data_analysis_page
        for item in NAV_ITEMS:
            if item.key in self._pages:
                continue
            if item.key in real_pages:
                page = real_pages[item.key](self.ctx)
            else:
                page = ComingSoonPage(
                    item.label,
                    self._department_blurb(item.key),
                    "This laboratory is being built in a later development phase.",
                )
            self._add_page(item.key, page, item.label)

        self._sync_switcher()

    def _real_department_pages(self):
        """Return a mapping of nav key -> page factory for built departments."""
        from ..modules.physics.physics_lab_page import PhysicsLabPage
        from ..modules.chemistry.chemistry_lab_page import ChemistryLabPage
        from ..modules.biology.biology_lab_page import BiologyLabPage
        from ..modules.astronomy.astronomy_lab_page import AstronomyLabPage
        from ..modules.engineering.engineering_lab_page import EngineeringLabPage
        from ..modules.mathematics.mathematics_lab_page import MathematicsLabPage
        from ..sandbox.sandbox_2d.sandbox_2d_page import Sandbox2DPage
        from ..sandbox.sandbox_3d.sandbox_3d_page import Sandbox3DPage

        return {
            "physics": PhysicsLabPage,
            "chemistry": ChemistryLabPage,
            "biology": BiologyLabPage,
            "astronomy": AstronomyLabPage,
            "engineering": EngineeringLabPage,
            "mathematics": MathematicsLabPage,
            "sandbox_2d": Sandbox2DPage,
            "sandbox_3d": Sandbox3DPage,
        }

    @staticmethod
    def _department_blurb(key: str) -> str:
        return {
            "physics": "Interactive mechanics, thermodynamics, electromagnetism, and optics.",
            "chemistry": "Periodic table, molecules, reactions, and stoichiometry.",
            "biology": "Cells, genetics, populations, and ecosystems.",
            "astronomy": "Orbital mechanics, planets, stars, and eclipses.",
            "engineering": "Mechanical, electrical, and civil engineering workspaces.",
            "mathematics": "Algebra, calculus, matrices, symbolic solving, and plotting.",
            "sandbox_2d": "A 2D physics sandbox with objects, forces, and measurement.",
            "sandbox_3d": "A 3D viewport with rigid bodies and a simulation engine.",
            "data_analysis": "Import datasets, run statistics, and generate graphs.",
            "library": "Offline scientific reference: constants, units, and formulas.",
        }.get(key, "A scientific workspace.")

    def _add_page(self, key: str, page: QWidget, title: str) -> None:
        self._pages[key] = page
        self._page_titles[key] = title

    # --------------------------------------------------------------- events
    def _wire_events(self) -> None:
        self.ctx.events.subscribe("settings.changed", self._on_settings_changed)
        self.ctx.events.subscribe("project.list_changed", self._sync_switcher)

    def _wire_console_commands(self) -> None:
        self.console.set_command_handler(self._handle_console_command)

    def _handle_console_command(self, text: str) -> None:
        cmd = text.strip().lower()
        if cmd in ("help", "?"):
            self.console.info(
                "Commands: help, clear, pages, open <key>, project, projects, "
                "version, echo <text>"
            )
        elif cmd == "clear":
            self.console.clear()
        elif cmd == "pages":
            self.console.info("Pages: " + ", ".join(self._page_titles.keys()))
        elif cmd.startswith("open "):
            key = cmd.split(" ", 1)[1].strip()
            if key in self._pages:
                self.navigate(key)
                self.console.success(f"Opened {self._page_titles[key]}")
            else:
                self.console.warn(f"Unknown page: {key}")
        elif cmd == "project":
            proj = self.ctx.active_project
            self.console.info(f"Active project: {proj['title'] if proj else '(none)'}")
        elif cmd == "projects":
            for p in self.ctx.projects.list_all():
                self.console.info(f"{p['id'][:8]}  {p['title']}")
        elif cmd == "version":
            from .. import __version__
            self.console.info(f"AXIOMATA {__version__}")
        elif cmd.startswith("echo "):
            self.console.info(text[5:])
        else:
            self.console.warn(f"Unknown command: {text!r}. Type 'help'.")

    # --------------------------------------------------------------- startup
    def _show_onboarding(self) -> None:
        self._onboarding = OnboardingDialog(self._on_profession_selected)
        self.workspace.addTab(self._onboarding, "Welcome")
        self.workspace.setCurrentWidget(self._onboarding)
        # Hide chrome that does not apply during onboarding.
        self.topbar.setVisible(False)
        self.sidebar.setVisible(False)
        self.inspector.setVisible(False)
        self.console.setVisible(False)
        self.menuBar().setVisible(False)
        for tb in self.findChildren(QToolBar):
            tb.setVisible(False)

    def _on_profession_selected(self, profession_key: str) -> None:
        self.ctx.settings.update(profession=profession_key, onboarded=True)
        self.ctx.settings.save()
        prof = get_profession(profession_key)
        if prof:
            self.sidebar.set_shortcuts(prof.shortcuts)
        # Remove onboarding page.
        idx = self.workspace.indexOf(self._onboarding)
        if idx != -1:
            self.workspace.removeTab(idx)
        self._onboarding.deleteLater()
        self._finish_startup()
        self.console.success(
            f"Profession set to {prof.name if prof else profession_key}. Welcome!"
        )
        self.toast.show_message(
            f"Profession set to {prof.name if prof else profession_key}. Welcome!",
            "success",
        )

    def _finish_startup(self) -> None:
        self.topbar.setVisible(True)
        self.sidebar.setVisible(True)
        self.inspector.setVisible(True)
        self.console.setVisible(True)
        self.menuBar().setVisible(True)
        for tb in self.findChildren(QToolBar):
            tb.setVisible(True)
        prof = get_profession(self.ctx.settings.get("profession"))
        if prof:
            self.sidebar.set_shortcuts(prof.shortcuts)
        self._refresh_profession_status()
        self._sync_switcher()
        self._restore_last_project()
        self.navigate("home")

    def _restore_last_project(self) -> None:
        pid = self.ctx.settings.get("active_project_id")
        if pid and self.ctx.projects.get(pid):
            self.open_project(pid, switch_page=False)

    # ----------------------------------------------------------- navigation
    def navigate(self, destination: str) -> None:
        if destination.startswith("open_project:"):
            self.open_project(destination.split(":", 1)[1])
            return
        key = destination
        if key not in self._pages:
            self.console.warn(f"Unknown destination: {key}")
            return
        page = self._pages[key]
        idx = self.workspace.indexOf(page)
        if idx == -1:
            idx = self.workspace.addTab(page, self._page_titles.get(key, key))
        else:
            self.workspace.tabBar().setTabVisible(idx, True)
        self.workspace.setCurrentIndex(idx)
        self._current_key = key
        self.sidebar.set_active(key)
        self._update_inspector_for_page(key)
        self._refresh_page(key)

    def _refresh_page(self, key: str) -> None:
        """Refresh dynamic pages on entry."""
        page = self._pages.get(key)
        if isinstance(page, (DashboardPage, ProjectsPage)):
            page.refresh()

    def _on_tab_changed(self, index: int) -> None:
        page = self.workspace.widget(index)
        for key, candidate in self._pages.items():
            if candidate is page:
                self._current_key = key
                self.sidebar.set_active(key)
                self._update_inspector_for_page(key)
                self._refresh_page(key)
                break

    def _on_tab_close_requested(self, index: int) -> None:
        page = self.workspace.widget(index)
        # The home overview and the onboarding screen stay open.
        for key, candidate in self._pages.items():
            if candidate is page and key == "home":
                self.console.info("The overview workspace cannot be closed.")
                return
        self.workspace.tabBar().setTabVisible(index, False)

    def _on_dashboard_nav(self, dest: str) -> None:
        self.navigate(dest)

    def _update_inspector_for_page(self, key: str) -> None:
        title = self._page_titles.get(key, key)
        page = self._pages.get(key)
        subtitle = ""
        if isinstance(page, ComingSoonPage):
            subtitle = "Module in development"
        self.inspector.set_context(title, subtitle)
        props: list[tuple[str, str]] = [("Destination", key)]
        proj = self.ctx.active_project
        props.append(("Active project", proj["title"] if proj else "(none)"))
        props.append(("Unit system", str(self.ctx.settings.get("default_units", "SI"))))
        props.append(("Precision", f"{self.precision_digits} significant figures"))
        self.inspector.set_properties(props)

    # -------------------------------------------------------------- projects
    def create_project(self) -> None:
        dlg = ProjectDialog(self)
        if dlg.exec() == ProjectDialog.Accepted:
            values = dlg.values()
            project = self.ctx.projects.create(
                title=values["title"],
                description=values["description"],
                disciplines=values["disciplines"],
                objectives=values["objectives"],
                hypothesis=values["hypothesis"],
                directory="",
            )
            # Ensure on-disk folder exists and record it.
            proj_dir = self.ctx.paths.project_dir(project["id"])
            self.ctx.projects.update(project["id"], directory=str(proj_dir))
            self.ctx.events.publish("project.list_changed")
            self._sync_switcher()
            self.console.success(f"Created project '{project['title']}'")
            self.toast.show_message(f"Created project '{project['title']}'", "success")
            self.open_project(project["id"])

    def open_project_dialog(self) -> None:
        """Show the projects workspace so an existing project can be chosen."""
        self.navigate("projects")

    def open_project(self, project_id: str, switch_page: bool = True) -> None:
        project = self.ctx.open_project(project_id)
        if not project:
            self.console.error(f"Project not found: {project_id}")
            return
        self._sync_switcher(project_id)
        self.console.success(f"Opened project '{project['title']}'")
        self.toast.show_message(f"Opened project '{project['title']}'", "info")
        self._refresh_profession_status()
        if switch_page:
            self.navigate("projects")

    def _sync_switcher(self, preferred: Optional[str] = None) -> None:
        current = preferred or self.ctx.settings.get("active_project_id")
        projects = self.ctx.projects.list_all(include_archived=False)
        self.topbar.set_projects(projects, current)
        if current and self.ctx.projects.get(current):
            # Keep active project object in sync.
            self.ctx._active_project = self.ctx.projects.get(current)

    def _on_topbar_project_changed(self, index: int) -> None:
        pid = self.topbar.project_switcher.itemData(index)
        if pid:
            self.open_project(pid, switch_page=False)
        else:
            self.ctx._active_project = None
            self.ctx.settings.set("active_project_id", None)
            self.ctx.settings.save()
        self._update_inspector_for_page(self._current_key)

    def new_experiment(self) -> None:
        proj = self.ctx.active_project
        if not proj:
            self.console.warn("Open or create a project before adding an experiment.")
            self.toast.show_message(
                "Create or open a project before adding an experiment.", "warn"
            )
            self.create_project()
            return
        # Minimal experiment creation prompt via an input dialog.
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Experiment", "Experiment name:")
        if ok and name.strip():
            exp = self.ctx.experiments.create(
                project_id=proj["id"], name=name.strip(), kind="generic"
            )
            self.console.success(f"Created experiment '{exp['name']}' in project '{proj['title']}'")
            self.toast.show_message(f"Created experiment '{exp['name']}'", "success")

    # Backwards-compatible alias for the previous private name.
    _on_new_experiment = new_experiment

    # ----------------------------------------------------------------- data
    def import_dataset(self) -> None:
        self.navigate("data_analysis")
        page = self._pages.get("data_analysis")
        if page is not None and hasattr(page, "import_dataset"):
            try:
                page.import_dataset()
            except Exception as exc:  # noqa: BLE001
                self.console.warn(f"Import cancelled: {exc}")

    def export_results(self) -> None:
        rows = self._current_result_rows()
        if not rows:
            self.console.warn("No results table is active in this workspace.")
            self.toast.show_message("No results available to export.", "warn")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export results", "results.csv", "CSV files (*.csv);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Quantity", "Value", "Unit", "Notes"])
                writer.writerows(rows)
        except OSError as exc:
            self.console.error(f"Export failed: {exc}")
            return
        self.console.success(f"Exported {len(rows)} rows to {path}")
        self.toast.show_message(f"Results exported to {path}", "success")

    def export_figure(self) -> None:
        page = self._pages.get(self._current_key)
        chart = None
        if page is not None:
            from .widgets.chart_widget import ChartWidget
            charts = page.findChildren(ChartWidget)
            if charts:
                chart = charts[0]
        if chart is None:
            self.console.warn("No figure is available in this workspace.")
            self.toast.show_message("No figure available to export.", "warn")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", "figure.png", "PNG image (*.png);;All files (*)"
        )
        if not path:
            return
        try:
            chart.figure.savefig(path, dpi=160, facecolor=chart.figure.get_facecolor())
        except Exception as exc:  # noqa: BLE001
            self.console.error(f"Figure export failed: {exc}")
            return
        self.console.success(f"Figure exported to {path}")
        self.toast.show_message("Figure exported.", "success")

    def _current_result_rows(self) -> list[tuple[str, str, str, str]]:
        """Collect result rows from the active page, if it exposes any."""
        page = self._pages.get(self._current_key)
        if page is None:
            return []
        if hasattr(page, "result_rows"):
            try:
                return [tuple(r) for r in page.result_rows()]
            except Exception:  # noqa: BLE001
                return []
        from .components import ResultTable
        tables = page.findChildren(ResultTable)
        if tables:
            return tables[0].current_rows()
        from PySide6.QtWidgets import QTableWidget
        plain = page.findChildren(QTableWidget)
        if plain:
            rows = []
            for r in range(plain[0].rowCount()):
                cells = []
                for c in range(plain[0].columnCount()):
                    it = plain[0].item(r, c)
                    cells.append(it.text() if it else "")
                rows.append(tuple(cells))
            return rows
        return []

    def backup_workspace(self) -> None:
        """Write a timestamped zip of the local data directory."""
        import shutil
        import zipfile

        root = self.ctx.paths.root
        if not root.exists():
            self.console.warn("No data directory to back up yet.")
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = root.parent / f"axiomata-backup-{stamp}.zip"
        try:
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in root.rglob("*"):
                    if item.is_file() and "cache" not in item.parts:
                        zf.write(item, item.relative_to(root))
        except (OSError, zipfile.BadZipFile) as exc:
            self.console.error(f"Backup failed: {exc}")
            return
        size_mb = target.stat().st_size / (1024 * 1024)
        self.console.success(f"Backup written to {target} ({size_mb:.2f} MB)")
        self.toast.show_message(f"Backup written to {target.name}", "success")

    # ------------------------------------------------------------- compute
    def run_current(self) -> None:
        """Recompute the active workspace if the page supports it."""
        page = self._pages.get(self._current_key)
        if page is None:
            return
        runner = getattr(page, "run_all", None)
        if runner is None:
            self.console.info(
                f"{self._page_titles.get(self._current_key, 'This workspace')} "
                "has no batch run; use the controls in the panel."
            )
            return
        self.status_engine.setText("RUNNING")
        try:
            runner()
        except Exception as exc:  # noqa: BLE001
            self.console.error(f"Run failed: {exc}")
            self.status_engine.setText("ERROR")
            return
        self.status_engine.setText("READY")

    def reset_current(self) -> None:
        page = self._pages.get(self._current_key)
        if page is None:
            return
        resetter = getattr(page, "reset_all", None)
        if resetter is None:
            self.console.info(
                f"{self._page_titles.get(self._current_key, 'This workspace')} "
                "has no reset action."
            )
            return
        resetter()
        self.console.info("Parameters reset to defaults.")

    # -------------------------------------------------------------- panels
    def toggle_sidebar(self) -> None:
        visible = not self.sidebar.isVisible()
        self.sidebar.setVisible(visible)
        self.toggle_sidebar_action.setChecked(visible)

    def toggle_console(self) -> None:
        visible = not self.console.isVisible()
        self.console.setVisible(visible)
        self.toggle_console_action.setChecked(visible)

    def toggle_inspector(self) -> None:
        visible = not self.inspector.isVisible()
        self.inspector.setVisible(visible)
        self.toggle_inspector_action.setChecked(visible)

    # ----------------------------------------------------------------- view
    def set_zoom(self, factor: float) -> None:
        self._zoom = max(0.8, min(1.6, round(factor, 2)))
        self.apply_theme(self._theme_name)
        self.console.info(f"Interface scale: {int(self._zoom * 100)}%")

    def set_precision(self, digits: int) -> None:
        self.precision_digits = int(digits)
        self.ctx.settings.set("precision_digits", self.precision_digits)
        self.ctx.settings.save()
        for d, act in getattr(self, "_precision_actions", {}).items():
            act.setChecked(int(d) == self.precision_digits)
        self.status_precision.setText(f"{self.precision_digits} sig")
        self.console.info(f"Precision set to {self.precision_digits} significant figures.")

    # ----------------------------------------------------------------- help
    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Help & Documentation",
            "AXIOMATA — Scientific Research & Simulation Environment\n\n"
            "Navigate with the sidebar or the menu bar, search with Ctrl+K,\n"
            "and use the console for quick commands (type 'help').\n\n"
            "Each workspace opens as a tab; press F5 to run, F2 to toggle\n"
            "the console, and Ctrl+S to export the current results table.",
        )

    def show_about(self) -> None:
        from .. import __version__
        QMessageBox.about(
            self,
            "About AXIOMATA",
            f"<b>AXIOMATA</b> {__version__}<br>"
            "Scientific Research &amp; Simulation Environment<br><br>"
            "Explore. Experiment. Understand.<br><br>"
            "All calculations use SI units and are unit-tested.<br>"
            "Results are labelled as calculated, simulated, or reference.",
        )

    # ----------------------------------------------------------------- search
    def _on_search(self, text: str = "") -> None:
        text = (text or "").strip().lower()
        if not text:
            return
        # Match pages first.
        for item in NAV_ITEMS:
            if text in item.label.lower() or text in item.key:
                self.navigate(item.key)
                return
        # Match projects.
        for p in self.ctx.projects.list_all():
            if text in p["title"].lower():
                self.open_project(p["id"])
                return
        self.console.warn(f"No matches for '{text}'.")
        self.toast.show_message(f"No results for '{text}'", "warn")

    # --------------------------------------------------------------- settings
    def _on_settings_changed(self) -> None:
        theme = self.ctx.settings.get("theme", "dark")
        self.apply_theme(theme)
        prof = get_profession(self.ctx.settings.get("profession"))
        if prof:
            self.sidebar.set_shortcuts(prof.shortcuts)
        # Refresh settings page in case external changes occurred.
        if isinstance(self._pages.get("settings"), SettingsPage):
            self._pages["settings"]._load()
        self.toast.show_message("Settings saved.", "success")

    def set_theme(self, name: str) -> None:
        """Switch the visual theme and persist the choice."""
        self._theme_name = name if name in ("dark", "light") else "dark"
        self.ctx.settings.set("theme", self._theme_name)
        self.ctx.settings.save()
        self.apply_theme(self._theme_name)
        if hasattr(self, "dark_theme_action"):
            self.dark_theme_action.setChecked(self._theme_name == "dark")
            self.light_theme_action.setChecked(self._theme_name == "light")
        self.console.info(f"Theme set to {self._theme_name}.")

    def apply_theme(self, theme: str) -> None:
        """Apply a theme's stylesheet to the whole application."""
        self._theme_name = theme if theme in ("dark", "light") else "dark"
        theme_mod.set_theme(self._theme_name)
        theme_mod.refresh_globals()
        sheet = build_stylesheet(self._theme_name)
        if self._zoom != 1.0:
            size = round(theme_mod.BASE_FONT_PX * self._zoom)
            sheet += f"\n* {{ font-size: {size}px; }}\n"
        self.setStyleSheet(sheet)

    # ------------------------------------------------------------ persistence
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        try:
            self.ctx.settings.update(
                window_geometry=base64.b64encode(self.saveGeometry().data()).decode("ascii"),
                sidebar_collapsed=self.sidebar._collapsed,
            )
            self.ctx.settings.save()
        finally:
            self.ctx.shutdown()
        super().closeEvent(event)


def _make_library_page(ctx):
    from .library_page import LibraryPage
    return LibraryPage(ctx)


def _make_experiments_page(ctx):
    from .experiments_page import ExperimentsPage
    return ExperimentsPage(ctx)


def _make_data_analysis_page(ctx):
    from .data_analysis_page import DataAnalysisPage
    return DataAnalysisPage(ctx)
