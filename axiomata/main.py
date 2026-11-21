"""AXIOMATA application entry point.

Usage:
    python -m axiomata
    python axiomata/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from axiomata.core.application import AppContext
    from axiomata.services.logging_service import setup_logging
    from axiomata.ui.main_window import MainWindow
    from axiomata.ui.themes.theme import build_stylesheet
else:
    from .core.application import AppContext
    from .services.logging_service import setup_logging
    from .ui.main_window import MainWindow
    from .ui.themes.theme import build_stylesheet

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def _app_icon():
    """Return the bundled window icon, or None if the asset is unavailable."""
    from PySide6.QtGui import QIcon

    candidates = []
    # Installed/frozen layout: assets live next to the executable.
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.append(Path(base) / "assets" / "logo.ico")
    candidates.append(Path(__file__).resolve().parent / "assets" / "logo.ico")
    candidates.append(Path(__file__).resolve().parent.parent / "packaging" / "assets" / "logo.ico")
    for path in candidates:
        if path.exists():
            return QIcon(str(path))
    return None


def main(argv: list[str] | None = None) -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("AXIOMATA")
    app.setOrganizationName("AXIOMATA")
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)

    ctx = AppContext()
    logger = setup_logging(ctx.paths.logs)
    logger.info("AXIOMATA starting; data root=%s", ctx.paths.root)

    app.setStyleSheet(build_stylesheet())

    window = MainWindow(ctx)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())