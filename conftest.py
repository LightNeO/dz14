"""Shared fixtures and runtime configuration for DZ-14 tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

import pytest

from drivers.device_driver import DeviceDriver


@dataclass(frozen=True)
class WifiConfig:
    """Credentials and negative-test values for station_WiFi."""

    ssid: str
    password: str
    wrong_password: str
    short_password: str
    nonexistent_ssid: str


def _required_env(name: str) -> str:
    """Return a non-empty environment variable or fail with guidance."""
    value = os.getenv(name, "").strip()
    if not value:
        pytest.fail(
            f"Missing {name}. Configure the DZ-14 environment before running "
            "hardware tests; do not hardcode credentials."
        )
    return value


def _optional_int_env(name: str) -> int | None:
    """Parse an optional decimal or 0x-prefixed integer environment value."""
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value, 0)
    except ValueError as exc:
        pytest.fail(f"{name} must be a decimal or 0x-prefixed integer: {value!r}")
        raise AssertionError from exc


def _description_tokens() -> tuple[str, ...]:
    """Read optional comma-separated USB description filters."""
    return tuple(
        token.strip()
        for token in os.getenv("ESP32_DESCRIPTION_TOKENS", "").split(",")
        if token.strip()
    )


def _open_uart_driver() -> DeviceDriver:
    """Find and open the unique ESP32 UART selected by USB metadata."""
    vid = _optional_int_env("ESP32_VID")
    if vid is None:
        pytest.fail("Missing ESP32_VID, for example ESP32_VID=0x403.")

    driver = DeviceDriver(
        DeviceDriver.find_port(
            vid=vid,
            pid=_optional_int_env("ESP32_PID"),
            serial_number=os.getenv("ESP32_SERIAL") or None,
            description_tokens=_description_tokens(),
        )
    )
    driver.open()
    return driver


@pytest.fixture(scope="session")
def wifi_config() -> WifiConfig:
    """Load Wi-Fi credentials and negative-test values from environment."""
    return WifiConfig(
        ssid=_required_env("WIFI_SSID"),
        password=_required_env("WIFI_PASSWORD"),
        wrong_password=os.getenv("WIFI_WRONG_PASSWORD", "wrong-password-14"),
        short_password=os.getenv("WIFI_SHORT_PASSWORD", "short"),
        nonexistent_ssid=os.getenv(
            "WIFI_NONEXISTENT_SSID",
            "__RANDOM_WRONG_SSID__",
        ),
    )


@pytest.fixture(scope="function")
def device() -> Iterator[DeviceDriver]:
    """Provide an opened station_WiFi UART driver and always close it."""
    driver = _open_uart_driver()
    try:
        yield driver
    finally:
        try:
            driver.wifi_disconnect()
        except Exception:
            pass
        finally:
            driver.close()


@pytest.fixture(scope="function")
def ble_uart_device() -> Iterator[DeviceDriver]:
    """Provide an opened SENTRY-BLE UART driver and always close it."""
    driver = _open_uart_driver()
    try:
        yield driver
    finally:
        driver.close()
