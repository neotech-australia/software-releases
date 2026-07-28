from __future__ import annotations

import queue
import socket
import platform
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from tiltmeter_installer import __version__
from tiltmeter_installer.config import InstallSettings, create_installation
from tiltmeter_installer.docker_ops import (
    check_docker,
    install_requirements_best_effort,
    open_path,
    pull_images,
    restart_stack,
    stack_logs,
    stack_running,
    stack_status,
    start_stack,
    stop_stack,
)
from tiltmeter_installer.paths import assets_dir, default_install_dir
from tiltmeter_installer import theme


class InstallerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Tiltmeter Collector Installer App v{__version__}")
        self.geometry("980x720")
        self.minsize(820, 620)
        self._set_window_icon()

        self._messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self._busy = False

        self.install_dir_var = ctk.StringVar(value=str(default_install_dir()))
        self.dashboard_port_var = ctk.StringVar(value="443")
        self.status_var = ctk.StringVar(value="Ready")
        self.running_var = ctk.StringVar(value="Not running")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_form()
        self._build_actions()
        self._build_log_panel()
        self._poll_messages()
        self.after(500, self._refresh_running_status_async)

    def _set_window_icon(self) -> None:
        icon_path = assets_dir() / "icon.png"
        if not icon_path.is_file():
            return
        try:
            self._window_icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._window_icon)
        except tk.TclError:
            pass

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=theme.PRIMARY, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Tiltmeter Collector Installer App",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=8)
        form.grid(row=1, column=0, sticky="nsew", padx=(14, 7), pady=14)
        form.grid_columnconfigure(1, weight=1)

        self._label(form, "Install folder", 0)
        path_entry = ctk.CTkEntry(form, textvariable=self.install_dir_var)
        path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(14, 8))
        ctk.CTkButton(form, text="Browse", command=self._browse_install_dir, **theme.secondary_button(width=86)).grid(
            row=0, column=2, sticky="ew", padx=(0, 14), pady=(14, 8)
        )

        self._label(form, "Dashboard Port", 1)
        ctk.CTkEntry(form, textvariable=self.dashboard_port_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=8
        )
        ctk.CTkLabel(
            form,
            text="After install, open the app at https://localhost:<Dashboard Port>",
            anchor="w",
            text_color=theme.TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=(0, 14)
        )

        status_box = ctk.CTkFrame(form, fg_color=theme.PANEL_BG, corner_radius=8)
        status_box.grid(row=3, column=0, columnspan=3, sticky="ew", padx=14, pady=(4, 14))
        status_box.grid_columnconfigure(2, weight=1)
        self.running_light = ctk.CTkLabel(status_box, text="", width=16, height=16, fg_color="#B3392E", corner_radius=8)
        self.running_light.grid(row=0, column=0, sticky="w", padx=(12, 8), pady=10)
        ctk.CTkLabel(status_box, textvariable=self.running_var, anchor="w").grid(row=0, column=1, sticky="w", padx=(0, 12), pady=10)
        ctk.CTkLabel(status_box, textvariable=self.status_var, anchor="w").grid(row=0, column=2, sticky="ew", padx=(0, 12), pady=10)

    def _build_actions(self) -> None:
        actions = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=8)
        actions.grid(row=2, column=0, sticky="ew", padx=(14, 7), pady=(0, 14))
        actions.grid_columnconfigure(0, weight=1)

        install_group = ctk.CTkFrame(actions, fg_color="transparent")
        install_group.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        for col in range(3):
            install_group.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(install_group, text="Install", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

        ctk.CTkButton(install_group, text="Check Docker", command=self._check_docker, **theme.secondary_button()).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=0
        )
        ctk.CTkButton(install_group, text="Install Docker", command=self._install_requirements, **theme.secondary_button()).grid(
            row=1, column=1, sticky="ew", padx=6, pady=0
        )
        ctk.CTkButton(install_group, text="Install / Update", command=self._install_stack, **theme.primary_button()).grid(
            row=1, column=2, sticky="ew", padx=(6, 0), pady=0
        )

        run_group = ctk.CTkFrame(actions, fg_color="transparent")
        run_group.grid(row=1, column=0, sticky="ew", padx=12, pady=(8, 12))
        for col in range(3):
            run_group.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(run_group, text="Application", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

        ctk.CTkButton(run_group, text="Start", command=lambda: self._run_stack_action("Starting stack", start_stack), **theme.primary_button()).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=0
        )
        ctk.CTkButton(run_group, text="Restart", command=lambda: self._run_stack_action("Restarting stack", restart_stack), **theme.secondary_button()).grid(
            row=1, column=1, sticky="ew", padx=6, pady=0
        )
        ctk.CTkButton(run_group, text="Stop", command=lambda: self._run_stack_action("Stopping stack", stop_stack), **theme.danger_button()).grid(
            row=1, column=2, sticky="ew", padx=(6, 0), pady=0
        )

    def _build_log_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=8)
        panel.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(7, 14), pady=14)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="Status and logs", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(top, text="Status", command=self._show_status, **theme.secondary_button(width=78)).grid(row=0, column=1, padx=(8, 0))
        ctk.CTkButton(top, text="Logs", command=self._show_logs, **theme.secondary_button(width=78)).grid(row=0, column=2, padx=(8, 0))
        ctk.CTkButton(top, text="Folder", command=self._open_install_folder, **theme.secondary_button(width=78)).grid(row=0, column=3, padx=(8, 0))

        self.log_text = ctk.CTkTextbox(panel, wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._append_log("Installer ready.\n")

    def _label(self, parent: ctk.CTkFrame, text: str, row: int) -> None:
        ctk.CTkLabel(parent, text=text, anchor="w", text_color=theme.TEXT_MUTED).grid(
            row=row, column=0, sticky="w", padx=14, pady=(14 if row == 0 else 8, 8)
        )

    def _browse_install_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(Path(self.install_dir_var.get()).parent))
        if selected:
            self.install_dir_var.set(selected)

    def _settings(self) -> InstallSettings:
        dashboard_port = self._parse_port(self.dashboard_port_var.get(), "Dashboard Port")
        return InstallSettings(
            install_dir=Path(self.install_dir_var.get()).expanduser(),
            dashboard_port=dashboard_port,
        )

    def _parse_port(self, value: str, label: str) -> int:
        try:
            port = int(value)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc
        if port < 1 or port > 65535:
            raise ValueError(f"{label} must be between 1 and 65535.")
        return port

    def _port_is_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            return sock.connect_ex(("127.0.0.1", port)) != 0

    def _run_background(self, title: str, worker) -> None:
        if self._busy:
            messagebox.showinfo("Busy", "Another operation is already running.")
            return
        self._busy = True
        self.status_var.set(title)
        self._append_log(f"\n== {title} ==\n")

        def run() -> None:
            try:
                worker()
            except Exception as exc:
                self._messages.put(("error", str(exc)))
            finally:
                self._messages.put(("done", ""))

        threading.Thread(target=run, daemon=True).start()

    def _check_docker(self) -> None:
        def worker() -> None:
            result = check_docker()
            self._messages.put(("log", result.output + "\n"))
            self._messages.put(("status", "Docker is ready" if result.ok else "Docker is not ready"))
            self._queue_running_refresh()

        self._run_background("Checking Docker", worker)

    def _install_requirements(self) -> None:
        def worker() -> None:
            self._messages.put(("log", "Downloading/installing Docker requirements. Progress output will appear below.\n"))
            result = install_requirements_best_effort(lambda line: self._messages.put(("log", line + "\n")))
            self._messages.put(("log", result.output + "\n"))
            if result.ok and platform.system().lower() == "windows":
                self._messages.put(("status", "Docker installed. Close and reopen this app, then click Check Docker."))
            else:
                self._messages.put(("status", "Docker requirement install completed" if result.ok else "Docker requirement install failed"))

        self._run_background("Installing Docker requirements", worker)

    def _install_stack(self) -> None:
        try:
            settings = self._settings()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        if not self._port_is_free(settings.dashboard_port):
            proceed = messagebox.askyesno(
                "Port in use",
                f"Port {settings.dashboard_port} is already in use. Continue anyway?",
            )
            if not proceed:
                return

        def worker() -> None:
            docker = check_docker()
            self._messages.put(("log", docker.output + "\n"))
            if not docker.ok:
                self._messages.put(("status", "Docker is not ready"))
                return
            result = create_installation(settings)
            self._messages.put(("log", f"Created runtime files in {result.install_dir}\n"))
            self._messages.put(("log", f"Credentials saved to {result.credentials_file}\n"))
            self._messages.put(("log", "Downloading Docker production images. Progress output will appear as each layer is pulled.\n"))
            pull_result = pull_images(settings.install_dir, lambda line: self._messages.put(("log", line + "\n")))
            if not pull_result.ok:
                self._messages.put(("status", "Image download failed"))
                self._messages.put(("log", pull_result.output + "\n"))
                return
            start_result = start_stack(settings.install_dir)
            self._messages.put(("log", start_result.output + "\n"))
            self._messages.put(("status", f"Installed: {result.dashboard_url}" if start_result.ok else "Install completed, start failed"))
            self._queue_running_refresh()

        self._run_background("Installing Tiltmeter Platform", worker)

    def _run_stack_action(self, title: str, action) -> None:
        try:
            settings = self._settings()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def worker() -> None:
            result = action(settings.install_dir)
            self._messages.put(("log", result.output + "\n"))
            self._messages.put(("status", title + (" completed" if result.ok else " failed")))
            self._queue_running_refresh()

        self._run_background(title, worker)

    def _show_status(self) -> None:
        def worker() -> None:
            settings = self._settings()
            result = stack_status(settings.install_dir)
            self._messages.put(("log", result.output + "\n"))
            self._messages.put(("status", "Status refreshed" if result.ok else "Status failed"))
            self._queue_running_refresh()

        self._run_background("Reading stack status", worker)

    def _show_logs(self) -> None:
        self._run_stack_action("Reading stack logs", stack_logs)

    def _open_install_folder(self) -> None:
        result = open_path(Path(self.install_dir_var.get()).expanduser())
        if not result.ok:
            messagebox.showerror("Open folder failed", result.output)

    def _append_log(self, text: str) -> None:
        self.log_text.insert("end", text)
        self.log_text.see("end")

    def _queue_running_refresh(self) -> None:
        try:
            settings = self._settings()
        except ValueError:
            self._messages.put(("running", "false"))
            return
        result = stack_running(settings.install_dir)
        self._messages.put(("running", "true" if result.ok else "false"))

    def _refresh_running_status_async(self) -> None:
        threading.Thread(target=self._queue_running_refresh, daemon=True).start()

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, text = self._messages.get_nowait()
                if kind == "log":
                    self._append_log(text)
                elif kind == "status":
                    self.status_var.set(text)
                elif kind == "running":
                    is_running = text == "true"
                    self.running_var.set("Running" if is_running else "Not running")
                    self.running_light.configure(fg_color="#198754" if is_running else "#B3392E")
                elif kind == "error":
                    self.status_var.set("Error")
                    self._append_log(text + "\n")
                    messagebox.showerror("Error", text)
                elif kind == "done":
                    self._busy = False
                    if text and self.status_var.get() not in {"Error"}:
                        self.status_var.set(text)
        except queue.Empty:
            pass
        self.after(150, self._poll_messages)


def main() -> None:
    theme.apply()
    app = InstallerApp()
    app.mainloop()
