# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path.cwd()
ICON = ROOT / "assets" / "icon.icns"
if sys.platform == "win32":
    ICON = ROOT / "assets" / "icon.ico"

datas = [(str(ROOT / "assets"), "assets")]
binaries = []
hiddenimports = ["customtkinter"]

for package_name in ("customtkinter", "vpython"):
    try:
        package_datas, package_binaries, package_hiddenimports = collect_all(
            package_name
        )
    except Exception:
        continue
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ["src/config_tool/gui/app.py"],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        name="NeoGT Device Configurator",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon=str(ICON),
        disable_windowed_traceback=False,
        exclude_binaries=True,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="NeoGT Device Configurator",
    )
    app = BUNDLE(
        coll,
        name="NeoGT Device Configurator.app",
        icon=str(ICON),
        bundle_identifier="com.neotechaustralia.neogt.device-configurator",
        info_plist={
            "CFBundleDisplayName": "NeoGT Device Configurator",
            "CFBundleName": "NeoGT Device Configurator",
            "CFBundleShortVersionString": "1.4.0",
            "CFBundleVersion": "1.4.0",
            "LSMinimumSystemVersion": "11.0",
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="NeoGT Device Configurator",
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
