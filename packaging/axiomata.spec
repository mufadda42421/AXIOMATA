# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AXIOMATA.

Build (from the project root):
    pyinstaller packaging\\axiomata.spec

Produces dist\\AXIOMATA\\AXIOMATA.exe together with the Qt/Python runtime.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

ROOT = Path(SPECPATH).resolve().parent            # D:\AXIOMATA (SPECPATH is packaging/)
PKG = ROOT / "axiomata"
ASSETS = ROOT / "packaging" / "assets"

datas = [(str(ASSETS / "logo.ico"), "assets")]
datas += collect_data_files("axiomata")

hiddenimports = []
hiddenimports += collect_submodules("axiomata")
hiddenimports += [
    "PySide6.QtSvg",
    "rdkit",
    "pyvista",
    "pyvistaqt",
    "pyqtgraph",
    "duckdb",
    "astropy",
    "sympy",
    "matplotlib.backends.backend_qt5agg",
]

# rdkit / pyvista / astropy ship data files that must be collected.
for pkg in ("rdkit", "pyvista", "pyvistaqt", "astropy", "matplotlib"):
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

a = Analysis(  # noqa: F821
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AXIOMATA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS / "logo.ico"),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AXIOMATA",
)