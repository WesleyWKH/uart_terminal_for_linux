"""Timestamped TX/RX communication window."""

from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from uart_terminal.display_format import format_payload
from uart_terminal.models import Direction, DisplayFormat, LogEntry


def format_log_line(entry: LogEntry, display_format: DisplayFormat) -> str:
    stamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") + f".{entry.timestamp.microsecond // 1000:03d}"
    payload = format_payload(entry.payload, display_format)
    return f"{stamp}  {entry.direction.value}  {payload}"


class MessageLog(ttk.LabelFrame):
    def __init__(
        self,
        parent: tk.Misc,
        on_line: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(parent, text="Communication Window", **kwargs)
        self.on_line = on_line
        self._display_format = DisplayFormat.ASCII
        self._entries: list[LogEntry] = []

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._text = tk.Text(
            container,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font="TkFixedFont",
            background="#ffffff",
            foreground="#222222",
            insertbackground="#222222",
            undo=False,
        )
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._text.yview)
        xscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self._text.xview)
        self._text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self._text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self._text.tag_configure("stamp", foreground="#666666")
        self._text.tag_configure("TX", foreground="#0047ab")
        self._text.tag_configure("RX", foreground="#0b6b0b")

    def set_display_format(self, display_format: DisplayFormat) -> None:
        if display_format is self._display_format:
            return
        self._display_format = display_format
        self._render_all()

    def append(self, entry: LogEntry, write_file: bool = True) -> None:
        self._entries.append(entry)
        line = format_log_line(entry, self._display_format)
        self._insert_line(entry)
        if write_file and self.on_line is not None:
            self.on_line(line)

    def clear_screen(self) -> None:
        self._entries.clear()
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)

    def _render_all(self) -> None:
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)
        for entry in self._entries:
            self._insert_line(entry)

    def _insert_line(self, entry: LogEntry) -> None:
        stamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") + (
            f".{entry.timestamp.microsecond // 1000:03d}"
        )
        payload = format_payload(entry.payload, self._display_format)
        self._text.configure(state=tk.NORMAL)
        self._text.insert(tk.END, stamp, ("stamp",))
        self._text.insert(tk.END, f"  {entry.direction.value}  ", (entry.direction.value,))
        self._text.insert(tk.END, payload + "\n", (entry.direction.value,))
        self._text.see(tk.END)
        self._text.configure(state=tk.DISABLED)
