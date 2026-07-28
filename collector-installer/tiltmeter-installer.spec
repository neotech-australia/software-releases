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

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        name="Tiltmeter Collector Installer App",
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
        name="Tiltmeter Collector Installer App",
    )
    app = BUNDLE(
        coll,
        name="Tiltmeter Collector Installer App.app",
        icon=str(ICON),
        bundle_identifier="com.neotechaustralia.tiltmeter.collector-installer",
        info_plist={
            "CFBundleDisplayName": "Tiltmeter Collector Installer",
            "CFBundleName": "Tiltmeter Collector Installer",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "LSMinimumSystemVersion": "11.0",
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
        name="Tiltmeter Collector Installer App",
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
