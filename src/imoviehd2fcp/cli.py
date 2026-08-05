from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .paths import REQUIRED_LEGACY, find_home, find_script
from .reporting import build_reports
from .runner import run_script


def command_log_path(command: str, output_hint: Path | None = None) -> Path:
    base = output_hint if output_hint is not None else Path.cwd()
    directory = base.expanduser().resolve() / "Logs"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directory / f"{stamp}-{command}.log"


def add_common_batch_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--force", action="store_true", help="Reconvert existing completed projects.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned work without conversion.")
    parser.add_argument("--match", help="Convert only projects whose path contains this text.")
    parser.add_argument("--limit", type=int, help="Limit the number of selected projects.")
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
    print("Correct the failed checks and run doctor again.")
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
    log = command_log_path("analyse", args.output)
    result = run_script(script, command, log_path=log)
    print(f"\nCommand log: {log}")
    return result


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

    log = command_log_path("convert", args.output)
    result = run_script(script, command, log_path=log)
    print(f"\nCommand log: {log}")

    if result == 0 and not args.dry_run:
        try:
            text_report, html_report = build_reports(args.output.expanduser().resolve())
            print(f"Archive report: {text_report}")
            print(f"HTML report: {html_report}")
        except ValueError as exc:
            print(f"Report note: {exc}")

    return result


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

    log = command_log_path("verify", args.output)
    result = run_script(script, command, log_path=log)
    print(f"\nCommand log: {log}")

    if result == 0:
        try:
            text_report, html_report = build_reports(args.output.expanduser().resolve())
            print(f"Archive report: {text_report}")
            print(f"HTML report: {html_report}")
        except ValueError as exc:
            print(f"Report note: {exc}")

    return result


def command_report(args: argparse.Namespace) -> int:
    text_report, html_report = build_reports(
        args.output.expanduser().resolve(),
        args.report_directory.expanduser().resolve() if args.report_directory else None,
    )
    print(f"Text report: {text_report}")
    print(f"HTML report: {html_report}")
    return 0


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
    log = command_log_path("plan-events", args.plan.parent)
    result = run_script(script, command, log_path=log)
    print(f"\nCommand log: {log}")
    return result


def command_build_imports(args: argparse.Namespace) -> int:
    home = find_home()
    script = find_script("event_builder", home)
    log = command_log_path("build-imports", args.output)
    result = run_script(
        script,
        ["--plan", str(args.plan), "--output", str(args.output)],
        log_path=log,
    )
    print(f"\nCommand log: {log}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imoviehd2fcp",
        description="Migrate legacy iMovie HD archives into Final Cut Pro.",
        epilog="Run 'imoviehd2fcp COMMAND --help' for command-specific examples.",
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

    report = sub.add_parser("report", help="Build readable text and HTML archive reports.")
    report.add_argument("output", type=Path)
    report.add_argument("--report-directory", type=Path)
    report.set_defaults(func=command_report)

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
        help="Prepare each project FCPXML in place with its planned Event name.",
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
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted. Rerun the same conversion command to resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
