"""Serial port listing, connect/disconnect, and background RX."""

from __future__ import annotations

import os
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import serial
from serial.tools import list_ports

from uart_terminal.models import Direction

_PORT_PREFIXES = ("ttyUSB", "ttyACM", "ttyS")
_READ_SIZE = 4096
_READ_TIMEOUT_S = 0.05


@dataclass
class SerialEvent:
    kind: str
    timestamp: datetime | None = None
    direction: Direction | None = None
    payload: bytes = b""
    message: str = ""


class SerialManager:
    """Owns the pyserial handle and a reader thread."""

    def __init__(self) -> None:
        self.events: queue.Queue[SerialEvent] = queue.Queue()
        self._serial: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    @staticmethod
    def list_ports() -> list[str]:
        ports: list[str] = []
        for info in list_ports.comports():
            name = os.path.basename(info.device)
            if name.startswith(_PORT_PREFIXES):
                ports.append(info.device)
        return sorted(ports)

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._serial is not None and self._serial.is_open

    def connect(
        self,
        port: str,
        baudrate: int,
        bytesize: int,
        parity: str,
        stopbits: float,
        rtscts: bool,
        xonxoff: bool,
    ) -> None:
        if self.is_connected:
            raise RuntimeError("Already connected")
        handle = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            rtscts=rtscts,
            xonxoff=xonxoff,
            timeout=_READ_TIMEOUT_S,
        )
        with self._lock:
            self._serial = handle
        self._stop.clear()
        self._thread = threading.Thread(target=self._reader, name="uart-rx", daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self._thread = None
        with self._lock:
            handle = self._serial
            self._serial = None
        if handle is not None:
            try:
                handle.close()
            except serial.SerialException:
                pass

    def write(self, data: bytes) -> None:
        if not data:
            return
        with self._lock:
            handle = self._serial
        if handle is None or not handle.is_open:
            raise RuntimeError("Not connected")
        handle.write(data)
        handle.flush()

    def _reader(self) -> None:
        buffer = bytearray()
        while not self._stop.is_set():
            try:
                with self._lock:
                    handle = self._serial
                if handle is None or not handle.is_open:
                    break
                chunk = handle.read(_READ_SIZE)
            except serial.SerialException as exc:
                self._flush_rx(buffer)
                self.events.put(
                    SerialEvent(kind="error", message=f"Serial read failed: {exc}")
                )
                break
            if chunk:
                buffer.extend(chunk)
            elif buffer:
                self._flush_rx(buffer)
        self._flush_rx(buffer)

    def _flush_rx(self, buffer: bytearray) -> None:
        if not buffer:
            return
        payload = bytes(buffer)
        buffer.clear()
        self.events.put(
            SerialEvent(
                kind="rx",
                timestamp=datetime.now(),
                direction=Direction.RX,
                payload=payload,
            )
        )


def drain_queue(source: queue.Queue[SerialEvent], handler: Callable[[SerialEvent], None]) -> None:
    while True:
        try:
            event = source.get_nowait()
        except queue.Empty:
            break
        handler(event)
