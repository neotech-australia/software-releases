# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

ROOT = Path.cwd()
ICON = ROOT / "assets" / "icon.icns"
if sys.platform == "win32":
    ICON = ROOT / "assets" / "icon.ico"

a = Analysis(
    ["src/tiltmeter_installer/__main__.py"],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "templates"), "templates"),
        (str(ROOT / "assets"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Tiltmeter Platform Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(ICON),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
