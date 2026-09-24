import pytest

from drivers.device_driver import IP_ADDRESS_RE


@pytest.mark.wifi
def test_scan_finds_networks(device, wifi_config):
    """The DUT can scan for Wi-Fi networks and finds the configured SSID."""
    networks = device.wifi_scan()

    assert any(
        network["ssid"] == wifi_config.ssid
        for network in networks
    ), (
        f"SSID {wifi_config.ssid!r} not found in scan results: {networks}. "
        f"Raw UART response: {device.last_response}"
    )


@pytest.mark.wifi
def test_connect_success(device, wifi_config):
    """The DUT connects with valid Wi-Fi credentials."""
    assert device.wifi_connect(
        wifi_config.ssid,
        wifi_config.password,
    ), f"Wi-Fi connection failed: {device.last_response}"

    status_response = device.wifi_status()

    assert status_response["connected"] is True, (
        f"Expected connected state, got {status_response!r}. "
        f"Raw UART response: {device.last_response}"
    )
    assert status_response["ssid"] == wifi_config.ssid, (
        f"Expected SSID {wifi_config.ssid!r}, "
        f"got {status_response['ssid']!r}. "
        f"Raw UART response: {device.last_response}"
    )
    assert status_response["ip"] is not None and IP_ADDRESS_RE.fullmatch(
        status_response["ip"]
    ), (
        f"Expected a valid IP address, got {status_response['ip']!r}. "
        f"Raw UART response: {device.last_response}"
    )


@pytest.mark.xfail(reason="Expected error implemented for testing")
def test_disconnect(device, wifi_config):
    """The DUT can disconnect from the Wi-Fi network."""
    assert device.wifi_connect(
        wifi_config.ssid,
        wifi_config.password,
    ), f"Wi-Fi connection failed: {device.last_response}"

    disconnect_result = device.wifi_disconnect()
    assert disconnect_result is True, (
        "The disconnect command did not produce the expected "
        "'wifi station: disconnected' marker. "
        f"Raw UART response: {device.last_response}"
    )

    status_response = device.wifi_status()

    # This is a separate assertion: the command response can be correct while
    # the subsequent status command exposes a firmware state-reporting defect.
    assert status_response["connected"] is False, (
        "The disconnect command passed, but status still reports connected. "
        f"Parsed status: {status_response!r}. "
        f"Raw UART response: {device.last_response}"
    )


@pytest.mark.wifi
def test_credentials_survive_reboot(device, wifi_config):
    """Saved credentials reconnect after reboot using an empty SSID."""
    assert device.wifi_connect(
        wifi_config.ssid,
        wifi_config.password,
    ), f"Initial Wi-Fi connection failed: {device.last_response}"

    device.reboot()

    assert device.wait_for_boot(), (
        "DUT did not emit a boot-ready marker after reboot. "
        f"Raw UART response: {device.last_response}"
    )

    assert device.wifi_connect("", ""), (
        "Reconnect with saved credentials failed. "
        f"Raw UART response: {device.last_response}"
    )

    status_response = device.wifi_status()

    assert status_response["connected"] is True, (
        f"Expected connected state after reboot, got {status_response!r}. "
        f"Raw UART response: {device.last_response}"
    )
    assert status_response["ssid"] == wifi_config.ssid, (
        f"Expected SSID {wifi_config.ssid!r} after reboot, "
        f"got {status_response['ssid']!r}. "
        f"Raw UART response: {device.last_response}"
    )
    assert status_response["ip"] is not None and IP_ADDRESS_RE.fullmatch(
        status_response["ip"]
    ), (
        f"Expected a valid IP address after reboot, "
        f"got {status_response['ip']!r}. "
        f"Raw UART response: {device.last_response}"
    )
