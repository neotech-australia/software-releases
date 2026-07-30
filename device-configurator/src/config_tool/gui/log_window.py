"""Log viewer window. Newest entries are shown at the top."""

from __future__ import annotations

import customtkinter as ctk

from config_tool.gui import theme
from config_tool.logging_config import get_log_lines


class LogWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("Application Logs")
        self.geometry("700x440")
        self.transient(master)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 0))

        ctk.CTkLabel(
            header,
            text="Newest entries first",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(side="left", padx=4)

        refresh_btn = ctk.CTkButton(
            header, text="Refresh", command=self.refresh,
            **theme.secondary_button(width=90, height=28),
        )
        refresh_btn.pack(side="right")

        self.text = ctk.CTkTextbox(
            self,
            wrap="none",
            font=ctk.CTkFont(family="Menlo", size=12),
        )
        self.text.pack(fill="both", expand=True, padx=8, pady=8)

        self.refresh()

    def refresh(self) -> None:
        lines = get_log_lines()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        # Newest first so the latest activity is visible without scrolling
        self.text.insert("1.0", "\n".join(reversed(lines)))
        self.text.configure(state="disabled")
        self.text.yview_moveto(0.0)
