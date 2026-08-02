from __future__ import annotations

import os
from pathlib import Path


REQUIRED_LEGACY = {
    "parser": "imoviehd_parser.py",
    "analyser": "imoviehd_archive_analyzer.py",
    "converter": "imoviehd_v1_converter.py",
    "batch": "imoviehd_v1_batch.py",
    "archive_builder": "imoviehd_v1_archive_builder_fixed.py",
    "event_builder": "imoviehd_v1_event_import_builder.py",
}


def candidate_homes() -> list[Path]:
    candidates: list[Path] = []

    env_home = os.environ.get("IMOVIEHD2FCP_HOME")
    if env_home:
        candidates.append(Path(env_home).expanduser())

    candidates.append(Path.cwd())

    package_file = Path(__file__).resolve()
    for parent in package_file.parents:
        candidates.append(parent)

    candidates.append(Path.home() / "Development" / "iMovieHD2FCP")

    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def find_home() -> Path:
    for home in candidate_homes():
        parser_locations = [
            home / "legacy" / REQUIRED_LEGACY["parser"],
            home / REQUIRED_LEGACY["parser"],
        ]
        if any(path.is_file() for path in parser_locations):
            return home
    return candidate_homes()[0]


def find_script(key: str, home: Path | None = None) -> Path:
    if key not in REQUIRED_LEGACY:
        raise KeyError(key)

    home = home or find_home()
    filename = REQUIRED_LEGACY[key]
    candidates = [
        home / "legacy" / filename,
        home / filename,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Required component not found: {filename}\n"
        f"Looked in:\n  " + "\n  ".join(str(path) for path in candidates)
    )
