"""AXIOMATA build orchestrator.

Runs the full Windows packaging pipeline with zero external tooling beyond
PyInstaller (already a dependency):

    1. Generate logo assets (packaging\\assets).
    2. Freeze the application  -> dist\\AXIOMATA\\AXIOMATA.exe
    3. Stage the frozen app into the installer payload.
    4. Build the single-file installer -> dist\\AXIOMATA-Setup.exe

Usage (from the project root):
    python packaging\\build.py

The distributable is dist\\AXIOMATA-Setup.exe.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"
DIST = ROOT / "dist"
BUILD = ROOT / "build"

# The system C: drive may be low on space; keep all temp scratch on the build
# drive (D:) so PyInstaller never fails with "not enough space on the disk".
_TMP = ROOT / "_build_tmp"
_TMP.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(_TMP)
os.environ["TMP"] = str(_TMP)


def run(cmd: list[str]) -> None:
    print("\n$", " ".join(str(c) for c in cmd), "\n")
    subprocess.run([str(c) for c in cmd], cwd=ROOT, check=True)


def clean_stale() -> None:
    for d in (DIST / "AXIOMATA", BUILD / "AXIOMATA",
              DIST / "AXIOMATA-Setup", BUILD / "AXIOMATA-Setup"):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    payload = PACKAGING / "installer" / "payload"
    if payload.exists():
        shutil.rmtree(payload, ignore_errors=True)


def main() -> int:
    pyinstaller = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean"]

    print("== [1/4] Generating logo assets ==")
    run([sys.executable, PACKAGING / "make_logo.py"])

    print("== [2/4] Freezing application ==")
    run(pyinstaller + [PACKAGING / "axiomata.spec"])

    app_dir = DIST / "AXIOMATA"
    if not (app_dir / "AXIOMATA.exe").exists():
        print("ERROR: application build failed (AXIOMATA.exe missing).")
        return 1

    print("== [3/4] Staging installer payload ==")
    payload_root = PACKAGING / "installer" / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    stage = payload_root / "AXIOMATA"
    if stage.exists():
        shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(app_dir, stage)
    print(f"Staged {app_dir} -> {stage}")

    print("== [4/4] Building installer ==")
    run(pyinstaller + [PACKAGING / "installer" / "installer.spec"])

    setup = DIST / "AXIOMATA-Setup.exe"
    if not setup.exists():
        print("ERROR: installer build failed (AXIOMATA-Setup.exe missing).")
        return 1

    size_mb = setup.stat().st_size / (1024 * 1024)
    print("\nBUILD COMPLETE")
    print(f"  Application : {app_dir / 'AXIOMATA.exe'}")
    print(f"  Installer   : {setup}  ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())