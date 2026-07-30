"""Tests for protocol parser."""

from config_tool.models.device_state import DeviceParameters
from config_tool.protocol.parser import (
    is_device_log_line,
    is_error_line,
    is_ignorable_line,
    is_ok_line,
    parse_dump_lines,
    parse_echo_value,
    prefix_for_key,
)


def test_parse_dump_lines():
    lines = [
        "DEVEUI=AC1F09FFFE12AB34",
        "APPEUI=0000000000000001",
        "BAND=4",
        "HWSTATUS=0",
    ]
    params = parse_dump_lines(lines)
    assert params.DEVEUI == "AC1F09FFFE12AB34"
    assert params.APPEUI == "0000000000000001"
    assert params.BAND == "4"
    assert params.HWSTATUS == "0"


def test_diff_writable():
    device = DeviceParameters(APPEUI="0000000000000001", BAND="4")
    changes = device.diff_writable({"APPEUI": "0000000000000001", "BAND": "5"})
    assert changes == {"BAND": "5"}


def test_response_helpers():
    assert is_ok_line("OK")
    assert is_error_line("AT_PARAM_ERROR")
    assert parse_echo_value("AT+APPEUI=0000000000000001") == ("APPEUI", "0000000000000001")
    assert parse_echo_value("ATC+UPLINKPERIOD=600") == ("UPLINKPERIOD", "600")


def test_prefix_for_key():
    assert prefix_for_key("APPEUI") == "AT"
    assert prefix_for_key("UPLINKPERIOD") == "ATC"


def test_device_log_lines():
    assert is_device_log_line("[00:07:05] [serial] [DEBUG] ATC+STARTCONFIG received")
    assert is_device_log_line("[12:34:56] [node] [INFO] save_config: done")
    assert not is_device_log_line("OK")
    assert not is_device_log_line("DEVEUI=AC1F09FFFE12AB34")
    assert is_ignorable_line("")
    assert is_ignorable_line("[00:07:05] [serial] [DEBUG] waiting for CONFIGDONE")
    assert not is_ignorable_line("OK")
