import pytest

from drivers.protocol_constants import (
    COMMAND_TIMEOUT_SECONDS,
    FAILURE_MARKERS,
    WIFI_SHORT_PASSWORD_MARKER,
)
from tests.helpers import contains_any_marker, response_text


@pytest.mark.wifi
def test_wrong_password(device, wifi_config):
    """A valid SSID with a wrong password must not connect."""
    result = device.wifi_connect(
        wifi_config.ssid,
        wifi_config.wrong_password,
    )
    response = response_text(device.last_response)

    assert result is False, (
        f"Wi-Fi connection unexpectedly succeeded. "
        f"UART response: {device.last_response}"
    )
    assert contains_any_marker(response, FAILURE_MARKERS), (
        "Wi-Fi connection failed, but no failure marker was found in the "
        f"UART response: {device.last_response}"
    )


@pytest.mark.wifi
def test_short_password(device, wifi_config):
    """Firmware rejects a password shorter than eight characters immediately."""
    result = device.wifi_connect(
        wifi_config.ssid,
        wifi_config.short_password,
    )
    response = response_text(device.last_response)

    assert len(wifi_config.short_password) < 8, (
        "WIFI_SHORT_PASSWORD must contain fewer than 8 characters for this test."
    )
    assert result is False, (
        f"Short password was unexpectedly accepted. "
        f"UART response: {device.last_response}"
    )
    assert WIFI_SHORT_PASSWORD_MARKER.casefold() in response, (
        "Expected the firmware marker 'password too short (min 8 chars)' "
        f"in UART response: {device.last_response}"
    )
    assert "connecting to ssid" not in response, (
        "Firmware started a Wi-Fi connection attempt despite rejecting the "
        f"short password. UART response: {device.last_response}"
    )


@pytest.mark.wifi
def test_nonexistent_ssid(device, wifi_config):
    """A nonexistent SSID must fail while the UART CLI remains alive."""
    result = device.wifi_connect(
        wifi_config.nonexistent_ssid,
        wifi_config.password,
    )
    response = response_text(device.last_response)

    assert result is False, (
        f"Connection to a nonexistent SSID unexpectedly succeeded. "
        f"UART response: {device.last_response}"
    )
    assert contains_any_marker(response, FAILURE_MARKERS), (
        "No connection failure/timeout marker was found for the nonexistent "
        f"SSID. UART response: {device.last_response}"
    )

    help_response = device.send_command(
        "help",
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    assert help_response, (
        "DUT returned no response to help after the failed attempt"
    )
