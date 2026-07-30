"""Parse KEY=VALUE dumps and AT responses."""

import re
from typing import List, Optional, Tuple

from config_tool.models.device_state import DeviceParameters
from config_tool.protocol.constants import AT_ERRORS, AT_OK, BUILTIN_KEYS, CUSTOM_KEYS

ECHO_PATTERN = re.compile(r"^ATC?\+(\w+)=(.+)$")
# Matches log lines starting with [HH:MM:SS] timestamp (the device's snprintf format)
DEVICE_LOG_PATTERN = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]")

# Special error/results lines from action commands (SAMPLETILT, GPSFIX, FULLSAMPLE)
ACTION_ERROR_LINES = frozenset({"INCLINATION_SENSOR_ERROR", "NO_GPS_FIX", "NO_DATA_FROM_GPS_MODULE"})


class ProtocolError(Exception):
    """Base protocol error."""


class AtResponseError(ProtocolError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        if not message:
            from config_tool.protocol.errors import format_at_error

            message = format_at_error(code)
        super().__init__(message)


class TimeoutError(ProtocolError):
    pass


def parse_dump_lines(lines: List[str]) -> DeviceParameters:
    return DeviceParameters.from_key_value_lines(lines)


def is_error_line(line: str) -> bool:
    return line.strip() in AT_ERRORS


def is_ok_line(line: str) -> bool:
    return line.strip() == AT_OK


def is_device_log_line(line: str) -> bool:
    """Return True for firmware debug log lines that share the UART."""
    return bool(DEVICE_LOG_PATTERN.match(line.strip()))


def is_ignorable_line(line: str) -> bool:
    """Lines that are not part of the AT/ATC protocol response."""
    stripped = line.strip()
    return not stripped or is_device_log_line(line)


def parse_echo_value(line: str) -> Optional[tuple]:
    match = ECHO_PATTERN.match(line.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def prefix_for_key(key: str) -> str:
    if key in BUILTIN_KEYS:
        return "AT"
    if key in CUSTOM_KEYS:
        return "ATC"
    raise ValueError(f"Unknown parameter key: {key}")
