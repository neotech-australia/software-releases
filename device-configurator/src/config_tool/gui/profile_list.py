"""Profile list with cards and FAB."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

from config_tool.models.profile import ConfigurationProfile
from config_tool.gui import theme
from config_tool.gui.tooltip import ToolTip


class ProfileCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        profile: ConfigurationProfile,
        is_active: bool,
        on_select: Callable[[ConfigurationProfile], None],
        on_edit: Callable[[ConfigurationProfile], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            corner_radius=10,
            fg_color=theme.CARD_BG,
            border_width=1,
            **kwargs,
        )
        self.profile = profile
        self._on_select = on_select
        self._on_edit = on_edit

        self.grid_columnconfigure(1, weight=1)

        self.checkbox_var = ctk.BooleanVar(value=is_active)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            width=24,
            corner_radius=6,
            border_width=2,
            fg_color=theme.PRIMARY,
            hover_color=theme.PRIMARY_HOVER,
            border_color=(theme.SLATE, theme.SLATE_DARK),
            variable=self.checkbox_var,
            command=self._on_check,
        )
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=10)

        self.name_label = ctk.CTkLabel(
            self, text=profile.name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT_HEADING, anchor="w",
        )
        self.name_label.grid(row=0, column=1, sticky="ew", padx=4, pady=(8, 0))

        self.appeui_label = ctk.CTkLabel(
            self, text=profile.APPEUI, anchor="w",
            font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED,
        )
        self.appeui_label.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 8))

        self.gear_btn = ctk.CTkButton(
            self, text="⚙", command=lambda: on_edit(profile),
            **theme.secondary_button(width=34, height=32),
        )
        self.gear_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=8)
        ToolTip(self.gear_btn, "Edit profile")

        # Whole card is clickable to select the profile
        for widget in (self, self.name_label, self.appeui_label):
            widget.bind("<Button-1>", self._on_card_click)

        self.set_active(is_active)

    def _on_card_click(self, _event=None) -> None:
        if not self.checkbox_var.get():
            self._on_select(self.profile)

    def _on_check(self) -> None:
        if self.checkbox_var.get():
            self._on_select(self.profile)
        else:
            self.checkbox_var.set(True)

    def set_active(self, active: bool) -> None:
        self.checkbox_var.set(active)
        if active:
            self.configure(border_width=2, border_color=theme.ACCENT)
        else:
            self.configure(border_width=1, border_color=("#C9D2DA", "#3A4550"))


class ProfileListFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_select: Callable[[ConfigurationProfile], None],
        on_edit: Callable[[ConfigurationProfile], None],
        on_add: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._on_edit = on_edit
        self._on_add = on_add
        self._cards: list[ProfileCard] = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Profiles",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=theme.TEXT_HEADING,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))

        # Plain frame (no scrollbar) for the profile cards
        self.card_container = ctk.CTkFrame(self, fg_color="transparent")
        self.card_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self.card_container.grid_columnconfigure(0, weight=1)

        # Centered "Add profile" button at the bottom
        self.add_btn = ctk.CTkButton(
            self,
            text="+  Add Profile",
            command=on_add,
            **theme.primary_button(width=170, height=38),
        )
        self.add_btn.grid(row=2, column=0, pady=(0, 10))

    def refresh(self, profiles: list[ConfigurationProfile], active_id: Optional[str]) -> None:
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        for idx, profile in enumerate(profiles):
            card = ProfileCard(
                self.card_container,
                profile,
                is_active=profile.id == active_id,
                on_select=self._on_select,
                on_edit=self._on_edit,
            )
            card.grid(row=idx, column=0, sticky="ew", pady=5, padx=2)
            self._cards.append(card)