"""ASCII/HEX conversion and HEX input validation."""

from __future__ import annotations

from typing import Any

from uart_terminal.models import DisplayFormat

_HEX_CHARS = set("0123456789abcdefABCDEF ")


def bytes_to_hex(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def bytes_to_ascii_editable(data: bytes) -> str:
    """Latin-1 decode so every byte 0-255 stays editable in the send list."""
    return data.decode("latin-1")


def bytes_to_ascii_log(data: bytes) -> str:
    """Printable ASCII for the log; other bytes become '.'."""
    return "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in data)


def parse_ascii(text: str) -> bytes:
    return text.encode("latin-1", errors="replace")


def parse_hex(text: str) -> bytes:
    compact = "".join(text.split())
    if not compact:
        return b""
    if len(compact) % 2 != 0:
        raise ValueError("HEX payload has an odd number of digits")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise ValueError("HEX payload contains invalid characters") from exc


def format_payload(data: bytes, display_format: DisplayFormat) -> str:
    if display_format is DisplayFormat.HEX:
        return bytes_to_hex(data)
    return bytes_to_ascii_log(data)


def parse_payload(text: str, display_format: DisplayFormat) -> bytes:
    if display_format is DisplayFormat.HEX:
        return parse_hex(text)
    return parse_ascii(text)


def is_hex_text(text: str) -> bool:
    return all(char in _HEX_CHARS for char in text)


def register_hex_validator(widget: Any) -> tuple[str, str]:
    """Restrict an Entry to HEX digits and spaces."""
    root = widget.winfo_toplevel()
    vcmd = (root.register(_validate_hex_key), "%P")
    widget.configure(validate="key", validatecommand=vcmd)
    return vcmd


def clear_validator(widget: Any) -> None:
    widget.configure(validate="none", validatecommand="")


def _validate_hex_key(proposed: str) -> bool:
    return is_hex_text(proposed)
