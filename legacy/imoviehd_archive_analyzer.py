#!/usr/bin/env python3
"""Batch-analyse an archive of legacy iMovie HD projects.

The archive is expected to look like:

    Archive Root/
      CD Name/
        Project Name/
          Project Name.iMovieProj
          Media/

This tool recursively discovers .iMovieProj files, runs the existing iMovie HD
parser for each project, and combines the resulting timeline JSON files into:

    analysis-output/
      projects/.../<project>-timeline.json
      projects/.../<project>-analysis.txt
      archive-summary.csv
      archive-summary.json
      plugin-inventory.csv
      plugin-inventory.json
      archive-report.txt

No media is converted or modified.

Example:
    python3 imoviehd_archive_analyzer.py \
      "/Volumes/10TB Seagate/iMovie HD Archive" \
      --parser "./YOUR-PARSER-SCRIPT.py" \
      --output "analysis-output"
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ProjectResult:
    cd_name: str
    project_name: str
    relative_project_path: str
    project_file: str
    media_folder_exists: bool
    parse_status: str
    duration_seconds: float | None
    timeline_items: int
    music_items: int
    missing_media_count: int
    warning_count: int
    title_plugins: list[str]
    transition_plugins: list[str]
    other_plugins: list[str]
    timeline_json: str | None
    analysis_report: str | None
    error: str | None = None


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return value or "Untitled"


def discover_projects(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.iMovieProj")
        if "__MACOSX" not in p.parts and not p.name.startswith("._")
    )


def classify_plugin(plugin: str) -> str:
    if plugin.startswith("Title "):
        return "title"
    if plugin.startswith("TX ") or plugin.lower().startswith(("fade ", "cross dissolve")):
        return "transition"
    return "other"


def find_generated_json(output_dir: Path, before: set[Path]) -> Path | None:
    candidates = [
        p for p in output_dir.rglob("*.json")
        if p not in before and p.name != "archive-summary.json"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime_ns)


def run_parser(parser: Path, project: Path, output_dir: Path) -> tuple[Path | None, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    before = set(output_dir.rglob("*.json"))

    command = [
        sys.executable,
        str(parser),
        str(project),
        "--output",
        str(output_dir),
    ]
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return None, f"Could not start parser: {exc}"

    if completed.returncode != 0:
        details = completed.stdout.strip()
        return None, f"Parser exited with code {completed.returncode}: {details}"

    generated = find_generated_json(output_dir, before)
    if generated is None:
        # Some parsers overwrite an existing JSON rather than creating a new one.
        existing = sorted(output_dir.glob("*-timeline.json"))
        if len(existing) == 1:
            generated = existing[0]
        else:
            project_stem = project.stem
            matching = sorted(output_dir.glob(f"{project_stem}*-timeline.json"))
            if matching:
                generated = matching[-1]

    if generated is None:
        return None, "Parser completed but no timeline JSON was found."

    return generated, None


def title_text(item: dict[str, Any]) -> str:
    block = item.get("title_block") or []
    if isinstance(block, list):
        text = "\n".join(str(x) for x in block if str(x).strip())
        if text:
            return text
    pairs = item.get("title_pairs") or []
    lines: list[str] = []
    if isinstance(pairs, list):
        for pair in pairs:
            if isinstance(pair, dict):
                for key in ("title", "subtitle"):
                    value = str(pair.get(key) or "").strip()
                    if value:
                        lines.append(value)
    return "\n".join(lines)


def analyse_timeline(data: dict[str, Any]) -> dict[str, Any]:
    timeline = data.get("timeline") or []
    music = data.get("music") or []
    warnings = data.get("warnings") or []
    summary = data.get("summary") or {}

    plugin_counts: Counter[str] = Counter()
    title_entries: list[dict[str, Any]] = []
    missing_paths: list[str] = []

    for item in timeline:
        if not isinstance(item, dict):
            continue
        plugin = str(item.get("plugin") or "").strip()
        if plugin:
            plugin_counts[plugin] += 1
        if plugin.startswith("Title "):
            title_entries.append({
                "plugin": plugin,
                "text": title_text(item),
                "start_frame": int(item.get("timeline_start_frame") or 0),
                "duration_frames": int(item.get("frames") or 0),
                "rendered_media": item.get("resolved_media"),
                "title_info": item.get("title_info"),
            })
        if item.get("media_exists") is False:
            missing_paths.append(str(item.get("resolved_media") or item.get("file_ref") or item.get("name")))

    for item in music:
        if isinstance(item, dict) and item.get("media_exists") is False:
            missing_paths.append(str(item.get("resolved_media") or item.get("file_ref") or item.get("name")))

    title_plugins = sorted(p for p in plugin_counts if classify_plugin(p) == "title")
    transition_plugins = sorted(p for p in plugin_counts if classify_plugin(p) == "transition")
    other_plugins = sorted(p for p in plugin_counts if classify_plugin(p) == "other")

    duration = summary.get("timeline_seconds")
    if duration is None:
        fps = float(summary.get("fps") or 25.0)
        duration = float(summary.get("timeline_frames") or 0) / fps if fps else None

    return {
        "duration_seconds": float(duration) if duration is not None else None,
        "timeline_items": int(summary.get("timeline_items") or len(timeline)),
        "music_items": int(summary.get("music_items") or len(music)),
        "warning_count": len(warnings),
        "warnings": warnings,
        "missing_paths": sorted(set(missing_paths)),
        "plugin_counts": dict(sorted(plugin_counts.items())),
        "title_plugins": title_plugins,
        "transition_plugins": transition_plugins,
        "other_plugins": other_plugins,
        "titles": title_entries,
    }


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    whole = int(round(seconds))
    minutes, secs = divmod(whole, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def write_project_report(
    destination: Path,
    project: ProjectResult,
    analysis: dict[str, Any],
) -> None:
    lines = [
        f"iMovie HD Project Analysis — {project.project_name}",
        "=" * (29 + len(project.project_name)),
        "",
        f"CD/folder: {project.cd_name}",
        f"Project path: {project.relative_project_path}",
        f"Project file: {project.project_file}",
        f"Media folder present: {'Yes' if project.media_folder_exists else 'No'}",
        f"Duration: {format_duration(project.duration_seconds)}",
        f"Timeline items: {project.timeline_items}",
        f"Music items: {project.music_items}",
        f"Warnings: {project.warning_count}",
        f"Missing media: {project.missing_media_count}",
        "",
        "PLUGIN INVENTORY",
        "----------------",
    ]

    counts = analysis["plugin_counts"]
    if counts:
        for plugin, count in counts.items():
            lines.append(f"{plugin}: {count}")
    else:
        lines.append("No plugins detected.")

    lines += ["", "TITLES", "------"]
    if analysis["titles"]:
        for index, title in enumerate(analysis["titles"], start=1):
            lines.extend([
                f"Title {index}",
                f"  Plugin: {title['plugin']}",
                f"  Text: {title['text'] or '(no text extracted)'}",
                f"  Start frame: {title['start_frame']}",
                f"  Duration frames: {title['duration_frames']}",
                f"  Rendered media: {title['rendered_media'] or ''}",
            ])
    else:
        lines.append("No titles detected.")

    lines += ["", "WARNINGS", "--------"]
    if analysis["warnings"]:
        lines.extend(str(w) for w in analysis["warnings"])
    else:
        lines.append("None.")

    lines += ["", "MISSING MEDIA", "-------------"]
    if analysis["missing_paths"]:
        lines.extend(analysis["missing_paths"])
    else:
        lines.append("None.")

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse an archive of iMovie HD projects.")
    parser.add_argument("archive_root", type=Path, help="Root folder containing copied CD folders.")
    parser.add_argument("--parser", required=True, type=Path, dest="parser_script",
                        help="Path to the existing working iMovie HD parser script.")
    parser.add_argument("--output", type=Path, default=Path("imoviehd-analysis"),
                        help="Analysis output folder (default: imoviehd-analysis).")
    parser.add_argument("--reuse-json", action="store_true",
                        help="Reuse existing generated timeline JSON when present.")
    args = parser.parse_args()

    archive_root = args.archive_root.expanduser().resolve()
    parser_script = args.parser_script.expanduser().resolve()
    output_root = args.output.expanduser().resolve()

    if not archive_root.is_dir():
        print(f"Archive root is not a folder: {archive_root}", file=sys.stderr)
        return 2
    if not parser_script.is_file():
        print(f"Parser script not found: {parser_script}", file=sys.stderr)
        return 2

    projects = discover_projects(archive_root)
    if not projects:
        print(f"No .iMovieProj files found beneath: {archive_root}")
        return 1

    output_root.mkdir(parents=True, exist_ok=True)
    project_output_root = output_root / "projects"

    results: list[ProjectResult] = []
    detailed: list[dict[str, Any]] = []
    global_plugins: Counter[str] = Counter()
    plugin_projects: dict[str, set[str]] = defaultdict(set)

    print(f"Found {len(projects)} iMovie HD project(s).")
    for index, project_file in enumerate(projects, start=1):
        project_folder = project_file.parent
        relative_folder = project_folder.relative_to(archive_root)
        parts = relative_folder.parts
        cd_name = parts[0] if len(parts) >= 2 else "(archive root)"
        project_name = project_folder.name
        relative_label = str(relative_folder)
        destination = project_output_root / relative_folder
        destination.mkdir(parents=True, exist_ok=True)

        print(f"[{index}/{len(projects)}] {relative_label}")

        timeline_json: Path | None = None
        parse_error: str | None = None
        existing = sorted(destination.glob("*-timeline.json"))
        if args.reuse_json and existing:
            timeline_json = existing[-1]
        else:
            timeline_json, parse_error = run_parser(parser_script, project_file, destination)

        if timeline_json is None:
            result = ProjectResult(
                cd_name=cd_name,
                project_name=project_name,
                relative_project_path=relative_label,
                project_file=str(project_file),
                media_folder_exists=(project_folder / "Media").is_dir(),
                parse_status="failed",
                duration_seconds=None,
                timeline_items=0,
                music_items=0,
                missing_media_count=0,
                warning_count=0,
                title_plugins=[],
                transition_plugins=[],
                other_plugins=[],
                timeline_json=None,
                analysis_report=None,
                error=parse_error,
            )
            results.append(result)
            print(f"    FAILED: {parse_error}")
            continue

        try:
            data = json.loads(timeline_json.read_text(encoding="utf-8"))
            analysis = analyse_timeline(data)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parse_error = f"Could not analyse timeline JSON: {exc}"
            result = ProjectResult(
                cd_name=cd_name,
                project_name=project_name,
                relative_project_path=relative_label,
                project_file=str(project_file),
                media_folder_exists=(project_folder / "Media").is_dir(),
                parse_status="failed",
                duration_seconds=None,
                timeline_items=0,
                music_items=0,
                missing_media_count=0,
                warning_count=0,
                title_plugins=[],
                transition_plugins=[],
                other_plugins=[],
                timeline_json=str(timeline_json),
                analysis_report=None,
                error=parse_error,
            )
            results.append(result)
            print(f"    FAILED: {parse_error}")
            continue

        report_path = destination / f"{safe_name(project_name)}-analysis.txt"
        result = ProjectResult(
            cd_name=cd_name,
            project_name=project_name,
            relative_project_path=relative_label,
            project_file=str(project_file),
            media_folder_exists=(project_folder / "Media").is_dir(),
            parse_status="ok",
            duration_seconds=analysis["duration_seconds"],
            timeline_items=analysis["timeline_items"],
            music_items=analysis["music_items"],
            missing_media_count=len(analysis["missing_paths"]),
            warning_count=analysis["warning_count"],
            title_plugins=analysis["title_plugins"],
            transition_plugins=analysis["transition_plugins"],
            other_plugins=analysis["other_plugins"],
            timeline_json=str(timeline_json),
            analysis_report=str(report_path),
            error=None,
        )
        write_project_report(report_path, result, analysis)
        results.append(result)
        detailed.append({
            "project": asdict(result),
            "analysis": analysis,
        })

        for plugin, count in analysis["plugin_counts"].items():
            global_plugins[plugin] += int(count)
            plugin_projects[plugin].add(relative_label)

    summary_rows: list[dict[str, Any]] = []
    for result in results:
        summary_rows.append({
            "cd_name": result.cd_name,
            "project_name": result.project_name,
            "relative_project_path": result.relative_project_path,
            "status": result.parse_status,
            "duration": format_duration(result.duration_seconds),
            "duration_seconds": "" if result.duration_seconds is None else f"{result.duration_seconds:.2f}",
            "timeline_items": result.timeline_items,
            "music_items": result.music_items,
            "titles": "; ".join(result.title_plugins),
            "transitions": "; ".join(result.transition_plugins),
            "other_plugins": "; ".join(result.other_plugins),
            "missing_media": result.missing_media_count,
            "warnings": result.warning_count,
            "media_folder_present": "Yes" if result.media_folder_exists else "No",
            "error": result.error or "",
        })

    summary_fields = [
        "cd_name", "project_name", "relative_project_path", "status",
        "duration", "duration_seconds", "timeline_items", "music_items",
        "titles", "transitions", "other_plugins", "missing_media",
        "warnings", "media_folder_present", "error",
    ]
    write_csv(output_root / "archive-summary.csv", summary_rows, summary_fields)

    plugin_rows: list[dict[str, Any]] = []
    for plugin, count in sorted(global_plugins.items(), key=lambda pair: (-pair[1], pair[0].lower())):
        category = classify_plugin(plugin)
        projects_using = sorted(plugin_projects[plugin])
        plugin_rows.append({
            "category": category,
            "plugin": plugin,
            "occurrences": count,
            "project_count": len(projects_using),
            "projects": "; ".join(projects_using),
        })
    write_csv(
        output_root / "plugin-inventory.csv",
        plugin_rows,
        ["category", "plugin", "occurrences", "project_count", "projects"],
    )

    json_summary = {
        "archive_root": str(archive_root),
        "parser_script": str(parser_script),
        "projects_found": len(projects),
        "projects_ok": sum(r.parse_status == "ok" for r in results),
        "projects_failed": sum(r.parse_status != "ok" for r in results),
        "projects": detailed,
    }
    (output_root / "archive-summary.json").write_text(
        json.dumps(json_summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_root / "plugin-inventory.json").write_text(
        json.dumps(plugin_rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "iMovie HD Archive Analysis",
        "==========================",
        "",
        f"Archive root: {archive_root}",
        f"Projects found: {len(projects)}",
        f"Successfully analysed: {sum(r.parse_status == 'ok' for r in results)}",
        f"Failed: {sum(r.parse_status != 'ok' for r in results)}",
        f"Projects with missing media: {sum(r.missing_media_count > 0 for r in results)}",
        "",
        "PLUGIN INVENTORY",
        "----------------",
    ]
    if plugin_rows:
        current_category = None
        for row in sorted(plugin_rows, key=lambda r: (r["category"], -int(r["occurrences"]), r["plugin"])):
            if row["category"] != current_category:
                current_category = row["category"]
                report_lines.extend(["", current_category.upper()])
            report_lines.append(
                f"{row['plugin']}: {row['occurrences']} occurrence(s) "
                f"in {row['project_count']} project(s)"
            )
    else:
        report_lines.append("No plugins detected.")

    failed = [r for r in results if r.parse_status != "ok"]
    report_lines.extend(["", "FAILED PROJECTS", "---------------"])
    if failed:
        for result in failed:
            report_lines.append(f"{result.relative_project_path}: {result.error}")
    else:
        report_lines.append("None.")

    missing = [r for r in results if r.missing_media_count > 0 or not r.media_folder_exists]
    report_lines.extend(["", "PROJECTS NEEDING ATTENTION", "--------------------------"])
    if missing:
        for result in missing:
            report_lines.append(
                f"{result.relative_project_path}: "
                f"missing media references={result.missing_media_count}, "
                f"Media folder={'present' if result.media_folder_exists else 'missing'}"
            )
    else:
        report_lines.append("None.")

    (output_root / "archive-report.txt").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    print("")
    print(f"Analysis complete: {output_root}")
    print(f"  Archive summary: {output_root / 'archive-summary.csv'}")
    print(f"  Plugin inventory: {output_root / 'plugin-inventory.csv'}")
    print(f"  Human-readable report: {output_root / 'archive-report.txt'}")
    return 0 if all(r.parse_status == "ok" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
