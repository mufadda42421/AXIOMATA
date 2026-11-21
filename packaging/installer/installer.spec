# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the AXIOMATA installer.

Run packaging\\build.py first: it builds the app and stages the frozen app into
packaging\\installer\\payload\\AXIOMATA. This spec then bundles that payload (plus
the logo assets) into a single installer executable.

Build standalone (after staging the payload):
    pyinstaller packaging\\installer\\installer.spec
"""
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

HERE = Path(SPECPATH).resolve()                 # packaging/installer
ROOT = HERE.parent.parent                          # D:\AXIOMATA
ASSETS = ROOT / "packaging" / "assets"
PAYLOAD = HERE / "payload" / "AXIOMATA"

datas = [
    (str(ASSETS / "logo.ico"), "assets"),
    (str(ASSETS / "logo.png"), "assets"),
]
# Bundle the entire frozen application as the install payload.
if PAYLOAD.exists():
    datas.append((str(PAYLOAD), "payload/AXIOMATA"))

hiddenimports = ["PySide6.QtSvg"] + collect_submodules("PySide6")

a = Analysis(  # noqa: F821
    [str(HERE / "build_installer.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "rdkit", "pyvista", "astropy", "matplotlib", "numpy",
              "scipy", "sympy", "pandas", "duckdb", "pyqtgraph"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

# Single-file installer: one distributable AXIOMATA-Setup.exe.
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AXIOMATA-Setup",
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