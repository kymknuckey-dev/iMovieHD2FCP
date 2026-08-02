from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO


class Tee:
    """Write terminal output to both the console and a persistent log."""

    def __init__(self, console: TextIO, log: TextIO):
        self.console = console
        self.log = log

    def write(self, value: str) -> int:
        self.console.write(value)
        self.log.write(value)
        self.log.flush()
        return len(value)

    def flush(self) -> None:
        self.console.flush()
        self.log.flush()

    def isatty(self) -> bool:
        return self.console.isatty()


def default_log_directory() -> Path:
    env = os.environ.get("IMOVIEHD2FCP_LOG_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd() / "logs"


def open_command_log(command_name: str, directory: Path | None = None):
    directory = (directory or default_log_directory()).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"{stamp}-{command_name}.log"
    handle = path.open("w", encoding="utf-8")
    handle.write(f"iMovieHD2FCP command log\n")
    handle.write(f"Command: {command_name}\n")
    handle.write(f"Started: {datetime.now().isoformat(timespec='seconds')}\n")
    handle.write("=" * 72 + "\n\n")
    handle.flush()
    return path, handle


def install_tee(log_handle) -> tuple[TextIO, TextIO]:
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(original_stdout, log_handle)
    sys.stderr = Tee(original_stderr, log_handle)
    return original_stdout, original_stderr


def restore_streams(original_stdout: TextIO, original_stderr: TextIO) -> None:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
