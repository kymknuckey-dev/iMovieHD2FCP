from pathlib import Path
import tomllib


def test_gui_entry_point_is_packaged():
    root = Path(__file__).parents[1]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["imoviehd2fcp-app"] == "imoviehd2fcp.gui:main"
    assert "PySide6>=6.7" in data["project"]["optional-dependencies"]["gui"]


def test_gui_source_exists():
    root = Path(__file__).parents[1]
    assert (root / "src" / "imoviehd2fcp" / "gui.py").is_file()
