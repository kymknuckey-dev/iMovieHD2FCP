from pathlib import Path
import tomllib


ROOT = Path(__file__).parents[1]


def test_rc1_version():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "1.1.0rc1"

    init_text = (
        ROOT / "src" / "imoviehd2fcp" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert '__version__ = "1.1.0rc1"' in init_text


def test_clean_fcpxml_naming_remains_enabled():
    source = (
        ROOT / "legacy" / "imoviehd_v1_converter.py"
    ).read_text(encoding="utf-8")
    assert 'f"{safe_name(project_name)}.fcpxml"' in source
    assert 'f"{safe_name(project_name)}-v1.fcpxml"' not in source


def test_guided_gui_has_no_preview_button():
    source = (
        ROOT / "src" / "imoviehd2fcp" / "gui.py"
    ).read_text(encoding="utf-8")
    assert 'QPushButton("Preview Conversion")' not in source
    assert "Prepare Final Cut Project Files" in source
    assert "Your projects are ready for Final Cut Pro" in source


def test_rc1_documents_exist():
    assert (ROOT / "docs" / "RELEASE_NOTES_1.1.0_RC1.md").is_file()
    assert (ROOT / "docs" / "RC1_TEST_CHECKLIST.md").is_file()
