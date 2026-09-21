"""Import send-message lists from the custom text format.

Format (TAB- or SPACE-separated, 1-100 whitespace chars between fields):

    # uart_terminal message list v1
    # index<TAB/SPACE>name<TAB/SPACE>encoding<TAB/SPACE>payload
    1	Ping	ASCII	AT
    2	Reset	HEX	AA 55 0D 0A
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from uart_terminal.display_format import parse_ascii, parse_hex
from uart_terminal.models import DisplayFormat, SendMessage

# One run of TAB and/or SPACE, up to 100 characters, separates two fields.
_FIELD_SEP = re.compile(r"[ \t]{1,100}")


@dataclass
class ImportResult:
    messages: list[SendMessage]
    skipped: list[str]


def _split_record(line: str) -> tuple[str, str, str, str] | None:
    """Split index, name, encoding, and payload.

    The first three fields are separated by 1-100 TAB/SPACE characters. The
    remainder of the line is the payload, so HEX byte spaces stay intact.
    """
    rest = line.lstrip(" \t")
    parts: list[str] = []
    for _ in range(3):
        match = _FIELD_SEP.search(rest)
        if match is None:
            return None
        parts.append(rest[: match.start()])
        rest = rest[match.end() :]
    return parts[0], parts[1], parts[2], rest


def load_messages(path: str | Path) -> ImportResult:
    messages: list[SendMessage] = []
    skipped: list[str] = []
    text = Path(path).read_text(encoding="utf-8")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = _split_record(raw.rstrip("\n\r"))
        if fields is None:
            skipped.append(f"line {line_no}: expected index, name, encoding, payload")
            continue
        _index, name, encoding_text, payload_text = fields
        name = name.strip()
        encoding_text = encoding_text.strip().upper()
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
