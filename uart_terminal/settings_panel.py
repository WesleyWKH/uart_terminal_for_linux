"""Baud rate, UART format, flow control, line ending, and ASCII/HEX display."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from uart_terminal.models import DisplayFormat

BAUD_RATES = (
    "9600",
    "19200",
    "38400",
    "57600",
    "115200",
    "230400",
    "460800",
    "921600",
)

UART_FORMATS = {
    "8N1": (8, "N", 1),
    "8E1": (8, "E", 1),
    "8O1": (8, "O", 1),
    "7E1": (7, "E", 1),
    "7O1": (7, "O", 1),
    "8N2": (8, "N", 2),
}

FLOW_CONTROL = {
    "None": (False, False),
    "RTS/CTS": (True, False),
    "XON/XOFF": (False, True),
}

LINE_ENDINGS = {
    "None": b"",
    "LF": b"\n",
    "CR": b"\r",
    "CRLF": b"\r\n",
}


class SettingsPanel(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_display_format_change: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._on_display_format_change = on_display_format_change

        ttk.Label(self, text="Baud").pack(side=tk.LEFT, padx=(0, 4))
        self._baud_var = tk.StringVar(value="115200")
        self._baud_combo = ttk.Combobox(
            self,
            textvariable=self._baud_var,
            values=BAUD_RATES,
            width=8,
        )
        self._baud_combo.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(self, text="Format").pack(side=tk.LEFT, padx=(0, 4))
        self._uart_var = tk.StringVar(value="8N1")
        self._uart_combo = ttk.Combobox(
            self,
            textvariable=self._uart_var,
            values=tuple(UART_FORMATS),
            state="readonly",
            width=6,
        )
        self._uart_combo.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(self, text="Flow").pack(side=tk.LEFT, padx=(0, 4))
        self._flow_var = tk.StringVar(value="None")
        self._flow_combo = ttk.Combobox(
            self,
            textvariable=self._flow_var,
            values=tuple(FLOW_CONTROL),
            state="readonly",
            width=10,
        )
        self._flow_combo.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(self, text="Ending").pack(side=tk.LEFT, padx=(0, 4))
        self._ending_var = tk.StringVar(value="CRLF")
        self._ending_combo = ttk.Combobox(
            self,
            textvariable=self._ending_var,
            values=tuple(LINE_ENDINGS),
            state="readonly",
            width=6,
        )
        self._ending_combo.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(self, text="Display").pack(side=tk.LEFT, padx=(0, 4))
        self._display_var = tk.StringVar(value=DisplayFormat.ASCII.value)
        self._display_combo = ttk.Combobox(
            self,
            textvariable=self._display_var,
            values=(DisplayFormat.ASCII.value, DisplayFormat.HEX.value),
            state="readonly",
            width=7,
        )
        self._display_combo.pack(side=tk.LEFT)
        self._display_combo.bind("<<ComboboxSelected>>", self._on_selected)

    def _on_selected(self, _event: tk.Event | None = None) -> None:
        self._on_display_format_change()

    def get_baudrate(self) -> int:
        text = self._baud_var.get().strip()
        baud = int(text)
        if baud <= 0:
            raise ValueError("Baud rate must be positive")
        return baud

    def get_uart_params(self) -> tuple[int, str, float]:
        key = self._uart_var.get()
        if key not in UART_FORMATS:
            raise ValueError(f"Unknown UART format: {key}")
        return UART_FORMATS[key]

    def get_flow(self) -> tuple[bool, bool]:
        key = self._flow_var.get()
        if key not in FLOW_CONTROL:
            raise ValueError(f"Unknown flow control: {key}")
        return FLOW_CONTROL[key]

    def get_line_ending(self) -> bytes:
        key = self._ending_var.get()
        if key not in LINE_ENDINGS:
            raise ValueError(f"Unknown line ending: {key}")
        return LINE_ENDINGS[key]

    def get_display_format(self) -> DisplayFormat:
        return DisplayFormat(self._display_var.get())

    def settings_summary(self) -> str:
        return (
            f"{self._baud_var.get()} {self._uart_var.get()} "
            f"flow={self._flow_var.get()} ending={self._ending_var.get()}"
        )

    def set_connected(self, connected: bool) -> None:
        state = tk.DISABLED if connected else "readonly"
        baud_state = tk.DISABLED if connected else tk.NORMAL
        self._baud_combo.configure(state=baud_state)
        self._uart_combo.configure(state=state)
        self._flow_combo.configure(state=state)
        # Line ending and display format stay enabled while connected.
