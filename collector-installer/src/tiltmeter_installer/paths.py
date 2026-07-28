from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Tiltmeter Platform"
PROJECT_NAME = "tiltmeter-platform"


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def template_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "templates"  # type: ignore[attr-defined]
    return package_root() / "templates"


def assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"  # type: ignore[attr-defined]
    return package_root() / "assets"


def default_install_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / "TiltmeterPlatform"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "TiltmeterPlatform"
    return home / ".local" / "share" / "tiltmeter-platform"
