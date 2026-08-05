from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_preferred_project_output_is_under_projects(tmp_path):
    module = load_module("delta3_batch", ROOT / "legacy" / "imoviehd_v1_batch.py")
    relative = Path("Disney Final") / "Small World"
    assert module.preferred_project_output(tmp_path, relative) == (
        tmp_path / "projects" / "Disney Final" / "Small World"
    )


def test_new_layout_is_preferred_for_fresh_conversion(tmp_path):
    module = load_module("delta3_batch_fresh", ROOT / "legacy" / "imoviehd_v1_batch.py")
    relative = Path("Europe Final 1") / "Paris"
    assert module.select_project_output(
        tmp_path, relative, force=False, verify_only=False
    ) == tmp_path / "projects" / relative


def test_legacy_outputs_remain_readable(tmp_path):
    module = load_module("delta3_batch_legacy", ROOT / "legacy" / "imoviehd_v1_batch.py")
    relative = Path("Britain Final 2") / "London"
    legacy = tmp_path / relative
    legacy.mkdir(parents=True)
    (legacy / "London.fcpxml").write_text("<fcpxml/>", encoding="utf-8")

    assert module.select_project_output(
        tmp_path, relative, force=False, verify_only=True
    ) == legacy


def test_projects_container_is_hidden_from_event_grouping():
    module = load_module(
        "delta3_builder",
        ROOT / "legacy" / "imoviehd_v1_archive_builder_fixed.py",
    )
    physical = Path("projects") / "Disney Final" / "Small World"
    logical = module.logical_project_folder(physical)
    assert logical == Path("Disney Final") / "Small World"
    assert module.suggested_event(logical, "parent", 1) == "Disney Final"
    assert module.suggested_event(logical, "top", 1) == "Disney Final"
