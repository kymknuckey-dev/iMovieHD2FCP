#!/usr/bin/env python3
"""Batch-convert an archive of legacy iMovie HD projects using the proven tools.

This is a production wrapper around:

    imoviehd_parser.py
    imoviehd_stage6_5.py

It does not replace those scripts. It discovers every ``*.iMovieProj`` file,
preserves the archive's folder hierarchy, runs the parser, runs Stage 6.5, and
writes resumable logs and summary reports.

Example archive:

    iMovie HD Archive/
      Disney Final/
        Small World/
          Small World.iMovieProj
          Media/
      Europe Final 2/
        Tour/
          Tour.iMovieProj
          Media/

Example command:

    python3 imoviehd_batch_convert.py \
      "/Volumes/10TB Seagate/iMovie HD Archive" \
      "/Volumes/10TB Seagate/Final Cut Conversions"

The default tool paths are the scripts in the same folder as this file.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


STATE_FILENAME = "batch-conversion-state.json"
SUMMARY_CSV = "batch-conversion-summary.csv"
SUMMARY_TXT = "batch-conversion-report.txt"
LOGS_DIRNAME = "_Batch Logs"
TIMELINE_DIRNAME = "_Parser Output"


@dataclass
class ConversionResult:
    relative_project_path: str
    project_name: str
    project_file: str
    output_directory: str
    status: str
    started_at: str
    finished_at: str
    elapsed_seconds: float
    timeline_json: str | None = None
    fcpxml: str | None = None
    log_file: str | None = None
    error: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return cleaned or "Untitled"


def discover_projects(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.iMovieProj")
        if "__MACOSX" not in path.parts and not path.name.startswith("._")
    )


def command_text(command: list[str]) -> str:
    return " ".join(shlex_quote(part) for part in command)


def shlex_quote(value: str) -> str:
    if not value:
        return "''"
    if re.fullmatch(r"[A-Za-z0-9_./:@%+=,-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def run_logged(command: list[str], log_handle) -> tuple[int, str]:
    log_handle.write(f"\n$ {command_text(command)}\n")
    log_handle.flush()

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    captured: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        log_handle.write(line)
        captured.append(line)

    return_code = process.wait()
    log_handle.write(f"\n[exit code: {return_code}]\n")
    log_handle.flush()
    return return_code, "".join(captured)


def locate_timeline_json(parser_output: Path, project_name: str) -> Path | None:
    preferred_names = [
        f"{project_name}-timeline.json",
        f"{safe_name(project_name)}-timeline.json",
    ]
    for filename in preferred_names:
        candidate = parser_output / filename
        if candidate.is_file():
            return candidate

    candidates = sorted(
        parser_output.rglob("*-timeline.json"),
        key=lambda item: item.stat().st_mtime_ns,
        reverse=True,
    )
    if candidates:
        return candidates[0]

    # Fall back to JSON files with a top-level timeline key.
    for candidate in sorted(
        parser_output.rglob("*.json"),
        key=lambda item: item.stat().st_mtime_ns,
        reverse=True,
    ):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("timeline"), list):
            return candidate

    return None


def locate_fcpxml(output_directory: Path, started_ns: int | None = None) -> Path | None:
    candidates = list(output_directory.glob("*.fcpxml"))
    if started_ns is not None:
        new_candidates = [
            item for item in candidates if item.stat().st_mtime_ns >= started_ns
        ]
        if new_candidates:
            candidates = new_candidates

    if not candidates:
        return None

    return max(candidates, key=lambda item: item.stat().st_mtime_ns)


def load_state(path: Path) -> dict:
    if not path.is_file():
        return {"version": 1, "projects": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "projects": {}}
    if not isinstance(data, dict):
        return {"version": 1, "projects": {}}
    data.setdefault("version", 1)
    data.setdefault("projects", {})
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def already_complete(
    state: dict,
    key: str,
    expected_output: Path,
) -> bool:
    record = state.get("projects", {}).get(key)
    if not isinstance(record, dict) or record.get("status") != "success":
        return False

    fcpxml_value = record.get("fcpxml")
    if fcpxml_value and Path(fcpxml_value).is_file():
        return True

    return bool(list(expected_output.glob("*.fcpxml")))


def write_summary(output_root: Path, results: list[ConversionResult]) -> None:
    csv_path = output_root / SUMMARY_CSV
    fields = [
        "relative_project_path",
        "project_name",
        "status",
        "elapsed_seconds",
        "project_file",
        "timeline_json",
        "fcpxml",
        "output_directory",
        "log_file",
        "started_at",
        "finished_at",
        "error",
    ]

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))

    successful = sum(item.status == "success" for item in results)
    skipped = sum(item.status == "skipped" for item in results)
    failed = sum(item.status == "failed" for item in results)
    elapsed = sum(item.elapsed_seconds for item in results)

    report = [
        "iMovie HD Batch Conversion Report",
        "================================",
        "",
        f"Projects listed: {len(results)}",
        f"Succeeded: {successful}",
        f"Skipped (already complete): {skipped}",
        f"Failed: {failed}",
        f"Total processing time: {format_elapsed(elapsed)}",
        "",
        "FAILED PROJECTS",
        "---------------",
    ]

    failures = [item for item in results if item.status == "failed"]
    if failures:
        for item in failures:
            report.append(f"{item.relative_project_path}: {item.error}")
            if item.log_file:
                report.append(f"  Log: {item.log_file}")
    else:
        report.append("None.")

    report.extend(["", "OUTPUTS", "-------"])
    for item in results:
        if item.status == "success" and item.fcpxml:
            report.append(f"{item.relative_project_path}: {item.fcpxml}")

    (output_root / SUMMARY_TXT).write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )


def format_elapsed(seconds: float) -> str:
    seconds_int = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds_int, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def select_projects(
    projects: list[Path],
    archive_root: Path,
    match: str | None,
    limit: int | None,
) -> list[Path]:
    selected = projects
    if match:
        expression = re.compile(match, re.IGNORECASE)
        selected = [
            project
            for project in selected
            if expression.search(str(project.relative_to(archive_root)))
        ]
    if limit is not None:
        selected = selected[:limit]
    return selected


def ensure_tools(parser_script: Path, converter_script: Path) -> None:
    missing: list[str] = []
    if not parser_script.is_file():
        missing.append(f"Parser not found: {parser_script}")
    if not converter_script.is_file():
        missing.append(f"Stage 6.5 converter not found: {converter_script}")
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg is not available on PATH")
    if shutil.which("ffprobe") is None:
        missing.append("ffprobe is not available on PATH")
    if missing:
        raise SystemExit("\n".join(missing))


def main() -> int:
    script_dir = Path(__file__).resolve().parent

    argument_parser = argparse.ArgumentParser(
        description="Batch-convert an iMovie HD archive using the proven parser and Stage 6.5 converter."
    )
    argument_parser.add_argument(
        "archive_root",
        type=Path,
        help="Root containing copied CD folders and project folders.",
    )
    argument_parser.add_argument(
        "output_root",
        type=Path,
        help="Destination root for converted projects.",
    )
    argument_parser.add_argument(
        "--parser",
        dest="parser_script",
        type=Path,
        default=script_dir / "imoviehd_parser.py",
        help="Path to imoviehd_parser.py.",
    )
    argument_parser.add_argument(
        "--converter",
        dest="converter_script",
        type=Path,
        default=script_dir / "imoviehd_stage6_5.py",
        help="Path to imoviehd_stage6_5.py.",
    )
    argument_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run projects even when their completed FCPXML already exists.",
    )
    argument_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be converted without running the tools.",
    )
    argument_parser.add_argument(
        "--match",
        help="Only convert project paths matching this regular expression.",
    )
    argument_parser.add_argument(
        "--limit",
        type=int,
        help="Convert only the first N selected projects (useful for testing).",
    )
    argument_parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop the batch after the first failure.",
    )
    argument_parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Pass --allow-missing to Stage 6.5.",
    )
    args = argument_parser.parse_args()

    archive_root = args.archive_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    parser_script = args.parser_script.expanduser().resolve()
    converter_script = args.converter_script.expanduser().resolve()

    if not archive_root.is_dir():
        print(f"Archive root is not a folder: {archive_root}", file=sys.stderr)
        return 2

    if not args.dry_run:
        ensure_tools(parser_script, converter_script)

    all_projects = discover_projects(archive_root)
    projects = select_projects(
        all_projects,
        archive_root,
        args.match,
        args.limit,
    )

    if not projects:
        print("No matching .iMovieProj files were found.")
        return 1

    output_root.mkdir(parents=True, exist_ok=True)
    logs_root = output_root / LOGS_DIRNAME
    logs_root.mkdir(exist_ok=True)
    state_path = output_root / STATE_FILENAME
    state = load_state(state_path)

    print(f"Archive: {archive_root}")
    print(f"Destination: {output_root}")
    print(f"Projects discovered: {len(all_projects)}")
    print(f"Projects selected: {len(projects)}")
    print("")

    results: list[ConversionResult] = []

    for index, project_file in enumerate(projects, start=1):
        project_folder = project_file.parent
        relative_folder = project_folder.relative_to(archive_root)
        relative_key = relative_folder.as_posix()
        project_name = project_folder.name
        project_output = output_root / relative_folder
        parser_output = project_output / TIMELINE_DIRNAME
        log_file = logs_root / (
            safe_name(relative_key.replace("/", " — ")) + ".log"
        )

        print("=" * 72)
        print(f"[{index}/{len(projects)}] {relative_key}")
        print("=" * 72)

        if not args.force and already_complete(state, relative_key, project_output):
            existing_fcpxml = locate_fcpxml(project_output)
            print("SKIP: already converted.")
            result = ConversionResult(
                relative_project_path=relative_key,
                project_name=project_name,
                project_file=str(project_file),
                output_directory=str(project_output),
                status="skipped",
                started_at=utc_now(),
                finished_at=utc_now(),
                elapsed_seconds=0.0,
                fcpxml=str(existing_fcpxml) if existing_fcpxml else None,
                log_file=str(log_file) if log_file.exists() else None,
            )
            results.append(result)
            continue

        if args.dry_run:
            print(f"Would parse: {project_file}")
            print(f"Would write: {project_output}")
            result = ConversionResult(
                relative_project_path=relative_key,
                project_name=project_name,
                project_file=str(project_file),
                output_directory=str(project_output),
                status="skipped",
                started_at=utc_now(),
                finished_at=utc_now(),
                elapsed_seconds=0.0,
                error="dry run",
            )
            results.append(result)
            continue

        project_output.mkdir(parents=True, exist_ok=True)
        parser_output.mkdir(parents=True, exist_ok=True)
        started_at = utc_now()
        start_time = time.monotonic()
        started_ns = time.time_ns()
        error: str | None = None
        timeline_json: Path | None = None
        fcpxml: Path | None = None

        with log_file.open("a", encoding="utf-8") as log_handle:
            log_handle.write("\n" + "=" * 72 + "\n")
            log_handle.write(f"Project: {relative_key}\n")
            log_handle.write(f"Started: {started_at}\n")
            log_handle.write("=" * 72 + "\n")

            parser_command = [
                sys.executable,
                str(parser_script),
                str(project_file),
                "--output",
                str(parser_output),
            ]
            parser_code, parser_text = run_logged(parser_command, log_handle)
            if parser_code != 0:
                error = f"Parser failed with exit code {parser_code}"
            else:
                timeline_json = locate_timeline_json(parser_output, project_name)
                if timeline_json is None:
                    error = "Parser completed but no timeline JSON was found."

            if error is None and timeline_json is not None:
                converter_command = [
                    sys.executable,
                    str(converter_script),
                    str(timeline_json),
                    "--output-dir",
                    str(project_output),
                    "--project-name",
                    project_name,
                ]
                if args.force:
                    converter_command.append("--force")
                if args.allow_missing:
                    converter_command.append("--allow-missing")

                converter_code, converter_text = run_logged(
                    converter_command,
                    log_handle,
                )
                if converter_code != 0:
                    error = f"Stage 6.5 failed with exit code {converter_code}"
                else:
                    fcpxml = locate_fcpxml(project_output, started_ns)
                    if fcpxml is None:
                        error = "Stage 6.5 completed but no FCPXML was found."

        elapsed = time.monotonic() - start_time
        finished_at = utc_now()

        if error is None and fcpxml is not None:
            status = "success"
            print(f"SUCCESS: {fcpxml}")
        else:
            status = "failed"
            print(f"FAILED: {error}")
            print(f"Log: {log_file}")

        result = ConversionResult(
            relative_project_path=relative_key,
            project_name=project_name,
            project_file=str(project_file),
            output_directory=str(project_output),
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=round(elapsed, 3),
            timeline_json=str(timeline_json) if timeline_json else None,
            fcpxml=str(fcpxml) if fcpxml else None,
            log_file=str(log_file),
            error=error,
        )
        results.append(result)

        state.setdefault("projects", {})[relative_key] = asdict(result)
        state["archive_root"] = str(archive_root)
        state["output_root"] = str(output_root)
        state["updated_at"] = finished_at
        save_state(state_path, state)
        write_summary(output_root, results)

        print(f"Elapsed: {format_elapsed(elapsed)}")
        print("")

        if status == "failed" and args.stop_on_error:
            break

    write_summary(output_root, results)

    successes = sum(item.status == "success" for item in results)
    skips = sum(item.status == "skipped" for item in results)
    failures = sum(item.status == "failed" for item in results)

    print("=" * 72)
    print("BATCH COMPLETE")
    print("=" * 72)
    print(f"Success: {successes}")
    print(f"Skipped: {skips}")
    print(f"Failed: {failures}")
    print(f"Report: {output_root / SUMMARY_TXT}")
    print(f"Summary CSV: {output_root / SUMMARY_CSV}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
