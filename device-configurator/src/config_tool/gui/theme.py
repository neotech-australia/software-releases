"""Shared UI theme for a Neotech Geotechnical Engineering (neogt.com.au) look.

Professional engineering palette: deep navy primary, slate secondary,
restrained red for destructive actions. All widgets should source their
colors and shapes from here so the app stays visually consistent.
"""

from __future__ import annotations

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Company / product identity
# ---------------------------------------------------------------------------

COMPANY_NAME = "Neotech Geotechnical Engineering"
COMPANY_SHORT = "NEOTECH"
COMPANY_TAGLINE = "Mining Geotechnical Consultants"
COMPANY_WEBSITE = "www.neogt.com.au"
COMPANY_WEBSITE_URL = "https://www.neogt.com.au/"
PRODUCT_NAME = "Settlement Monitoring Sensor"

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

PRIMARY = "#24466E"          # deep engineering navy
PRIMARY_HOVER = "#1A3450"
PRIMARY_TEXT = "#FFFFFF"

ACCENT = "#3E7CB1"           # steel blue for highlights / links
ACCENT_HOVER = "#336793"

SLATE = "#8A97A5"            # secondary button border / muted text
SLATE_DARK = "#5B6B7C"

DANGER = "#B3392E"
DANGER_HOVER = "#8F2D24"

# (light, dark) tuples for text on transparent backgrounds
TEXT_MUTED = ("#5B6B7C", "#9AA7B4")
TEXT_HEADING = ("#1E2E40", "#E8EDF2")
LINK_COLOR = ("#3E7CB1", "#7FB3DC")

PANEL_BG = ("#E9EDF1", "#242B33")     # info column background
CARD_BG = ("#F5F7F9", "#2E3640")      # cards on top of panels

CORNER_RADIUS = 8
BUTTON_HEIGHT = 36


# ---------------------------------------------------------------------------
# Button kwargs helpers
#
# CTkFont must be created after the root window exists, so these are
# functions rather than module-level constants.
# ---------------------------------------------------------------------------

def primary_button(**overrides) -> dict:
    """Kwargs for the main call-to-action buttons (Connect, Configure, Save)."""
    kwargs = dict(
        corner_radius=CORNER_RADIUS,
        height=BUTTON_HEIGHT,
        fg_color=PRIMARY,
        hover_color=PRIMARY_HOVER,
        text_color=PRIMARY_TEXT,
        font=ctk.CTkFont(size=13, weight="bold"),
    )
    kwargs.update(overrides)
    return kwargs


def secondary_button(**overrides) -> dict:
    """Kwargs for secondary/outline buttons (Refresh, Cancel, Logs...)."""
    kwargs = dict(
        corner_radius=CORNER_RADIUS,
        height=BUTTON_HEIGHT,
        fg_color="transparent",
        hover_color=("#D8DFE6", "#3A4550"),
        border_width=1,
        border_color=(SLATE, SLATE_DARK),
        text_color=(PRIMARY, "#C6D3DF"),
        font=ctk.CTkFont(size=13),
    )
    kwargs.update(overrides)
    return kwargs


def danger_button(**overrides) -> dict:
    """Kwargs for destructive buttons (Delete, Cancel operation)."""
    kwargs = dict(
        corner_radius=CORNER_RADIUS,
        height=BUTTON_HEIGHT,
        fg_color=DANGER,
        hover_color=DANGER_HOVER,
        text_color=PRIMARY_TEXT,
        font=ctk.CTkFont(size=13, weight="bold"),
    )
    kwargs.update(overrides)
    return kwargs


def apply_global_theme() -> None:
    """Set customtkinter global appearance. Call once before creating the app."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
