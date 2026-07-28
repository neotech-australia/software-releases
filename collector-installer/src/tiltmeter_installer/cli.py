from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

from tiltmeter_installer import __version__
from tiltmeter_installer.config import InstallSettings, create_installation
from tiltmeter_installer.docker_ops import (
    CommandResult,
    check_docker,
    install_requirements_best_effort,
    pull_images,
    restart_stack,
    stack_logs,
    stack_status,
    start_stack,
    stop_stack,
)
from tiltmeter_installer.paths import default_install_dir


def _print_line(line: str) -> None:
    print(line, flush=True)


def _print_result(result: CommandResult) -> int:
    if result.output:
        print(result.output)
    return 0 if result.ok else 1


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be a number") from exc
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _settings(args: argparse.Namespace) -> InstallSettings:
    return InstallSettings(
        install_dir=Path(args.install_dir).expanduser(),
        dashboard_port=args.dashboard_port,
    )


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--install-dir",
        default=str(default_install_dir()),
        help=f"runtime folder (default: {default_install_dir()})",
    )
    parser.add_argument(
        "--dashboard-port",
        default=443,
        type=_parse_port,
        help="HTTPS dashboard port (default: 443)",
    )


def _cmd_check_docker(_args: argparse.Namespace) -> int:
    return _print_result(check_docker())


def _cmd_install_docker(_args: argparse.Namespace) -> int:
    _print_line("Installing Docker requirements. This can take several minutes.")
    return _print_result(install_requirements_best_effort(_print_line))


def _cmd_install(args: argparse.Namespace) -> int:
    settings = _settings(args)
    if not args.yes and not _port_is_free(settings.dashboard_port):
        print(f"Port {settings.dashboard_port} is already in use. Use --yes to continue anyway.", file=sys.stderr)
        return 2

    _print_line("Checking Docker...")
    docker = check_docker()
    if docker.output:
        print(docker.output)
    if not docker.ok:
        print("Docker is not ready.", file=sys.stderr)
        return 1

    _print_line(f"Creating runtime files in {settings.install_dir}...")
    result = create_installation(settings)
    _print_line(f"Credentials saved to {result.credentials_file}")

    _print_line("Pulling Docker production images...")
    pull_result = pull_images(settings.install_dir, _print_line)
    if pull_result.output:
        print(pull_result.output)
    if not pull_result.ok:
        print("Image download failed.", file=sys.stderr)
        return 1

    _print_line("Starting Tiltmeter Platform...")
    start_result = start_stack(settings.install_dir)
    if start_result.output:
        print(start_result.output)
    if not start_result.ok:
        print("Install files were created, but starting the stack failed.", file=sys.stderr)
        return 1

    _print_line(f"Installed: {result.dashboard_url}")
    _print_line(f"Admin username: {result.admin_username}")
    _print_line(f"Admin password: {result.admin_password}")
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    return _print_result(start_stack(_settings(args).install_dir))


def _cmd_stop(args: argparse.Namespace) -> int:
    return _print_result(stop_stack(_settings(args).install_dir))


def _cmd_restart(args: argparse.Namespace) -> int:
    return _print_result(restart_stack(_settings(args).install_dir))


def _cmd_status(args: argparse.Namespace) -> int:
    return _print_result(stack_status(_settings(args).install_dir))


def _cmd_logs(args: argparse.Namespace) -> int:
    return _print_result(stack_logs(_settings(args).install_dir, tail=args.tail))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiltmeter-installer",
        description="Tiltmeter Collector Installer command line interface.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    check_docker_parser = subparsers.add_parser("check-docker", help="check Docker and Docker Compose readiness")
    check_docker_parser.set_defaults(func=_cmd_check_docker)

    install_docker_parser = subparsers.add_parser("install-docker", help="install Docker requirements where supported")
    install_docker_parser.set_defaults(func=_cmd_install_docker)

    install_parser = subparsers.add_parser("install", help="create runtime files, pull images, and start the stack")
    _add_common_options(install_parser)
    install_parser.add_argument("-y", "--yes", action="store_true", help="continue if the dashboard port is already in use")
    install_parser.set_defaults(func=_cmd_install)

    for name, help_text, handler in (
        ("start", "start the installed stack", _cmd_start),
        ("stop", "stop the installed stack", _cmd_stop),
        ("restart", "restart the installed stack", _cmd_restart),
        ("status", "show Docker Compose status", _cmd_status),
    ):
        subparser = subparsers.add_parser(name, help=help_text)
        _add_common_options(subparser)
        subparser.set_defaults(func=handler)

    logs_parser = subparsers.add_parser("logs", help="show Docker Compose logs")
    _add_common_options(logs_parser)
    logs_parser.add_argument("--tail", type=int, default=300, help="number of log lines to show (default: 300)")
    logs_parser.set_defaults(func=_cmd_logs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
