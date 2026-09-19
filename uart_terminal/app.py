"""Main window: Docklight-style layout and feature wiring."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from uart_terminal import APP_NAME, APP_VERSION
from uart_terminal.log_recorder import LogRecorder
from uart_terminal.message_list import MessageList
from uart_terminal.message_log import MessageLog
from uart_terminal.models import Direction, DisplayFormat, LogEntry, SendMessage
from uart_terminal.port_panel import PortPanel
from uart_terminal.serial_manager import SerialEvent, SerialManager, drain_queue
from uart_terminal.settings_panel import SettingsPanel

_POLL_MS = 30


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.minsize(960, 560)
        self.geometry("1180x720")

        try:
            self.tk.call("tk", "scaling", 1.1)
            style = ttk.Style(self)
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except tk.TclError:
            pass

        self._serial = SerialManager()
        self._recorder = LogRecorder()
        self._display_format = DisplayFormat.ASCII

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(_POLL_MS, self._poll_serial)

    def _build(self) -> None:
        title_row = ttk.Frame(self, padding=(8, 8, 8, 0))
        title_row.pack(fill=tk.X)
        ttk.Label(title_row, text=APP_NAME, font=("TkDefaultFont", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_row, text=APP_VERSION).pack(side=tk.LEFT, padx=(8, 0))

        toolbar = ttk.Frame(self, padding=(8, 6, 8, 4))
        toolbar.pack(fill=tk.X)

        row1 = ttk.Frame(toolbar)
        row1.pack(fill=tk.X, pady=(0, 4))
        self._ports = PortPanel(row1, on_toggle_connect=self._toggle_connect)
        self._ports.pack(side=tk.LEFT, padx=(0, 16))
        self._settings = SettingsPanel(row1, on_display_format_change=self._on_display_format_change)
        self._settings.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row2 = ttk.Frame(toolbar)
        row2.pack(fill=tk.X)
        self._log_btn = ttk.Button(row2, text="Start Logging", width=14, command=self._toggle_logging)
        self._log_btn.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row2, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        self._messages = MessageList(body, on_send=self._send_message)
        self._log = MessageLog(body, on_line=self._recorder.write_line)
        body.add(self._messages, weight=1)
        body.add(self._log, weight=2)

        self._status = ttk.Label(self, text="", anchor="w", padding=(8, 4))
        self._status.pack(fill=tk.X, side=tk.BOTTOM)
        self._update_status()

    def _toggle_connect(self) -> None:
        if self._serial.is_connected:
            self._serial.disconnect()
            self._set_connection_widgets(False)
            self._update_status()
            return
        port = self._ports.get_port()
        if not port:
            messagebox.showerror("Connect failed", "No COM port selected. Refresh the list and try again.")
            return
        try:
            baud = self._settings.get_baudrate()
            bytesize, parity, stopbits = self._settings.get_uart_params()
            rtscts, xonxoff = self._settings.get_flow()
            self._serial.connect(
                port=port,
                baudrate=baud,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                rtscts=rtscts,
                xonxoff=xonxoff,
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("Connect failed", str(exc))
            return
        self._set_connection_widgets(True)
        self._update_status()

    def _set_connection_widgets(self, connected: bool) -> None:
        self._ports.set_connected(connected)
        self._settings.set_connected(connected)

    def _on_display_format_change(self) -> None:
        new_format = self._settings.get_display_format()
        if new_format is self._display_format:
            return
        self._messages.commit_edits(self._display_format)
        self._display_format = new_format
        self._messages.set_display_format(new_format)
        self._log.set_display_format(new_format)

    def _send_message(self, _index: int, message: SendMessage) -> None:
        if not self._serial.is_connected:
            messagebox.showwarning("Not connected", "Connect to a COM port before sending.")
            return
        payload = message.payload
        if self._display_format is DisplayFormat.ASCII:
            payload = payload + self._settings.get_line_ending()
        if not payload:
            messagebox.showwarning("Empty message", "Nothing to send.")
            return
        try:
            self._serial.write(payload)
        except RuntimeError as exc:
            messagebox.showerror("Send failed", str(exc))
            return
        except OSError as exc:
            self._handle_disconnect_error(str(exc))
            return
        self._log.append(
            LogEntry(timestamp=datetime.now(), direction=Direction.TX, payload=payload)
        )

    def _toggle_logging(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
            self._log_btn.configure(text="Start Logging")
            self._update_status()
            return
        try:
            path = self._recorder.start()
        except OSError as exc:
            messagebox.showerror("Logging failed", str(exc))
            return
        self._log_btn.configure(text="Stop Logging")
        self._update_status(extra=f"Logging to {path}")

    def _clear_log(self) -> None:
        self._log.clear_screen()

    def _poll_serial(self) -> None:
        drain_queue(self._serial.events, self._on_serial_event)
        self.after(_POLL_MS, self._poll_serial)

    def _on_serial_event(self, event: SerialEvent) -> None:
        if event.kind == "rx" and event.payload:
            stamp = event.timestamp or datetime.now()
            self._log.append(LogEntry(timestamp=stamp, direction=Direction.RX, payload=event.payload))
        elif event.kind == "error":
            self._handle_disconnect_error(event.message)

    def _handle_disconnect_error(self, message: str) -> None:
        if self._serial.is_connected:
            self._serial.disconnect()
        self._set_connection_widgets(False)
        self._update_status()
        messagebox.showerror("Serial port", message)

    def _update_status(self, extra: str = "") -> None:
        if self._serial.is_connected:
            state = f"Connected {self._ports.get_port()} {self._settings.settings_summary()}"
        else:
            state = "Disconnected"
        if self._recorder.is_recording and self._recorder.path is not None:
            state += f"  |  Logging {self._recorder.path.name}"
        else:
            state += "  |  Logging off"
        if extra:
            state += f"  |  {extra}"
        self._status.configure(text=state)

    def _on_close(self) -> None:
        self._serial.disconnect()
        self._recorder.stop()
        self.destroy()


def run() -> None:
    app = MainWindow()
    app.mainloop()
