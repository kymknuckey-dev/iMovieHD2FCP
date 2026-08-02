import json

from imoviehd2fcp.reporting import aggregate, build_reports, project_status


def test_project_status():
    assert project_status({"status": "complete", "verification_passed": True}) == "PASS"
    assert project_status({
        "status": "complete",
        "verification_passed": True,
        "warnings": ["review"],
    }) == "WARN"
    assert project_status({"status": "failed", "verification_passed": False}) == "FAIL"


def test_report_build(tmp_path):
    data = [
        {
            "project_name": "Small World",
            "status": "complete",
            "verification_passed": True,
            "warnings": [],
            "missing_references": [],
            "statistics": {
                "timeline_items": 29,
                "transition_items": 15,
                "title_items": 1,
                "converted_media_files": 24,
                "converted_media_bytes": 1024,
            },
        }
    ]
    (tmp_path / "batch-conversion-summary.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    text_path, html_path = build_reports(tmp_path)
    assert text_path.is_file()
    assert html_path.is_file()
    assert "Small World" in text_path.read_text(encoding="utf-8")
    assert "Small World" in html_path.read_text(encoding="utf-8")


def test_aggregate_status():
    summary = aggregate([
        {"status": "complete", "verification_passed": True},
        {"status": "complete", "verification_passed": False},
    ])
    assert summary["overall"] == "WARN"
    assert summary["projects"] == 2
