"""Device connection and configuration orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from config_tool.models.device_state import DeviceParameters
from config_tool.models.profile import ConfigurationProfile
from config_tool.protocol.at_client import AtClient
from config_tool.protocol.mock_transport import MockTransport
from config_tool.protocol.parser import AtResponseError, TimeoutError
from config_tool.protocol.serial_transport import SerialTransport, Transport, list_serial_ports

logger = logging.getLogger("config_tool.controller")


@dataclass
class ApplyResult:
    success: bool
    changes_applied: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    message: str = ""


class DeviceController:
    def __init__(self, use_mock: bool = False) -> None:
        self._use_mock = use_mock
        self._transport: Optional[Transport] = None
        self._client: Optional[AtClient] = None
        self._connected_port: Optional[str] = None
        self._device_state: Optional[DeviceParameters] = None

    @property
    def is_connected(self) -> bool:
        return self._transport is not None and self._transport.is_open()

    @property
    def connected_port(self) -> Optional[str]:
        return self._connected_port

    @property
    def device_state(self) -> Optional[DeviceParameters]:
        return self._device_state

    def list_ports(self) -> list[str]:
        if self._use_mock:
            return ["MOCK"]
        return list_serial_ports()

    def connect(self, port: str) -> None:
        if self.is_connected:
            self.disconnect()
        if self._use_mock or port.upper() == "MOCK":
            self._transport = MockTransport(port=port)
        else:
            self._transport = SerialTransport(port=port)
        self._transport.open()
        self._client = AtClient(self._transport)
        self._connected_port = port
        logger.info("Connected to %s", port)

    def disconnect(self) -> None:
        if self._client:
            self._client.ensure_config_done()
        self._close_transport()

    def abort(self) -> None:
        """Forcefully abort any in-progress I/O without sending CONFIGDONE."""
        logger.info("Aborting connection")
        self._close_transport()

    def _close_transport(self) -> None:
        if self._transport and self._transport.is_open():
            self._transport.close()
        self._transport = None
        self._client = None
        self._connected_port = None
        self._device_state = None
        logger.info("Disconnected")

    def read_device(self) -> DeviceParameters:
        self._ensure_connected()
        assert self._client is not None
        if self._client.in_config_session:
            self._client.ensure_config_done()
        params = self._client.start_config()
        self._device_state = params
        return params

    def apply_profile(self, profile: ConfigurationProfile) -> ApplyResult:
        self._ensure_connected()
        assert self._client is not None

        profile.validate()
        if self._device_state is None or not self._client.in_config_session:
            self._device_state = self._client.start_config()

        changes = self._device_state.diff_writable(profile.writable_values())
        if not changes:
            self._client.config_done()
            return ApplyResult(success=True, message="Device already matches profile")

        applied: dict[str, str] = {}
        errors: dict[str, str] = {}

        for key, value in changes.items():
            try:
                self._client.write_parameter(key, value)
                applied[key] = value
            except (AtResponseError, TimeoutError) as exc:
                errors[key] = str(exc)
                logger.error("Failed to write %s: %s", key, exc)

        try:
            self._client.config_done()
        except (AtResponseError, TimeoutError) as exc:
            return ApplyResult(
                success=False,
                changes_applied=applied,
                errors=errors,
                message=f"CONFIGDONE failed: {exc}",
            )

        success = len(errors) == 0
        message = "Configuration applied successfully" if success else "Configuration partially failed"
        return ApplyResult(success=success, changes_applied=applied, errors=errors, message=message)

    @property
    def at_client(self) -> Optional[AtClient]:
        return self._client

    def sample_tilt(self):
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        return self._client.sample_tilt()

    def gps_fix(self):
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        return self._client.gps_fix()

    def abort_gps_fix(self) -> None:
        """Send ATC+ABORTGPSFIX to the device to cancel an ongoing GPS fix."""
        if self._client is None:
            return
        try:
            self._client.abort_gps_fix()
        except Exception as exc:
            logger.warning("Failed to abort GPS fix: %s", exc)

    def full_sample(self):
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        return self._client.full_sample()

    def read_battery_charge(self) -> str:
        """Read the remaining battery charge percentage from the device."""
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        return self._client.read_battery_charge()

    def write_battery_charge(self, percent: str) -> None:
        """Write the remaining battery charge percentage to the device."""
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        self._client.write_battery_charge(percent)
        if self._device_state is not None:
            self._device_state.set("BATTERYCHARGE", percent)

    def read_battery_capacity(self) -> str:
        """Read the total battery capacity (mAh) from the device."""
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        return self._client.read_battery_capacity()

    def write_battery_capacity(self, mah: str) -> None:
        """Write the total battery capacity (mAh) to the device."""
        if self._client is None:
            raise RuntimeError("Not connected to a device")
        self._client.write_battery_capacity(mah)
        if self._device_state is not None:
            self._device_state.set("BATTERYCAPACITY", mah)

    def _ensure_connected(self) -> None:
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to a device")
