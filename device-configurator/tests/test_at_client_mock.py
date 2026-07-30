"""Tests for AtClient with mock transport."""

from config_tool.controller.device_controller import DeviceController
from config_tool.models.profile import create_profile
from config_tool.protocol.at_client import AtClient
from config_tool.protocol.constants import AT_OK
from config_tool.protocol.mock_transport import MockTransport


def test_mock_start_config():
    transport = MockTransport()
    transport.open()
    client = AtClient(transport)
    params = client.start_config()
    assert params.DEVEUI == "AC1F09FFFE12AB34"
    assert params.BAND == "4"
    client.config_done()
    transport.close()


def test_start_config_ignores_device_logs():
    transport = MockTransport()
    transport.open()
    transport._rx_queue.extend(
        [
            "[00:07:05] [serial] [DEBUG] ATC+STARTCONFIG received",
            "DEVEUI=AC1F09FFFE12AB34",
            "[00:07:05] [serial] [DEBUG] print_configuration: complete",
            "APPEUI=0000000000000001",
            "BAND=4",
            AT_OK,
        ]
    )
    client = AtClient(transport)
    params = client.start_config()
    assert params.DEVEUI == "AC1F09FFFE12AB34"
    assert params.APPEUI == "0000000000000001"
    transport.close()


def test_mock_write_parameter():
    transport = MockTransport()
    transport.open()
    client = AtClient(transport)
    client.start_config()
    client.write_parameter("BAND", "5")
    assert client.last_dump is not None
    assert client.last_dump.BAND == "5"
    client.config_done()
    transport.close()


def test_controller_apply_profile_mock():
    controller = DeviceController(use_mock=True)
    profile = create_profile(
        name="Test",
        APPEUI="0000000000000002",
        APPKEY="2B7E151628AED2A6ABF7158809CF4F3C",
        BAND=5,
        MASK="0002",
        UPLINKPERIOD=600,
        GPSDECIMATIONFACTOR=4,
    )
    controller.connect("MOCK")
    result = controller.apply_profile(profile)
    assert result.success
    assert "APPEUI" in result.changes_applied or "BAND" in result.changes_applied
    controller.disconnect()


def test_controller_read_device_mock():
    controller = DeviceController(use_mock=True)
    controller.connect("MOCK")
    params = controller.read_device()
    assert params.HWSTATUS == "0"
    controller.disconnect()
