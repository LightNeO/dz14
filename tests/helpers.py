"""Small test-only helpers shared by UART/BLE tests."""

from __future__ import annotations

from collections.abc import Iterable


def response_text(lines: Iterable[str]) -> str:
    """Join cleaned UART lines and normalize them for case-insensitive checks."""
    return "\n".join(lines).casefold()


def contains_any_marker(response: str, markers: Iterable[str]) -> bool:
    """Return True when any case-insensitive marker occurs in a response."""
    normalized_response = response.casefold()
    return any(
        marker.casefold() in normalized_response
        for marker in markers
    )
