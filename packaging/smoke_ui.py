"""Headless smoke test: construct the full MainWindow offscreen, visit every
page, exercise the chrome (menus, toolbar, tabs, themes) and capture
screenshots so the layout can be reviewed without a full rebuild.

Run:  python packaging\\smoke_ui.py
"""
import os
import sys
import traceback
from pathlib import Path

# Isolate data + temp on D: (C: is full) and use the offscreen Qt backend.
tmp = Path(r"D:\AXIOMATA-Data\tmp")
tmp.mkdir(parents=True, exist_ok=True)
os.environ["AXIOMATA_DATA"] = str(tmp.parent)
os.environ["TEMP"] = str(tmp)
os.environ["TMP"] = str(tmp)
os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHOTS = Path(r"D:\AXIOMATA-Data\shots")
SHOTS.mkdir(parents=True, exist_ok=True)

from PySide6.QtWidgets import QApplication  # noqa: E402

from axiomata.core.application import AppContext  # noqa: E402
from axiomata.ui.main_window import MainWindow  # noqa: E402
from axiomata.ui.themes.theme import build_stylesheet  # noqa: E402


def _shot(widget, name: str) -> None:
    try:
        widget.grab().save(str(SHOTS / f"{name}.png"))
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(build_stylesheet())
    ctx = AppContext()
    ctx.settings.update(onboarded=True, profession="physicist")
    ctx.settings.save()

    errors: list[str] = []
    try:
        win = MainWindow(ctx)
        win.resize(1560, 960)
        win.show()
        app.processEvents()

        for key in list(win._pages.keys()):
            try:
                win.navigate(key)
                app.processEvents()
                _shot(win, f"page-{key}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"navigate {key}: {type(exc).__name__}: {exc}\n"
                              + traceback.format_exc())

        # Re-open dashboard (refresh path).
        try:
            win.navigate("home")
            app.processEvents()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"home-refresh: {type(exc).__name__}: {exc}")

        # Theme switching.
        for name in ("light", "dark"):
            try:
                win.set_theme(name)
                app.processEvents()
                win.navigate("physics")
                app.processEvents()
                _shot(win, f"theme-{name}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"theme {name}: {type(exc).__name__}: {exc}")

        # Tab lifecycle: open, close, reopen.
        try:
            win.navigate("chemistry")
            app.processEvents()
            idx = win.workspace.indexOf(win._pages["chemistry"])
            win._on_tab_close_requested(idx)
            app.processEvents()
            win.navigate("chemistry")
            app.processEvents()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"tab lifecycle: {type(exc).__name__}: {exc}\n"
                          + traceback.format_exc())

        # Menu bar / toolbar sanity.
        try:
            menus = [a.text() for a in win.menuBar().actions()]
            if len(menus) < 6:
                errors.append(f"menu bar incomplete: {menus}")
            tb_count = len(win.findChildren(type(win.findChildren(__import__(
                'PySide6.QtWidgets', fromlist=['QToolBar']).QToolBar)[0])))
            if tb_count < 1:
                errors.append("no tool bar found")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"chrome: {type(exc).__name__}: {exc}")

        _shot(win, "final-dark")
        win.close()
        app.processEvents()
    except Exception:  # noqa: BLE001
        errors.append("MainWindow: " + traceback.format_exc())

    if errors:
        print("SMOKE ERRORS:")
        for e in errors:
            print("  -", e)
        return 1
    print("SMOKE OK: all pages constructed, chrome exercised, no errors")
    print(f"Screenshots: {SHOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
