"""Headless installer for AXIOMATA (installs to a chosen drive, default D:).

The C: drive on this machine is full, so this installs the frozen app to
``D:\\Programs\\AXIOMATA`` and stores user data on the same drive via a tiny
portable launcher that sets ``AXIOMATA_DATA`` for the app process only (no global
environment changes).

    python packaging\\headless_install.py            # installs to D:\\Programs\\AXIOMATA
    python packaging\\headless_install.py "E:\\..."   # custom install dir

Steps:
  1. Copy dist\\AXIOMATA -> <install dir>.
  2. Create <data dir> (default D:\\AXIOMATA-Data).
  3. Write AXIOMATA.exe.config.json (data dir marker).
  4. Create Start Menu + Desktop shortcuts to the portable launcher.
  5. Register an uninstaller in the registry.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "AXIOMATA"
APP_EXE = "AXIOMATA.exe"
VERSION = "0.1.0"
PUBLISHER = "AXIOMATA"
REG_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"

ROOT = Path(__file__).resolve().parent.parent
DIST_APP = ROOT / "dist" / APP_NAME
SETUP = ROOT / "dist" / "AXIOMATA-Setup.exe"
ASSETS = ROOT / "packaging" / "assets"

DEFAULT_INSTALL = Path("D:/Programs/AXIOMATA")
DEFAULT_DATA = Path("D:/AXIOMATA-Data")


def _ps_shortcut(lnk: Path, target_exe: Path, workdir: Path, icon: Path,
                 argument: str = "") -> None:
    # Pass values through the environment to avoid fragile quoting in PowerShell.
    ps = (
        "$s=(New-Object -ComObject WScript.Shell);"
        "$d=$s.CreateShortcut($env:AX_LNK);"
        "$d.TargetPath=$env:AX_EXE;"
        "$d.Arguments=$env:AX_ARG;"
        "$d.WorkingDirectory=$env:AX_WD;"
        "$d.IconLocation=$env:AX_ICON;"
        "$d.Description='AXIOMATA - Scientific Research & Simulation Environment';"
        "$d.Save()"
    )
    lnk.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "AX_LNK": str(lnk),
        "AX_EXE": str(target_exe),
        "AX_ARG": argument,
        "AX_WD": str(workdir),
        "AX_ICON": str(icon),
    })
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   check=False, capture_output=True, timeout=30, env=env)


def _write_launcher(target: Path, data_dir: Path) -> Path:
    """Create a hidden VBScript launcher that sets AXIOMATA_DATA and runs the exe."""
    launcher = target / "launch.vbs"
    launcher.write_text(
        "Set sh = CreateObject(\"WScript.Shell\")\r\n"
        f"sh.Environment(\"Process\")(\"AXIOMATA_DATA\") = \"{data_dir}\"\r\n"
        f"sh.CurrentDirectory = \"{target}\"\r\n"
        f"sh.Run \"\"\"{target / APP_EXE}\"\"\", 1, False\r\n",
        encoding="utf-8",
    )
    return launcher


def create_shortcuts(target: Path, launcher: Path) -> None:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    start = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}.lnk"
    desktop = Path(os.path.expanduser("~")) / "Desktop" / f"{APP_NAME}.lnk"
    icon = target / "assets" / "logo.ico"
    # Shortcuts target wscript.exe running the hidden VBScript launcher.
    wscript = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "wscript.exe"
    for lnk in (start, desktop):
        _ps_shortcut(lnk, wscript, target, icon, argument=f'"{launcher}"')
        print(f"  shortcut: {lnk}  exists={lnk.exists()}")


def register_uninstaller(target: Path) -> None:
    import winreg
    uninstaller = target / "uninstall.exe"
    if SETUP.exists():
        shutil.copy2(SETUP, uninstaller)
    launcher = target / "AXIOMATA.cmd"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(target / "assets" / "logo.ico"))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller}" --uninstall')
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninstaller}" --uninstall --silent')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(key, "Comments", 0, winreg.REG_SZ, f"Data stored in {target.parent}")
    print(f"  registered uninstaller in HKCU\\{REG_KEY}")


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_INSTALL
    # Store user data on the same drive as the install (e.g. D:\\AXIOMATA-Data).
    data_dir = Path(target.drive + "\\AXIOMATA-Data")

    if not (DIST_APP / APP_EXE).exists():
        print(f"ERROR: {DIST_APP / APP_EXE} not found. Run packaging\\build.py first.")
        return 1

    free = shutil.disk_usage(target.drive + "\\").free
    print(f"Install dir : {target}")
    print(f"Data dir    : {data_dir}")
    print(f"Free on {target.drive}: {free / (1024**3):.1f} GB")

    if target.exists():
        print("  removing previous install…")
        shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    print("  copying application files…")
    shutil.copytree(DIST_APP, target, dirs_exist_ok=True)

    launcher = _write_launcher(target, data_dir)
    (target / "config.json").write_text(json.dumps({"data_dir": str(data_dir)}, indent=2), encoding="utf-8")

    create_shortcuts(target, launcher)
    register_uninstaller(target)

    print(f"\nINSTALL COMPLETE")
    print(f"  App (launcher) : {launcher}")
    print(f"  Data           : {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())