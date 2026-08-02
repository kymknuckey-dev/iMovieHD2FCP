#!/usr/bin/env python3
"""Polished batch converter for legacy iMovie HD archives.

This remains a production wrapper around the proven tools:

    imoviehd_parser.py
    imoviehd_stage6_5.py

Enhancements over the first batch wrapper:

* Clear per-project and overall progress with elapsed time and ETA.
* Resume-safe state tracking.
* Post-conversion verification of FCPXML, media, manifest, timeline JSON,
  title inventory, and every local media URL referenced by FCPXML.
* Archive statistics including timeline items, titles, music, converted media
  counts and disk usage.
* Detailed CSV, JSON and human-readable reports.
* Verification failures are reported distinctly from conversion failures.

Example:

    python3 imoviehd_batch_convert_v2.py \
      "/Volumes/10TB Seagate/iMovie HD Archive" \
      "/Volumes/10TB Seagate/Final Cut Conversions"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

STATE_FILENAME = "batch-conversion-state.json"
SUMMARY_CSV = "batch-conversion-summary.csv"
SUMMARY_JSON = "batch-conversion-summary.json"
SUMMARY_TXT = "batch-conversion-report.txt"
LOGS_DIRNAME = "_Batch Logs"
TIMELINE_DIRNAME = "_Parser Output"
CONVERTED_MEDIA_DIRNAME = "Converted Media"


@dataclass
class VerificationResult:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    missing_references: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProjectStatistics:
    timeline_items: int = 0
    timeline_seconds: float = 0.0
    music_items: int = 0
    title_items: int = 0
    transition_items: int = 0
    still_items: int = 0
    video_items: int = 0
    missing_media_items: int = 0
    converted_media_files: int = 0
    converted_media_bytes: int = 0


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
    verification_passed: bool = False
    verification_checks: dict[str, bool] = field(default_factory=dict)
    missing_references: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    statistics: ProjectStatistics = field(default_factory=ProjectStatistics)
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


def shlex_quote(value: str) -> str:
    if not value:
        return "''"
    if re.fullmatch(r"[A-Za-z0-9_./:@%+=,-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def command_text(command: list[str]) -> str:
    return " ".join(shlex_quote(part) for part in command)


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
    for filename in (
        f"{project_name}-timeline.json",
        f"{safe_name(project_name)}-timeline.json",
    ):
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
        recent = [item for item in candidates if item.stat().st_mtime_ns >= started_ns]
        if recent:
            candidates = recent
    return max(candidates, key=lambda item: item.stat().st_mtime_ns) if candidates else None


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 2, "projects": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "projects": {}}
    if not isinstance(data, dict):
        return {"version": 2, "projects": {}}
    data.setdefault("version", 2)
    data.setdefault("projects", {})
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def local_path_from_file_url(value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path))


def parse_fcpxml_references(fcpxml: Path) -> tuple[bool, list[Path], str | None]:
    try:
        root = ET.parse(fcpxml).getroot()
    except (OSError, ET.ParseError) as exc:
        return False, [], str(exc)

    references: list[Path] = []
    for element in root.iter():
        src = element.attrib.get("src")
        if not src:
            continue
        path = local_path_from_file_url(src)
        if path is not None:
            references.append(path)
    return True, references, None


def load_timeline_statistics(timeline_json: Path) -> ProjectStatistics:
    stats = ProjectStatistics()
    try:
        data = json.loads(timeline_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return stats

    timeline = data.get("timeline") if isinstance(data, dict) else []
    music = data.get("music") if isinstance(data, dict) else []
    summary = data.get("summary") if isinstance(data, dict) else {}
    timeline = timeline if isinstance(timeline, list) else []
    music = music if isinstance(music, list) else []
    summary = summary if isinstance(summary, dict) else {}

    stats.timeline_items = int(summary.get("timeline_items") or len(timeline))
    stats.timeline_seconds = float(summary.get("timeline_seconds") or 0.0)
    stats.music_items = int(summary.get("music_items") or len(music))

    for item in timeline:
        if not isinstance(item, dict):
            continue
        plugin = str(item.get("plugin") or "")
        if plugin.startswith("Title "):
            stats.title_items += 1
        if plugin.startswith("TX "):
            stats.transition_items += 1
        if item.get("still_image") or item.get("type_code") == 6:
            stats.still_items += 1
        else:
            stats.video_items += 1
        if item.get("media_exists") is False:
            stats.missing_media_items += 1

    for item in music:
        if isinstance(item, dict) and item.get("media_exists") is False:
            stats.missing_media_items += 1
    return stats


def add_converted_media_statistics(output_directory: Path, stats: ProjectStatistics) -> None:
    media_dir = output_directory / CONVERTED_MEDIA_DIRNAME
    if not media_dir.is_dir():
        return
    files = [path for path in media_dir.rglob("*") if path.is_file()]
    stats.converted_media_files = len(files)
    stats.converted_media_bytes = sum(path.stat().st_size for path in files)


def verify_project(
    output_directory: Path,
    timeline_json: Path | None,
    fcpxml: Path | None,
) -> VerificationResult:
    checks: dict[str, bool] = {}
    warnings: list[str] = []
    missing_references: list[str] = []

    checks["fcpxml_exists"] = bool(fcpxml and fcpxml.is_file())
    checks["timeline_json_exists"] = bool(timeline_json and timeline_json.is_file())
    checks["converted_media_folder_exists"] = (output_directory / CONVERTED_MEDIA_DIRNAME).is_dir()
    checks["manifest_exists"] = (output_directory / "conversion-manifest.json").is_file()

    title_inventory = output_directory / "title-inventory.txt"
    checks["title_inventory_exists"] = title_inventory.is_file()
    if not title_inventory.is_file():
        warnings.append("title-inventory.txt is absent")

    xml_valid = False
    references: list[Path] = []
    if fcpxml and fcpxml.is_file():
        xml_valid, references, xml_error = parse_fcpxml_references(fcpxml)
        if xml_error:
            warnings.append(f"FCPXML parse error: {xml_error}")
    checks["fcpxml_well_formed"] = xml_valid

    for reference in references:
        if not reference.exists():
            missing_references.append(str(reference))
    checks["all_fcpxml_media_references_exist"] = xml_valid and not missing_references
    checks["fcpxml_has_media_references"] = bool(references)

    required_checks = (
        "fcpxml_exists",
        "timeline_json_exists",
        "converted_media_folder_exists",
        "manifest_exists",
        "fcpxml_well_formed",
        "all_fcpxml_media_references_exist",
        "fcpxml_has_media_references",
    )
    passed = all(checks.get(name, False) for name in required_checks)
    return VerificationResult(
        passed=passed,
        checks=checks,
        missing_references=missing_references,
        warnings=warnings,
    )


def result_to_dict(result: ConversionResult) -> dict[str, Any]:
    data = asdict(result)
    return data


def already_complete(state: dict[str, Any], key: str, expected_output: Path) -> bool:
    record = state.get("projects", {}).get(key)
    if not isinstance(record, dict):
        return False
    if record.get("status") not in {"success", "verified"}:
        return False
    fcpxml_value = record.get("fcpxml")
    if fcpxml_value and Path(fcpxml_value).is_file():
        return True
    return bool(list(expected_output.glob("*.fcpxml")))


def format_elapsed(seconds: float) -> str:
    seconds_int = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds_int, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024.0 or unit == "TB":
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024.0
    return f"{value} B"


def progress_bar(done: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "[" + "-" * width + "]"
    ratio = min(1.0, max(0.0, done / total))
    filled = round(ratio * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_overall_progress(done: int, total: int, batch_start: float, durations: list[float]) -> None:
    elapsed = time.monotonic() - batch_start
    remaining = total - done
    eta_text = "calculating"
    if durations and remaining > 0:
        average = sum(durations) / len(durations)
        eta_text = format_elapsed(average * remaining)
    elif remaining == 0:
        eta_text = "0s"
    percent = (done / total * 100.0) if total else 0.0
    print(
        f"Overall {progress_bar(done, total)} {done}/{total} ({percent:5.1f}%)  "
        f"elapsed {format_elapsed(elapsed)}  ETA {eta_text}"
    )


def write_summary(output_root: Path, results: list[ConversionResult], batch_elapsed: float) -> None:
    fields = [
        "relative_project_path", "project_name", "status", "verification_passed",
        "elapsed_seconds", "timeline_items", "timeline_seconds", "music_items",
        "title_items", "transition_items", "still_items", "video_items",
        "missing_media_items", "converted_media_files", "converted_media_bytes",
        "converted_media_size", "project_file", "timeline_json", "fcpxml",
        "output_directory", "log_file", "started_at", "finished_at",
        "missing_references", "warnings", "error",
    ]
    rows: list[dict[str, Any]] = []
    for result in results:
        stats = result.statistics
        rows.append({
            "relative_project_path": result.relative_project_path,
            "project_name": result.project_name,
            "status": result.status,
            "verification_passed": result.verification_passed,
            "elapsed_seconds": result.elapsed_seconds,
            "timeline_items": stats.timeline_items,
            "timeline_seconds": round(stats.timeline_seconds, 3),
            "music_items": stats.music_items,
            "title_items": stats.title_items,
            "transition_items": stats.transition_items,
            "still_items": stats.still_items,
            "video_items": stats.video_items,
            "missing_media_items": stats.missing_media_items,
            "converted_media_files": stats.converted_media_files,
            "converted_media_bytes": stats.converted_media_bytes,
            "converted_media_size": format_bytes(stats.converted_media_bytes),
            "project_file": result.project_file,
            "timeline_json": result.timeline_json or "",
            "fcpxml": result.fcpxml or "",
            "output_directory": result.output_directory,
            "log_file": result.log_file or "",
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "missing_references": "; ".join(result.missing_references),
            "warnings": "; ".join(result.warnings),
            "error": result.error or "",
        })

    with (output_root / SUMMARY_CSV).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    totals = {
        "projects": len(results),
        "success": sum(r.status == "success" for r in results),
        "skipped": sum(r.status == "skipped" for r in results),
        "failed": sum(r.status == "failed" for r in results),
        "verification_failed": sum(r.status == "verification_failed" for r in results),
        "verified": sum(r.verification_passed for r in results),
        "timeline_items": sum(r.statistics.timeline_items for r in results),
        "timeline_seconds": sum(r.statistics.timeline_seconds for r in results),
        "music_items": sum(r.statistics.music_items for r in results),
        "title_items": sum(r.statistics.title_items for r in results),
        "transition_items": sum(r.statistics.transition_items for r in results),
        "still_items": sum(r.statistics.still_items for r in results),
        "video_items": sum(r.statistics.video_items for r in results),
        "converted_media_files": sum(r.statistics.converted_media_files for r in results),
        "converted_media_bytes": sum(r.statistics.converted_media_bytes for r in results),
        "batch_elapsed_seconds": round(batch_elapsed, 3),
    }

    (output_root / SUMMARY_JSON).write_text(
        json.dumps({"totals": totals, "projects": [result_to_dict(r) for r in results]}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = [
        "iMovie HD Batch Conversion Report",
        "================================",
        "",
        f"Projects listed: {totals['projects']}",
        f"Succeeded: {totals['success']}",
        f"Skipped (already complete): {totals['skipped']}",
        f"Conversion failures: {totals['failed']}",
        f"Verification failures: {totals['verification_failed']}",
        f"Verified outputs: {totals['verified']}",
        f"Batch elapsed: {format_elapsed(batch_elapsed)}",
        "",
        "ARCHIVE STATISTICS",
        "------------------",
        f"Timeline duration: {format_elapsed(totals['timeline_seconds'])}",
        f"Timeline items: {totals['timeline_items']}",
        f"Video/effect items: {totals['video_items']}",
        f"Still items: {totals['still_items']}",
        f"Transition items: {totals['transition_items']}",
        f"Title items: {totals['title_items']}",
        f"Music items: {totals['music_items']}",
        f"Converted media files: {totals['converted_media_files']}",
        f"Converted media size: {format_bytes(totals['converted_media_bytes'])}",
        "",
        "PROJECTS NEEDING ATTENTION",
        "--------------------------",
    ]
    attention = [r for r in results if r.status in {"failed", "verification_failed"}]
    if attention:
        for result in attention:
            report.append(f"{result.relative_project_path}: {result.error or result.status}")
            for missing in result.missing_references:
                report.append(f"  Missing reference: {missing}")
            if result.log_file:
                report.append(f"  Log: {result.log_file}")
    else:
        report.append("None.")

    report.extend(["", "VERIFICATION CHECKLIST", "----------------------"])
    for result in results:
        mark = "PASS" if result.verification_passed else ("SKIP" if result.status == "skipped" else "FAIL")
        report.append(f"{mark:4}  {result.relative_project_path}")
        if result.status != "skipped":
            for name, passed in result.verification_checks.items():
                report.append(f"      {'✓' if passed else '✗'} {name}")

    (output_root / SUMMARY_TXT).write_text("\n".join(report) + "\n", encoding="utf-8")


def select_projects(projects: list[Path], archive_root: Path, match: str | None, limit: int | None) -> list[Path]:
    selected = projects
    if match:
        expression = re.compile(match, re.IGNORECASE)
        selected = [p for p in selected if expression.search(str(p.relative_to(archive_root)))]
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
    parser = argparse.ArgumentParser(description="Polished batch converter for an iMovie HD archive.")
    parser.add_argument("archive_root", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--parser", dest="parser_script", type=Path, default=script_dir / "imoviehd_parser.py")
    parser.add_argument("--converter", dest="converter_script", type=Path, default=script_dir / "imoviehd_stage6_5.py")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--verify-only", action="store_true", help="Verify existing outputs without converting.")
    args = parser.parse_args()

    archive_root = args.archive_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    parser_script = args.parser_script.expanduser().resolve()
    converter_script = args.converter_script.expanduser().resolve()

    if not archive_root.is_dir():
        print(f"Archive root is not a folder: {archive_root}", file=sys.stderr)
        return 2
    if not args.dry_run and not args.verify_only:
        ensure_tools(parser_script, converter_script)

    all_projects = discover_projects(archive_root)
    projects = select_projects(all_projects, archive_root, args.match, args.limit)
    if not projects:
        print("No matching .iMovieProj files were found.")
        return 1

    output_root.mkdir(parents=True, exist_ok=True)
    logs_root = output_root / LOGS_DIRNAME
    logs_root.mkdir(exist_ok=True)
    state_path = output_root / STATE_FILENAME
    state = load_state(state_path)

    print("=" * 72)
    print("iMovieHD2FCP BATCH CONVERTER")
    print("=" * 72)
    print(f"Archive:      {archive_root}")
    print(f"Destination:  {output_root}")
    print(f"Discovered:   {len(all_projects)} project(s)")
    print(f"Selected:     {len(projects)} project(s)")
    print(f"Mode:         {'verify only' if args.verify_only else 'dry run' if args.dry_run else 'convert and verify'}")
    print("")

    batch_start = time.monotonic()
    durations: list[float] = []
    results: list[ConversionResult] = []

    for index, project_file in enumerate(projects, start=1):
        project_folder = project_file.parent
        relative_folder = project_folder.relative_to(archive_root)
        relative_key = relative_folder.as_posix()
        project_name = project_folder.name
        project_output = output_root / relative_folder
        parser_output = project_output / TIMELINE_DIRNAME
        log_file = logs_root / (safe_name(relative_key.replace("/", " — ")) + ".log")

        print("=" * 72)
        print(f"PROJECT {index} OF {len(projects)}: {relative_key}")
        print("=" * 72)
        print_overall_progress(index - 1, len(projects), batch_start, durations)

        started_at = utc_now()
        start_time = time.monotonic()
        timeline_json = locate_timeline_json(parser_output, project_name)
        fcpxml = locate_fcpxml(project_output)

        if args.verify_only:
            stats = load_timeline_statistics(timeline_json) if timeline_json else ProjectStatistics()
            add_converted_media_statistics(project_output, stats)
            verification = verify_project(project_output, timeline_json, fcpxml)
            status = "success" if verification.passed else "verification_failed"
            error = None if verification.passed else "Existing output failed verification"
            elapsed = time.monotonic() - start_time
            result = ConversionResult(
                relative_project_path=relative_key,
                project_name=project_name,
                project_file=str(project_file),
                output_directory=str(project_output),
                status=status,
                started_at=started_at,
                finished_at=utc_now(),
                elapsed_seconds=round(elapsed, 3),
                timeline_json=str(timeline_json) if timeline_json else None,
                fcpxml=str(fcpxml) if fcpxml else None,
                log_file=str(log_file) if log_file.exists() else None,
                verification_passed=verification.passed,
                verification_checks=verification.checks,
                missing_references=verification.missing_references,
                warnings=verification.warnings,
                statistics=stats,
                error=error,
            )
            results.append(result)
            print("PASS" if verification.passed else "FAIL")
            continue

        if not args.force and already_complete(state, relative_key, project_output):
            print("SKIP: already converted. Use --force to rebuild.")
            elapsed = time.monotonic() - start_time
            stats = load_timeline_statistics(timeline_json) if timeline_json else ProjectStatistics()
            add_converted_media_statistics(project_output, stats)
            verification = verify_project(project_output, timeline_json, fcpxml)
            result = ConversionResult(
                relative_project_path=relative_key,
                project_name=project_name,
                project_file=str(project_file),
                output_directory=str(project_output),
                status="skipped",
                started_at=started_at,
                finished_at=utc_now(),
                elapsed_seconds=round(elapsed, 3),
                timeline_json=str(timeline_json) if timeline_json else None,
                fcpxml=str(fcpxml) if fcpxml else None,
                log_file=str(log_file) if log_file.exists() else None,
                verification_passed=verification.passed,
                verification_checks=verification.checks,
                missing_references=verification.missing_references,
                warnings=verification.warnings,
                statistics=stats,
            )
            results.append(result)
            continue

        if args.dry_run:
            print(f"Would parse:   {project_file}")
            print(f"Would output:  {project_output}")
            result = ConversionResult(
                relative_project_path=relative_key,
                project_name=project_name,
                project_file=str(project_file),
                output_directory=str(project_output),
                status="skipped",
                started_at=started_at,
                finished_at=utc_now(),
                elapsed_seconds=0.0,
                error="dry run",
            )
            results.append(result)
            continue

        project_output.mkdir(parents=True, exist_ok=True)
        parser_output.mkdir(parents=True, exist_ok=True)
        started_ns = time.time_ns()
        error: str | None = None

        with log_file.open("a", encoding="utf-8") as log_handle:
            log_handle.write("\n" + "=" * 72 + "\n")
            log_handle.write(f"Project: {relative_key}\nStarted: {started_at}\n")
            log_handle.write("=" * 72 + "\n")

            print("[1/3] Parsing project")
            parser_command = [sys.executable, str(parser_script), str(project_file), "--output", str(parser_output)]
            parser_code, _ = run_logged(parser_command, log_handle)
            if parser_code != 0:
                error = f"Parser failed with exit code {parser_code}"
            else:
                timeline_json = locate_timeline_json(parser_output, project_name)
                if timeline_json is None:
                    error = "Parser completed but no timeline JSON was found"

            if error is None and timeline_json is not None:
                print("[2/3] Converting media and writing FCPXML")
                converter_command = [
                    sys.executable, str(converter_script), str(timeline_json),
                    "--output-dir", str(project_output), "--project-name", project_name,
                ]
                if args.force:
                    converter_command.append("--force")
                if args.allow_missing:
                    converter_command.append("--allow-missing")
                converter_code, _ = run_logged(converter_command, log_handle)
                if converter_code != 0:
                    error = f"Stage 6.5 failed with exit code {converter_code}"
                else:
                    fcpxml = locate_fcpxml(project_output, started_ns)
                    if fcpxml is None:
                        error = "Stage 6.5 completed but no FCPXML was found"

        print("[3/3] Verifying output")
        stats = load_timeline_statistics(timeline_json) if timeline_json else ProjectStatistics()
        add_converted_media_statistics(project_output, stats)
        verification = verify_project(project_output, timeline_json, fcpxml)

        elapsed = time.monotonic() - start_time
        durations.append(elapsed)
        finished_at = utc_now()

        if error is not None:
            status = "failed"
        elif not verification.passed:
            status = "verification_failed"
            error = "Conversion completed, but verification failed"
        else:
            status = "success"

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
            verification_passed=verification.passed,
            verification_checks=verification.checks,
            missing_references=verification.missing_references,
            warnings=verification.warnings,
            statistics=stats,
            error=error,
        )
        results.append(result)

        state.setdefault("projects", {})[relative_key] = result_to_dict(result)
        state["archive_root"] = str(archive_root)
        state["output_root"] = str(output_root)
        state["updated_at"] = finished_at
        save_state(state_path, state)
        write_summary(output_root, results, time.monotonic() - batch_start)

        if status == "success":
            print("✓ PASS")
            print(f"  FCPXML: {fcpxml}")
            print(f"  Media:  {stats.converted_media_files} file(s), {format_bytes(stats.converted_media_bytes)}")
        else:
            print(f"✗ {status.upper()}: {error}")
            print(f"  Log: {log_file}")
            for missing in verification.missing_references[:10]:
                print(f"  Missing: {missing}")
        print(f"Project elapsed: {format_elapsed(elapsed)}")
        print("")

        if status in {"failed", "verification_failed"} and args.stop_on_error:
            break

    batch_elapsed = time.monotonic() - batch_start
    write_summary(output_root, results, batch_elapsed)
    print_overall_progress(len(results), len(projects), batch_start, durations)

    successes = sum(r.status == "success" for r in results)
    skips = sum(r.status == "skipped" for r in results)
    failures = sum(r.status == "failed" for r in results)
    verification_failures = sum(r.status == "verification_failed" for r in results)
    total_bytes = sum(r.statistics.converted_media_bytes for r in results)

    print("=" * 72)
    print("BATCH COMPLETE")
    print("=" * 72)
    print(f"Succeeded:             {successes}")
    print(f"Skipped:               {skips}")
    print(f"Conversion failures:   {failures}")
    print(f"Verification failures: {verification_failures}")
    print(f"Converted media:       {format_bytes(total_bytes)}")
    print(f"Elapsed:               {format_elapsed(batch_elapsed)}")
    print(f"Report:                {output_root / SUMMARY_TXT}")
    print(f"CSV:                   {output_root / SUMMARY_CSV}")
    print(f"JSON:                  {output_root / SUMMARY_JSON}")

    return 0 if failures == 0 and verification_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
