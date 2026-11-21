"""Application menu bar.

Scientific workstations are driven from a menu bar rather than a strip of
buttons, so every command in AXIOMATA has a stable location and a keyboard
shortcut. The menu is built from the :class:`~axiomata.ui.main_window.MainWindow`
instance, which owns the actions themselves.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

from .icons import icon
from .themes.theme import TEXT_SECONDARY

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .main_window import MainWindow


def _action(
    window: "MainWindow",
    menu: QMenu,
    text: str,
    slot,
    shortcut: str = "",
    icon_name: str = "",
    tip: str = "",
) -> QAction:
    act = QAction(text, window)
    if icon_name:
        act.setIcon(icon(icon_name, color=TEXT_SECONDARY, size=16))
    if shortcut:
        act.setShortcut(QKeySequence(shortcut))
    if tip:
        act.setStatusTip(tip)
    act.triggered.connect(slot)
    menu.addAction(act)
    return act


def build_menu_bar(window: "MainWindow") -> QMenuBar:
    """Construct and install the AXIOMATA menu bar on ``window``."""
    bar = QMenuBar()
    bar.setNativeMenuBar(False)
    window.setMenuBar(bar)

    # ---------------------------------------------------------------- File
    file_menu = bar.addMenu("&File")
    _action(window, file_menu, "&New Project…", window.create_project,
           "Ctrl+N", "plus", "Create a new research project")
    _action(window, file_menu, "New &Experiment…", window.new_experiment,
           "Ctrl+E", "activity", "Record a new experiment in the active project")
    file_menu.addSeparator()
    _action(window, file_menu, "&Open Project…", window.open_project_dialog,
           "Ctrl+O", "folder_open", "Open an existing research project")
    _action(window, file_menu, "&Import Dataset…", window.import_dataset,
           "Ctrl+I", "upload", "Import a CSV, JSON, Excel, Parquet or HDF5 dataset")
    file_menu.addSeparator()
    _action(window, file_menu, "&Export Results…", window.export_results,
           "Ctrl+S", "download", "Export the current results as CSV")
    _action(window, file_menu, "Export &Figure…", window.export_figure,
           "Ctrl+Shift+E", "chart", "Save the active chart as an image")
    file_menu.addSeparator()
    _action(window, file_menu, "E&xit", window.close, "Ctrl+Q", "close",
           "Close AXIOMATA")

    # ---------------------------------------------------------------- Edit
    edit_menu = bar.addMenu("&Edit")
    edit_menu.addAction(window.undo_action)
    edit_menu.addAction(window.redo_action)
    edit_menu.addSeparator()
    edit_menu.addAction(window.cut_action)
    edit_menu.addAction(window.copy_action)
    edit_menu.addAction(window.paste_action)
    edit_menu.addAction(window.select_all_action)

    # ---------------------------------------------------------------- View
    view_menu = bar.addMenu("&View")
    view_menu.addAction(window.toggle_sidebar_action)
    view_menu.addAction(window.toggle_console_action)
    view_menu.addAction(window.toggle_inspector_action)
    view_menu.addSeparator()
    view_menu.addAction(window.zoom_in_action)
    view_menu.addAction(window.zoom_out_action)
    view_menu.addAction(window.zoom_reset_action)
    view_menu.addSeparator()

    theme_menu = view_menu.addMenu("&Theme")
    window.dark_theme_action = QAction("Scientific Dark", window)
    window.dark_theme_action.setCheckable(True)
    window.dark_theme_action.setChecked(window.ctx.settings.get("theme", "dark") == "dark")
    window.dark_theme_action.triggered.connect(lambda: window.set_theme("dark"))
    theme_menu.addAction(window.dark_theme_action)

    window.light_theme_action = QAction("Lab Light", window)
    window.light_theme_action.setCheckable(True)
    window.light_theme_action.setChecked(window.ctx.settings.get("theme", "dark") == "light")
    window.light_theme_action.triggered.connect(lambda: window.set_theme("light"))
    theme_menu.addAction(window.light_theme_action)

    precision_menu = view_menu.addMenu("&Precision")
    window._precision_actions = {}
    for label, digits in (("3 significant figures", 3), ("6 significant figures", 6),
                          ("12 significant figures", 12)):
        act = QAction(label, window)
        act.setCheckable(True)
        act.triggered.connect(lambda _checked=False, d=digits: window.set_precision(d))
        precision_menu.addAction(act)
        window._precision_actions[digits] = act

    # ------------------------------------------------------------- Compute
    compute_menu = bar.addMenu("&Compute")
    _action(window, compute_menu, "&Run Simulation", window.run_current,
           "F5", "play", "Recompute the active workspace")
    _action(window, compute_menu, "&Reset Parameters", window.reset_current,
           "Shift+F5", "reset", "Restore default parameters")
    compute_menu.addSeparator()
    _action(window, compute_menu, "Show &Console", window.toggle_console,
           "F2", "menu", "Show or hide the scientific console")

    # ---------------------------------------------------------------- Data
    data_menu = bar.addMenu("&Data")
    _action(window, data_menu, "Open &Data Analysis", lambda: window.navigate("data_analysis"),
           "Ctrl+D", "chart", "Import and analyse datasets")
    _action(window, data_menu, "Open Research &Notebook", lambda: window.navigate("notebook"),
           "Ctrl+Shift+N", "note", "Open the research notebook")
    _action(window, data_menu, "Open Scientific &Library", lambda: window.navigate("library"),
           "Ctrl+L", "book", "Constants, units and formulas")
    data_menu.addSeparator()
    _action(window, data_menu, "&Back Up Workspace…", window.backup_workspace,
           "", "archive", "Write a backup of the local data directory")

    # --------------------------------------------------------------- Tools
    tools_menu = bar.addMenu("&Tools")
    _action(window, tools_menu, "Unit &Converter", lambda: window.navigate("library"),
           "Ctrl+U", "target", "Convert between SI units")
    _action(window, tools_menu, "&Sandbox (2D)", lambda: window.navigate("sandbox_2d"),
           "Ctrl+2", "grid", "Open the 2D physics sandbox")
    _action(window, tools_menu, "Sandbox (3&D)", lambda: window.navigate("sandbox_3d"),
           "Ctrl+3", "cube", "Open the 3D sandbox")
    tools_menu.addSeparator()
    _action(window, tools_menu, "&Settings…", lambda: window.navigate("settings"),
           "Ctrl+,", "settings", "Open application settings")

    # ---------------------------------------------------------------- Help
    help_menu = bar.addMenu("&Help")
    _action(window, help_menu, "&Quick Start", window.show_help, "F1", "help",
            "How to use AXIOMATA")
    _action(window, help_menu, "&About AXIOMATA", window.show_about, "", "atom",
            "Version and build information")

    return bar
