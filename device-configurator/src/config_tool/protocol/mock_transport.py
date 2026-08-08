"""Mock serial transport for offline testing."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from config_tool.models.device_state import DeviceParameters
from config_tool.protocol.commands import build_config_done, build_start_config, build_write_command
from config_tool.protocol.constants import AT_OK, LINE_ENDING
from config_tool.protocol.parser import TimeoutError
from config_tool.protocol.serial_transport import Transport


class MockTransport(Transport):
    """Scriptable fake device returning canned responses."""

    DEFAULT_DUMP = DeviceParameters(
        DEVEUI="AC1F09FFFE12AB34",
        APPEUI="0000000000000001",
        APPKEY="2B7E151628AED2A6ABF7158809CF4F3C",
        BAND="4",
        MASK="0000",
        UPLINKPERIOD="1800",
        GPSDECIMATIONFACTOR="8",
        BATTERYCHARGE="85",
        BATTERYCAPACITY="1900",
        HWSTATUS="0",
    )

    def __init__(self, port: str = "MOCK", dump: Optional[DeviceParameters] = None) -> None:
        self.port = port
        self._open = False
        self._dump = dump or self.DEFAULT_DUMP
        self._state = dict(self._dump.as_dict())
        self._rx_queue: Deque[str] = deque()
        self._pending_command: Optional[str] = None

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False
        self._rx_queue.clear()

    def is_open(self) -> bool:
        return self._open

    def write_line(self, data: str) -> None:
        if not self._open:
            raise RuntimeError("Mock port is not open")
        cmd = data.rstrip(LINE_ENDING)
        self._pending_command = cmd
        self._process_command(cmd)

    def _enqueue_lines(self, lines: list[str]) -> None:
        self._rx_queue.extend(lines)

    def _process_command(self, cmd: str) -> None:
        if cmd == "ATC+STARTCONFIG":
            dump_lines = [f"{k}={v}" for k, v in self._state.items() if v]
            self._enqueue_lines(dump_lines + [AT_OK])
            return

        if cmd == "ATC+CONFIGDONE":
            self._enqueue_lines([AT_OK])
            return

        if cmd == "ATC+SAMPLETILT":
            self._enqueue_lines(["tilt_x=-0.02", "tilt_y=1.34", AT_OK])
            return

        if cmd == "ATC+ABORTGPSFIX":
            self._enqueue_lines([AT_OK])
            return

        if cmd == "ATC+GPSFIX":
            self._enqueue_lines(["latitude=35.689487", "longitude=51.389046", "altitude=1200.5", AT_OK])
            return

        if cmd == "ATC+FULLSAMPLE":
            self._enqueue_lines(
                [
                    "tilt_x=0.01",
                    "tilt_y=1.22",
                    "compass_heading=180.5",
                    "temperature=24.3",
                    "battery_charge_percent=85",
                    "battery_voltage_v=3.70",
                    AT_OK,
                ]
            )
            return

        if cmd.startswith("AT+") or cmd.startswith("ATC+"):
            if cmd.endswith("=?"):
                key = cmd.split("+", 1)[1].split("=", 1)[0]
                value = self._state.get(key, "")
                prefix = "ATC" if cmd.startswith("ATC+") else "AT"
                self._enqueue_lines([f"{prefix}+{key}={value}", AT_OK])
                return

            key_value = cmd.split("+", 1)[1]
            key, value = key_value.split("=", 1)
            self._state[key] = value
            self._enqueue_lines([AT_OK])
            return

        self._enqueue_lines(["AT_ERROR"])

    def read_line(self, timeout: Optional[float] = None) -> str:
        if not self._open:
            raise RuntimeError("Mock port is not open")
        if not self._rx_queue:
            raise TimeoutError("Mock read timeout")
        return self._rx_queue.popleft()

    def reset_state(self, dump: Optional[DeviceParameters] = None) -> None:
        self._dump = dump or self.DEFAULT_DUMP
        self._state = dict(self._dump.as_dict())
