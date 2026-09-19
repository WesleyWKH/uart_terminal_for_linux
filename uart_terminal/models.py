"""Shared data models for the UART terminal."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DisplayFormat(str, Enum):
    ASCII = "ASCII"
    HEX = "HEX"


class Direction(str, Enum):
    TX = "TX"
    RX = "RX"


@dataclass
class SendMessage:
    name: str = ""
    payload: bytes = b""


@dataclass
class LogEntry:
    timestamp: datetime
    direction: Direction
    payload: bytes
