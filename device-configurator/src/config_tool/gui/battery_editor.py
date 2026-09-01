"""Modal popup for editing battery charge / capacity values."""

from __future__ import annotations

import tkinter.messagebox as messagebox
from typing import Callable, Optional

import customtkinter as ctk

from config_tool.gui import theme


# Long instruction text shown inside the popup for each editable field.
EDITOR_INSTRUCTIONS = {
    "BATTERYCHARGE": (
        "Remaining battery charge is normally estimated automatically by the "
        "firmware (coulomb counting) and decreases over time.\n\n"
        "Only change this value when:\n"
        "  • A fresh / different battery has just been installed — set it to 100 "
        "so the estimator starts from a known-full state.\n"
        "  • A previously-used battery has been re-installed — set it to the "
        "measured / known remaining charge.\n\n"
        "This bypasses the normal estimation, so only set it after a battery "
        "change."
    ),
    "BATTERYCAPACITY": (
        "Total battery capacity (mAh) is used by the firmware's charge "
        "estimator to convert current draw into percentage.\n\n"
        "Change this value when the installed battery changes:\n"
        "  • A different-capacity battery is fitted.\n"
        "  • Multiple batteries are paralleled (sum their capacities).\n\n"
        "Set it to the rated capacity written on the battery label."
    ),
}

# Short tooltip shown on hover of the value / edit icon.
EDITOR_TOOLTIPS = {
    "BATTERYCHARGE": "Edit remaining charge. Set to 100 after fitting a fresh battery.",
    "BATTERYCAPACITY": "Edit total capacity (mAh). Update when the battery is changed or paralleled.",
}


class BatteryEditorWindow(ctk.CTkToplevel):
    """Modal to read / change BATTERYCHARGE and BATTERYCAPACITY."""

    FIELD_WIDTH = 220

    def __init__(
        self,
        master,
        charge_percent: str,
        capacity_mah: str,
        on_save_charge: Optional[Callable[[str], None]] = None,
        on_save_capacity: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(master)
        self.title("Battery Settings")
        self.geometry("480x520")
        self.transient(master)
        self.grab_set()

        self._on_save_charge = on_save_charge
        self._on_save_capacity = on_save_capacity

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        container.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------------
        # Row 0: Remaining charge
        # ---------------------------------------------------------------
        ctk.CTkLabel(
            container, text="Remaining Battery Charge", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(0, 2))

        self._charge_entry = ctk.CTkEntry(container, width=self.FIELD_WIDTH)
        self._charge_entry.insert(0, str(charge_percent))
        self._charge_entry.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 2))

        ctk.CTkLabel(
            container,
            text=EDITOR_INSTRUCTIONS["BATTERYCHARGE"],
            anchor="w", justify="left", wraplength=430,
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 10))

        self._charge_save_btn = ctk.CTkButton(
            container,
            text="Save Charge",
            command=self._save_charge,
            **theme.primary_button(width=140, height=30),
        )
        self._charge_save_btn.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        # ---------------------------------------------------------------
        # Separator
        # ---------------------------------------------------------------
        ctk.CTkFrame(container, height=1, fg_color=theme.SLATE).grid(
            row=4, column=0, sticky="ew", padx=8, pady=(0, 10)
        )

        # ---------------------------------------------------------------
        # Row 5+: Total capacity
        # ---------------------------------------------------------------
        ctk.CTkLabel(
            container, text="Total Battery Capacity (mAh)", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=5, column=0, sticky="w", padx=8, pady=(0, 2))

        self._capacity_entry = ctk.CTkEntry(container, width=self.FIELD_WIDTH)
        self._capacity_entry.insert(0, str(capacity_mah))
        self._capacity_entry.grid(row=6, column=0, sticky="w", padx=8, pady=(0, 2))

        ctk.CTkLabel(
            container,
            text=EDITOR_INSTRUCTIONS["BATTERYCAPACITY"],
            anchor="w", justify="left", wraplength=430,
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED,
        ).grid(row=7, column=0, sticky="w", padx=8, pady=(0, 10))

        self._capacity_save_btn = ctk.CTkButton(
            container,
            text="Save Capacity",
            command=self._save_capacity,
            **theme.primary_button(width=140, height=30),
        )
        self._capacity_save_btn.grid(row=8, column=0, sticky="w", padx=8, pady=(0, 8))

        # Close button
        close_btn = ctk.CTkButton(
            container, text="Close", command=self.destroy,
            **theme.secondary_button(width=140),
        )
        close_btn.grid(row=9, column=0, sticky="w", padx=8, pady=(8, 0))

    # ------------------------------------------------------------------

    def _validate_charge(self, value: str) -> int | None:
        """Return validated percent (0-100) or None and show an error."""
        try:
            percent = int(value)
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Value",
                "Battery charge must be a whole number between 0 and 100.",
                parent=self,
            )
            return None
        if percent < 0 or percent > 100:
            messagebox.showerror(
                "Invalid Value",
                "Battery charge must be between 0 and 100.",
                parent=self,
            )
            return None
        return percent

    def _save_charge(self) -> None:
        percent = self._validate_charge(self._charge_entry.get().strip())
        if percent is None:
            return
        if self._on_save_charge:
            self._on_save_charge(str(percent))

    def _save_capacity(self) -> None:
        value = self._capacity_entry.get().strip()
        try:
            mah = int(value)
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Value",
                "Battery capacity must be a whole number of mAh greater than 0.",
                parent=self,
            )
            return
        if mah <= 0:
            messagebox.showerror(
                "Invalid Value",
                "Battery capacity must be greater than 0 mAh.",
                parent=self,
            )
            return
        if self._on_save_capacity:
            self._on_save_capacity(str(mah))