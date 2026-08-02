from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence


def run_script(
    script: Path,
    arguments: Sequence[str],
    *,
    log_path: Path | None = None,
) -> int:
    command = [sys.executable, str(script), *arguments]
    print("$ " + " ".join(quote(item) for item in command))

    log_handle = None
    try:
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = log_path.open("a", encoding="utf-8")
            log_handle.write("$ " + " ".join(quote(item) for item in command) + "\n")
            log_handle.flush()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            if log_handle:
                log_handle.write(line)
                log_handle.flush()
        return int(process.wait())
    except OSError as exc:
        print(f"Unable to start command: {exc}", file=sys.stderr)
        return 2
    finally:
        if log_handle:
            log_handle.close()


def quote(value: str) -> str:
    if not value:
        return "''"
    if all(char.isalnum() or char in "_./:-" for char in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"
