"""Tests for profile validation."""

import pytest

from config_tool.profiles.validation import (
    ValidationError,
    validate_appeui,
    validate_appkey,
    validate_band,
    validate_gps_decimation_factor,
    validate_mask,
    validate_uplink_period,
)


def test_validate_appeui_ok():
    assert validate_appeui("0000000000000001") == "0000000000000001"


def test_validate_appeui_bad_length():
    with pytest.raises(ValidationError):
        validate_appeui("1234")


def test_validate_appkey_ok():
    assert validate_appkey("2B7E151628AED2A6ABF7158809CF4F3C") == "2B7E151628AED2A6ABF7158809CF4F3C"


def test_validate_band_range():
    assert validate_band(4) == 4
    with pytest.raises(ValidationError):
        validate_band(13)


def test_validate_mask_eu868_optional():
    assert validate_mask("", band=4) == "0000"


def test_validate_mask_us915_required():
    assert validate_mask("0002", band=5) == "0002"
    with pytest.raises(ValidationError):
        validate_mask("12", band=5)


def test_validate_uplink_period():
    assert validate_uplink_period(600) == 600
    with pytest.raises(ValidationError):
        validate_uplink_period("-1")


def test_validate_gps_decimation():
    assert validate_gps_decimation_factor(0) == 0
