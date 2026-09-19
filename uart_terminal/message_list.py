"""Indexed send-message list with names, editing, and reorder controls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from uart_terminal.display_format import (
    bytes_to_ascii_editable,
    bytes_to_hex,
    clear_validator,
    parse_payload,
    register_hex_validator,
)
from uart_terminal.message_file import load_messages
from uart_terminal.models import DisplayFormat, SendMessage


@dataclass
class _Row:
    message: SendMessage
    frame: tk.Frame
    index_label: ttk.Label
    name_var: tk.StringVar
    payload_var: tk.StringVar
    name_entry: ttk.Entry
    payload_entry: ttk.Entry
    send_btn: ttk.Button
    selected: bool = field(default=False)


class MessageList(ttk.LabelFrame):
    def __init__(
        self,
        parent: tk.Misc,
        on_send: Callable[[int, SendMessage], None],
        **kwargs: object,
    ) -> None:
        super().__init__(parent, text="Send Sequences", **kwargs)
        self._on_send = on_send
        self._display_format = DisplayFormat.ASCII
        self._rows: list[_Row] = []
        self._selected = -1

        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 0))
        ttk.Label(header, text="#", width=4).pack(side=tk.LEFT)
        ttk.Label(header, text="Name", width=14).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(header, text="Message").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(header, text="Send", width=8).pack(side=tk.RIGHT)

        table = ttk.Frame(self)
        table.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._canvas = tk.Canvas(table, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)
        self._inner.bind(
            "<Configure>",
            lambda _event: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.bind(
            "<Configure>",
            lambda event: self._canvas.itemconfigure(self._window, width=event.width),
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind("<Enter>", self._bind_wheel)
        self._canvas.bind("<Leave>", self._unbind_wheel)
        self._inner.bind("<Enter>", self._bind_wheel)
        self._inner.bind("<Leave>", self._unbind_wheel)

        buttons = ttk.Frame(self)
        buttons.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Button(buttons, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(buttons, text="Up", command=lambda: self.move_selected(-1)).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(buttons, text="Down", command=lambda: self.move_selected(1)).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(buttons, text="Import", command=self.import_from_file).pack(side=tk.LEFT)

        self.add_row()

    def _bind_wheel(self, _event: tk.Event | None = None) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_wheel(self, _event: tk.Event | None = None) -> None:
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.num == 4 or event.delta > 0:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self._canvas.yview_scroll(1, "units")

    def commit_edits(self, display_format: DisplayFormat | None = None) -> None:
        fmt = display_format or self._display_format
        for row in self._rows:
            row.message.name = row.name_var.get()
            try:
                row.message.payload = parse_payload(row.payload_var.get(), fmt)
            except ValueError:
                pass

    def set_display_format(self, display_format: DisplayFormat) -> None:
        if display_format is self._display_format:
            self._apply_validators()
            return
        self.commit_edits(self._display_format)
        self._display_format = display_format
        for row in self._rows:
            row.payload_var.set(self._payload_text(row.message.payload))
        self._apply_validators()

    def _payload_text(self, payload: bytes) -> str:
        if self._display_format is DisplayFormat.HEX:
            return bytes_to_hex(payload)
        return bytes_to_ascii_editable(payload)

    def _apply_validators(self) -> None:
        for row in self._rows:
            if self._display_format is DisplayFormat.HEX:
                register_hex_validator(row.payload_entry)
            else:
                clear_validator(row.payload_entry)

    def add_row(self, message: SendMessage | None = None) -> None:
        self.commit_edits()
        item = message or SendMessage()
        row = self._make_row(item)
        self._rows.append(row)
        self._relayout()
        self._select(len(self._rows) - 1)

    def delete_selected(self) -> None:
        if not self._rows:
            return
        self.commit_edits()
        index = self._selected if 0 <= self._selected < len(self._rows) else len(self._rows) - 1
        row = self._rows.pop(index)
        row.frame.destroy()
        if not self._rows:
            self._selected = -1
            return
        self._select(min(index, len(self._rows) - 1))
        self._relayout()

    def move_selected(self, delta: int) -> None:
        if not (0 <= self._selected < len(self._rows)):
            return
        target = self._selected + delta
        if target < 0 or target >= len(self._rows):
            return
        self.commit_edits()
        self._rows[self._selected], self._rows[target] = (
            self._rows[target],
            self._rows[self._selected],
        )
        self._select(target)
        self._relayout()

    def set_messages(self, messages: list[SendMessage]) -> None:
        for row in self._rows:
            row.frame.destroy()
        self._rows.clear()
        self._selected = -1
        for message in messages:
            self._rows.append(self._make_row(message))
        self._relayout()
        if self._rows:
            self._select(0)

    def import_from_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Import message list",
            filetypes=[("Message lists", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        result = load_messages(path)
        if not result.messages and result.skipped:
            messagebox.showerror(
                "Import failed",
                "No valid messages found.\n" + "\n".join(result.skipped[:8]),
            )
            return
        self.set_messages(result.messages)
        if result.skipped:
            messagebox.showwarning(
                "Import completed with errors",
                "Skipped:\n" + "\n".join(result.skipped[:12]),
            )

    def get_committed_message(self, index: int) -> SendMessage:
        if not (0 <= index < len(self._rows)):
            raise IndexError(index)
        self.commit_edits()
        row = self._rows[index]
        return SendMessage(name=row.message.name, payload=row.message.payload)

    def parse_row_for_send(self, index: int) -> SendMessage:
        """Parse the visible fields; raise ValueError if HEX is invalid."""
        if not (0 <= index < len(self._rows)):
            raise IndexError(index)
        row = self._rows[index]
        payload = parse_payload(row.payload_var.get(), self._display_format)
        name = row.name_var.get()
        row.message.name = name
        row.message.payload = payload
        return SendMessage(name=name, payload=payload)

    def _make_row(self, message: SendMessage) -> _Row:
        frame = tk.Frame(self._inner, bg="#ffffff")
        index_label = ttk.Label(frame, text="0", width=4, anchor="center")
        index_label.pack(side=tk.LEFT)
        name_var = tk.StringVar(value=message.name)
        name_entry = ttk.Entry(frame, textvariable=name_var, width=14)
        name_entry.pack(side=tk.LEFT, padx=(0, 4))
        payload_var = tk.StringVar(value=self._payload_text(message.payload))
        payload_entry = ttk.Entry(frame, textvariable=payload_var)
        payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        send_btn = ttk.Button(frame, text="Send", width=8)
        send_btn.pack(side=tk.RIGHT)

        row = _Row(
            message=message,
            frame=frame,
            index_label=index_label,
            name_var=name_var,
            payload_var=payload_var,
            name_entry=name_entry,
            payload_entry=payload_entry,
            send_btn=send_btn,
        )
        send_btn.configure(command=lambda r=row: self._send_row(r))
        for widget in (frame, index_label):
            widget.bind("<Button-1>", lambda _event, r=row: self._select_row(r))
        name_entry.bind("<FocusIn>", lambda _event, r=row: self._select_row(r))
        payload_entry.bind("<FocusIn>", lambda _event, r=row: self._select_row(r))
        if self._display_format is DisplayFormat.HEX:
            register_hex_validator(payload_entry)
        return row

    def _send_row(self, row: _Row) -> None:
        self._select_row(row)
        index = self._rows.index(row)
        try:
            message = self.parse_row_for_send(index)
        except ValueError as exc:
            messagebox.showerror("Invalid message", str(exc))
            return
        self._on_send(index, message)

    def _select_row(self, row: _Row) -> None:
        if row in self._rows:
            self._select(self._rows.index(row))

    def _select(self, index: int) -> None:
        self._selected = index
        for i, row in enumerate(self._rows):
            color = "#d6e4ff" if i == index else "#ffffff"
            row.frame.configure(bg=color)
            row.selected = i == index

    def _relayout(self) -> None:
        for row in self._rows:
            row.frame.pack_forget()
        for i, row in enumerate(self._rows):
            row.index_label.configure(text=str(i + 1))
            row.frame.pack(fill=tk.X, pady=1)
        self._inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
