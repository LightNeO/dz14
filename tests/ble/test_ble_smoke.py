"""BLE + UART dual-channel smoke test for SENTRY-BLE."""

from __future__ import annotations

import asyncio

import pytest
from bleak import BleakClient, BleakScanner

from drivers.protocol_constants import (
    BLE_CONNECT_TIMEOUT_SECONDS,
    BLE_DEVICE_NAME,
    BLE_LED_CHARACTERISTIC_UUID,
    BLE_LED_OFF_MARKER,
    BLE_LED_ON_MARKER,
    BLE_SCAN_TIMEOUT_SECONDS,
    BLE_UART_PATTERN_TIMEOUT_SECONDS,
)


async def _find_ble_device():
    """Find SENTRY-BLE by advertised name."""
    devices = await BleakScanner.discover(
        timeout=BLE_SCAN_TIMEOUT_SECONDS,
    )
    for device in devices:
        if device.name == BLE_DEVICE_NAME:
            return device
    return None


@pytest.mark.ble
@pytest.mark.hw
@pytest.mark.asyncio
async def test_ble_led_dual_channel(ble_uart_device):
    """Write LED over BLE and verify both LED transitions over UART."""
    ble_device = await _find_ble_device()
    assert ble_device is not None, (
        f"BLE device {BLE_DEVICE_NAME!r} was not found by scanner."
    )

    client = BleakClient(
        ble_device,
        timeout=BLE_CONNECT_TIMEOUT_SECONDS,
    )
    await client.connect()

    try:
        assert client.is_connected, "Bleak client did not connect to SENTRY-BLE"

        ble_uart_device.clear_input_buffer()
        await client.write_gatt_char(
            BLE_LED_CHARACTERISTIC_UUID,
            b"\x01",
            response=True,
        )
        assert ble_uart_device.wait_for_pattern(
            BLE_LED_ON_MARKER,
            timeout=BLE_UART_PATTERN_TIMEOUT_SECONDS,
        ), (
            "BLE write 0x01 completed, but UART did not report LED ON!. "
            f"UART response: {ble_uart_device.last_response}"
        )

        ble_uart_device.clear_input_buffer()
        await client.write_gatt_char(
            BLE_LED_CHARACTERISTIC_UUID,
            b"\x00",
            response=True,
        )
        assert ble_uart_device.wait_for_pattern(
            BLE_LED_OFF_MARKER,
            timeout=BLE_UART_PATTERN_TIMEOUT_SECONDS,
        ), (
            "BLE write 0x00 completed, but UART did not report LED OFF!. "
            f"UART response: {ble_uart_device.last_response}"
        )
    finally:
        if client.is_connected:
            await client.disconnect()
