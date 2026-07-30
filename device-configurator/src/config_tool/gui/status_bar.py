"""Status bar with logs button."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

from config_tool.gui import theme


class StatusBar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_logs: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self, text="Ready", anchor="w",
            font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED,
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=4)

        self.logs_button = ctk.CTkButton(
            self, text="Logs", command=on_logs,
            **theme.secondary_button(width=70, height=28),
        )
        self.logs_button.grid(row=0, column=1, padx=(4, 8), pady=4)

    def set_status(self, message: str) -> None:
        self.status_label.configure(text=message)
