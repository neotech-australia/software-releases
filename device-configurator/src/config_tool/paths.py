"""Application data directory resolution."""

import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return directory for profiles.json (next to executable when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def get_assets_dir() -> Path:
    """Return the bundled assets directory (icons, logo, device image).

    When frozen with PyInstaller, assets are unpacked into ``sys._MEIPASS``
    (bundle them with ``--add-data "assets:assets"``). During development
    this resolves to ``<project root>/assets``.
    """
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return base / "assets"
    return Path(__file__).resolve().parents[2] / "assets"
