"""Shared fixtures and runtime configuration for DZ-14 tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

import pytest

from drivers.device_driver import DeviceDriver


@dataclass(frozen=True)
class WifiConfig:
    """Credentials and test values for the station_WiFi firmware."""

    ssid: str
    password: str
    wrong_password: str
    short_password: str
    nonexistent_ssid: str


def _required_env(name: str) -> str:
    """Return a non-empty environment variable or fail with setup guidance."""
    value = os.getenv(name, "").strip()
    if not value:
        pytest.fail(
            f"Missing {name}. Configure the test environment before "
            "running hardware tests; do not hardcode credentials in tests."
        )
    return value


def _optional_int_env(name: str) -> int | None:
    """Parse an optional decimal/hex integer environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value, 0)
    except ValueError as exc:
        pytest.fail(f"{name} must be a decimal or prefixed integer: {value!r}")
        raise AssertionError from exc


@pytest.fixture(scope="session")
def wifi_config() -> WifiConfig:
    """Load Wi-Fi credentials and negative-test data from environment variables."""
    password = _required_env("WIFI_PASSWORD")
    return WifiConfig(
        ssid=_required_env("WIFI_SSID"),
        password=password,
        wrong_password=os.getenv("WIFI_WRONG_PASSWORD", "wrong-password-14"),
        short_password=os.getenv("WIFI_SHORT_PASSWORD", "short"),
        nonexistent_ssid=os.getenv(
            "WIFI_NONEXISTENT_SSID",
            "__RANDOM_WRONG_SSID__",
        ),
    )


@pytest.fixture(scope="function")
def device() -> Iterator[DeviceDriver]:
    """Open the unique DUT selected by USB metadata and close it after the run.

    ESP32_VID is required. ESP32_PID and ESP32_SERIAL are optional.
    """
    vid = _optional_int_env("ESP32_VID")
    if vid is None:
        pytest.fail(
            "Missing ESP32_VID. Example: set ESP32_VID=0x303A in the shell."
        )

    driver = DeviceDriver(
        DeviceDriver.find_port(
            vid=vid,
            pid=_optional_int_env("ESP32_PID"),
            serial_number=os.getenv("ESP32_SERIAL") or None,
            description_tokens=tuple(
                token.strip()
                for token in os.getenv("ESP32_DESCRIPTION_TOKENS", "").split(
                    ","
                )
                if token.strip()
            ),
        )
    )
    driver.open()

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
    """Open the BLE firmware UART for the dual-channel smoke test."""
    vid = _optional_int_env("ESP32_VID")
    if vid is None:
        pytest.fail("Missing ESP32_VID for the BLE UART fixture.")

    driver = DeviceDriver(
        DeviceDriver.find_port(
            vid=vid,
            pid=_optional_int_env("ESP32_PID"),
            serial_number=os.getenv("ESP32_SERIAL") or None,
            description_tokens=tuple(
                token.strip()
                for token in os.getenv("ESP32_DESCRIPTION_TOKENS", "").split(",")
                if token.strip()
            ),
        )
    )
    driver.open()

    try:
        yield driver
    finally:
        driver.close()
