"""Protocol constants."""

LINE_ENDING = "\r\n"
BAUD_RATE = 115200

BUILTIN_KEYS = frozenset({"DEVEUI", "APPEUI", "APPKEY", "BAND", "MASK"})
CUSTOM_KEYS = frozenset(
    {
        "UPLINKPERIOD",
        "GPSDECIMATIONFACTOR",
        "BATTERYCHARGE",
        "BATTERYCAPACITY",
        "HWSTATUS",
        "SAMPLETILT",
        "GPSFIX",
        "FULLSAMPLE",
        "ABORTGPSFIX",
    }
)
WRITABLE_KEYS = frozenset(
    {
        "APPEUI",
        "APPKEY",
        "BAND",
        "MASK",
        "UPLINKPERIOD",
        "GPSDECIMATIONFACTOR",
        "BATTERYCHARGE",
        "BATTERYCAPACITY",
    }
)
PROFILE_KEYS = frozenset({"APPEUI", "APPKEY", "BAND", "MASK", "UPLINKPERIOD", "GPSDECIMATIONFACTOR"})
DEVICE_DUMP_KEYS = frozenset(
    {
        "DEVEUI",
        "APPEUI",
        "APPKEY",
        "BAND",
        "MASK",
        "UPLINKPERIOD",
        "GPSDECIMATIONFACTOR",
        "BATTERYCHARGE",
        "BATTERYCAPACITY",
        "HWSTATUS",
    }
)

# Bands where MASK applies (US915, CN470, AU915, LA915)
MASK_APPLICABLE_BANDS = frozenset({1, 5, 6, 12})

AT_OK = "OK"
AT_ERRORS = frozenset(
    {
        "AT_ERROR",
        "AT_PARAM_ERROR",
        "AT_BUSY_ERROR",
        "AT_TEST_PARAM_OVERFLOW",
        "AT_NO_CLASSB_ENABLE",
        "AT_NO_NETWORK_JOINED",
        "AT_RX_ERROR",
    }
)

DEFAULT_READ_TIMEOUT = 3.0
DEFAULT_WRITE_TIMEOUT = 5.0
DEFAULT_SESSION_TIMEOUT = 15.0

# RAK RUI3 LoRaWAN regional band ids.
BAND_OPTIONS = (
    (0, "EU433", "433 MHz Europe"),
    (1, "CN470", "470 MHz China"),
    (2, "RU864", "864 MHz Russia"),
    (3, "IN865", "865 MHz India"),
    (4, "EU868", "868 MHz Europe"),
    (5, "US915", "915 MHz United States"),
    (6, "AU915", "915 MHz Australia"),
    (7, "KR920", "920 MHz Korea"),
    (8, "AS923-1", "923 MHz Asia"),
    (9, "AS923-2", "923 MHz Asia"),
    (10, "AS923-3", "923 MHz Asia"),
    (11, "AS923-4", "923 MHz Asia"),
    (12, "LA915", "915 MHz Latin America"),
)
BAND_BY_ID = {band_id: (name, description) for band_id, name, description in BAND_OPTIONS}


def format_band_option(band_id: int) -> str:
    name, description = BAND_BY_ID[band_id]
    return f"{name} - {description} ({band_id})"


def format_band_value(value) -> str:
    try:
        band_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    if band_id not in BAND_BY_ID:
        return str(value)
    name, description = BAND_BY_ID[band_id]
    return f"{name} - {description} ({band_id})"
