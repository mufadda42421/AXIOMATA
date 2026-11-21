"""AXIOMATA installer (GUI).

A self-contained, dependency-free Windows installer built with PyInstaller. The
frozen AXIOMATA application (dist\\AXIOMATA) is bundled into this installer as a
payload folder; running the installer copies it to the install directory, creates
Start Menu + Desktop shortcuts, and registers an uninstaller in the registry.

Build via packaging\\build.py (which runs PyInstaller on both the app and this
installer). When run as a plain script (not frozen) it expects the app payload at
packaging\\payload\\AXIOMATA for testing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

APP_NAME = "AXIOMATA"
APP_EXE = "AXIOMATA.exe"
VERSION = "0.1.0"
PUBLISHER = "AXIOMATA"
INSTALL_SUBDIR = Path("Programs") / APP_NAME
REG_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"

# Palette (matches the app)
BG = "#080D16"
PANEL = "#111B2A"
ELEVATED = "#172337"
BORDER = "#24344A"
ACCENT = "#36C5E8"
TEXT = "#E8F0FA"
TEXT2 = "#91A2B8"

QSS = f"""
* {{ font-family: 'Segoe UI Variable Text','Segoe UI',sans-serif; }}
QWidget#Root {{ background-color: {BG}; }}
QLabel#Title {{ color: {TEXT}; font-size: 26px; font-weight: 700; }}
QLabel#Sub {{ color: {TEXT2}; font-size: 13px; }}
QLabel#H {{ color: {TEXT}; font-size: 13px; font-weight: 600; }}
QLabel#Meta {{ color: {TEXT2}; font-size: 12px; }}
QFrame#Card {{ background-color: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}
QPushButton#Primary {{
    background-color: {ACCENT}; color: {BG}; border: none; border-radius: 8px;
    padding: 10px 22px; font-size: 13px; font-weight: 600;
}}
QPushButton#Primary:hover {{ background-color: #4FD2F0; }}
QPushButton#Ghost {{
    background: transparent; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 10px 22px; font-size: 13px;
}}
QPushButton#Ghost:hover {{ border-color: {ACCENT}; }}
QProgressBar {{
    background-color: {ELEVATED}; border: none; border-radius: 6px;
    height: 8px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 6px; }}
"""


# --------------------------------------------------------------------------
# Resources
# --------------------------------------------------------------------------
def _resource_dir() -> Path:
    """Directory containing bundled resources (assets, payload)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base)
    return Path(__file__).resolve().parent


def _icon() -> QIcon:
    for name in ("assets/logo.ico", "assets/logo.png"):
        p = _resource_dir() / name
        if p.exists():
            return QIcon(str(p))
    return QIcon()


def _payload_dir() -> Path | None:
    """Location of the frozen app payload to install."""
    d = _resource_dir() / "payload" / APP_NAME
    if (d / APP_EXE).exists():
        return d
    # Dev fallback.
    dev = Path(__file__).resolve().parent / "payload" / APP_NAME
    if (dev / APP_EXE).exists():
        return dev
    return None


def install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    return Path(base) / INSTALL_SUBDIR


# --------------------------------------------------------------------------
# Install worker
# --------------------------------------------------------------------------
class InstallWorker(QThread):
    progress = Signal(int, str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, payload: Path, target: Path):
        super().__init__()
        self.payload = payload
        self.target = target

    def run(self) -> None:  # noqa: C901
        try:
            self.progress.emit(5, "Preparing…")
            if self.target.exists():
                shutil.rmtree(self.target, ignore_errors=True)
            self.target.mkdir(parents=True, exist_ok=True)

            self.progress.emit(15, "Copying application files…")
            shutil.copytree(self.payload, self.target, dirs_exist_ok=True)

            self.progress.emit(70, "Creating shortcuts…")
            _create_shortcuts(self.target)

            self.progress.emit(85, "Registering uninstaller…")
            _register_uninstaller(self.target)

            self.progress.emit(100, "Complete")
            self.finished_ok.emit(str(self.target))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{exc}\n\n{traceback.format_exc()}")


def _shortcuts_path(*parts: str) -> Path:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    return Path(appdata) / Path(*parts)


def _create_shortcuts(target: Path) -> None:
    exe = str(target / APP_EXE)
    icon = str(target / "assets" / "logo.ico")
    workdir = str(target)
    ps = (
        "$s=(New-Object -ComObject WScript.Shell);"
        "$d=$s.CreateShortcut('{path}');"
        "$d.TargetPath='{exe}';"
        "$d.WorkingDirectory='{wd}';"
        "$d.IconLocation='{icon}';"
        "$d.Description='AXIOMATA - Scientific Research & Simulation Environment';"
        "$d.Save()"
    )
    places = {
        "start_menu": _shortcuts_path(
            "Microsoft", "Windows", "Start Menu", "Programs", f"{APP_NAME}.lnk"
        ),
        "desktop": Path(os.path.expanduser("~")) / "Desktop" / f"{APP_NAME}.lnk",
    }
    for key, lnk in places.items():
        try:
            lnk.parent.mkdir(parents=True, exist_ok=True)
            cmd = ps.format(path=str(lnk).replace("\\", "\\\\"),
                            exe=exe.replace("\\", "\\\\"),
                            wd=workdir.replace("\\", "\\\\"),
                            icon=icon.replace("\\", "\\\\"))
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                check=False, capture_output=True, timeout=30,
            )
        except Exception:
            pass


