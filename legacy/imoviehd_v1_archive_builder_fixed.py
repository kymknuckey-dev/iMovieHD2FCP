#!/usr/bin/env python3
"""Build combined, multi-Event FCPXML imports with global ID remapping from completed v1 conversions.

This tool does not modify media or reconvert projects. It combines the individual
FCPXML files produced by ``imoviehd_v1_batch.py`` into one import file containing
multiple Final Cut Events and Projects.

Typical workflow:

1. Create a planning CSV:

   python3 imoviehd_v1_archive_builder.py plan \
       "/Volumes/10TB Seagate/Europe 2005 Final Projects Converted v1" \
       --plan "Europe 2005 Event Plan.csv"

2. Open the CSV in Numbers or Excel and edit the ``event_name`` column.

3. Build one combined FCPXML:

   python3 imoviehd_v1_archive_builder.py build \
       "/Volumes/10TB Seagate/Europe 2005 Final Projects Converted v1" \
       --plan "Europe 2005 Event Plan.csv" \
       --output "Europe 2005 Import.fcpxml"

Import the resulting FCPXML into an empty Final Cut library. Final Cut creates the
Events and Projects; it remains responsible for its own library database.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


FCPXML_VERSION = "1.14"
PLAN_FIELDS = [
    "include",
    "event_name",
    "project_name",
    "relative_project_path",
    "fcpxml_path",
]


@dataclass
class PlanRow:
    include: bool
    event_name: str
    project_name: str
    relative_project_path: str
    fcpxml_path: str


@dataclass
class BuildProject:
    project_name: str
    event_name: str
    relative_project_path: str
    source_fcpxml: str
    browser_clips: int
    projects: int
    resources: int


def indent_xml(element: ET.Element, level: int = 0) -> None:
    space = "\n" + "    " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = space + "    "
        for child in element:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = space
    if level and (not element.tail or not element.tail.strip()):
        element.tail = space


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return cleaned or "Final Cut Import"


def discover_fcpxml(root: Path) -> list[Path]:
    candidates = sorted(
        path
        for path in root.rglob("*.fcpxml")
        if not path.name.startswith("._")
        and "_Parser Output" not in path.parts
        and "Final Cut Imports" not in path.parts
    )

    # Prefer v1 XML when a folder also contains older Stage files.
    by_parent: dict[Path, list[Path]] = defaultdict(list)
    for path in candidates:
        by_parent[path.parent].append(path)

    selected: list[Path] = []
    for _, files in sorted(by_parent.items(), key=lambda item: str(item[0]).lower()):
        v1 = [path for path in files if "-v1" in path.stem.lower()]
        if v1:
            selected.append(max(v1, key=lambda path: path.stat().st_mtime_ns))
        else:
            selected.append(max(files, key=lambda path: path.stat().st_mtime_ns))
    return selected


def read_xml(path: Path) -> ET.Element:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if root.tag != "fcpxml":
        raise ValueError(f"Not an FCPXML document: {path}")
    return root


def source_event(root: ET.Element, path: Path) -> ET.Element:
    library = root.find("library")
    if library is None:
        raise ValueError(f"No <library> element in {path}")
    events = library.findall("event")
    if len(events) != 1:
        raise ValueError(
            f"Expected one Event in {path}, found {len(events)}. "
            "Use individual converter output files as inputs."
        )
    return events[0]


def source_project_name(root: ET.Element, fallback: str) -> str:
    library = root.find("library")
    if library is not None:
        for event in library.findall("event"):
            project = event.find("project")
            if project is not None and project.get("name"):
                return str(project.get("name"))
    return fallback


def logical_project_folder(relative_folder: Path) -> Path:
    """Hide the Delta 3 projects/ container from user-facing grouping."""
    parts = relative_folder.parts
    if parts and parts[0].lower() == "projects":
        remaining = parts[1:]
        return Path(*remaining) if remaining else Path(".")
    return relative_folder


def suggested_event(relative_folder: Path, mode: str, level: int) -> str:
    relative_folder = logical_project_folder(relative_folder)
    parts = relative_folder.parts

    if mode == "project":
        return relative_folder.name

    if mode == "parent":
        return relative_folder.parent.name if relative_folder.parent.name else relative_folder.name

    if mode == "top":
        return parts[0] if parts else relative_folder.name

    if mode == "level":
        if not parts:
            return relative_folder.name
        index = max(0, min(level - 1, len(parts) - 1))
        return parts[index]

    raise ValueError(f"Unknown event mode: {mode}")


def bool_from_csv(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "n", "exclude", "skip"}


def make_plan(
    converted_root: Path,
    *,
    event_mode: str,
    event_level: int,
) -> list[PlanRow]:
    rows: list[PlanRow] = []
    for fcpxml in discover_fcpxml(converted_root):
        physical_folder = fcpxml.parent.relative_to(converted_root)
        relative_folder = logical_project_folder(physical_folder)
        root = read_xml(fcpxml)
        project_name = source_project_name(root, fcpxml.stem)
        rows.append(
            PlanRow(
                include=True,
                event_name=suggested_event(relative_folder, event_mode, event_level),
                project_name=project_name,
                relative_project_path=relative_folder.as_posix(),
                fcpxml_path=str(fcpxml.resolve()),
            )
        )
    return rows


def write_plan(path: Path, rows: list[PlanRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "include": "Yes" if row.include else "No",
                    "event_name": row.event_name,
                    "project_name": row.project_name,
                    "relative_project_path": row.relative_project_path,
                    "fcpxml_path": row.fcpxml_path,
                }
            )


def load_plan(path: Path) -> list[PlanRow]:
    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Could not open plan CSV: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        missing = [field for field in PLAN_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Plan CSV is missing column(s): " + ", ".join(missing))

        rows: list[PlanRow] = []
        for line_number, raw in enumerate(reader, start=2):
            if not bool_from_csv(raw.get("include", "Yes")):
                continue

            event_name = (raw.get("event_name") or "").strip()
            project_name = (raw.get("project_name") or "").strip()
            relative_path = (raw.get("relative_project_path") or "").strip()
            fcpxml_path = (raw.get("fcpxml_path") or "").strip()

            if not event_name:
                raise ValueError(f"Blank event_name at CSV line {line_number}")
            if not project_name:
                raise ValueError(f"Blank project_name at CSV line {line_number}")
            if not fcpxml_path:
                raise ValueError(f"Blank fcpxml_path at CSV line {line_number}")

            rows.append(
                PlanRow(
                    include=True,
                    event_name=event_name,
                    project_name=project_name,
                    relative_project_path=relative_path,
                    fcpxml_path=fcpxml_path,
                )
            )
    return rows


def remap_resource_references(element: ET.Element, mapping: dict[str, str]) -> None:
    for node in element.iter():
        for key, value in list(node.attrib.items()):
            if value in mapping:
                node.set(key, mapping[value])


def collect_document_ids(source_root: ET.Element) -> list[str]:
    """Return every XML ID declared anywhere in one source document.

    FCPXML uses IDs not only for top-level resources (r1, r2, ...), but also
    for nested objects such as text-style definitions. When several complete
    FCPXML documents are merged, *all* of those IDs must remain unique across
    the resulting document.
    """
    ids: list[str] = []
    seen: set[str] = set()
    for node in source_root.iter():
        value = node.get("id")
        if value and value not in seen:
            seen.add(value)
            ids.append(value)
    return ids


def allocate_document_id_map(
    source_root: ET.Element,
    *,
    document_number: int,
    next_resource_number: int,
    used_ids: set[str],
) -> tuple[dict[str, str], int]:
    """Allocate globally unique replacements for every ID in a source XML."""
    source_resources = source_root.find("resources")
    resource_ids = {
        node.get("id")
        for node in list(source_resources) if source_resources is not None
        if node.get("id")
    }

    mapping: dict[str, str] = {}
    for old_id in collect_document_ids(source_root):
        if old_id in resource_ids:
            while f"r{next_resource_number}" in used_ids:
                next_resource_number += 1
            new_id = f"r{next_resource_number}"
            next_resource_number += 1
        else:
            # Keep a readable form for local IDs such as ts1 while adding a
            # document suffix. Fall back to a numeric disambiguator if needed.
            base = re.sub(r"[^A-Za-z0-9_.-]+", "_", old_id) or "id"
            new_id = f"{base}_p{document_number}"
            disambiguator = 2
            while new_id in used_ids:
                new_id = f"{base}_p{document_number}_{disambiguator}"
                disambiguator += 1

        mapping[old_id] = new_id
        used_ids.add(new_id)

    return mapping, next_resource_number


def copy_resources(
    source_root: ET.Element,
    destination_resources: ET.Element,
    id_mapping: dict[str, str],
) -> int:
    source_resources = source_root.find("resources")
    if source_resources is None:
        raise ValueError("Source FCPXML has no <resources> element")

    copied = 0
    for resource in list(source_resources):
        clone = copy.deepcopy(resource)
        remap_resource_references(clone, id_mapping)
        destination_resources.append(clone)
        copied += 1

    return copied


def unique_project_names(rows: list[PlanRow]) -> dict[str, str]:
    counts = Counter(row.project_name for row in rows)
    result: dict[str, str] = {}
    for row in rows:
        key = str(Path(row.fcpxml_path).resolve())
        if counts[row.project_name] == 1:
            result[key] = row.project_name
        else:
            result[key] = f"{row.project_name} — {row.event_name}"
    return result


def add_source_to_event(
    source_root: ET.Element,
    source_path: Path,
    destination_event: ET.Element,
    resource_mapping: dict[str, str],
    desired_project_name: str,
) -> tuple[int, int]:
    source = source_event(source_root, source_path)
    browser_count = 0
    project_count = 0

    for child in list(source):
        # Smart collections are added once at Library level.
        if child.tag == "smart-collection":
            continue

        clone = copy.deepcopy(child)
        remap_resource_references(clone, resource_mapping)

        if clone.tag == "asset-clip":
            browser_count += 1
        elif clone.tag == "project":
            project_count += 1
            clone.set("name", desired_project_name)

        destination_event.append(clone)

    return browser_count, project_count


def validate_unique_ids(root: ET.Element) -> None:
    """Raise a clear error if any XML ID is declared more than once."""
    owners: dict[str, str] = {}
    duplicates: list[str] = []
    for node in root.iter():
        value = node.get("id")
        if not value:
            continue
        description = f"<{node.tag}>"
        if value in owners:
            duplicates.append(f"{value}: {owners[value]} and {description}")
        else:
            owners[value] = description

    if duplicates:
        preview = "; ".join(duplicates[:10])
        if len(duplicates) > 10:
            preview += f"; plus {len(duplicates) - 10} more"
        raise ValueError(f"Combined FCPXML contains duplicate IDs: {preview}")


def add_smart_collections(library: ET.Element) -> None:
    projects = ET.SubElement(library, "smart-collection", {"name": "Projects", "match": "all"})
    ET.SubElement(projects, "match-clip", {"rule": "is", "type": "project"})

    video = ET.SubElement(library, "smart-collection", {"name": "All Video", "match": "any"})
    ET.SubElement(video, "match-media", {"rule": "is", "type": "videoOnly"})
    ET.SubElement(video, "match-media", {"rule": "is", "type": "videoWithAudio"})

    audio = ET.SubElement(library, "smart-collection", {"name": "Audio Only", "match": "all"})
    ET.SubElement(audio, "match-media", {"rule": "is", "type": "audioOnly"})


def build_combined(
    rows: list[PlanRow],
    output_path: Path,
    report_path: Path,
) -> list[BuildProject]:
    if not rows:
        raise ValueError("The plan contains no included projects")

    root = ET.Element("fcpxml", {"version": FCPXML_VERSION})
    resources = ET.SubElement(root, "resources")
    library = ET.SubElement(root, "library")

    events: dict[str, ET.Element] = {}
    event_order: list[str] = []
    for row in rows:
        if row.event_name not in events:
            events[row.event_name] = ET.Element("event", {"name": row.event_name})
            event_order.append(row.event_name)

    desired_names = unique_project_names(rows)
    next_resource_number = 1
    used_ids: set[str] = set()
    build_records: list[BuildProject] = []

    for document_number, row in enumerate(rows, start=1):
        source_path = Path(row.fcpxml_path).expanduser().resolve()
        if not source_path.is_file():
            raise ValueError(f"FCPXML file does not exist: {source_path}")

        source_root = read_xml(source_path)
        mapping, next_resource_number = allocate_document_id_map(
            source_root,
            document_number=document_number,
            next_resource_number=next_resource_number,
            used_ids=used_ids,
        )
        resource_count = copy_resources(
            source_root,
            resources,
            mapping,
        )
        browser_count, project_count = add_source_to_event(
            source_root,
            source_path,
            events[row.event_name],
            mapping,
            desired_names[str(source_path)],
        )
        if project_count == 0:
            raise ValueError(f"No Project found in {source_path}")

        build_records.append(
            BuildProject(
                project_name=desired_names[str(source_path)],
                event_name=row.event_name,
                relative_project_path=row.relative_project_path,
                source_fcpxml=str(source_path),
                browser_clips=browser_count,
                projects=project_count,
                resources=resource_count,
            )
        )

    for event_name in event_order:
        library.append(events[event_name])
    add_smart_collections(library)

    validate_unique_ids(root)
    indent_xml(root)
    xml_body = ET.tostring(root, encoding="unicode")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE fcpxml>\n"
        + xml_body
        + "\n",
        encoding="utf-8",
    )

    # Parse our own output before reporting success.
    ET.parse(output_path)

    events_summary: dict[str, list[BuildProject]] = defaultdict(list)
    for record in build_records:
        events_summary[record.event_name].append(record)

    lines = [
        "iMovieHD2FCP v1 Archive Import Build (alpha 2.1)",
        "====================================",
        "",
        f"Combined FCPXML: {output_path}",
        f"Events: {len(events_summary)}",
        f"Projects: {sum(record.projects for record in build_records)}",
        f"Browser clips: {sum(record.browser_clips for record in build_records)}",
        f"Resources: {sum(record.resources for record in build_records)}",
        "",
        "EVENT PLAN",
        "----------",
    ]
    for event_name in event_order:
        lines.append("")
        lines.append(event_name)
        for record in events_summary[event_name]:
            lines.append(f"  • {record.project_name}")
            lines.append(f"    Source: {record.relative_project_path}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    json_path = report_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(
            {
                "output_fcpxml": str(output_path),
                "events": {
                    event: [asdict(record) for record in records]
                    for event, records in events_summary.items()
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return build_records


def print_plan(rows: Iterable[PlanRow]) -> None:
    grouped: dict[str, list[PlanRow]] = defaultdict(list)
    for row in rows:
        grouped[row.event_name].append(row)

    print("")
    print("Proposed Final Cut Event plan")
    print("=============================")
    for event_name, event_rows in grouped.items():
        print("")
        print(event_name)
        for row in event_rows:
            print(f"  - {row.project_name}  [{row.relative_project_path}]")


def command_plan(args: argparse.Namespace) -> int:
    converted_root = args.converted_root.expanduser().resolve()
    if not converted_root.is_dir():
        print(f"Converted root is not a folder: {converted_root}", file=sys.stderr)
        return 2

    rows = make_plan(
        converted_root,
        event_mode=args.event_mode,
        event_level=args.event_level,
    )
    if not rows:
        print("No individual FCPXML conversion files were found.", file=sys.stderr)
        return 1

    plan_path = args.plan.expanduser().resolve()
    write_plan(plan_path, rows)
    print_plan(rows)
    print("")
    print(f"Plan CSV written: {plan_path}")
    print("Edit the event_name column if required, then run the build command.")
    return 0


def command_build(args: argparse.Namespace) -> int:
    converted_root = args.converted_root.expanduser().resolve()
    if not converted_root.is_dir():
        print(f"Converted root is not a folder: {converted_root}", file=sys.stderr)
        return 2

    if args.plan:
        rows = load_plan(args.plan.expanduser().resolve())
    else:
        rows = make_plan(
            converted_root,
            event_mode=args.event_mode,
            event_level=args.event_level,
        )

    print_plan(rows)
    if args.dry_run:
        print("")
        print("Dry run only. No combined FCPXML was written.")
        return 0

    output_path = args.output.expanduser().resolve()
    report_path = (
        args.report.expanduser().resolve()
        if args.report
        else output_path.with_name(output_path.stem + "-build-report.txt")
    )

    records = build_combined(rows, output_path, report_path)
    print("")
    print("Build complete")
    print("==============")
    print(f"FCPXML: {output_path}")
    print(f"Report: {report_path}")
    print(f"Events: {len(set(record.event_name for record in records))}")
    print(f"Projects: {sum(record.projects for record in records)}")
    print("")
    print("Import this FCPXML into a new or existing Final Cut library.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan and build combined multi-Event Final Cut XML imports."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Create an editable Event planning CSV.")
    plan.add_argument("converted_root", type=Path)
    plan.add_argument("--plan", type=Path, required=True, help="Destination CSV path.")
    plan.add_argument(
        "--event-mode",
        choices=["top", "parent", "project", "level"],
        default="parent",
        help="How to suggest Event names (default: parent).",
    )
    plan.add_argument(
        "--event-level",
        type=int,
        default=1,
        help="1-based folder level used with --event-mode level.",
    )
    plan.set_defaults(func=command_plan)

    build = subparsers.add_parser("build", help="Build a combined FCPXML import.")
    build.add_argument("converted_root", type=Path)
    build.add_argument("--plan", type=Path, help="Previously generated and edited plan CSV.")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--report", type=Path)
    build.add_argument("--dry-run", action="store_true")
    build.add_argument(
        "--event-mode",
        choices=["top", "parent", "project", "level"],
        default="parent",
        help="Used only when --plan is omitted.",
    )
    build.add_argument(
        "--event-level",
        type=int,
        default=1,
        help="1-based folder level used with --event-mode level.",
    )
    build.set_defaults(func=command_build)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
