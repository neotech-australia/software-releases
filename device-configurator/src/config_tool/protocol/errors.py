"""Human-readable messages for AT error codes."""

AT_ERROR_MESSAGES = {
    "AT_ERROR": "Generic device error.",
    "AT_PARAM_ERROR": "Invalid parameter value or format.",
    "AT_BUSY_ERROR": "LoRa network is busy; try again.",
    "AT_TEST_PARAM_OVERFLOW": "Parameter value is too long.",
    "AT_NO_CLASSB_ENABLE": "Device has not switched to Class B.",
    "AT_NO_NETWORK_JOINED": "Device has not joined the LoRa network.",
    "AT_RX_ERROR": "Error receiving the command on the device.",
}


def format_at_error(code: str) -> str:
    detail = AT_ERROR_MESSAGES.get(code, "Unknown device error.")
    return f"{code}: {detail}"
