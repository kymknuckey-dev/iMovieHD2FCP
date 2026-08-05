#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        print("ERROR: Activate the project virtual environment first.")
        print("Run: source .venv/bin/activate")
        return 2

    print("Installing iMovieHD2FCP graphical application...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-user", "-e", f"{root}[gui]"],
        check=False,
    )
    if result.returncode:
        return result.returncode

    print("")
    print("Installation complete.")
    print("Launch with: imoviehd2fcp-app")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
