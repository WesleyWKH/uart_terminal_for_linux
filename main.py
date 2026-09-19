#!/usr/bin/env python3
"""Launch the UART Terminal application."""

try:
    from uart_terminal.app import run
except ModuleNotFoundError as exc:
    if "tkinter" in str(exc):
        raise SystemExit(
            "Tkinter is required. On Debian/Ubuntu run: sudo apt install python3-tk"
        ) from exc
    raise

if __name__ == "__main__":
    run()
