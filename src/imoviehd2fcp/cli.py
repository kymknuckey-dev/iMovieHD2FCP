from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .paths import REQUIRED_LEGACY, find_home, find_script
from .runner import run_script


def add_common_batch_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")


def command_doctor(_: argparse.Namespace) -> int:
    home = find_home()
    print(f"iMovieHD2FCP {__version__}")
    print(f"Product home: {home}")
    print("")

    ok = True
    print("Components")
    print("----------")
    for key, filename in REQUIRED_LEGACY.items():
        try:
            path = find_script(key, home)
            print(f"✓ {filename}: {path}")
        except FileNotFoundError:
            ok = False
            print(f"✗ {filename}: missing")

    print("")
    print("External tools")
    print("--------------")
    for tool in ("ffmpeg", "ffprobe"):
        location = shutil.which(tool)
        if location:
            print(f"✓ {tool}: {location}")
        else:
            ok = False
            print(f"✗ {tool}: missing")

    print("")
    print("Python environment")
    print("------------------")
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        ok = False
        print("✗ No active virtual environment")
    else:
        print(f"✓ Active virtual environment: {venv}")
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if completed.returncode == 0 and venv in completed.stdout:
            print(f"✓ pip belongs to virtual environment: {completed.stdout.strip()}")
        else:
            ok = False
            print(f"✗ pip is outside virtual environment: {completed.stdout.strip()}")

    print("")
    if ok:
        print("READY")
        return 0

    print("NOT READY")
    print("Run python3 install_product.py from the project folder, then run doctor again.")
    return 1


def command_analyse(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("analyser", home)
    parser_script = find_script("parser", home)
    command = [
        str(args.archive),
        "--parser", str(parser_script),
        "--output", str(args.output),
    ]
    if args.reuse_json:
        command.append("--reuse-json")
    return run_script(script, command)


def command_convert(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("batch", home)
    parser_script = find_script("parser", home)
    converter_script = find_script("converter", home)
    command = [
        str(args.archive),
        str(args.output),
        "--parser", str(parser_script),
        "--converter", str(converter_script),
    ]
    for flag in ("force", "dry_run", "stop_on_error", "allow_missing"):
        if getattr(args, flag):
            command.append("--" + flag.replace("_", "-"))
    if args.match:
        command += ["--match", args.match]
    if args.limit is not None:
        command += ["--limit", str(args.limit)]
    return run_script(script, command)


def command_verify(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("batch", home)
    parser_script = find_script("parser", home)
    converter_script = find_script("converter", home)
    command = [
        str(args.archive),
        str(args.output),
        "--parser", str(parser_script),
        "--converter", str(converter_script),
        "--verify-only",
    ]
    if args.match:
        command += ["--match", args.match]
    if args.limit is not None:
        command += ["--limit", str(args.limit)]
    return run_script(script, command)


def command_plan_events(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("archive_builder", home)
    command = [
        "plan",
        str(args.converted_root),
        "--plan", str(args.plan),
        "--event-mode", args.event_mode,
        "--event-level", str(args.event_level),
    ]
    return run_script(script, command)


def command_build_imports(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("event_builder", home)
    return run_script(
        script,
        ["--plan", str(args.plan), "--output", str(args.output)],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imoviehd2fcp",
        description="Migrate legacy iMovie HD archives into Final Cut Pro.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check installation and dependencies.")
    doctor.set_defaults(func=command_doctor)

    analyse = sub.add_parser("analyse", help="Scan an archive without converting media.")
    analyse.add_argument("archive", type=Path)
    analyse.add_argument("output", type=Path)
    analyse.add_argument("--reuse-json", action="store_true")
    analyse.set_defaults(func=command_analyse)

    convert = sub.add_parser("convert", help="Convert all projects in an archive.")
    convert.add_argument("archive", type=Path)
    convert.add_argument("output", type=Path)
    add_common_batch_options(convert)
    convert.set_defaults(func=command_convert)

    verify = sub.add_parser("verify", help="Verify existing conversion outputs.")
    verify.add_argument("archive", type=Path)
    verify.add_argument("output", type=Path)
    verify.add_argument("--match")
    verify.add_argument("--limit", type=int)
    verify.set_defaults(func=command_verify)

    plan = sub.add_parser("plan-events", help="Create an editable Final Cut Event-plan CSV.")
    plan.add_argument("converted_root", type=Path)
    plan.add_argument("--plan", required=True, type=Path)
    plan.add_argument(
        "--event-mode",
        choices=["top", "parent", "project", "level"],
        default="parent",
    )
    plan.add_argument("--event-level", type=int, default=1)
    plan.set_defaults(func=command_plan_events)

    imports = sub.add_parser(
        "build-imports",
        help="Create safe, intact per-project XML imports grouped by Event.",
    )
    imports.add_argument("--plan", required=True, type=Path)
    imports.add_argument("--output", required=True, type=Path)
    imports.set_defaults(func=command_build_imports)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
