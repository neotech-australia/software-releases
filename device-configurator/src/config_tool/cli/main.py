"""CLI entry point."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from config_tool.controller.device_controller import DeviceController
from config_tool.controller.profile_service import ProfileService
from config_tool.logging_config import setup_logging
from config_tool.models.profile import ConfigurationProfile, create_profile
from config_tool.profiles.store import ProfileNotFoundError
from config_tool.profiles.validation import ValidationError


def _print_profiles(profiles: list, active_id: Optional[str]) -> None:
    if not profiles:
        print("No profiles defined.")
        return
    for p in profiles:
        active = " *" if p.id == active_id else ""
        print(f"{p.name}{active}")
        print(f"  APPEUI: {p.APPEUI}")
        print(f"  APPKEY: {p.APPKEY}")
        print(f"  BAND: {p.BAND}  MASK: {p.MASK}")
        print(f"  UPLINKPERIOD: {p.UPLINKPERIOD}  GPSDECIMATIONFACTOR: {p.GPSDECIMATIONFACTOR}")
        print()


def _print_device(params) -> None:
    for key, value in params.as_dict().items():
        print(f"{key}: {value}")


def _profiles_parser(sub: argparse._SubParsersAction) -> None:
    profiles = sub.add_parser("profiles", help="Manage configuration profiles")
    psub = profiles.add_subparsers(dest="profiles_cmd", required=True)

    psub.add_parser("list", help="List all profiles")

    add_p = psub.add_parser("add", help="Add a profile")
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--appeui", required=True)
    add_p.add_argument("--appkey", required=True)
    add_p.add_argument("--band", type=int, required=True)
    add_p.add_argument("--mask", required=True)
    add_p.add_argument("--uplinkperiod", type=int, required=True)
    add_p.add_argument("--gpsdecimationfactor", type=int, required=True)

    edit_p = psub.add_parser("edit", help="Edit a profile by name")
    edit_p.add_argument("--name", required=True)
    edit_p.add_argument("--new-name")
    edit_p.add_argument("--appeui")
    edit_p.add_argument("--appkey")
    edit_p.add_argument("--band", type=int)
    edit_p.add_argument("--mask")
    edit_p.add_argument("--uplinkperiod", type=int)
    edit_p.add_argument("--gpsdecimationfactor", type=int)

    del_p = psub.add_parser("delete", help="Delete a profile")
    del_p.add_argument("--name", required=True)

    active_p = psub.add_parser("set-active", help="Set active profile")
    active_p.add_argument("--name", required=True)

    imp_p = psub.add_parser("import", help="Import profile from JSON file")
    imp_p.add_argument("--file", required=True, type=Path)

    exp_p = psub.add_parser("export", help="Export profile to JSON file")
    exp_p.add_argument("--name", required=True)
    exp_p.add_argument("--file", required=True, type=Path)


def _connect_parser(sub: argparse._SubParsersAction) -> None:
    connect = sub.add_parser("connect", help="Connect to device")
    connect.add_argument("--port", required=True)
    connect.add_argument("--profile", help="Profile name for apply action")
    csub = connect.add_subparsers(dest="connect_cmd", required=True)
    csub.add_parser("read", help="Read device parameters")
    csub.add_parser("disconnect", help="Disconnect from device")
    apply_p = csub.add_parser("apply", help="Apply active or named profile")
    apply_p.add_argument("--profile")


def _handle_profiles(args: argparse.Namespace, service: ProfileService) -> int:
    try:
        if args.profiles_cmd == "list":
            active = service.get_active()
            active_id = active.id if active else None
            _print_profiles(service.list_profiles(), active_id)
            return 0

        if args.profiles_cmd == "add":
            service.add(
                name=args.name,
                APPEUI=args.appeui,
                APPKEY=args.appkey,
                BAND=args.band,
                MASK=args.mask,
                UPLINKPERIOD=args.uplinkperiod,
                GPSDECIMATIONFACTOR=args.gpsdecimationfactor,
            )
            print(f"Added profile: {args.name}")
            return 0

        if args.profiles_cmd == "edit":
            profile = service.get_by_name(args.name)
            if args.new_name:
                profile.name = args.new_name
            if args.appeui:
                profile.APPEUI = args.appeui
            if args.appkey:
                profile.APPKEY = args.appkey
            if args.band is not None:
                profile.BAND = args.band
            if args.mask:
                profile.MASK = args.mask
            if args.uplinkperiod is not None:
                profile.UPLINKPERIOD = args.uplinkperiod
            if args.gpsdecimationfactor is not None:
                profile.GPSDECIMATIONFACTOR = args.gpsdecimationfactor
            profile.validate()
            service.update(profile)
            print(f"Updated profile: {profile.name}")
            return 0

        if args.profiles_cmd == "delete":
            service.delete_by_name(args.name)
            print(f"Deleted profile: {args.name}")
            return 0

        if args.profiles_cmd == "set-active":
            service.set_active_by_name(args.name)
            print(f"Active profile: {args.name}")
            return 0

        if args.profiles_cmd == "import":
            profile = service.import_profile(args.file)
            print(f"Imported profile: {profile.name}")
            return 0

        if args.profiles_cmd == "export":
            service.export_profile(args.name, args.file)
            print(f"Exported profile to {args.file}")
            return 0

    except (ValidationError, ValueError, ProfileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 1


def _handle_connect(args: argparse.Namespace, controller: DeviceController, service: ProfileService) -> int:
    try:
        if args.connect_cmd == "disconnect":
            controller.disconnect()
            print("Disconnected")
            return 0

        controller.connect(args.port)

        if args.connect_cmd == "read":
            params = controller.read_device()
            _print_device(params)
            controller.disconnect()
            return 0

        if args.connect_cmd == "apply":
            profile_name = getattr(args, "profile", None)
            if profile_name:
                profile = service.get_by_name(profile_name)
            else:
                profile = service.get_active()
                if profile is None:
                    print("Error: No active profile set", file=sys.stderr)
                    controller.disconnect()
                    return 1
            result = controller.apply_profile(profile)
            print(result.message)
            if result.changes_applied:
                print("Applied:", json.dumps(result.changes_applied))
            if result.errors:
                print("Errors:", json.dumps(result.errors), file=sys.stderr)
            controller.disconnect()
            return 0 if result.success else 1

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        try:
            controller.disconnect()
        except Exception:
            pass
        return 1
    return 1


def main(argv: Optional[list] = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="LoRaWAN Configuration Tool CLI")
    parser.add_argument("--mock", action="store_true", help="Use mock serial device")
    sub = parser.add_subparsers(dest="command", required=True)

    _profiles_parser(sub)
    sub.add_parser("ports", help="List available COM ports")
    _connect_parser(sub)

    args = parser.parse_args(argv)
    service = ProfileService()
    controller = DeviceController(use_mock=args.mock)

    if args.command == "ports":
        ports = controller.list_ports()
        if not ports:
            print("No COM ports found.")
        else:
            for port in ports:
                print(port)
        return 0

    if args.command == "profiles":
        return _handle_profiles(args, service)

    if args.command == "connect":
        return _handle_connect(args, controller, service)

    return 1


if __name__ == "__main__":
    sys.exit(main())
