"""Start/stop writing the communication log to a timestamped text file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import IO


class LogRecorder:
    def __init__(self, directory: str | Path = "logs") -> None:
        self._directory = Path(directory)
        self._file: IO[str] | None = None
        self._path: Path | None = None

    @property
    def is_recording(self) -> bool:
        return self._file is not None

    @property
    def path(self) -> Path | None:
        return self._path

    def start(self) -> Path:
        if self.is_recording:
            raise RuntimeError("Logging is already active")
        self._directory.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        path = self._directory / name
        self._file = path.open("w", encoding="utf-8")
        self._path = path
        return path

    def write_line(self, line: str) -> None:
        if self._file is None:
            return
        self._file.write(line + "\n")
        self._file.flush()

    def stop(self) -> None:
        if self._file is None:
            return
        try:
            self._file.close()
        finally:
            self._file = None
