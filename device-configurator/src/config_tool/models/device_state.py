"""Device parameters from serial dump."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Optional


@dataclass
class DeviceParameters:
    DEVEUI: str = ""
    APPEUI: str = ""
    APPKEY: str = ""
    BAND: str = ""
    MASK: str = ""
    UPLINKPERIOD: str = ""
    GPSDECIMATIONFACTOR: str = ""
    BATTERYCHARGE: str = ""
    BATTERYCAPACITY: str = ""
    HWSTATUS: str = ""
    tilt_x: str = ""
    tilt_y: str = ""
    compass_heading: str = ""
    temperature: str = ""
    battery_charge_percent: str = ""
    battery_voltage_v: str = ""
    latitude: str = ""
    longitude: str = ""
    altitude: str = ""
    ehpe: str = ""
    satellite_count: str = ""

    def as_dict(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def get(self, key: str) -> str:
        return getattr(self, key, "")

    def set(self, key: str, value: str) -> None:
        if hasattr(self, key):
            setattr(self, key, value)

    @classmethod
    def from_key_value_lines(cls, lines: list[str]) -> DeviceParameters:
        params = cls()
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if hasattr(params, key):
                params.set(key, value)
        return params

    def diff_writable(self, profile_values: dict[str, str]) -> dict[str, str]:
        """Return profile fields that differ from current device values."""
        changes: dict[str, str] = {}
        for key, target in profile_values.items():
            current = self.get(key)
            if current != target:
                changes[key] = target
        return changes
