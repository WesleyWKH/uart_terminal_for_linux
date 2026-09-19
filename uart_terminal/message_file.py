"""Import send-message lists from the custom text format.

Format (TAB-separated):

    # uart_terminal message list v1
    # index<TAB>name<TAB>encoding<TAB>payload
    1	Ping	ASCII	AT
    2	Reset	HEX	AA 55 0D 0A
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from uart_terminal.display_format import parse_ascii, parse_hex
from uart_terminal.models import DisplayFormat, SendMessage


@dataclass
class ImportResult:
    messages: list[SendMessage]
    skipped: list[str]


def load_messages(path: str | Path) -> ImportResult:
    messages: list[SendMessage] = []
    skipped: list[str] = []
    text = Path(path).read_text(encoding="utf-8")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.rstrip("\n").split("\t")
        if len(parts) < 4:
            skipped.append(f"line {line_no}: expected index, name, encoding, payload")
            continue
        _index, name, encoding_text, payload_text = (
            parts[0],
            parts[1],
            parts[2].strip().upper(),
            "\t".join(parts[3:]),
        )
        try:
            encoding = DisplayFormat(encoding_text)
        except ValueError:
            skipped.append(f"line {line_no}: encoding must be ASCII or HEX")
            continue
        try:
            payload = (
                parse_hex(payload_text)
                if encoding is DisplayFormat.HEX
                else parse_ascii(payload_text)
            )
        except ValueError as exc:
            skipped.append(f"line {line_no}: {exc}")
            continue
        messages.append(SendMessage(name=name, payload=payload))
    return ImportResult(messages=messages, skipped=skipped)
