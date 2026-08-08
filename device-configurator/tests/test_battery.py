"""Tests for battery capacity/charge AT commands and lifetime estimation."""

from config_tool.models.battery import estimate_battery_lifetime_days
from config_tool.protocol.at_client import AtClient
from config_tool.protocol.mock_transport import MockTransport


def test_estimate_battery_lifetime_days():
    # 100% charge, 1000 mAh, 1800 s uplink, GPS every 8 → some finite lifetime
    days = estimate_battery_lifetime_days(
        charge_percent="100",
        capacity_mah="1000",
        uplink_period_s="1800",
        gps_decimation_factor="8",
    )
    assert days is not None and days > 0

    # Missing capacity → cannot estimate
    assert (
        estimate_battery_lifetime_days(
            charge_percent="100",
            capacity_mah=None,
            uplink_period_s="1800",
            gps_decimation_factor="8",
        )
        is None
    )

    # 0% charge → zero lifetime
    assert (
        estimate_battery_lifetime_days(
            charge_percent="0",
            capacity_mah="1000",
            uplink_period_s="1800",
            gps_decimation_factor="8",
        )
        == 0
    )


def test_mock_read_battery_charge_and_capacity():
    transport = MockTransport()
    transport.open()
    client = AtClient(transport)
    params = client.start_config()
    assert params.BATTERYCHARGE == "85"
    assert params.BATTERYCAPACITY == "1900"

    charge = client.read_battery_charge()
    assert charge == "85"
    capacity = client.read_battery_capacity()
    assert capacity == "1900"
    transport.close()


def test_mock_write_battery_charge_and_capacity():
    transport = MockTransport()
    transport.open()
    client = AtClient(transport)
    params = client.start_config()
    assert params.BATTERYCHARGE == "85"

    client.write_battery_charge("100")
    assert client.last_dump is not None
    assert client.last_dump.BATTERYCHARGE == "100"

    client.write_battery_capacity("1900")
    assert client.last_dump is not None
    assert client.last_dump.BATTERYCAPACITY == "1900"
    transport.close()


def test_mock_fullsample_includes_battery():
    transport = MockTransport()
    transport.open()
    client = AtClient(transport)
    params = client.full_sample()
    assert params.battery_charge_percent == "85"
    assert params.battery_voltage_v == "3.70"
    transport.close()
