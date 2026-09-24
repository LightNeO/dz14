"""UART DeviceDriver for the station_WiFi / SENTRY-BLE firmware."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Iterable, Sequence
from typing import Any

import serial
from serial.tools import list_ports

from drivers.protocol_constants import (
    BOOT_READY_MARKERS,
    BOOT_TIMEOUT_SECONDS,
    COMMAND_TIMEOUT_SECONDS,
    REBOOT_COMMAND,
    UART_BAUDRATE,
    UART_TIMEOUT_SECONDS,
    WIFI_CONNECT_COMMAND,
    WIFI_CONNECT_SUCCESS_MARKER,
    WIFI_DISCONNECTED_STATE_MARKER,
    WIFI_PASSWORD_PROMPT,
    WIFI_SCAN_COMMAND,
    WIFI_SSID_PROMPT,
    WIFI_DISCONNECT_COMMAND,
    WIFI_STATUS_COMMAND,
)

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
IP_ADDRESS_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RSSI_RE = re.compile(r"(?:rssi|signal)\s*[:=]?\s*(-?\d+)", re.IGNORECASE)


class DeviceDriver:
    """UART transport and firmware command protocol."""

    def __init__(
        self,
        port: str,
        timeout: float = UART_TIMEOUT_SECONDS,
        baudrate: int = UART_BAUDRATE,
    ) -> None:
        """Store the selected port and UART parameters; do not open yet."""
        self.port_name = port
        self.timeout = timeout
        self.baudrate = baudrate
        self.ser: serial.Serial | None = None
        self.last_response: list[str] = []

    @staticmethod
    def _normalise_ids(
        value: int | str | Iterable[int | str] | None,
    ) -> set[int] | None:
        """Convert VID/PID input to ints."""
        if value is None:
            return None
        if isinstance(value, (int, str)):
            value = (value,)
        result: set[int] = set()
        for item in value:
            if isinstance(item, str):
                result.add(int(item, 0))
            else:
                result.add(int(item))
        return result

    @staticmethod
    def _port_text(info: Any) -> str:
        """Return searchable metadata for one pyserial ListPortInfo object."""
        return " ".join(
            str(getattr(info, field, "") or "")
            for field in (
                "device",
                "description",
                "manufacturer",
                "hwid",
                "serial_number",
                "location",
            )
        ).casefold()

    @classmethod
    def discover_ports(
        cls,
        vid: int | str | Iterable[int | str] | None = None,
        pid: int | str | Iterable[int | str] | None = None,
        description_tokens: Sequence[str] = (),
    ) -> list[Any]:
        """Return every port matching the supplied hardware criteria."""
        vids = cls._normalise_ids(vid)
        pids = cls._normalise_ids(pid)
        tokens = tuple(
            token.casefold() for token in description_tokens if token
        )
        matches: list[Any] = []

        for info in list_ports.comports():
            info_vid = getattr(info, "vid", None)
            info_pid = getattr(info, "pid", None)
            if vids is not None and info_vid not in vids:
                continue
            if pids is not None and info_pid not in pids:
                continue
            searchable = cls._port_text(info)
            if tokens and not all(token in searchable for token in tokens):
                continue
            matches.append(info)
        return matches

    @classmethod
    def find_port(
        cls,
        vid: int | str | Iterable[int | str] | None = None,
        pid: int | str | Iterable[int | str] | None = None,
        serial_number: str | None = None,
        description_tokens: Sequence[str] = (),
    ) -> str:
        """Find one DUT port using all available USB metadata.

        Recommended usage is ``find_port(vid=os.environ["ESP32_VID"])``.
        If several devices share a VID, add PID or ``serial_number``. A
        description token such as ``("USB", "JTAG")`` can be used.
        """
        all_ports = list(list_ports.comports())
        candidates = cls.discover_ports(
            vid=vid, pid=pid, description_tokens=description_tokens
        )

        if serial_number is not None:
            wanted = serial_number.casefold()
            candidates = [
                info
                for info in candidates
                if wanted
                in str(getattr(info, "serial_number", "") or "").casefold()
            ]

        if (
            not candidates
            and vid is None
            and pid is None
            and serial_number is None
            and not description_tokens
        ):
            known_tokens = ("usb serial", "cp210", "ch340", "esp32", "jtag")
            candidates = [
                info
                for info in all_ports
                if any(token in cls._port_text(info) for token in known_tokens)
            ]

        if len(candidates) == 1:
            return str(candidates[0].device)

        def describe(info: Any) -> str:
            return (
                f"{info.device} vid={getattr(info, 'vid', None)!r} "
                f"pid={getattr(info, 'pid', None)!r} "
                f"serial={getattr(info, 'serial_number', None)!r} "
                f"description={getattr(info, 'description', '')!r}"
            )

        if not candidates:
            inventory = (
                "; ".join(describe(info) for info in all_ports)
                or "<no serial ports>"
            )
            raise RuntimeError(
                "DUT port was not found. Configure ESP32_VID/PID or check the USB cable. "
                f"Available ports: {inventory}"
            )

        options = "; ".join(describe(info) for info in candidates)
        raise RuntimeError(
            "DUT port selection is ambiguous. Do not choose a COM port by position; "
            "add PID or ESP32_SERIAL to the configuration. Candidates: "
            + options
        )

    def open(self) -> None:
        """Open UART as 115200 8N1 and discard stale input."""
        if self.ser and self.ser.is_open:
            return
        self.ser = serial.Serial(
            port=self.port_name,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        self.ser.reset_input_buffer()

    def close(self) -> None:
        """Close UART safely; repeated close calls are allowed."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def __enter__(self) -> "DeviceDriver":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def _require_open(self) -> serial.Serial:
        """Return the open serial object or raise a useful error."""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port is not open")
        return self.ser

    @staticmethod
    def clean_line(raw: bytes) -> str:
        """Decode UART bytes, replace invalid UTF-8, strip ANSI and EOL."""
        text = raw.decode("utf-8", errors="replace")
        return ANSI_ESCAPE_RE.sub("", text).rstrip("\r\n")

    def read_lines(
        self, timeout: float | None = None, end_pattern: str | None = None
    ) -> list[str]:
        """Read non-empty lines until deadline or case-insensitive marker."""
        ser = self._require_open()
        deadline = time.monotonic() + (
            self.timeout if timeout is None else timeout
        )
        result: list[str] = []
        while time.monotonic() < deadline:
            raw = ser.readline()
            if not raw:
                continue
            line = self.clean_line(raw)
            if not line:
                continue
            result.append(line)
            if end_pattern and end_pattern.casefold() in line.casefold():
                break
        return result

    def _write_line(self, text: str) -> None:
        """Write exactly one CRLF-terminated line without waiting."""
        ser = self._require_open()
        payload = text.rstrip("\r\n") + "\r\n"
        ser.write(payload.encode("utf-8"))
        ser.flush()

    def send_command(
        self,
        command: str,
        timeout: float | None = None,
        end_pattern: str | None = None,
        clear_buffer: bool = True,
    ) -> list[str]:
        """Send a command and read its response without arbitrary sleeps."""
        ser = self._require_open()
        if clear_buffer:
            ser.reset_input_buffer()
        self._write_line(command)
        self.last_response = self.read_lines(
            timeout=timeout, end_pattern=end_pattern
        )
        return self.last_response

    def clear_input_buffer(self) -> None:
        """Discard stale UART input before a cross-channel BLE action."""
        self._require_open().reset_input_buffer()

    def wait_for_pattern(self, pattern: str, timeout: float = 10.0) -> bool:
        """Consume UART lines until ``pattern`` appears or timeout expires."""
        self.last_response = self.read_lines(
            timeout=timeout,
            end_pattern=pattern,
        )
        return any(
            pattern.casefold() in line.casefold()
            for line in self.last_response
        )

    def _read_until_any(
        self, patterns: Sequence[str], timeout: float
    ) -> list[str]:
        """Read until any case-insensitive prompt/marker appears."""
        ser = self._require_open()
        wanted = tuple(pattern.casefold() for pattern in patterns)
        deadline = time.monotonic() + timeout
        lines: list[str] = []
        while time.monotonic() < deadline:
            raw = ser.readline()
            if not raw:
                continue
            line = self.clean_line(raw)
            if line:
                lines.append(line)
                if any(pattern in line.casefold() for pattern in wanted):
                    break
        return lines

    # ---------- station_WiFi API ----------

    def wifi_scan(self) -> list[dict[str, Any]]:
        """Run ``scan`` and return structured Wi-Fi network records.

        The test contract is a list of dictionaries, for example::

            [{"ssid": "NeO", "rssi": -51, "channel": 11}]

        The station_WiFi firmware normally prints ``SSID: ... RSSI: ...``;
        the second parser also accepts the numbered ``[1] SSID -52 dBm``
        variant used by the connect dialog.
        """
        lines = self.send_command(
            WIFI_SCAN_COMMAND,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        networks: list[dict[str, Any]] = []

        for line in lines:
            match = re.search(
                r"SSID:\s*(.*?)\s+RSSI:\s*(-?\d+)\s*dBm"
                r"(?:\s+CH:\s*(\d+))?",
                line,
                re.IGNORECASE,
            )
            if match:
                networks.append(
                    {
                        "ssid": match.group(1).strip(),
                        "rssi": int(match.group(2)),
                        "channel": int(match.group(3)) if match.group(3) else None,
                    }
                )
                continue

            numbered_match = re.search(
                r"\[\s*\d+\]\s+(.*?)\s+(-?\d+)\s*dBm"
                r"(?:\s+CH:\s*(\d+))?\s*$",
                line,
                re.IGNORECASE,
            )
            if numbered_match:
                networks.append(
                    {
                        "ssid": numbered_match.group(1).strip(),
                        "rssi": int(numbered_match.group(2)),
                        "channel": (
                            int(numbered_match.group(3))
                            if numbered_match.group(3)
                            else None
                        ),
                    }
                )

        return networks

    def wifi_connect(
        self,
        ssid: str,
        password: str,
        timeout: float = COMMAND_TIMEOUT_SECONDS,
    ) -> bool:
        """Complete the real station_WiFi ``connect`` dialog."""
        transcript: list[str] = []
        self._require_open().reset_input_buffer()
        self._write_line(WIFI_CONNECT_COMMAND)

        first = self._read_until_any(
            (WIFI_SSID_PROMPT,),
            timeout,
        )
        transcript.extend(first)
        if not first:
            self.last_response = transcript
            return False

        self._write_line(ssid)

        # An empty SSID means: use credentials saved by the firmware. In this
        # mode station_WiFi does not ask for a password; it starts the
        # connection attempt immediately after the empty line.
        if ssid == "":
            transcript.extend(self.read_lines(
                timeout=timeout,
                end_pattern=WIFI_CONNECT_SUCCESS_MARKER,
            ))
            self.last_response = transcript
            response = "\n".join(transcript).casefold()
            return WIFI_CONNECT_SUCCESS_MARKER in response

        second = self._read_until_any(
            (WIFI_PASSWORD_PROMPT,),
            timeout,
        )
        transcript.extend(second)
        if not second:
            self.last_response = transcript
            return False

        self._write_line(password)
        transcript.extend(
            self.read_lines(
                timeout=timeout,
                end_pattern=WIFI_CONNECT_SUCCESS_MARKER,
            )
        )
        self.last_response = transcript
        response = "\n".join(transcript).casefold()
        return WIFI_CONNECT_SUCCESS_MARKER in response

    def wifi_status(self) -> dict[str, Any]:
        """Parse the text status format emitted by ``station_WiFi``."""
        lines = self.send_command(
            WIFI_STATUS_COMMAND,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        text = "\n".join(lines)
        result: dict[str, Any] = {
            "connected": False,
            "ssid": None,
            "ip": None,
            "rssi": None,
        }

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            for key in result:
                if key in parsed:
                    result[key] = parsed[key]

        # Support both status formats emitted by the firmware:
        # ``WiFi: connected`` and ``wifi station: disconnected``.
        state_match = re.search(
            r"\bwifi(?:\s+station)?\s*:\s*"
            r"(?P<state>connected|disconnected)\b",
            text,
            re.IGNORECASE,
        )
        if state_match:
            result["connected"] = (
                state_match.group("state").casefold() == "connected"
            )
        else:
            # No explicit state marker means that the status is not proven
            # connected. Do not infer connectivity from arbitrary ESP-IDF log
            # text, where words such as ``connect`` and ``disconnected`` are
            # common diagnostics.
            result["connected"] = False

        # Do not use ``\s*`` after SSID: here: it also matches newlines and
        # can accidentally capture the following IP line when SSID is empty.
        ssid_match = re.search(
            r"\bSSID\s*:[ \t]*([^\r\n]*)",
            text,
            re.IGNORECASE,
        )
        if ssid_match:
            result["ssid"] = ssid_match.group(1).strip() or None

        ip_match = IP_ADDRESS_RE.search(text)
        if ip_match:
            result["ip"] = ip_match.group(0)

        rssi_match = RSSI_RE.search(text)
        if rssi_match:
            result["rssi"] = int(rssi_match.group(1))

        # Do not infer a corrected state from SSID/IP/RSSI. If firmware emits
        # ``WiFi: connected``, return that raw protocol result. A contradictory
        # response such as connected + empty SSID + 0.0.0.0 is a firmware bug
        # that the test must expose, not hide in the driver.
        return result

    def wifi_disconnect(self) -> bool:
        """Disconnect Wi-Fi and return whether the DUT reached disconnected state."""
        lines = self.send_command(
            WIFI_DISCONNECT_COMMAND, timeout=COMMAND_TIMEOUT_SECONDS
        )
        text = "\n".join(lines).casefold()
        disconnected = WIFI_DISCONNECTED_STATE_MARKER in text
        if disconnected:
            return True

        return False

    def reboot(self) -> None:
        """Send reboot without waiting for a response that disappears."""
        self._require_open().reset_input_buffer()
        self._write_line(REBOOT_COMMAND)

    def wait_for_boot(self, timeout: float = BOOT_TIMEOUT_SECONDS) -> bool:
        """Wait for a station_WiFi boot marker after reset/reboot."""
        lines = self.read_lines(timeout=timeout)
        text = "\n".join(lines).casefold()
        return any(marker.casefold() in text for marker in BOOT_READY_MARKERS)
