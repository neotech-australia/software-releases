"""Build AT/ATC command strings."""

from config_tool.protocol.constants import LINE_ENDING
from config_tool.protocol.parser import prefix_for_key


def build_write_command(key: str, value: str) -> str:
    prefix = prefix_for_key(key)
    return f"{prefix}+{key}={value}{LINE_ENDING}"


def build_read_command(key: str) -> str:
    prefix = prefix_for_key(key)
    return f"{prefix}+{key}=?{LINE_ENDING}"


def build_start_config() -> str:
    return f"ATC+STARTCONFIG{LINE_ENDING}"


def build_config_done() -> str:
    return f"ATC+CONFIGDONE{LINE_ENDING}"


def build_action_command(key: str) -> str:
    prefix = prefix_for_key(key)
    return f"{prefix}+{key}{LINE_ENDING}"
