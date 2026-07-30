"""High-level AT/ATC client."""

from __future__ import annotations

import logging
import time
from typing import Optional

from config_tool.models.device_state import DeviceParameters
from config_tool.protocol.commands import (
    build_action_command,
    build_config_done,
    build_read_command,
    build_start_config,
    build_write_command,
)
from config_tool.protocol.constants import DEFAULT_READ_TIMEOUT, DEFAULT_SESSION_TIMEOUT, DEVICE_DUMP_KEYS
from config_tool.protocol.parser import (
    AtResponseError,
    TimeoutError,
    is_error_line,
    is_ignorable_line,
    is_ok_line,
    parse_dump_lines,
    parse_echo_value,
)
from config_tool.protocol.serial_transport import Transport

logger = logging.getLogger("config_tool.protocol")


class AtClient:
    def __init__(
        self,
        transport: Transport,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        session_timeout: float = DEFAULT_SESSION_TIMEOUT,
    ) -> None:
        self.transport = transport
        self.read_timeout = read_timeout
        self.session_timeout = session_timeout
        self._in_config_session = False
        self._last_dump: Optional[DeviceParameters] = None

    @property
    def in_config_session(self) -> bool:
        return self._in_config_session

    @property
    def last_dump(self) -> Optional[DeviceParameters]:
        return self._last_dump

    def _read_protocol_line(self, deadline: float) -> str:
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError("Timed out waiting for device response")
            line = self.transport.read_line(timeout=self.read_timeout)
            if is_ignorable_line(line):
                logger.debug("Ignoring non-protocol line: %r", line)
                continue
            return line

    def _read_until_ok(self) -> list[str]:
        lines: list[str] = []
        deadline = time.monotonic() + self.session_timeout
        while True:
            line = self._read_protocol_line(deadline)
            lines.append(line)
            if is_error_line(line):
                raise AtResponseError(line)
            if is_ok_line(line):
                return lines

    @staticmethod
    def _strip_at_prefix(key: str) -> str:
        """Remove AT+ or ATC+ prefix from a key string."""
        for prefix in ("ATC+", "AT+"):
            if key.startswith(prefix):
                return key[len(prefix):]
        return key

    @staticmethod
    def _strip_at_prefix_from_line(line: str) -> str:
        """Remove AT+ or ATC+ prefix from the beginning of a KEY=VALUE line."""
        for prefix in ("ATC+", "AT+"):
            if line.startswith(prefix):
                return line[len(prefix):]
        return line

    def start_config(self) -> DeviceParameters:
        self.transport.write_line(build_start_config())
        dump_lines: list[str] = []
        deadline = time.monotonic() + self.session_timeout
        while True:
            try:
                line = self._read_protocol_line(deadline)
            except TimeoutError:
                if dump_lines:
                    # Collected some params; timeout marks end of async dump
                    logger.info("TIMEOUT after collecting %d parameter(s) - dump complete", len(dump_lines))
                    break
                # No params collected - device didn't respond
                logger.error("TIMEOUT waiting for device response to ATC+STARTCONFIG - no data received")
                raise

            if is_error_line(line):
                logger.error("AT_ERROR during config start: %s", line.strip())
                raise AtResponseError(line)
            if is_ok_line(line):
                # OK acknowledges command but params may follow asynchronously
                logger.debug("STARTCONFIG acknowledged, collecting parameters...")
                continue
            if "=" in line:
                raw_key = line.split("=", 1)[0].strip()
                key = self._strip_at_prefix(raw_key)
                if key in DEVICE_DUMP_KEYS:
                    clean_line = self._strip_at_prefix_from_line(line.strip())
                    dump_lines.append(clean_line)
                    logger.debug("Collected parameter: %s", key)

        params = parse_dump_lines(dump_lines)
        self._last_dump = params
        self._in_config_session = True

        if not dump_lines:
            logger.error("PARSING FAILED - no device parameters collected from dump")
        else:
            logger.info("PARSE SUCCESS - read %d device parameters from dump", len(dump_lines))

        return params

    def write_parameter(self, key: str, value: str) -> None:
        self.transport.write_line(build_write_command(key, value))
        self._read_until_ok()
        if self._last_dump is not None:
            self._last_dump.set(key, value)

    def read_parameter(self, key: str) -> str:
        self.transport.write_line(build_read_command(key))
        value = ""
        deadline = time.monotonic() + self.session_timeout
        while True:
            line = self._read_protocol_line(deadline)
            if is_error_line(line):
                raise AtResponseError(line)
            parsed = parse_echo_value(line)
            if parsed and parsed[0] == key:
                value = parsed[1]
                continue
            if is_ok_line(line):
                break
        return value

    def config_done(self) -> None:
        if self._in_config_session:
            self.transport.write_line(build_config_done())
            self._read_until_ok()
            self._in_config_session = False
            logger.info("Configuration session ended")

    def ensure_config_done(self) -> None:
        if self._in_config_session:
            try:
                self.config_done()
            except (AtResponseError, TimeoutError) as exc:
                logger.warning("Failed to send CONFIGDONE: %s", exc)
                self._in_config_session = False

    def run_action(self, key: str) -> DeviceParameters:
        """Send an action-only command (no parameters) and collect result lines.

        The device responds with KEY=VALUE lines (or special error lines)
        followed by OK. All valid key=value pairs are stored in a returned
        DeviceParameters.
        """
        self.transport.write_line(build_action_command(key))
        result_lines: list[str] = []
        deadline = time.monotonic() + self.session_timeout

        while True:
            line = self._read_protocol_line(deadline)
            if is_ok_line(line):
                break
            if is_error_line(line):
                raise AtResponseError(line)
            if "=" in line:
                clean_line = self._strip_at_prefix_from_line(line.strip())
                result_lines.append(clean_line)

        params = DeviceParameters.from_key_value_lines(result_lines)
        logger.info("Action %s returned %d value(s)", key, len(result_lines))
        return params

    def sample_tilt(self) -> DeviceParameters:
        """Send ATC+SAMPLETILT and return tilt readings.

        Returns DeviceParameters with tilt_x and tilt_y populated.
        """
        return self.run_action("SAMPLETILT")

    def gps_fix(self) -> DeviceParameters:
        """Send ATC+GPSFIX and return GPS fix readings.

        May take up to 30 seconds. Returns DeviceParameters with
        latitude, longitude, altitude populated.
        """
        original_session = self.session_timeout
        original_read = self.read_timeout
        # GPS fix may need up to 30s; use generous per-line read timeout
        # to avoid read_line() timing out while device is acquiring a fix.
        self.session_timeout = max(self.session_timeout, 35.0)
        self.read_timeout = 35.0
        try:
            return self.run_action("GPSFIX")
        finally:
            self.session_timeout = original_session
            self.read_timeout = original_read

    def abort_gps_fix(self) -> None:
        """Send ATC+ABORTGPSFIX to cancel an ongoing GPS fix acquisition.

        Fire-and-forget: writes the abort command without reading the response.
        The pending GPSFIX action (blocked in another thread) will complete
        (the ABORTGPSFIX response line and any remaining GPSFIX response lines
        will be read by the blocked gps_fix() reader). After gps_fix() returns,
        call drain() to clean up any leftover lines.
        """
        try:
            self.transport.write_line(build_action_command("ABORTGPSFIX"))
            logger.info("GPS fix abort command sent to device")
        except (RuntimeError, OSError) as exc:
            logger.warning("Failed to send GPS abort command: %s", exc)

    def drain(self) -> None:
        """Drain any leftover response lines from the serial buffer.
        
        Call this after abort_gps_fix() interrupts a gps_fix() call to
        clear any remaining lines (e.g., NO_GPS_FIX + OK from the aborted
        GPSFIX command) from the serial read buffer.
        """
        deadline = time.monotonic() + self.read_timeout
        drained = 0
        while time.monotonic() < deadline:
            try:
                line = self.transport.read_line(timeout=0.1)
                logger.debug("Drained line: %r", line)
                drained += 1
            except TimeoutError:
                break  # No more data to drain
            except RuntimeError:
                break  # Port closed
        if drained > 0:
            logger.info("Drained %d leftover line(s) after GPS abort", drained)

    def full_sample(self) -> DeviceParameters:
        """Send ATC+FULLSAMPLE and return all sensor readings.

        Returns DeviceParameters with tilt_x, tilt_y, compass_heading,
        temperature, battery_charge_percent, battery_voltage_v populated.
        """
        return self.run_action("FULLSAMPLE")
