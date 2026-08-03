#!/usr/bin/env python3
"""Parse legacy iMovie HD .iMovieProj text files.

This first version focuses on extracting project metadata, timeline clips, music,
effects, replaced-source clips, title text, volume markers, and resolving media
inside the sibling Media folder.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Optional

FRAME_RE = re.compile(r"Frames:\s*(-?\d+)\s+In:(-?\d+)\s+Out:(-?\d+)\s+Thumb:(-?\d+)")
KEY_VALUE_RE = re.compile(r"^([^:]+):(?:\s?(.*))?$")


def decode_project(data: bytes) -> str:
    """Decode an iMovie HD project, preferring MacRoman used by classic Mac OS."""
    for encoding in ("utf-8", "mac_roman", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("mac_roman", errors="replace")


def classic_path_to_filename(value: str) -> str:
    """Convert classic Mac colon-separated names to Finder-visible filenames."""
    return value.replace(":", " ").strip()


@dataclass
class VolumeMarker:
    location: Optional[int] = None
    volume: Optional[float] = None
    flags: Optional[int] = None


@dataclass
class MediaRef:
    name: str
    kind: str
    file_ref: Optional[str] = None
    frames: Optional[int] = None
    in_frame: Optional[int] = None
    out_frame: Optional[int] = None
    thumb: Optional[int] = None
    type_code: Optional[int] = None
    timestamp: Optional[float] = None
    record_date: Optional[int] = None
    frames_taken: list[int] = field(default_factory=list)
    fade_in: Optional[int] = None
    fade_out: Optional[int] = None
    volume_fade: list[int] = field(default_factory=list)
    still_image: Optional[str] = None
    still_image_thumb: Optional[str] = None
    selected: Optional[int] = None
    audio_info: list[float] = field(default_factory=list)
    file_type: Optional[str] = None
    plugin: Optional[str] = None
    effect_info: list[int] = field(default_factory=list)
    transition_info: Optional[str] = None
    title_info: Optional[str] = None
    title_pairs: list[dict[str, str]] = field(default_factory=list)
    title_block: list[str] = field(default_factory=list)
    replaced: list["MediaRef"] = field(default_factory=list)
    volume_markers: list[VolumeMarker] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)
    timeline_start_frame: Optional[int] = None
    resolved_media: Optional[str] = None
    media_exists: Optional[bool] = None

    @property
    def duration_frames(self) -> int:
        if self.frames is not None:
            return self.frames
        if self.in_frame is not None and self.out_frame is not None:
            return self.out_frame - self.in_frame
        return 0


@dataclass
class Project:
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timeline: list[MediaRef] = field(default_factory=list)
    music: list[MediaRef] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def fps(self) -> float:
        standard = str(self.metadata.get("VideoStandard", "")).upper()
        return 25.0 if standard == "PAL" else 29.97 if standard == "NTSC" else 25.0

    @property
    def timeline_frames(self) -> int:
        return sum(item.duration_frames for item in self.timeline)


class IMovieHDParser:
    def parse_file(self, path: Path) -> Project:
        text = decode_project(path.read_bytes()).replace("\r\n", "\n").replace("\r", "\n")
        project = self.parse_text(text, source=str(path))
        self._assign_timeline_positions(project)
        self._resolve_media(project, path.parent / "Media")
        return project

    def parse_text(self, text: str, source: str = "<memory>") -> Project:
        lines = text.splitlines()
        project = Project(source=source)
        if not lines or lines[0].strip() != "iMovie Project File":
            project.warnings.append("File does not begin with 'iMovie Project File'.")

        i = 1
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped:
                i += 1
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent == 0 and stripped.startswith("Clip: "):
                item, i = self._parse_media(lines, i, kind="clip", base_indent=0)
                project.timeline.append(item)
                continue
            if indent == 0 and stripped.startswith("Music: "):
                item, i = self._parse_media(lines, i, kind="music", base_indent=0)
                project.music.append(item)
                continue
            if indent == 0:
                key, value = self._split_key_value(stripped)
                if key:
                    project.metadata[key] = self._coerce(value)
            i += 1
        return project

    def _parse_media(self, lines: list[str], start: int, kind: str, base_indent: int) -> tuple[MediaRef, int]:
        header = lines[start].strip()
        prefix = "Clip:" if kind == "clip" else "Music:"
        item = MediaRef(name=header[len(prefix):].strip(), kind=kind)
        i = start + 1
        in_effect = False
        in_replaced = False
        in_title_pairs = False
        in_title_block = False
        current_pair: Optional[dict[str, str]] = None

        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" "))
            if stripped and indent <= base_indent:
                break
            if not stripped:
                i += 1
                continue

            if stripped == "BeginEffectInfo":
                in_effect = True; i += 1; continue
            if stripped == "EndEffectInfo":
                in_effect = False; i += 1; continue
            if stripped == "BeginReplacedList":
                in_replaced = True; i += 1; continue
            if stripped == "EndReplacedList":
                in_replaced = False; i += 1; continue
            if stripped.startswith("BeginTitlePairs:"):
                in_title_pairs = True; i += 1; continue
            if stripped == "EndTitlePairs":
                if current_pair is not None:
                    item.title_pairs.append(current_pair)
                    current_pair = None
                in_title_pairs = False; i += 1; continue
            if stripped.startswith("BeginTitleBlock:"):
                in_title_block = True; i += 1; continue
            if stripped == "EndTitleBlock":
                in_title_block = False; i += 1; continue

            if in_replaced and stripped.startswith("Clip: "):
                child, i = self._parse_media(lines, i, kind="clip", base_indent=indent)
                item.replaced.append(child)
                continue

            if stripped == "ClipVolumeMarker:":
                marker, i = self._parse_volume_marker(lines, i, indent)
                item.volume_markers.append(marker)
                continue

            if in_title_block:
                item.title_block.append(stripped)
                i += 1
                continue

            key, value = self._split_key_value(stripped)
            if key is None:
                i += 1
                continue

            if in_title_pairs and key in {"Title", "SubTitle"}:
                if key == "Title":
                    if current_pair is not None:
                        item.title_pairs.append(current_pair)
                    current_pair = {"title": value or "", "subtitle": ""}
                else:
                    if current_pair is None:
                        current_pair = {"title": "", "subtitle": value or ""}
                    else:
                        current_pair["subtitle"] = value or ""
                i += 1
                continue

            self._apply_field(item, key, value or "", in_effect)
            i += 1
        return item, i

    def _parse_volume_marker(self, lines: list[str], start: int, base_indent: int) -> tuple[VolumeMarker, int]:
        marker = VolumeMarker()
        i = start + 1
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" "))
            if stripped and indent <= base_indent:
                break
            key, value = self._split_key_value(stripped)
            if key == "ClipVolumeMarkerLocation": marker.location = self._int(value)
            elif key == "ClipVolumeMarkerVolume": marker.volume = self._float(value)
            elif key == "ClipVolumeMarkerFlags": marker.flags = self._int(value)
            i += 1
        return marker, i

    def _apply_field(self, item: MediaRef, key: str, value: str, in_effect: bool) -> None:
        if key == "File": item.file_ref = value
        elif key == "Frames":
            m = FRAME_RE.match(f"Frames: {value}")
            if m:
                item.frames, item.in_frame, item.out_frame, item.thumb = map(int, m.groups())
        elif key == "Type": item.type_code = self._int(value)
        elif key == "Timestamp": item.timestamp = self._float(value)
        elif key == "RecordDate": item.record_date = self._int(value)
        elif key == "FramesTaken": item.frames_taken = self._int_list(value)
        elif key == "FadeIn":
            # Some lines contain both FadeIn and FadeOut.
            m = re.match(r"(-?\d+)\s+FadeOut:(-?\d+)", value)
            if m: item.fade_in, item.fade_out = map(int, m.groups())
            else: item.fade_in = self._int(value)
        elif key == "Volume/Fade": item.volume_fade = self._int_list(value)
        elif key == "StillImage": item.still_image = value.split()[0] if value else None
        elif key == "StillImageThumb": item.still_image_thumb = value
        elif key == "Selected": item.selected = self._int(value)
        elif key == "AudioInfo": item.audio_info = [self._float(x) or 0.0 for x in value.split()]
        elif key == "FileType": item.file_type = value
        elif key == "Plugin": item.plugin = value
        elif key == "EffectInfo": item.effect_info = self._int_list(value)
        elif key == "TransitionInfo": item.transition_info = value
        elif key == "TitleInfo": item.title_info = value
        else: item.extras[key] = self._coerce(value)

    def _assign_timeline_positions(self, project: Project) -> None:
        cursor = 0
        for item in project.timeline:
            item.timeline_start_frame = cursor
            cursor += item.duration_frames

    def _resolve_media(self, project: Project, media_dir: Path) -> None:
        if not media_dir.exists():
            project.warnings.append(f"Media folder not found: {media_dir}")
            return
        files = [p for p in media_dir.iterdir() if p.is_file() and not p.name.startswith("._") and p.name != ".DS_Store"]
        by_name = {p.name.casefold(): p for p in files}

        def resolve(item: MediaRef) -> None:
            candidates: list[str] = []
            if item.file_ref:
                candidates.extend([classic_path_to_filename(item.file_ref), item.file_ref])
            if item.still_image:
                candidates.append(item.still_image)
            # Finder may alter case only; compare case-insensitively.
            found = None
            for candidate in candidates:
                found = by_name.get(candidate.casefold())
                if found: break
            item.media_exists = found is not None
            item.resolved_media = str(found) if found else None
            for child in item.replaced:
                resolve(child)

        for item in project.timeline + project.music:
            resolve(item)

    @staticmethod
    def _split_key_value(line: str) -> tuple[Optional[str], Optional[str]]:
        m = KEY_VALUE_RE.match(line)
        return (m.group(1).strip(), (m.group(2) or "").strip()) if m else (None, None)

    @staticmethod
    def _int(value: Optional[str]) -> Optional[int]:
        try: return int(str(value).strip())
        except (TypeError, ValueError): return None

    @staticmethod
    def _float(value: Optional[str]) -> Optional[float]:
        try: return float(str(value).strip())
        except (TypeError, ValueError): return None

    def _int_list(self, value: str) -> list[int]:
        result = []
        for token in value.split():
            parsed = self._int(token)
            if parsed is not None: result.append(parsed)
        return result

    def _coerce(self, value: Optional[str]) -> Any:
        if value is None: return None
        value = value.strip()
        if not value: return ""
        if re.fullmatch(r"-?\d+", value): return int(value)
        if re.fullmatch(r"-?\d+\.\d+", value): return float(value)
        parts = value.split()
        if len(parts) > 1 and all(re.fullmatch(r"-?\d+(?:\.\d+)?", p) for p in parts):
            return [float(p) if "." in p else int(p) for p in parts]
        return value


def iter_all_media(items: Iterable[MediaRef]) -> Iterable[MediaRef]:
    for item in items:
        yield item
        yield from iter_all_media(item.replaced)


def project_to_dict(project: Project) -> dict[str, Any]:
    data = asdict(project)
    data["summary"] = summarize(project)
    return data


def summarize(project: Project) -> dict[str, Any]:
    all_items = list(iter_all_media(project.timeline + project.music))
    top = project.timeline
    plugins: dict[str, int] = {}
    for item in all_items:
        if item.plugin: plugins[item.plugin] = plugins.get(item.plugin, 0) + 1
    missing = sorted({classic_path_to_filename(x.file_ref) for x in all_items if x.file_ref and x.media_exists is False})
    return {
        "video_standard": project.metadata.get("VideoStandard"),
        "fps": project.fps,
        "timeline_items": len(top),
        "timeline_frames": project.timeline_frames,
        "timeline_seconds": round(project.timeline_frames / project.fps, 3),
        "music_items": len(project.music),
        "transition_or_effect_items": sum(1 for x in top if x.plugin),
        "plugins": plugins,
        "missing_media": missing,
    }


def format_time(frames: int, fps: float) -> str:
    total = frames / fps
    h = int(total // 3600); m = int((total % 3600) // 60); s = total % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def make_report(project: Project) -> str:
    s = summarize(project)
    lines = [
        "iMovie HD Project Report",
        "=" * 24,
        f"Source: {project.source}",
        f"Video standard: {s['video_standard']}",
        f"Frame rate used: {s['fps']} fps",
        f"Timeline: {s['timeline_frames']} frames ({format_time(s['timeline_frames'], s['fps'])})",
        f"Top-level timeline items: {s['timeline_items']}",
        f"Music items: {s['music_items']}",
        "",
        "Metadata",
        "--------",
    ]
    lines.extend(f"{k}: {v}" for k, v in project.metadata.items())
    lines += ["", "Timeline", "--------"]
    for idx, item in enumerate(project.timeline, 1):
        start = item.timeline_start_frame or 0
        plugin = f" | {item.plugin}" if item.plugin else ""
        media = Path(item.resolved_media).name if item.resolved_media else "MISSING" if item.media_exists is False else "unresolved"
        lines.append(
            f"{idx:03d} {format_time(start, project.fps)}  {item.name} | "
            f"frames={item.duration_frames} in={item.in_frame} out={item.out_frame} | media={media}{plugin}"
        )
        if item.title_pairs:
            for pair in item.title_pairs:
                lines.append(f"      TITLE: {pair.get('title','')} / {pair.get('subtitle','')}")
        if item.replaced:
            for child in item.replaced:
                lines.append(f"      replaces: {child.name} [{child.in_frame}:{child.out_frame}] file={child.file_ref}")
    if project.music:
        lines += ["", "Music", "-----"]
        for item in project.music:
            media = Path(item.resolved_media).name if item.resolved_media else "MISSING"
            lines.append(f"{item.name} | frames={item.frames} | media={media}")
    lines += ["", "Effects / transitions", "---------------------"]
    if s["plugins"]:
        lines.extend(f"{name}: {count}" for name, count in sorted(s["plugins"].items()))
    else:
        lines.append("None detected")
    lines += ["", "Missing media", "-------------"]
    lines.extend(s["missing_media"] or ["None"])
    if project.warnings:
        lines += ["", "Warnings", "--------", *project.warnings]
    return "\n".join(lines) + "\n"


def find_project(root: Path) -> Path:
    if root.is_file() and root.suffix.lower() == ".imovieproj":
        return root
    candidates = sorted(p for p in root.rglob("*.iMovieProj") if "__MACOSX" not in p.parts and not p.name.startswith("._"))
    if not candidates:
        raise FileNotFoundError(f"No .iMovieProj found under {root}")
    if len(candidates) > 1:
        raise RuntimeError(f"More than one .iMovieProj found; specify one directly: {candidates}")
    return candidates[0]


def process_path(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    parser = IMovieHDParser()
    if input_path.suffix.lower() == ".zip":
        with TemporaryDirectory(prefix="imoviehd_") as temp:
            with zipfile.ZipFile(input_path) as zf:
                zf.extractall(temp)
            project_path = find_project(Path(temp))
            project = parser.parse_file(project_path)
            project.source = f"{input_path}!/{project_path.relative_to(temp)}"
    else:
        project_path = find_project(input_path)
        project = parser.parse_file(project_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(project_path).stem
    json_path = output_dir / f"{stem}-timeline.json"
    report_path = output_dir / f"{stem}-report.txt"
    json_path.write_text(json.dumps(project_to_dict(project), indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(make_report(project), encoding="utf-8")
    return json_path, report_path


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Parse an iMovie HD .iMovieProj project")
    ap.add_argument("input", type=Path, help=".iMovieProj file, project folder, or ZIP")
    ap.add_argument("-o", "--output", type=Path, default=Path.cwd(), help="Output folder")
    args = ap.parse_args(argv)
    try:
        json_path, report_path = process_path(args.input.expanduser(), args.output.expanduser())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
