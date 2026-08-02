import importlib.util
from pathlib import Path


def load_converter():
    path = Path(__file__).parents[1] / "legacy" / "imoviehd_v1_converter.py"
    spec = importlib.util.spec_from_file_location("converter_rc2", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_duplicate_name_cleanup():
    module = load_converter()

    class Item:
        def __init__(self, name):
            self.original_asset_name = name
            self.asset_name = name

    items = [Item("Clip 13"), Item("Clip 13/1"), Item("Clip 13/2")]
    module.assign_clean_asset_names(items)
    assert [item.asset_name for item in items] == [
        "Clip 13", "Clip 13 (2)", "Clip 13 (3)"
    ]


def test_timestamp_provenance_has_selection(tmp_path):
    module = load_converter()
    source = tmp_path / "sample.dat"
    source.write_bytes(b"sample")
    info = module.timestamp_provenance(source)
    assert info["selected"]["value"]
    assert info["selected"]["reason"]
