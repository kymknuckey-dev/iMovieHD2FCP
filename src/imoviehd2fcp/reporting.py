from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SUMMARY_JSON = "batch-conversion-summary.json"


def load_summary(output_root: Path) -> list[dict[str, Any]]:
    path = output_root / SUMMARY_JSON
    if not path.is_file():
        raise ValueError(f"Batch summary not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read batch summary: {exc}") from exc

    if isinstance(data, dict):
        projects = data.get("projects")
        if isinstance(projects, list):
            return [item for item in projects if isinstance(item, dict)]
        # Support earlier output where results may be under another common key.
        results = data.get("results")
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    raise ValueError(f"Unsupported summary structure in {path}")


def project_status(project: dict[str, Any]) -> str:
    status = str(project.get("status") or "").lower()
    verified = bool(project.get("verification_passed"))

    if status in {"failed", "error", "conversion_failed"}:
        return "FAIL"
    if not verified:
        return "WARN"
    warnings = project.get("warnings")
    missing = project.get("missing_references")
    if warnings or missing:
        return "WARN"
    return "PASS"


def aggregate(projects: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(project_status(project) for project in projects)
    totals = Counter()

    for project in projects:
        stats = project.get("statistics") or {}
        if not isinstance(stats, dict):
            stats = {}
        for key in (
            "timeline_items",
            "music_items",
            "title_items",
            "transition_items",
            "still_items",
            "video_items",
            "missing_media_items",
            "converted_media_files",
            "converted_media_bytes",
        ):
            try:
                totals[key] += int(stats.get(key) or 0)
            except (TypeError, ValueError):
                pass

    overall = "PASS"
    if status_counts["FAIL"]:
        overall = "FAIL"
    elif status_counts["WARN"]:
        overall = "WARN"

    return {
        "overall": overall,
        "projects": len(projects),
        "pass": status_counts["PASS"],
        "warn": status_counts["WARN"],
        "fail": status_counts["FAIL"],
        **dict(totals),
    }


def format_bytes(value: int) -> str:
    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if abs(size) < 1024.0 or unit == units[-1]:
            return f"{size:,.1f} {unit}"
        size /= 1024.0
    return f"{value:,} B"


def write_text_report(
    output_root: Path,
    projects: list[dict[str, Any]],
    destination: Path,
) -> None:
    summary = aggregate(projects)
    lines = [
        "iMovieHD2FCP Archive Verification Report",
        "========================================",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Conversion root: {output_root}",
        f"Overall status: {summary['overall']}",
        "",
        "SUMMARY",
        "-------",
        f"Projects: {summary['projects']}",
        f"PASS: {summary['pass']}",
        f"WARN: {summary['warn']}",
        f"FAIL: {summary['fail']}",
        f"Timeline items: {summary.get('timeline_items', 0):,}",
        f"Video items: {summary.get('video_items', 0):,}",
        f"Still items: {summary.get('still_items', 0):,}",
        f"Music items: {summary.get('music_items', 0):,}",
        f"Transitions: {summary.get('transition_items', 0):,}",
        f"Titles: {summary.get('title_items', 0):,}",
        f"Converted media files: {summary.get('converted_media_files', 0):,}",
        f"Converted media size: {format_bytes(summary.get('converted_media_bytes', 0))}",
        "",
        "PROJECTS",
        "--------",
    ]

    for project in projects:
        name = str(project.get("project_name") or project.get("relative_project_path") or "Untitled")
        status = project_status(project)
        lines.append(f"[{status}] {name}")
        if project.get("error"):
            lines.append(f"  Error: {project['error']}")
        for warning in project.get("warnings") or []:
            lines.append(f"  Warning: {warning}")
        for missing in project.get("missing_references") or []:
            lines.append(f"  Missing: {missing}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html_report(
    output_root: Path,
    projects: list[dict[str, Any]],
    destination: Path,
) -> None:
    summary = aggregate(projects)

    rows: list[str] = []
    for project in projects:
        name = html.escape(str(project.get("project_name") or project.get("relative_project_path") or "Untitled"))
        status = project_status(project)
        stats = project.get("statistics") or {}
        warnings = list(project.get("warnings") or [])
        missing = list(project.get("missing_references") or [])
        error = project.get("error")
        notes = []
        if error:
            notes.append(f"Error: {error}")
        notes.extend(f"Warning: {item}" for item in warnings)
        notes.extend(f"Missing: {item}" for item in missing)
        note_text = "<br>".join(html.escape(str(item)) for item in notes) or "—"

        rows.append(
            "<tr>"
            f"<td><span class='status {status.lower()}'>{status}</span></td>"
            f"<td>{name}</td>"
            f"<td>{int(stats.get('converted_media_files') or 0):,}</td>"
            f"<td>{int(stats.get('timeline_items') or 0):,}</td>"
            f"<td>{int(stats.get('transition_items') or 0):,}</td>"
            f"<td>{int(stats.get('title_items') or 0):,}</td>"
            f"<td>{note_text}</td>"
            "</tr>"
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>iMovieHD2FCP Archive Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; line-height: 1.4; }}
h1 {{ margin-bottom: .25rem; }}
.muted {{ color: #666; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 1rem; }}
.value {{ font-size: 1.55rem; font-weight: 700; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
th, td {{ border-bottom: 1px solid #ddd; text-align: left; padding: .65rem; vertical-align: top; }}
th {{ position: sticky; top: 0; background: white; }}
.status {{ display: inline-block; border-radius: 999px; padding: .2rem .55rem; font-weight: 700; font-size: .8rem; }}
.pass {{ background: #dff5e3; }}
.warn {{ background: #fff2c7; }}
.fail {{ background: #ffd9d9; }}
</style>
</head>
<body>
<h1>iMovieHD2FCP Archive Report</h1>
<div class="muted">Generated {html.escape(datetime.now().isoformat(timespec='seconds'))}<br>
Conversion root: {html.escape(str(output_root))}</div>

<div class="cards">
  <div class="card"><div>Overall</div><div class="value">{summary['overall']}</div></div>
  <div class="card"><div>Projects</div><div class="value">{summary['projects']:,}</div></div>
  <div class="card"><div>PASS</div><div class="value">{summary['pass']:,}</div></div>
  <div class="card"><div>WARN</div><div class="value">{summary['warn']:,}</div></div>
  <div class="card"><div>FAIL</div><div class="value">{summary['fail']:,}</div></div>
  <div class="card"><div>Media files</div><div class="value">{summary.get('converted_media_files', 0):,}</div></div>
  <div class="card"><div>Media size</div><div class="value">{format_bytes(summary.get('converted_media_bytes', 0))}</div></div>
  <div class="card"><div>Timeline items</div><div class="value">{summary.get('timeline_items', 0):,}</div></div>
</div>

<table>
<thead>
<tr><th>Status</th><th>Project</th><th>Media</th><th>Timeline</th><th>Transitions</th><th>Titles</th><th>Notes</th></tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body>
</html>
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")


def build_reports(output_root: Path, report_directory: Path | None = None) -> tuple[Path, Path]:
    projects = load_summary(output_root)
    report_directory = (report_directory or output_root / "Reports").resolve()
    text_path = report_directory / "Archive Verification Report.txt"
    html_path = report_directory / "Archive Verification Report.html"
    write_text_report(output_root, projects, text_path)
    write_html_report(output_root, projects, html_path)
    return text_path, html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build archive verification reports.")
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--report-directory", type=Path)
    args = parser.parse_args(argv)

    try:
        text_path, html_path = build_reports(
            args.output_root.expanduser().resolve(),
            args.report_directory.expanduser().resolve() if args.report_directory else None,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Text report: {text_path}")
    print(f"HTML report: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
