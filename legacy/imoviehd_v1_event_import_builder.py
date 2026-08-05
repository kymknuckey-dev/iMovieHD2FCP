#!/usr/bin/env python3
"""Create safe per-project FCPXML imports grouped by Final Cut Event.

Unlike the combined archive builder, this tool does not merge XML documents or
renumber resources. Each source FCPXML remains internally intact. The only XML
change is the Event name.

The output is organised as:

    Final Cut Event Imports/
      Ireland/
        01 - Ring of Kerry.fcpxml
        02 - Blarney Cork.fcpxml
      France/
        01 - Arc de Triomphe.fcpxml

Import the files into the same Final Cut library. Files assigned the same Event
name are intended to populate the same Event while retaining one Project per
original iMovie project.

The tool reads the same Event-plan CSV used by the archive builder.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


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
class ExportRecord:
    event_name: str
    project_name: str
    relative_project_path: str
    source_fcpxml: str
    output_fcpxml: str


def bool_from_csv(value: str) -> bool:
    return value.strip().lower() not in {
        "0", "false", "no", "n", "exclude", "skip"
    }


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return value or "Untitled"


def load_plan(path: Path) -> list[PlanRow]:
    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Could not open plan CSV: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [field for field in PLAN_FIELDS if field not in fields]
        if missing:
            raise ValueError(
                "Plan CSV is missing column(s): " + ", ".join(missing)
            )

        rows: list[PlanRow] = []
        for line_number, raw in enumerate(reader, start=2):
            if not bool_from_csv(raw.get("include", "Yes")):
                continue

            event_name = (raw.get("event_name") or "").strip()
            project_name = (raw.get("project_name") or "").strip()
            relative_path = (raw.get("relative_project_path") or "").strip()
            fcpxml_path = (raw.get("fcpxml_path") or "").strip()

            if not event_name:
                raise ValueError(f"Blank event_name at line {line_number}")
            if not project_name:
                raise ValueError(f"Blank project_name at line {line_number}")
            if not fcpxml_path:
                raise ValueError(f"Blank fcpxml_path at line {line_number}")

            rows.append(
                PlanRow(
                    include=True,
                    event_name=event_name,
                    project_name=project_name,
                    relative_project_path=relative_path,
                    fcpxml_path=fcpxml_path,
                )
            )

    if not rows:
        raise ValueError("The plan contains no included projects.")
    return rows


def set_event_name(root: ET.Element, event_name: str, source: Path) -> None:
    library = root.find("library")
    if library is None:
        raise ValueError(f"No <library> element in {source}")

    events = library.findall("event")
    if len(events) != 1:
        raise ValueError(
            f"Expected exactly one Event in {source}; found {len(events)}"
        )

    events[0].set("name", event_name)


def indent_xml(element: ET.Element, level: int = 0) -> None:
    spacing = "\n" + "    " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = spacing + "    "
        for child in element:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = spacing
    if level and (not element.tail or not element.tail.strip()):
        element.tail = spacing


def write_xml(root: ET.Element, destination: Path) -> None:
    indent_xml(root)
    body = ET.tostring(root, encoding="unicode")
    destination.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE fcpxml>\n"
        + body
        + "\n",
        encoding="utf-8",
    )
    # Confirm the generated XML is well formed.
    ET.parse(destination)


def finalise_project_xmls(
    rows: list[PlanRow],
    report_root: Path,
) -> list[ExportRecord]:
    """Apply Event names to each project's own FCPXML file.

    Delta 4 deliberately keeps one importable XML per project. The source file
    is updated atomically in its existing project folder rather than copied to
    a second Final Cut Imports tree.
    """
    records: list[ExportRecord] = []
    report_root.mkdir(parents=True, exist_ok=True)

    for row in rows:
        source = Path(row.fcpxml_path).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"Project FCPXML does not exist: {source}")

        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError) as exc:
            raise ValueError(f"Could not read {source}: {exc}") from exc

        if root.tag != "fcpxml":
            raise ValueError(f"Not an FCPXML document: {source}")

        set_event_name(root, row.event_name, source)

        temporary = source.with_name(source.name + ".tmp")
        try:
            write_xml(root, temporary)
            temporary.replace(source)
        finally:
            temporary.unlink(missing_ok=True)

        records.append(
            ExportRecord(
                event_name=row.event_name,
                project_name=row.project_name,
                relative_project_path=row.relative_project_path,
                source_fcpxml=str(source),
                output_fcpxml=str(source),
            )
        )

    return records

def write_reports(
    output_root: Path,
    records: list[ExportRecord],
) -> None:
    csv_path = output_root / "event-import-set.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "event_name",
                "project_name",
                "relative_project_path",
                "source_fcpxml",
                "output_fcpxml",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))

    json_path = output_root / "event-import-set.json"
    json_path.write_text(
        json.dumps(
            [asdict(record) for record in records],
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    grouped: dict[str, list[ExportRecord]] = defaultdict(list)
    for record in records:
        grouped[record.event_name].append(record)

    lines = [
        "iMovieHD2FCP Finalised Project Imports",
        "=================================",
        "",
        f"Events: {len(grouped)}",
        f"Projects: {len(records)}",
        "",
        "IMPORT PLAN",
        "-----------",
    ]
    for event_name, event_records in grouped.items():
        lines += ["", event_name]
        for record in event_records:
            lines.append(f"  • {record.project_name}")

    lines += [
        "",
        "Each project XML remains beside its converted project media.",
        "Import the required project XML files into the same Final Cut library.",
    ]
    (output_root / "event-import-set-report.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    status_path = output_root / "final-cut-import-status.json"
    status_path.write_text(
        json.dumps(
            {
                "status": "ready",
                "mode": "per-project-in-place",
                "events": len(grouped),
                "projects": len(records),
                "project_xml_files": [
                    record.output_fcpxml for record in records
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare each project FCPXML in place with its planned Event name."
        )
    )
    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="Event-plan CSV created by the archive builder.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination folder for build reports and completion status.",
    )
    args = parser.parse_args()

    try:
        rows = load_plan(args.plan.expanduser().resolve())
        output_root = args.output.expanduser().resolve()
        records = finalise_project_xmls(rows, output_root)
        write_reports(output_root, records)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    event_count = len({record.event_name for record in records})
    print("Final Cut project files prepared")
    print("================================")
    print(f"Events: {event_count}")
    print(f"Projects: {len(records)}")
    print(f"Build reports: {output_root}")
    print("")
    print("Each final XML remains inside its respective project folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
