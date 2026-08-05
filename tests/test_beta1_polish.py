from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_converter_uses_clean_project_xml_filename():
    source = (
        ROOT / "legacy" / "imoviehd_v1_converter.py"
    ).read_text(encoding="utf-8")
    assert 'f"{safe_name(project_name)}.fcpxml"' in source
    assert 'f"{safe_name(project_name)}-v1.fcpxml"' not in source


def test_gui_uses_final_user_language():
    source = (
        ROOT / "src" / "imoviehd2fcp" / "gui.py"
    ).read_text(encoding="utf-8")
    assert "Preview Conversion" not in source
    assert "Your projects are ready for Final Cut Pro" in source
    assert "Prepare Final Cut Project Files" in source
