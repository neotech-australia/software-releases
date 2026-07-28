from __future__ import annotations

import customtkinter as ctk


PRIMARY = "#24466E"
PRIMARY_HOVER = "#1A3450"
ACCENT = "#3E7CB1"
PANEL_BG = ("#E9EDF1", "#242B33")
CARD_BG = ("#F5F7F9", "#2E3640")
TEXT_MUTED = ("#5B6B7C", "#9AA7B4")
DANGER = "#B3392E"
DANGER_HOVER = "#8F2D24"


def apply() -> None:
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")


def primary_button(**overrides) -> dict:
    kwargs = {
        "corner_radius": 8,
        "height": 36,
        "fg_color": PRIMARY,
        "hover_color": PRIMARY_HOVER,
        "text_color": "#FFFFFF",
        "font": ctk.CTkFont(size=13, weight="bold"),
    }
    kwargs.update(overrides)
    return kwargs


def secondary_button(**overrides) -> dict:
    kwargs = {
        "corner_radius": 8,
        "height": 36,
        "fg_color": "transparent",
        "hover_color": ("#D8DFE6", "#3A4550"),
        "border_width": 1,
        "border_color": ("#8A97A5", "#5B6B7C"),
        "text_color": (PRIMARY, "#C6D3DF"),
        "font": ctk.CTkFont(size=13),
    }
    kwargs.update(overrides)
    return kwargs


def danger_button(**overrides) -> dict:
    kwargs = {
        "corner_radius": 8,
        "height": 36,
        "fg_color": DANGER,
        "hover_color": DANGER_HOVER,
        "text_color": "#FFFFFF",
        "font": ctk.CTkFont(size=13, weight="bold"),
    }
    kwargs.update(overrides)
    return kwargs
