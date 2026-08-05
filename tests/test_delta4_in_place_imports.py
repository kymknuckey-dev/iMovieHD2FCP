from __future__ import annotations

import csv
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_project_xml(path: Path, event_name: str = "Original") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE fcpxml>\n'
        '<fcpxml version="1.10"><library><event name="'
        + event_name
        + '"><project name="Project"/></event></library></fcpxml>\n',
        encoding="utf-8",
    )


def test_finalise_updates_existing_xml_without_duplicate(tmp_path):
    module = load_module(
        "delta4_event_builder",
        ROOT / "legacy" / "imoviehd_v1_event_import_builder.py",
    )
    project_xml = (
        tmp_path / "projects" / "Disney Final" / "Small World" / "Small World.fcpxml"
    )
    write_project_xml(project_xml)

    row = module.PlanRow(
        include=True,
        event_name="Disney Final",
        project_name="Small World",
        relative_project_path="Disney Final/Small World",
        fcpxml_path=str(project_xml),
    )
    report_root = tmp_path / "Final Cut Build Reports"
    records = module.finalise_project_xmls([row], report_root)
    module.write_reports(report_root, records)

    event = ET.parse(project_xml).getroot().find("library/event")
    assert event is not None
    assert event.get("name") == "Disney Final"
    assert records[0].source_fcpxml == records[0].output_fcpxml
    assert list(tmp_path.rglob("*.fcpxml")) == [project_xml]
    assert (report_root / "final-cut-import-status.json").is_file()


def test_gui_has_no_preview_conversion_button():
    source = (ROOT / "src" / "imoviehd2fcp" / "gui.py").read_text(encoding="utf-8")
    assert 'QPushButton("Preview Conversion")' not in source
    assert '"--dry-run"' not in source


def test_cli_retains_dry_run_for_advanced_use():
    source = (ROOT / "src" / "imoviehd2fcp" / "cli.py").read_text(encoding="utf-8")
    assert '"--dry-run"' in source