def _register_uninstaller(target: Path) -> None:
    try:
        import winreg
        uninstaller = target / "uninstall.exe"
        # Ship a copy of this installer as the uninstaller if frozen.
        if getattr(sys, "frozen", False):
            shutil.copy2(sys.executable, uninstaller)
        cmd = f'"{uninstaller}" --uninstall' if uninstaller.exists() else ""
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(target / "assets" / "logo.ico"))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, cmd)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass


def _uninstall(target: Path) -> None:
    # Remove shortcuts.
    for lnk in (
        _shortcuts_path("Microsoft", "Windows", "Start Menu", "Programs", f"{APP_NAME}.lnk"),
        Path(os.path.expanduser("~")) / "Desktop" / f"{APP_NAME}.lnk",
    ):
        try:
            lnk.unlink()
        except OSError:
            pass
    # Remove registry key.
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
    except OSError:
        pass
    # Remove install dir (best effort; running exe may be locked).
    shutil.rmtree(target, ignore_errors=True)


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Install {APP_NAME}")
        self.setWindowIcon(_icon())
        self.setFixedSize(560, 440)
        self.setObjectName("Root")
        self.setStyleSheet(QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 32)
        root.setSpacing(16)

        # Header
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(_resource_dir() / "assets" / "logo.png")).scaled(
            72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        head.addWidget(logo)
        titles = QVBoxLayout()
        t = QLabel(APP_NAME)
        t.setObjectName("Title")
        titles.addWidget(t)
        s = QLabel("Scientific Research & Simulation Environment")
        s.setObjectName("Sub")
        titles.addWidget(s)
        head.addLayout(titles, 1)
        root.addLayout(head)

        # Card
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(10)
        self.status = QLabel("Ready to install.")
        self.status.setObjectName("H")
        cl.addWidget(self.status)
        self.detail = QLabel(
            f"Version {VERSION}\n"
            f"Install location: {install_dir()}\n\n"
            "User data and projects are stored separately and are not affected."
        )
        self.detail.setObjectName("Meta")
        self.detail.setWordWrap(True)
        cl.addWidget(self.detail)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setVisible(False)
        cl.addWidget(self.bar)
        root.addWidget(card, 1)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("Ghost")
        self.cancel_btn.clicked.connect(self.close)
        btns.addWidget(self.cancel_btn)
        self.install_btn = QPushButton("Install")
        self.install_btn.setObjectName("Primary")
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.clicked.connect(self._start)
        btns.addWidget(self.install_btn)
        root.addLayout(btns)

        self.worker: InstallWorker | None = None

    def _start(self) -> None:
        payload = _payload_dir()
        if payload is None:
            self.status.setText("Installation error")
            self.detail.setText(
                "Application payload not found. Rebuild the installer with "
                "packaging\\build.py."
            )
            return
        self.install_btn.setEnabled(False)
        self.cancel_btn.setText("Close")
        self.bar.setVisible(True)
        self.worker = InstallWorker(payload, install_dir())
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_ok)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str) -> None:
        self.bar.setValue(pct)
        self.status.setText(msg)

    def _on_ok(self, target: str) -> None:
        self.status.setText("Installation complete")
        self.detail.setText(
            f"AXIOMATA {VERSION} has been installed to:\n{target}\n\n"
            "Shortcuts were added to your Start Menu and Desktop.\n"
            "Launch AXIOMATA now?"
        )
        self.install_btn.setText("Launch AXIOMATA")
        self.install_btn.setEnabled(True)
        self.install_btn.clicked.disconnect()
        self.install_btn.clicked.connect(lambda: self._launch(target))

    def _launch(self, target: str) -> None:
        exe = Path(target) / APP_EXE
        if exe.exists():
            subprocess.Popen([str(exe)], cwd=target)
        self.close()

    def _on_fail(self, msg: str) -> None:
        self.bar.setVisible(False)
        self.status.setText("Installation failed")
        self.detail.setText(msg)
        self.install_btn.setEnabled(True)
        self.install_btn.setText("Retry")
        self.install_btn.clicked.disconnect()
        self.install_btn.clicked.connect(lambda: (self.bar.setValue(0), self._start()))


def run_uninstall() -> int:
    target = install_dir()
    _uninstall(target)
    print(f"AXIOMATA uninstalled from {target}")
    return 0


def main() -> int:
    if "--uninstall" in sys.argv:
        return run_uninstall()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = InstallerWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())