"""Configuration profile model."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from config_tool.profiles.validation import (
    ValidationError,
    validate_appeui,
    validate_appkey,
    validate_band,
    validate_gps_decimation_factor,
    validate_mask,
    validate_profile_name,
    validate_uplink_period,
)


@dataclass
class ConfigurationProfile:
    name: str
    APPEUI: str
    APPKEY: str
    BAND: int
    MASK: str
    UPLINKPERIOD: int
    GPSDECIMATIONFACTOR: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def validate(self) -> None:
        self.name = validate_profile_name(self.name)
        self.APPEUI = validate_appeui(self.APPEUI)
        self.APPKEY = validate_appkey(self.APPKEY)
        self.BAND = validate_band(self.BAND)
        self.MASK = validate_mask(self.MASK, self.BAND)
        self.UPLINKPERIOD = validate_uplink_period(self.UPLINKPERIOD)
        self.GPSDECIMATIONFACTOR = validate_gps_decimation_factor(self.GPSDECIMATIONFACTOR)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfigurationProfile:
        profile = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            APPEUI=data["APPEUI"],
            APPKEY=data["APPKEY"],
            BAND=data["BAND"],
            MASK=data["MASK"],
            UPLINKPERIOD=data["UPLINKPERIOD"],
            GPSDECIMATIONFACTOR=data["GPSDECIMATIONFACTOR"],
        )
        profile.validate()
        return profile

    def writable_values(self) -> dict[str, str]:
        return {
            "APPEUI": self.APPEUI,
            "APPKEY": self.APPKEY,
            "BAND": str(self.BAND),
            "MASK": self.MASK,
            "UPLINKPERIOD": str(self.UPLINKPERIOD),
            "GPSDECIMATIONFACTOR": str(self.GPSDECIMATIONFACTOR),
        }


def create_profile(**kwargs: Any) -> ConfigurationProfile:
    profile = ConfigurationProfile(
        name=kwargs.get("name", ""),
        APPEUI=kwargs.get("APPEUI", kwargs.get("appeui", "")),
        APPKEY=kwargs.get("APPKEY", kwargs.get("appkey", "")),
        BAND=kwargs.get("BAND", kwargs.get("band", 4)),
        MASK=kwargs.get("MASK", kwargs.get("mask", "0000")),
        UPLINKPERIOD=kwargs.get("UPLINKPERIOD", kwargs.get("uplinkperiod", 1800)),
        GPSDECIMATIONFACTOR=kwargs.get(
            "GPSDECIMATIONFACTOR", kwargs.get("gpsdecimationfactor", 8)
        ),
        id=kwargs.get("id", str(uuid.uuid4())),
    )
    profile.validate()
    return profile
