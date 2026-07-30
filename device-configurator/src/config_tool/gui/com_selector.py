"""COM port selector frame."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

from config_tool.gui import theme


class ComSelectorFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_connect: Callable[[str], None],
        list_ports: Callable[[], list[str]],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_connect = on_connect
        self._list_ports = list_ports

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Select COM Port",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=theme.TEXT_HEADING,
        ).grid(row=0, column=0, columnspan=3, pady=(20, 10))

        self.port_var = ctk.StringVar(value="")
        self.port_menu = ctk.CTkOptionMenu(
            self,
            variable=self.port_var,
            values=[""],
            corner_radius=theme.CORNER_RADIUS,
            height=theme.BUTTON_HEIGHT,
            fg_color=theme.PRIMARY,
            button_color=theme.PRIMARY_HOVER,
            button_hover_color=theme.ACCENT_HOVER,
            font=ctk.CTkFont(size=13),
        )
        self.port_menu.grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=8)

        self.refresh_btn = ctk.CTkButton(
            self, text="Refresh", command=self.refresh_ports,
            **theme.secondary_button(width=84),
        )
        self.refresh_btn.grid(row=1, column=1, padx=4, pady=8)

        self.connect_btn = ctk.CTkButton(
            self, text="Connect", command=self._connect,
            **theme.primary_button(width=120),
        )
        self.connect_btn.grid(row=1, column=2, padx=(4, 16), pady=8)

        self.refresh_ports()

    def refresh_ports(self) -> None:
        ports = self._list_ports()
        if not ports:
            ports = ["No ports found"]
        current_selection = self.port_var.get()
        self.port_menu.configure(values=ports)
        # Select first port if nothing selected, or current selection is no longer valid
        if ports and (not current_selection or current_selection not in ports):
            self.port_var.set(ports[0])

    def _connect(self) -> None:
        port = self.port_var.get()
        if port and port != "No ports found":
            self._on_connect(port)

    def set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.connect_btn.configure(state=state)
        self.port_menu.configure(state=state)
        self.refresh_btn.configure(state=state)
