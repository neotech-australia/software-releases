"""Validation helpers for profiles and device parameters."""

import re
from typing import List, Optional

from config_tool.protocol.constants import MASK_APPLICABLE_BANDS

HEX16 = re.compile(r"^[0-9a-fA-F]{16}$")
HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")
HEX4 = re.compile(r"^[0-9a-fA-F]{4}$")
DECIMAL = re.compile(r"^\d+$")


class ValidationError(ValueError):
    """Raised when a field fails validation."""


def validate_appeui(value: str) -> str:
    if not HEX16.match(value):
        raise ValidationError("APPEUI must be exactly 16 hex digits")
    return value.upper()


def validate_appkey(value: str) -> str:
    if not HEX32.match(value):
        raise ValidationError("APPKEY must be exactly 32 hex digits")
    return value.upper()


def validate_band(value) -> int:
    try:
        band = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("BAND must be an integer 0-12") from exc
    if not 0 <= band <= 12:
        raise ValidationError("BAND must be between 0 and 12")
    return band


def validate_mask(value: str, band: Optional[int] = None) -> str:
    if band is not None and band not in MASK_APPLICABLE_BANDS:
        if not value:
            return "0000"
        if HEX4.match(value):
            return value.upper()
        raise ValidationError("MASK must be 4 hex digits when provided")
    if not HEX4.match(value):
        raise ValidationError("MASK must be exactly 4 hex digits")
    return value.upper()


def validate_uplink_period(value) -> int:
    text = str(value)
    if not DECIMAL.match(text):
        raise ValidationError("UPLINKPERIOD must be a non-negative decimal integer")
    return int(text)


def validate_gps_decimation_factor(value) -> int:
    text = str(value)
    if not DECIMAL.match(text):
        raise ValidationError("GPSDECIMATIONFACTOR must be a non-negative decimal integer")
    return int(text)


def validate_profile_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValidationError("Profile name cannot be empty")
    return name
