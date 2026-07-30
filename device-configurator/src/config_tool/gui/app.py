"""Main application window."""

from __future__ import annotations

import threading
import time
import tkinter.messagebox as messagebox
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk
import serial

from config_tool import __version__
from config_tool.controller.device_controller import DeviceController
from config_tool.controller.profile_service import ProfileService
from config_tool.gui import theme
from config_tool.gui.com_selector import ComSelectorFrame
from config_tool.gui.device_frame import DeviceFrame
from config_tool.gui.info_panel import InfoPanel
from config_tool.gui.log_window import LogWindow
from config_tool.gui.profile_editor import ProfileEditorWindow
from config_tool.gui.profile_list import ProfileListFrame
from config_tool.gui.status_bar import StatusBar
from config_tool.paths import get_assets_dir
from config_tool.logging_config import setup_logging
from config_tool.models.profile import ConfigurationProfile
from config_tool.protocol.parser import AtResponseError, TimeoutError


class ConfigToolApp(ctk.CTk):
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 720

    def __init__(self, use_mock: bool = False) -> None:
        super().__init__()
        setup_logging()

        self.title(f"LoRaWAN Configuration Tool v{__version__}")
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(680, 600)
        self._set_window_icon()

        self.profile_service = ProfileService()
        self.controller = DeviceController(use_mock=use_mock)
        self._log_window: Optional[LogWindow] = None
        self._busy = False
        self._cancel_requested = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)   # main content
        self.grid_columnconfigure(1, weight=0)   # info column (fixed)

        self.profile_frame = ProfileListFrame(
            self,
            on_select=self._on_profile_select,
            on_edit=self._open_editor,
            on_add=self._open_new_editor,
        )
        self.profile_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=(8, 2))

        # ---- Right info column (device image + company info) ----
        self.info_panel = InfoPanel(self)
        self.info_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)

        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(2, 8))
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.com_selector = ComSelectorFrame(
            self.bottom_frame,
            on_connect=self._on_connect,
            list_ports=self.controller.list_ports,
        )
        self.com_selector.grid(row=0, column=0, sticky="nsew")

        self.device_frame = DeviceFrame(
            self.bottom_frame,
            on_disconnect=self._on_disconnect,
            on_configure=self._on_configure,
            on_tab_change=self._on_tab_change,
            on_gps_poll=self._on_gps_poll,
            on_gps_cancel=self._on_gps_cancel,
        )
        self.device_frame.grid(row=0, column=0, sticky="nsew")
        self.device_frame.grid_remove()

        self.status_bar = StatusBar(self.bottom_frame, on_logs=self._show_logs)
        self.status_bar.grid(row=1, column=0, sticky="ew")

        # --- Loading overlay for connect phase ---
        self._loading_frame: Optional[ctk.CTkFrame] = None
        self._cancel_btn: Optional[ctk.CTkButton] = None

        # --- GPS polling cancellation ---
        self._gps_polling_cancelled = False

        # --- Tilt polling ---
        self._tilt_polling = False
        self._tilt_poll_thread: Optional[threading.Thread] = None
        self._tilt_poll_interval = 0.1  # 100 ms

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_profiles()

    def _set_window_icon(self) -> None:
        """Set the window/Dock icon from assets/icon.png (best effort)."""
        try:
            import tkinter as tk

            icon_path = get_assets_dir() / "icon.png"
            if icon_path.is_file():
                self._icon_image = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, self._icon_image)
        except Exception:
            pass  # icon is cosmetic — never block startup

    def _show_loading(self, message: str) -> None:
        """Show a loading overlay with progress bar and cancel button."""
        self._loading_frame = ctk.CTkFrame(self.bottom_frame, corner_radius=8)
        self._loading_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self._loading_frame.grid_rowconfigure(0, weight=1)
        self._loading_frame.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self._loading_frame, fg_color="transparent")
        inner.grid(row=0, column=0)

        self._loading_label = ctk.CTkLabel(inner, text=message, font=ctk.CTkFont(size=14))
        self._loading_label.pack(pady=(0, 8))

        self._progress_bar = ctk.CTkProgressBar(inner, mode="indeterminate", width=200)
        self._progress_bar.pack(pady=(0, 4))
        self._progress_bar.start()

        self._cancel_btn = ctk.CTkButton(
            inner,
            text="Cancel",
            command=self._request_cancel,
            **theme.danger_button(),
        )
        self._cancel_btn.pack(pady=(8, 0))

        self._loading_frame.tkraise()

    def _hide_loading(self) -> None:
        if self._loading_frame is not None:
            self._loading_frame.destroy()
            self._loading_frame = None
            self._progress_bar = None
            self._cancel_btn = None
            self._loading_label = None

    def _request_cancel(self) -> None:
        self._cancel_requested = True
        if self._loading_label:
            self._loading_label.configure(text="Cancelling...")
        if self._cancel_btn:
            self._cancel_btn.configure(state="disabled")
        # Force-close the serial port from the main thread.
        # This will break any blocking read_line() in the worker thread,
        # causing a RuntimeError that gets caught by _connect_worker.
        self.controller.abort()

    # --------------- Profile management ---------------

    def _refresh_profiles(self) -> None:
        active = self.profile_service.get_active()
        active_id = active.id if active else None
        self.profile_frame.refresh(self.profile_service.list_profiles(), active_id)

    def _on_profile_select(self, profile: ConfigurationProfile) -> None:
        self.profile_service.set_active(profile.id)
        self._refresh_profiles()
        self.status_bar.set_status(f"Active profile: {profile.name}")

    def _open_new_editor(self) -> None:
        ProfileEditorWindow(
            self,
            profile=None,
            on_save=self._save_profile,
            on_import=self._import_profile_dialog,
        )

    def _open_editor(self, profile: ConfigurationProfile) -> None:
        ProfileEditorWindow(
            self,
            profile=profile,
            on_save=self._save_profile,
            on_delete=self._delete_profile,
            on_import=self._import_profile_dialog,
            on_export=self._export_profile_dialog,
        )

    def _save_profile(self, profile: ConfigurationProfile) -> None:
        try:
            existing = None
            try:
                existing = self.profile_service.get_by_name(profile.name)
            except Exception:
                pass
            if existing and existing.id == profile.id:
                self.profile_service.update(profile)
            elif existing:
                messagebox.showerror("Error", f"Profile name '{profile.name}' already exists.")
                return
            else:
                profiles = self.profile_service.list_profiles()
                if any(p.id == profile.id for p in profiles):
                    self.profile_service.update(profile)
                else:
                    self.profile_service.store.add(profile)
            self._refresh_profiles()
            self.status_bar.set_status(f"Saved profile: {profile.name}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _delete_profile(self, profile: ConfigurationProfile) -> None:
        self.profile_service.delete(profile.id)
        self._refresh_profiles()
        self.status_bar.set_status(f"Deleted profile: {profile.name}")

    def _import_profile_dialog(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                imported = self.profile_service.import_profile(Path(path))
                self._refresh_profiles()
                self.status_bar.set_status(f"Imported profile: {imported.name}")
            except Exception as exc:
                messagebox.showerror("Import Error", str(exc))

    def _export_profile_dialog(self, profile: ConfigurationProfile) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"{profile.name}.json",
        )
        if path:
            try:
                self.profile_service.export_profile(profile.name, Path(path))
                self.status_bar.set_status(f"Exported to {path}")
            except Exception as exc:
                messagebox.showerror("Export Error", str(exc))

    # --------------- Connect / Disconnect ---------------

    def _on_connect(self, port: str) -> None:
        if self._busy:
            return
        self._cancel_requested = False
        self._show_loading(f"Connecting to {port}…")
        self._run_async(self._connect_worker, port)

    def _connect_worker(self, port: str) -> None:
        try:
            self.controller.connect(port)
            if self._cancel_requested:
                try:
                    self.controller.disconnect()
                except Exception:
                    pass
                self.after(0, lambda: self._after_connect_cancelled(port))
                return

            params = self.controller.read_device()
            if self._cancel_requested:
                try:
                    self.controller.disconnect()
                except Exception:
                    pass
                self.after(0, lambda: self._after_connect_cancelled(port))
                return

            self.after(0, lambda: self._show_device_frame(params, port))
        except Exception as exc:
            try:
                self.controller.disconnect()
            except Exception:
                pass
            if self._cancel_requested:
                self.after(0, lambda: self._after_connect_cancelled(port))
            else:
                import traceback
                traceback.print_exc()
                message = self._format_connection_error(port, exc)
                self.after(0, lambda: self._after_connect_error(message))

    def _after_connect_cancelled(self, port: str) -> None:
        self._hide_loading()
        self.status_bar.set_status(f"Cancelled connection to {port}")

    def _after_connect_error(self, message: str) -> None:
        self._hide_loading()
        self._show_error(message)

    def _format_connection_error(self, port: str, exc: Exception | None = None) -> str:
        if exc is None:
            return (
                f"Could not connect to the device on {port}.\n\n"
                "Check that the selected port is correct and the USB cable is connected.\n"
                "If a Serial Monitor, Arduino IDE, or another tool is using the port, close it and try again.\n"
                "If the device does not respond, reset it so it enters configuration mode, then reconnect."
            )

        text = str(exc).lower()
        if isinstance(exc, TimeoutError) or "timeout" in text:
            return (
                f"The device on {port} did not respond in time.\n\n"
                "Reset the device so it enters configuration mode, then try Connect again."
            )
        if isinstance(exc, serial.SerialException) or "busy" in text or "permission" in text or "access is denied" in text:
            return (
                f"Could not open {port}.\n\n"
                "The port may be in use. Close Serial Monitor, Arduino IDE, or any other app connected to the device, then try again.\n"
                "Also check that you selected the correct port."
            )
        return (
            f"Could not connect to the device on {port}.\n\n"
            "Check that the selected port is correct, the USB cable is connected, and the device is in configuration mode."
        )

    def _show_device_frame(self, params, port: str) -> None:
        self._hide_loading()
        self.com_selector.grid_remove()
        self.device_frame.grid()
        self.device_frame.set_parameters(params)
        self.info_panel.set_device_info(params)
        self.status_bar.set_status(f"Connected to {port}")

    def _can_execute_action(self) -> bool:
        """Check if a user action can proceed.
        
        Returns True if no operation is in progress. If GPS polling is the
        only thing keeping us busy, cancels it first and returns False.
        """
        if not self._busy:
            return True
        # If GPS polling is the reason we're busy, cancel it
        if self.device_frame._gps_polling and not self._gps_polling_cancelled:
            self._cancel_gps_if_active()
            return False
        return False

    def _cancel_gps_if_active(self) -> None:
        """If GPS polling is in progress, trigger a cancel.
        
        This is called when the user wants to perform another action
        (disconnect, configure, close) while GPS is being polled.
        """
        if self.device_frame._gps_polling and not self._gps_polling_cancelled:
            self._gps_polling_cancelled = True
            try:
                self.controller.abort_gps_fix()
            except Exception:
                self.controller.abort()

    def _on_disconnect(self) -> None:
        if not self._can_execute_action():
            return
        self._run_async(self._disconnect_worker)

    def _disconnect_worker(self) -> None:
        try:
            self.controller.disconnect()
            self.after(0, self._show_com_selector)
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _show_com_selector(self) -> None:
        self._stop_tilt_polling()
        self.device_frame.grid_remove()
        self.device_frame.set_parameters(None)
        self.info_panel.set_device_info(None)
        self.com_selector.grid()
        self.com_selector.refresh_ports()
        self.status_bar.set_status("Disconnected")

    # --------------- Configure ---------------

    def _on_configure(self) -> None:
        if not self._can_execute_action():
            return
        active = self.profile_service.get_active()
        if active is None:
            messagebox.showwarning("No Profile", "Select an active profile first.")
            return
        self._run_async(self._configure_worker, active)

    def _configure_worker(self, profile: ConfigurationProfile) -> None:
        try:
            result = self.controller.apply_profile(profile)
            params = self.controller.device_state
            self.after(
                0,
                lambda: self._configure_done(result.message, params, result.success),
            )
        except Exception as exc:
            self.after(0, lambda: self._show_error(f"Configure failed: {exc}"))

    def _configure_done(self, message: str, params, success: bool) -> None:
        if params:
            self.device_frame.set_parameters(params)
        self.status_bar.set_status(message)
        if not success:
            messagebox.showerror("Configuration", message)

    # --------------- Error / Logs ---------------

    def _show_error(self, message: str) -> None:
        self.status_bar.set_status(message)
        messagebox.showerror("Error", message)

    def _show_logs(self) -> None:
        if self._log_window is None or not self._log_window.winfo_exists():
            self._log_window = LogWindow(self)
        else:
            self._log_window.refresh()
            self._log_window.lift()

    # --------------- Async helpers ---------------

    def _run_async(self, func, *args, gps_only: bool = False) -> None:
        self._busy = True
        self.device_frame.set_busy(True, gps_only=gps_only)
        self.com_selector.set_enabled(False)

        def wrapper() -> None:
            try:
                func(*args)
            finally:
                self.after(0, self._clear_busy)

        threading.Thread(target=wrapper, daemon=True).start()

    def _clear_busy(self) -> None:
        self._busy = False
        self.device_frame.set_busy(False)
        self.com_selector.set_enabled(True)
        # Don't hide loading here — the individual callback handles it

    # --------------- Tilt polling ---------------

    def _on_tab_change(self, tab_name: str) -> None:
        """Start or stop tilt polling based on active tab."""
        if tab_name == "Measurements":
            self._start_tilt_polling()
        else:
            self._stop_tilt_polling()

    def _start_tilt_polling(self) -> None:
        if self._tilt_polling:
            return
        if not self.controller.is_connected:
            return
        self._tilt_polling = True
        self._tilt_poll_thread = threading.Thread(
            target=self._tilt_poll_worker, daemon=True, name="tilt-poll"
        )
        self._tilt_poll_thread.start()

    def _stop_tilt_polling(self) -> None:
        self._tilt_polling = False

    def _tilt_poll_worker(self) -> None:
        """Background thread: sample all sensors every 100 ms while active."""
        while self._tilt_polling and self.controller.is_connected:
            try:
                params = self.controller.full_sample()
            except (AtResponseError, TimeoutError, RuntimeError):
                # Device disconnected or comm error — stop polling
                self._tilt_polling = False
                break
            except Exception:
                # Other unexpected errors — stop polling
                self._tilt_polling = False
                break

            if params is not None:
                self.after(0, lambda p=params: self.device_frame.set_parameters(p))

            # Sleep in small increments so we can exit promptly
            slept = 0.0
            while slept < self._tilt_poll_interval and self._tilt_polling:
                time.sleep(0.01)
                slept += 0.01

    # --------------- GPS polling ---------------

    def _on_gps_poll(self) -> None:
        """User clicked 'Poll GPS Fix' in the device frame."""
        if self._busy:
            return
        if not self.controller.is_connected:
            self.device_frame.on_gps_poll_done()
            self._show_error("Not connected to a device")
            return
        self._gps_polling_cancelled = False
        self._run_async(self._gps_poll_worker, gps_only=True)

    def _on_gps_cancel(self) -> None:
        """User cancelled GPS poll — send graceful abort to device.
        
        Sends ATC+ABORTGPSFIX to tell the device to stop GPS acquisition.
        The device will then complete the pending GPSFIX with NO_GPS_FIX.
        """
        self._gps_polling_cancelled = True
        try:
            self.controller.abort_gps_fix()
        except Exception:
            # Fall back to brute-force abort if graceful abort fails
            self.controller.abort()

    def _gps_poll_worker(self) -> None:
        """Background thread: request GPS fix from device (may take up to 60s)."""
        try:
            if self.device_frame.gps_cancel_requested:
                self.after(0, self.device_frame.on_gps_poll_done)
                return

            params = self.controller.gps_fix()

            # After gps_fix() returns (possibly due to abort), drain leftover
            # response lines from the serial buffer (e.g., NO_GPS_FIX, trailing OK)
            if self.controller.is_connected and self.controller.at_client is not None:
                self.controller.at_client.drain()

            if self.device_frame.gps_cancel_requested:
                self.after(0, self.device_frame.on_gps_poll_done)
                return

            if params is not None:
                self.after(0, lambda p=params: self._gps_poll_done(p))
            else:
                self.after(0, self.device_frame.on_gps_poll_done)
        except (AtResponseError, TimeoutError, RuntimeError) as exc:
            self.after(0, lambda e=exc: self._gps_poll_error(e))
        except Exception as exc:
            self.after(0, lambda e=exc: self._gps_poll_error(e))

    def _gps_poll_done(self, params) -> None:
        """GPS fix obtained successfully — update display."""
        self.device_frame.on_gps_poll_done()
        self.device_frame.set_parameters(params)
        self.status_bar.set_status("GPS fix obtained")

    def _gps_poll_error(self, exc: Exception) -> None:
        """GPS fix failed — clean up and show error."""
        self.device_frame.on_gps_poll_done()
        self._show_error(f"GPS poll failed: {exc}")

    def _on_close(self) -> None:
        self._stop_tilt_polling()
        # Cancel any GPS poll in progress
        if self.device_frame._gps_polling and not self._gps_polling_cancelled:
            self._cancel_gps_if_active()
        if self.controller.is_connected:
            try:
                self.controller.disconnect()
            except Exception:
                pass
        self.destroy()


def main() -> None:
    theme.apply_global_theme()
    app = ConfigToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
