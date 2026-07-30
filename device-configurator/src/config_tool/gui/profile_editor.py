"""Profile editor modal."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable, Optional

from config_tool.gui import theme
from config_tool.models.profile import ConfigurationProfile, create_profile
from config_tool.protocol.constants import BAND_OPTIONS, format_band_option
from config_tool.profiles.validation import ValidationError


class ProfileEditorWindow(ctk.CTkToplevel):
    FIELD_PAD_X = 14
    FIELD_WIDTH = 360

    FIELDS = [
        ("name", "Name"),
        ("APPEUI", "APPEUI (16 hex)"),
        ("APPKEY", "APPKEY (32 hex)"),
        ("BAND", "BAND"),
        ("MASK", "MASK (4 hex)"),
        ("UPLINKPERIOD", "Uplink Period (seconds)"),
        ("GPSDECIMATIONFACTOR", "GPS Decimation Factor"),
    ]

    def __init__(
        self,
        master,
        profile: Optional[ConfigurationProfile] = None,
        on_save: Optional[Callable[[ConfigurationProfile], None]] = None,
        on_delete: Optional[Callable[[ConfigurationProfile], None]] = None,
        on_import: Optional[Callable[[], None]] = None,
        on_export: Optional[Callable[[ConfigurationProfile], None]] = None,
    ) -> None:
        super().__init__(master)
        self.title("Profile Editor")
        self.geometry("460x560")
        self.transient(master)
        self.grab_set()

        self._profile = profile
        self._is_new = profile is None
        self._on_save = on_save
        self._on_delete = on_delete
        self._on_import = on_import
        self._on_export = on_export

        self._entries: dict[str, ctk.CTkEntry] = {}
        self._band_var = ctk.StringVar()

        form = ctk.CTkFrame(self)
        form.pack(fill="both", expand=True, padx=12, pady=12)

        defaults = profile or create_profile(
            name="New Profile",
            APPEUI="0000000000000001",
            APPKEY="2B7E151628AED2A6ABF7158809CF4F3C",
            BAND=4,
            MASK="0000",
            UPLINKPERIOD=1800,
            GPSDECIMATIONFACTOR=8,
        )

        for idx, (key, label) in enumerate(self.FIELDS):
            ctk.CTkLabel(form, text=label, anchor="w").grid(
                row=idx * 2,
                column=0,
                sticky="w",
                padx=self.FIELD_PAD_X,
                pady=(4, 0),
            )
            if key == "BAND":
                options = [format_band_option(band_id) for band_id, _, _ in BAND_OPTIONS]
                current_band = int(getattr(defaults, key))
                self._band_var.set(format_band_option(current_band))
                option_menu = ctk.CTkComboBox(
                    form,
                    variable=self._band_var,
                    values=options,
                    state="readonly",
                    width=self.FIELD_WIDTH,
                    height=32,
                    corner_radius=theme.CORNER_RADIUS,
                    fg_color=("#FFFFFF", "#343638"),
                    border_width=2,
                    border_color=("#9AA0A6", "#565B5E"),
                    button_color=("#E9EDF1", "#3A4550"),
                    button_hover_color=(theme.ACCENT, theme.ACCENT_HOVER),
                    text_color=("#1F1F1F", "#FFFFFF"),
                    dropdown_fg_color=("#FFFFFF", "#343638"),
                    dropdown_hover_color=("#E9EDF1", "#3A4550"),
                    dropdown_text_color=("#1F1F1F", "#FFFFFF"),
                    font=ctk.CTkFont(size=13),
                )
                option_menu.grid(
                    row=idx * 2 + 1,
                    column=0,
                    sticky="ew",
                    padx=self.FIELD_PAD_X,
                    pady=(0, 4),
                )
            else:
                entry = ctk.CTkEntry(form, width=self.FIELD_WIDTH)
                entry.grid(
                    row=idx * 2 + 1,
                    column=0,
                    sticky="ew",
                    padx=self.FIELD_PAD_X,
                    pady=(0, 4),
                )
                entry.insert(0, str(getattr(defaults, key)))
                self._entries[key] = entry

        form.grid_columnconfigure(0, weight=1)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))

        # Row 1: Import | Export (both 1.5x width to match bottom row width)
        row1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))

        import_btn = ctk.CTkButton(row1, text="Import", command=self._import, **theme.secondary_button())
        import_btn.pack(side="left", padx=4, fill="x", expand=True)

        export_btn = ctk.CTkButton(row1, text="Export", command=self._export, **theme.secondary_button())
        export_btn.pack(side="left", padx=4, fill="x", expand=True)

        # Row 2: Save | Cancel | Delete
        row2 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row2.pack(fill="x")

        ctk.CTkButton(row2, text="Save", command=self._save, **theme.primary_button()).pack(
            side="left", padx=4, fill="x", expand=True
        )
        ctk.CTkButton(row2, text="Cancel", command=self.destroy, **theme.secondary_button()).pack(
            side="left", padx=4, fill="x", expand=True
        )
        if not self._is_new:
            ctk.CTkButton(row2, text="Delete", command=self._delete, **theme.danger_button()).pack(
                side="left", padx=4, fill="x", expand=True
            )
        else:
            # Spacer to keep layout consistent — same number of buttons so widths match
            ctk.CTkLabel(row2, text="").pack(side="left", padx=4, fill="x", expand=True)

    def _collect_profile(self) -> ConfigurationProfile:
        data = {key: entry.get().strip() for key, entry in self._entries.items()}
        band_id = int(self._band_var.get().rsplit("(", 1)[1].rstrip(")"))
        kwargs = dict(
            name=data["name"],
            APPEUI=data["APPEUI"],
            APPKEY=data["APPKEY"],
            BAND=band_id,
            MASK=data["MASK"],
            UPLINKPERIOD=int(data["UPLINKPERIOD"]),
            GPSDECIMATIONFACTOR=int(data["GPSDECIMATIONFACTOR"]),
        )
        if self._profile:
            kwargs["id"] = self._profile.id
        return create_profile(**kwargs)

    def _save(self) -> None:
        try:
            profile = self._collect_profile()
        except (ValidationError, ValueError) as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return
        if self._on_save:
            self._on_save(profile)
        self.destroy()

    def _delete(self) -> None:
        if self._profile and self._on_delete:
            if messagebox.askyesno("Delete Profile", f"Delete '{self._profile.name}'?", parent=self):
                self._on_delete(self._profile)
                self.destroy()

    def _import(self) -> None:
        if self._on_import:
            self._on_import()

    def _export(self) -> None:
        try:
            profile = self._collect_profile()
        except (ValidationError, ValueError) as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return
        if self._on_export:
            self._on_export(profile)
