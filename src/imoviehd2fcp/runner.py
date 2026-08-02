from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence


def run_script(script: Path, arguments: Sequence[str]) -> int:
    command = [sys.executable, str(script), *arguments]
    print("$ " + " ".join(quote(item) for item in command))
    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:
        print(f"Unable to start command: {exc}", file=sys.stderr)
        return 2
    return int(completed.returncode)


def quote(value: str) -> str:
    if not value:
        return "''"
    if all(char.isalnum() or char in "_./:-" for char in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"
