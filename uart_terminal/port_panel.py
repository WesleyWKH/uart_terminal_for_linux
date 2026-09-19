"""COM port dropdown, refresh, and connect/disconnect toggle."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from uart_terminal.serial_manager import SerialManager


class PortPanel(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_toggle_connect: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._on_toggle_connect = on_toggle_connect

        ttk.Label(self, text="Port").pack(side=tk.LEFT, padx=(0, 4))
        self._port_var = tk.StringVar()
        self._port_combo = ttk.Combobox(
            self,
            textvariable=self._port_var,
            state="readonly",
            width=18,
        )
        self._port_combo.pack(side=tk.LEFT, padx=(0, 4))

        self._refresh_btn = ttk.Button(self, text="Refresh", command=self.refresh)
        self._refresh_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._connect_btn = ttk.Button(
            self,
            text="Connect",
            command=self._on_toggle_connect,
            width=12,
        )
        self._connect_btn.pack(side=tk.LEFT)

        self.refresh()

    def refresh(self) -> None:
        ports = SerialManager.list_ports()
        current = self._port_var.get()
        self._port_combo["values"] = ports
        if current in ports:
            self._port_var.set(current)
        elif ports:
            self._port_var.set(ports[0])
        else:
            self._port_var.set("")

    def get_port(self) -> str:
        return self._port_var.get().strip()

    def set_connected(self, connected: bool) -> None:
        self._connect_btn.configure(text="Disconnect" if connected else "Connect")
        combo_state = "disabled" if connected else "readonly"
        self._port_combo.configure(state=combo_state)
        self._refresh_btn.configure(state=tk.DISABLED if connected else tk.NORMAL)
