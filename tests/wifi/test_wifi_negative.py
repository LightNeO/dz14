import pytest

from drivers.protocol_constants import (
    FAILURE_MARKERS,
    COMMAND_TIMEOUT_SECONDS,
    WIFI_SHORT_PASSWORD_MARKER,
)


@pytest.mark.debug
def test_wrong_password(device, wifi_config):
    """Test that the device does not connect to a Wi-Fi network with a wrong password."""
    assert not device.wifi_connect(
        wifi_config.ssid,
        wifi_config.wrong_password,
    ), f"Wi-Fi connection unexpectedly succeeded: {device.last_response}"

    assert device.wait_for_pattern(
        FAILURE_MARKERS, timeout=COMMAND_TIMEOUT_SECONDS
    ), "Wi-Fi connection failed, but no failure marker was found in the UART response. "


@pytest.mark.debug
def test_short_password(device, wifi_config):
    """Test that the device does not connect to a Wi-Fi network with a short password."""
    assert not device.wifi_connect(
        wifi_config.ssid,
        wifi_config.short_password,
    ), f"Wi-Fi connection unexpectedly succeeded: {device.last_response}"

    assert device.wait_for_pattern(
        WIFI_SHORT_PASSWORD_MARKER, timeout=COMMAND_TIMEOUT_SECONDS
    ), "Wi-Fi connection failed, but no failure marker was found in the UART response. "


@pytest.mark.debug
def test_nonexistent_ssid(device, wifi_config):
    """Test that the device does not connect to a Wi-Fi network with a nonexistent SSID."""
    assert not device.wifi_connect(
        wifi_config.nonexistent_ssid,
        wifi_config.password,
    ), f"Wi-Fi connection unexpectedly succeeded: {device.last_response}"

    assert device.wait_for_pattern(
        FAILURE_MARKERS, timeout=COMMAND_TIMEOUT_SECONDS
    ), "Wi-Fi connection failed, but no failure marker was found in the UART response. "
