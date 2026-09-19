# UART Terminal for Linux

A Docklight-style serial terminal written in Python and Tkinter. Use it to open a UART/COM port, send named sequences from a list, and watch timestamped TX/RX traffic in ASCII or HEX.

## Requirements

- Python 3.10+
- Tkinter (`sudo apt install python3-tk` on Debian/Ubuntu)
- [pyserial](https://pyserial.readthedocs.io/) (`sudo apt install python3-serial` or pip)
- Linux serial-device permission (usually membership in the `dialout` group)

```bash
sudo usermod -aG dialout "$USER"
# log out and back in after changing groups
```

## Install and run

```bash
# Debian/Ubuntu system packages
sudo apt install python3-tk python3-serial

# or a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 main.py
```

## Features

- Port dropdown, refresh, and Connect/Disconnect
- Baud rate, UART format (`8N1`, `8E1`, `8O1`, `7E1`, `7O1`, `8N2`), flow control, and ASCII line ending
- Left-side send list: index, name, payload, Send, plus Add / Delete / Up / Down / Import
- Right-side communication log with timestamps and TX/RX coloring
- Global ASCII/HEX display; HEX mode rejects invalid payload characters
- Start/Stop logging to `logs/YYYYMMDD_HHMMSS.txt`
- Clear log screen (does not stop an active log file)

Port, baud, format, and flow control are locked while the port is open. Display format, the send list, logging, and clear stay available.

## ASCII vs HEX

Internal payloads are always bytes. The Display dropdown only changes how the send list and log are shown.

- **ASCII:** type text in the send list. The selected line ending (`None` / `LF` / `CR` / `CRLF`) is appended when you press Send. Non-printable bytes appear as `.` in the log.
- **HEX:** type space-separated bytes such as `41 54 0D 0A`. Only `0-9`, `A-F`, `a-f`, and spaces are accepted. An odd number of digits is rejected on Send. Line ending is not appended; include `0D` / `0A` yourself if needed.

## Message list file format

Import replaces the current send list. Lines starting with `#` and blank lines are ignored. Fields are TAB-separated:

```
# uart_terminal message list v1
# index<TAB>name<TAB>encoding<TAB>payload
1	Ping	ASCII	AT
2	Reset	HEX	AA 55 0D 0A
```

`encoding` must be `ASCII` or `HEX`. The index column is only for readability; messages are loaded in file order. A sample file is in `examples/sample_messages.txt`.

## Log files

Start Logging creates `logs/YYYYMMDD_HHMMSS.txt` in the working directory. Each line matches what you see in the communication window at the time it arrives. Changing ASCII/HEX after that only updates the screen; already-written file lines stay as they were.
