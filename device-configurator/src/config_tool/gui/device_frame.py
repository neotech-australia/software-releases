"""Device parameters display and configure/disconnect."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

from config_tool.gui import theme
from config_tool.gui.board_3d_viewer import AngleSource
from config_tool.models.device_state import DeviceParameters
from config_tool.gui.tooltip import ToolTip
from config_tool.protocol.constants import format_band_value

COPY_FIELDS = {"DEVEUI", "APPEUI", "APPKEY"}

# Each group is a list of (key, label) tuples that share a row
DISPLAY_GROUPS = [
    [("DEVEUI", "DevEUI")],
    [("APPEUI", "AppEUI")],
    [("APPKEY", "AppKey")],
    [("BAND", "Band"), ("MASK", "Mask")],
    [("UPLINKPERIOD", "Uplink Period"), ("GPSDECIMATIONFACTOR", "GPS Decimation")],
    [("HWSTATUS", "HW Status")],
]

# Fields for the Measurements tab: (key, label)
MEASUREMENT_FIELDS = [
    ("tilt_x", "Tilt X"),
    ("tilt_y", "Tilt Y"),
    ("temperature", "Temperature"),
    ("compass_heading", "Compass Heading"),
]

# Fields for the GPS tab: (key, label)
GPS_FIELDS = [
    ("longitude", "Longitude"),
    ("latitude", "Latitude"),
    ("altitude", "Altitude"),
]


class DeviceFrame(ctk.CTkFrame):
    GPS_POLL_TIMEOUT = 30  # seconds

    def __init__(
        self,
        master,
        on_disconnect: Callable[[], None],
        on_configure: Callable[[], None],
        on_tab_change: Optional[Callable[[str], None]] = None,
        on_gps_poll: Optional[Callable[[], None]] = None,
        on_gps_cancel: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_disconnect = on_disconnect
        self._on_configure = on_configure
        self._on_tab_change = on_tab_change
        self._on_gps_poll = on_gps_poll
        self._on_gps_cancel = on_gps_cancel
        self._value_labels: dict[str, ctk.CTkLabel] = {}
        self._angle_source = AngleSource()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---- TabView ----
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        self.tab_config = self.tabview.add("Configuration")
        self.tab_measurements = self.tabview.add("Measurements")
        self.tab_gps = self.tabview.add("GPS")

        # Tab change detection via configure callback on each segment button
        self.tabview.configure(command=self._on_tab_selected)

        # Build each tab's content
        self._build_config_tab()
        self._build_measurements_tab()
        self._build_gps_tab()

        # ---- GPS progress bar overlay (hidden initially) ----
        self._gps_progress_frame: Optional[ctk.CTkFrame] = None
        self._gps_progress_bar: Optional[ctk.CTkProgressBar] = None
        self._gps_progress_label: Optional[ctk.CTkLabel] = None
        self._gps_polling = False
        self._gps_cancel_requested = False

        # ---- Bottom button bar ----
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=8)

        self.configure_btn = ctk.CTkButton(
            btn_frame, text="Configure", command=on_configure,
            **theme.primary_button(width=130),
        )
        self.configure_btn.pack(side="left", padx=6, pady=4)

        self.disconnect_btn = ctk.CTkButton(
            btn_frame, text="Disconnect", command=on_disconnect,
            **theme.secondary_button(width=110),
        )
        self.disconnect_btn.pack(side="right", padx=6, pady=4)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_config_tab(self) -> None:
        """Existing configuration fields inside the 'Configuration' tab."""
        self.tab_config.grid_columnconfigure(0, weight=1)
        self.tab_config.grid_columnconfigure(1, weight=1)
        self.tab_config.grid_columnconfigure(2, weight=1)
        self.tab_config.grid_columnconfigure(3, weight=1)

        for row_idx, group in enumerate(DISPLAY_GROUPS):
            if len(group) == 1:
                key, label = group[0]
                ctk.CTkLabel(self.tab_config, text=f"{label}:", anchor="w").grid(
                    row=row_idx, column=0, sticky="w", padx=(4, 8), pady=4
                )
                value_lbl = ctk.CTkLabel(self.tab_config, text="—", anchor="w")
                value_lbl.grid(row=row_idx, column=1, sticky="ew", padx=4, pady=4)
                self._value_labels[key] = value_lbl

                if key in COPY_FIELDS:
                    copy_btn = ctk.CTkButton(
                        self.tab_config,
                        text="📋",
                        width=32,
                        height=28,
                        command=lambda k=key: self._copy(k),
                    )
                    copy_btn.grid(row=row_idx, column=3, padx=4, pady=4)
                    ToolTip(copy_btn, f"Copy {label}")
            else:
                for col_offset, (key, label) in enumerate(group):
                    col = col_offset * 2  # 0 or 2
                    field_frame = ctk.CTkFrame(self.tab_config, fg_color="transparent")
                    field_frame.grid(row=row_idx, column=col, columnspan=2, sticky="ew", padx=4, pady=4)
                    field_frame.grid_columnconfigure(1, weight=1)

                    ctk.CTkLabel(field_frame, text=f"{label}:", anchor="w").grid(
                        row=0, column=0, sticky="w", padx=(0, 4)
                    )
                    value_lbl = ctk.CTkLabel(field_frame, text="—", anchor="w")
                    value_lbl.grid(row=0, column=1, sticky="ew", padx=0)
                    self._value_labels[key] = value_lbl

    def _build_field_grid(self, parent: ctk.CTkFrame, fields: list[tuple[str, str]]) -> None:
        """Build a simple label: — grid for a list of (key, label) fields."""
        parent.grid_columnconfigure(0, weight=0)
        parent.grid_columnconfigure(1, weight=1)

        for row_idx, (key, label) in enumerate(fields):
            ctk.CTkLabel(parent, text=f"{label}:", anchor="w").grid(
                row=row_idx, column=0, sticky="w", padx=(8, 8), pady=4
            )
            value_lbl = ctk.CTkLabel(parent, text="—", anchor="w")
            value_lbl.grid(row=row_idx, column=1, sticky="ew", padx=8, pady=4)
            self._value_labels[key] = value_lbl

    def _build_measurements_tab(self) -> None:
        """Sensor measurements fields inside the 'Measurements' tab."""
        self._build_field_grid(self.tab_measurements, MEASUREMENT_FIELDS)

        # "3D" button to open the orientation viewer
        btn_3d = ctk.CTkButton(
            self.tab_measurements,
            text="3D View",
            command=self._open_3d_viewer,
            **theme.secondary_button(width=90, height=30),
        )
        btn_3d.grid(row=len(MEASUREMENT_FIELDS), column=0, columnspan=2, pady=(12, 8))

    def _open_3d_viewer(self) -> None:
        """Launch the 3D board orientation viewer with the shared AngleSource."""
        from config_tool.gui.board_3d_viewer import launch

        launch(angle_source=self._angle_source)

    def _build_gps_tab(self) -> None:
        """GPS fix fields inside the 'GPS' tab."""
        self._build_field_grid(self.tab_gps, GPS_FIELDS)

        # GPS Poll button
        self.gps_poll_btn = ctk.CTkButton(
            self.tab_gps,
            text="Poll GPS Fix",
            command=self._on_gps_poll_click,
            **theme.primary_button(width=140),
        )
        self.gps_poll_btn.grid(row=len(GPS_FIELDS), column=0, columnspan=2, pady=(12, 8))

    # ------------------------------------------------------------------
    # GPS Poll with progress bar
    # ------------------------------------------------------------------

    def _on_gps_poll_click(self) -> None:
        """User clicked 'Poll GPS Fix' — show progress bar and notify parent."""
        if self._gps_polling:
            return
        self._gps_polling = True
        self._gps_cancel_requested = False
        self._show_gps_progress()
        self._start_progress_animation()
        if self._on_gps_poll is not None:
            self._on_gps_poll()

    def _show_gps_progress(self) -> None:
        """Display a progress bar overlay on the GPS tab."""
        self.gps_poll_btn.configure(state="disabled")

        self._gps_progress_frame = ctk.CTkFrame(self.tab_gps, corner_radius=8)
        self._gps_progress_frame.grid(
            row=len(GPS_FIELDS) + 1, column=0, columnspan=2,
            sticky="ew", padx=16, pady=8,
        )

        self._gps_progress_label = ctk.CTkLabel(
            self._gps_progress_frame,
            text="Polling GPS fix — this may take up to 30 seconds...",
            font=ctk.CTkFont(size=13),
        )
        self._gps_progress_label.pack(pady=(8, 4))

        self._gps_progress_bar = ctk.CTkProgressBar(
            self._gps_progress_frame,
            mode="determinate",
            width=300,
        )
        self._gps_progress_bar.set(0)
        self._gps_progress_bar.pack(pady=(0, 4))

        cancel_btn = ctk.CTkButton(
            self._gps_progress_frame,
            text="Cancel",
            command=self._cancel_gps_poll,
            **theme.danger_button(width=110),
        )
        cancel_btn.pack(pady=(4, 8))

    def _start_progress_animation(self) -> None:
        """Animate the GPS progress bar to fill over GPS_POLL_TIMEOUT seconds."""
        if not self._gps_polling or self._gps_progress_bar is None:
            return
        if self._gps_cancel_requested:
            return

        current = self._gps_progress_bar.get()
        step = 0.1 / self.GPS_POLL_TIMEOUT  # update at ~10 Hz
        new_val = min(current + step, 1.0)
        self._gps_progress_bar.set(new_val)

        if new_val < 1.0:
            self.after(100, self._start_progress_animation)

    def _cancel_gps_poll(self) -> None:
        """User cancels the GPS poll."""
        self._gps_cancel_requested = True
        self._hide_gps_progress()
        if self._on_gps_cancel is not None:
            self._on_gps_cancel()

    def _hide_gps_progress(self) -> None:
        """Remove the GPS progress bar overlay."""
        self._gps_polling = False
        if self._gps_progress_frame is not None:
            self._gps_progress_frame.destroy()
            self._gps_progress_frame = None
            self._gps_progress_bar = None
            self._gps_progress_label = None
        self.gps_poll_btn.configure(state="normal")

    def on_gps_poll_done(self) -> None:
        """Called by the parent when GPS poll finishes (success or error)."""
        self._hide_gps_progress()

    @property
    def gps_cancel_requested(self) -> bool:
        return self._gps_cancel_requested

    # ------------------------------------------------------------------

    def _copy(self, key: str) -> None:
        value = self._value_labels[key].cget("text")
        if value and value != "—":
            self.clipboard_clear()
            self.clipboard_append(value)

    @staticmethod
    def _format_measurement(value_str: str, decimals: int) -> str:
        """Round a numeric string to the given number of decimal places.
        
        If the string cannot be parsed as a float, it is returned unchanged.
        """
        try:
            return f"{float(value_str):.{decimals}f}"
        except (ValueError, TypeError):
            return value_str

    def set_parameters(self, params: Optional[DeviceParameters]) -> None:
        """Update all tab labels from a DeviceParameters object."""
        if params is None:
            for key, lbl in self._value_labels.items():
                if key in {k for group in DISPLAY_GROUPS for k, _ in group}:
                    lbl.configure(text="—")
            return

        for key, lbl in self._value_labels.items():
            value = params.get(key)
            if value is not None:
                # Apply rounding rules for measurement fields
                if key == "temperature":
                    value = self._format_measurement(value, 1)
                elif key == "compass_heading":
                    value = self._format_measurement(value, 0)
                elif key == "BAND":
                    value = format_band_value(value)
                lbl.configure(text=value)

        # Push tilt angles to the 3D viewer if available
        tilt_x_str = params.get("tilt_x")
        tilt_y_str = params.get("tilt_y")
        if tilt_x_str is not None and tilt_y_str is not None:
            try:
                tilt_x_deg = float(tilt_x_str)
                tilt_y_deg = float(tilt_y_str)
                self._angle_source.push(tilt_x_deg, tilt_y_deg)
            except (ValueError, TypeError):
                pass  # non-parseable value; just skip

    def set_busy(self, busy: bool, gps_only: bool = False) -> None:
        """Set busy state for device frame.
        
        Args:
            busy: True if an operation is in progress.
            gps_only: If True, only the GPS poll button is disabled
                     (Configure and Disconnect remain enabled so user
                     can cancel GPS by performing those actions).
        """
        if gps_only:
            # Only disable the GPS poll button during GPS-only operations
            self.configure_btn.configure(state="normal")
            self.disconnect_btn.configure(state="normal")
            if hasattr(self, 'gps_poll_btn'):
                self.gps_poll_btn.configure(state="disabled")
        else:
            state = "disabled" if busy else "normal"
            self.configure_btn.configure(state=state)
            self.disconnect_btn.configure(state=state)
            if hasattr(self, 'gps_poll_btn'):
                self.gps_poll_btn.configure(state=state)

    def _on_tab_selected(self) -> None:
        """Notify the parent app when the user switches tabs.
        
        If GPS polling is in progress and user switches away from the GPS tab,
        automatically cancel the GPS poll.
        """
        selected = self.tabview.get()
        
        # If GPS is being polled and user switches away from GPS tab, cancel it
        if self._gps_polling and selected != "GPS":
            self._cancel_gps_poll()
        
        if self._on_tab_change is not None:
            self._on_tab_change(selected)
