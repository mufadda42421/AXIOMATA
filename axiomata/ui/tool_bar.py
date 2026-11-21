"""Application tool bar.

A single row of the highest-frequency actions, mirroring the strip beneath
the menu bar in MATLAB, Origin and Igor. Buttons carry both an icon and a
short label so the tool bar stays readable when the icons are small.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from .icons import icon
from .themes.theme import TEXT_SECONDARY

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .main_window import MainWindow


def _add(
    bar: QToolBar,
    window: "MainWindow",
    text: str,
    icon_name: str,
    slot,
    tooltip: str,
) -> QAction:
    act = QAction(icon(icon_name, color=TEXT_SECONDARY, size=17), text, window)
    act.setToolTip(tooltip)
    act.triggered.connect(slot)
    bar.addAction(act)
    return act


def build_tool_bar(window: "MainWindow") -> QToolBar:
    """Construct and install the AXIOMATA tool bar on ``window``."""
    bar = QToolBar("Main", window)
    bar.setObjectName("MainToolBar")
    bar.setMovable(False)
    bar.setFloatable(False)
    bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    bar.setIconSize(QSize(17, 17))

    _add(bar, window, "New Project", "plus", window.create_project,
         "Create a new research project (Ctrl+N)")
    _add(bar, window, "Experiment", "activity", window.new_experiment,
         "Record a new experiment (Ctrl+E)")
    _add(bar, window, "Data", "upload", window.import_dataset,
         "Import a dataset (Ctrl+I)")

    bar.addSeparator()

    _add(bar, window, "Run", "play", window.run_current,
         "Run the active simulation (F5)")
    _add(bar, window, "Reset", "reset", window.reset_current,
         "Reset the active parameters (Shift+F5)")

    bar.addSeparator()

    _add(bar, window, "Export", "download", window.export_results,
         "Export results as CSV (Ctrl+S)")
    _add(bar, window, "Figure", "chart", window.export_figure,
         "Export the active figure as an image")

    bar.addSeparator()

    bar.addAction(window.toggle_sidebar_action)
    bar.addAction(window.toggle_console_action)
    bar.addAction(window.toggle_inspector_action)

    window.addToolBar(bar)
    return bar
