from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PROJECT_NAME = "tiltmeter-platform"


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    output: str


def run_command(args: list[str], cwd: Path | None = None, timeout: int | None = None) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return CommandResult(completed.returncode == 0, completed.stdout.strip())
    except FileNotFoundError:
        return CommandResult(False, f"Command not found: {args[0]}")
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return CommandResult(False, f"Command timed out.\n{output}".strip())


def stream_command(
    args: list[str],
    cwd: Path | None = None,
    on_line: Callable[[str], None] | None = None,
    timeout: int | None = None,
) -> CommandResult:
    output_lines: list[str] = []
    timer: threading.Timer | None = None
    try:
        process = subprocess.Popen(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
    except FileNotFoundError:
        return CommandResult(False, f"Command not found: {args[0]}")

    def kill_process() -> None:
        if process.poll() is None:
            process.kill()

    if timeout is not None:
        timer = threading.Timer(timeout, kill_process)
        timer.daemon = True
        timer.start()

    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.rstrip()
        if line:
            output_lines.append(line)
            if on_line:
                on_line(line)
    return_code = process.wait()
    if timer is not None:
        timer.cancel()
    if return_code != 0 and timeout is not None and not output_lines:
        output_lines.append("Command failed or timed out.")
    return CommandResult(return_code == 0, "\n".join(output_lines).strip())


def check_docker() -> CommandResult:
    if not shutil.which("docker"):
        return CommandResult(False, "Docker CLI is not installed or is not on PATH.")
    info = run_command(["docker", "info"], timeout=20)
    if not info.ok:
        return CommandResult(False, "Docker is installed, but Docker Desktop/Engine is not ready.\n" + info.output)
    compose = run_command(["docker", "compose", "version"], timeout=15)
    if not compose.ok:
        return CommandResult(False, "Docker Compose v2 is not available.\n" + compose.output)
    server_line = next((line.strip() for line in info.output.splitlines() if "Server Version:" in line), "Docker Engine is running")
    context_line = next((line.strip() for line in info.output.splitlines() if "Context:" in line), "")
    parts = [server_line]
    if context_line:
        parts.append(context_line)
    parts.append(compose.output)
    return CommandResult(True, "\n".join(parts))


def install_requirements_best_effort(on_line: Callable[[str], None] | None = None) -> CommandResult:
    system = platform.system().lower()
    if system == "darwin":
        if shutil.which("brew"):
            return stream_command(["brew", "install", "--cask", "docker"], timeout=1800, on_line=on_line)
        return CommandResult(False, "Homebrew is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/.")
    if system == "windows":
        if shutil.which("winget"):
            return stream_command(
                [
                    "winget",
                    "install",
                    "--id",
                    "Docker.DockerDesktop",
                    "-e",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                timeout=1800,
                on_line=on_line,
            )
        return CommandResult(False, "winget is not available. Install Docker Desktop from https://www.docker.com/products/docker-desktop/.")
    if shutil.which("apt-get"):
        return stream_command(["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose-plugin"], timeout=1800, on_line=on_line)
    if shutil.which("dnf"):
        return stream_command(["sudo", "dnf", "install", "-y", "docker", "docker-compose-plugin"], timeout=1800, on_line=on_line)
    if shutil.which("pacman"):
        return stream_command(["sudo", "pacman", "-S", "--noconfirm", "docker", "docker-compose"], timeout=1800, on_line=on_line)
    return CommandResult(False, "No supported package manager was found. Install Docker Engine and Docker Compose v2 manually.")


def compose_base_args(install_dir: Path) -> list[str]:
    return [
        "docker",
        "compose",
        "--env-file",
        str(install_dir / ".env"),
        "-f",
        str(install_dir / "docker-compose.yml"),
        "-p",
        PROJECT_NAME,
    ]


def docker_login(registry: str, username: str, token: str) -> CommandResult:
    try:
        completed = subprocess.run(
            ["docker", "login", registry, "-u", username, "--password-stdin"],
            input=token,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
        return CommandResult(completed.returncode == 0, completed.stdout.strip())
    except FileNotFoundError:
        return CommandResult(False, "Docker CLI is not installed or is not on PATH.")


def pull_images(install_dir: Path, on_line: Callable[[str], None] | None = None) -> CommandResult:
    return stream_command(compose_base_args(install_dir) + ["pull"], cwd=install_dir, timeout=1800, on_line=on_line)


def start_stack(install_dir: Path) -> CommandResult:
    return run_command(compose_base_args(install_dir) + ["up", "-d"], cwd=install_dir, timeout=600)


def stop_stack(install_dir: Path) -> CommandResult:
    return run_command(compose_base_args(install_dir) + ["stop"], cwd=install_dir, timeout=300)


def restart_stack(install_dir: Path) -> CommandResult:
    return run_command(compose_base_args(install_dir) + ["restart"], cwd=install_dir, timeout=300)


def stack_status(install_dir: Path) -> CommandResult:
    return run_command(compose_base_args(install_dir) + ["ps"], cwd=install_dir, timeout=60)


def stack_running(install_dir: Path) -> CommandResult:
    result = run_command(compose_base_args(install_dir) + ["ps", "--status", "running", "--services"], cwd=install_dir, timeout=60)
    if not result.ok:
        return result
    services = {line.strip() for line in result.output.splitlines() if line.strip()}
    return CommandResult({"dashboard", "collector"}.issubset(services), result.output)


def stack_logs(install_dir: Path, tail: int = 300) -> CommandResult:
    return run_command(compose_base_args(install_dir) + ["logs", "--tail", str(tail)], cwd=install_dir, timeout=120)


def open_path(path: Path) -> CommandResult:
    system = platform.system().lower()
    if system == "darwin":
        return run_command(["open", str(path)])
    if system == "windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return CommandResult(True, "")
    return run_command(["xdg-open", str(path)])
