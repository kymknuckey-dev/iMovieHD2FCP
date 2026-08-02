#!/usr/bin/env python3
"""Prepare the product layout inside the existing iMovieHD2FCP project."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


FILES = [
    "imoviehd_parser.py",
    "imoviehd_archive_analyzer.py",
    "imoviehd_v1_converter.py",
    "imoviehd_v1_batch.py",
    "imoviehd_v1_archive_builder_fixed.py",
    "imoviehd_v1_event_import_builder.py",
]


def active_virtual_environment() -> Path | None:
    value = os.environ.get("VIRTUAL_ENV")
    return Path(value).resolve() if value else None


def pip_belongs_to_venv(venv: Path) -> bool:
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode == 0 and str(venv) in completed.stdout


def main() -> int:
    root = Path(__file__).resolve().parent
    venv = active_virtual_environment()
    if venv is None:
        print("ERROR: No active virtual environment.")
        print("Run: source .venv/bin/activate")
        return 2
    if Path(sys.executable).resolve().parent != venv / "bin":
        print(f"ERROR: Python is not from the active virtual environment: {sys.executable}")
        return 2
    if not pip_belongs_to_venv(venv):
        print("ERROR: pip is not installed inside the active virtual environment.")
        print("Recreate .venv or run: python3 -m ensurepip --upgrade")
        return 2
    legacy = root / "legacy"
    legacy.mkdir(exist_ok=True)

    missing: list[str] = []
    for filename in FILES:
        source = root / filename
        destination = legacy / filename

        if destination.is_file():
            print(f"✓ Already present: legacy/{filename}")
            continue

        if source.is_file():
            shutil.copy2(source, destination)
            print(f"✓ Copied: {filename} -> legacy/{filename}")
        else:
            missing.append(filename)
            print(f"✗ Missing: {filename}")

    if missing:
        print("")
        print("Some required proven scripts were not found in the project root:")
        for filename in missing:
            print(f"  - {filename}")
        print("Copy them into the project root and rerun this installer.")
        return 1

    print("")
    print("Installing iMovieHD2FCP in editable mode...")
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-user", "-e", str(root)],
        check=False,
    )
    if completed.returncode:
        return int(completed.returncode)

    print("")
    print("Installation complete.")
    print("Run: imoviehd2fcp doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
