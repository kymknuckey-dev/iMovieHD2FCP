#!/usr/bin/env python3
"""iMovie HD -> modern media + import-safe FCPXML (v1.0 alpha).

Version 1.0 alpha builds on the proven Stage 6.5 workflow and adds archive-preservation metadata, project-qualified Final Cut browser names, and configurable Event naming. It mirrors Apple-generated FCPXML by
placing one asset-clip for every converted asset directly inside the Event, before the
Project. Timeline clips reference the same asset resources. Embedded source audio is
left to Final Cut to infer naturally. Separate soundtrack audio is converted and restored as a connected audio clip. Rendered transitions, effects, and titles remain preserved as ordinary media clips. Title metadata is inventoried in the manifest and a human-readable report.

Requirements:
    ffmpeg and ffprobe on PATH

Example:
    python3 imoviehd_stage6_5.py \
      "output/Small World-timeline.json" \
      --output-dir "output/Small World Stage 6"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

FPS = 25
FRAME_DURATION = "1/25s"
FCPXML_VERSION = "1.14"


@dataclass
class Probe:
    path: str
    format_name: str | None = None
    duration_seconds: float | None = None
    video_codec: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    field_order: str | None = None
    pixel_format: str | None = None
    audio_codec: str | None = None
    audio_rate: int | None = None
    audio_channels: int | None = None
    has_video: bool = False
    has_audio: bool = False
    error: str | None = None


@dataclass
class MediaPlan:
    source: str
    output: str
    asset_name: str
    uid: str
    max_required_frame: int
    probe: dict[str, Any]
    status: str = "planned"


@dataclass
class TitlePlan:
    plugin: str
    text: list[str]
    rendered_media: str | None
    timeline_start_frame: int
    duration_frames: int
    timeline_end_frame: int
    underlying_clips: list[str]
    font: str | None = None
    foreground: str | None = None
    background: str | None = None
    direction: int | None = None
    speed: int | None = None
    font_size_scale: int | None = None
    hang_time: int | None = None
    over_black: int | None = None
    tv_safe: int | None = None
    raw_title_info: str | None = None


@dataclass
class AudioPlan:
    source: str
    output: str
    asset_name: str
    uid: str
    timeline_start_frame: int
    source_start_frame: int
    duration_frames: int
    probe: dict[str, Any]
    status: str = "planned"


def frame_time(frames: int | None) -> str:
    n = int(frames or 0)
    return "0s" if n == 0 else f"{n}/25s"


def file_url(path: Path) -> str:
    return "file://" + quote(str(path.expanduser().resolve()), safe="/:")


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" ._")
    return cleaned or "media"


def stable_uid(text: str) -> str:
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest().upper()


def unique_output_name(source: Path) -> str:
    stem = safe_name(source.stem if source.suffix else source.name)
    digest = hashlib.sha1(str(source).encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return f"{stem}-{digest}.mov"


def source_timestamp(path: Path) -> float:
    """Return the best available original timestamp for archival metadata."""
    stat = path.stat()
    birth = getattr(stat, "st_birthtime", None)
    return float(birth if birth and birth > 0 else stat.st_mtime)


def source_creation_time(path: Path) -> str:
    """Return an ISO-8601 UTC timestamp suitable for QuickTime metadata."""
    return datetime.fromtimestamp(source_timestamp(path), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def preserve_file_dates(source: Path, output: Path) -> None:
    """Preserve source modification time and, on macOS, creation time when possible."""
    timestamp = source_timestamp(source)
    os.utime(output, (timestamp, timestamp))

    # SetFile is supplied by Apple's Command Line Tools. Failure is non-fatal.
    setfile = shutil.which("SetFile") or ("/usr/bin/SetFile" if Path("/usr/bin/SetFile").exists() else None)
    if setfile:
        local = datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y %H:%M:%S")
        subprocess.run([setfile, "-d", local, str(output)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([setfile, "-m", local, str(output)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def browser_asset_name(project_name: str, asset_name: str) -> str:
    """Generate a library-safe display name while keeping timeline names unchanged."""
    return f"{project_name} — {asset_name}"


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise SystemExit(
            "Missing required tool(s): " + ", ".join(missing) +
            "\nInstall with Homebrew: brew install ffmpeg"
        )


def parse_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        if "/" in value:
            a, b = value.split("/", 1)
            return float(a) / float(b)
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def probe_media(path: Path) -> Probe:
    result = Probe(path=str(path))
    try:
        p = run([
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path)
        ], capture=True)
        data = json.loads(p.stdout)
    except FileNotFoundError:
        result.error = "ffprobe not installed"
        return result
    except subprocess.CalledProcessError as exc:
        result.error = (exc.stderr or "ffprobe failed").strip()
        return result
    except json.JSONDecodeError as exc:
        result.error = f"invalid ffprobe JSON: {exc}"
        return result

    fmt = data.get("format", {})
    result.format_name = fmt.get("format_name")
    try:
        result.duration_seconds = float(fmt["duration"])
    except (KeyError, TypeError, ValueError):
        pass

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and not result.has_video:
            result.has_video = True
            result.video_codec = stream.get("codec_name")
            result.width = stream.get("width")
            result.height = stream.get("height")
            result.fps = parse_rate(stream.get("avg_frame_rate")) or parse_rate(stream.get("r_frame_rate"))
            result.field_order = stream.get("field_order")
            result.pixel_format = stream.get("pix_fmt")
        elif stream.get("codec_type") == "audio" and not result.has_audio:
            result.has_audio = True
            result.audio_codec = stream.get("codec_name")
            try:
                result.audio_rate = int(stream.get("sample_rate"))
            except (TypeError, ValueError):
                pass
            result.audio_channels = stream.get("channels")
    return result


def load_timeline(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Timeline JSON not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid timeline JSON: {exc}")
    if not isinstance(data.get("timeline"), list):
        raise SystemExit("Timeline JSON has no 'timeline' list")
    return data


def collect_media(data: dict[str, Any], converted_dir: Path, *, allow_missing: bool) -> tuple[list[MediaPlan], dict[str, MediaPlan]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in data["timeline"]:
        source = item.get("resolved_media")
        if not source:
            continue
        frames = int(item.get("frames") or 0)
        in_frame = int(item.get("in_frame") or 0)
        needed = max(1, in_frame + frames, int(item.get("out_frame") or 0))
        entry = grouped.setdefault(source, {
            "name": item.get("name") or Path(source).name,
            "max_required_frame": needed,
        })
        entry["max_required_frame"] = max(entry["max_required_frame"], needed)

    plans: list[MediaPlan] = []
    by_source: dict[str, MediaPlan] = {}
    for source_text, info in grouped.items():
        source = Path(source_text)
        exists = source.exists()
        if not exists and not allow_missing:
            raise SystemExit(f"Required media is missing: {source}")
        probe = probe_media(source) if exists else Probe(path=str(source), error="missing")
        output = converted_dir / unique_output_name(source)
        plan = MediaPlan(
            source=str(source),
            output=str(output),
            asset_name=str(info["name"]),
            uid=stable_uid(str(source.resolve() if exists else source)),
            max_required_frame=int(info["max_required_frame"]),
            probe=asdict(probe),
            status="missing" if not exists else "planned",
        )
        plans.append(plan)
        by_source[source_text] = plan
    return plans, by_source


def ffmpeg_command(source: Path, output: Path, probe: Probe) -> list[str]:
    cmd = ["ffmpeg", "-hide_banner", "-y", "-i", str(source)]

    # Stage 6 targets PAL SD. Preserve interlacing and lower-field-first DV behaviour.
    if probe.has_video:
        cmd += [
            "-map", "0:v:0",
            "-c:v", "prores_ks", "-profile:v", "1",
            "-pix_fmt", "yuv422p10le",
            "-vf", "fps=25,scale=720:576:flags=lanczos,setfield=bff",
            "-flags", "+ildct+ilme", "-top", "0",
        ]
    if probe.has_audio:
        cmd += [
            "-map", "0:a:0?",
            "-c:a", "pcm_s16le", "-ar", "48000",
        ]
    elif probe.has_video:
        # Do not synthesize audio. FCPXML will mark the asset video-only.
        cmd += ["-an"]

    cmd += [
        "-metadata", f"creation_time={source_creation_time(source)}",
        "-movflags", "+faststart", str(output),
    ]
    return cmd


def convert_plans(plans: list[MediaPlan], *, force: bool) -> None:
    for index, plan in enumerate(plans, start=1):
        source = Path(plan.source)
        output = Path(plan.output)
        if plan.status == "missing":
            print(f"[{index}/{len(plans)}] MISSING {source}", file=sys.stderr)
            continue
        if output.exists() and not force:
            plan.status = "reused"
            print(f"[{index}/{len(plans)}] Reusing {output.name}")
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        probe = Probe(**plan.probe)
        if not probe.has_video:
            plan.status = "unsupported"
            print(f"[{index}/{len(plans)}] No video stream; skipping {source}", file=sys.stderr)
            continue
        print(f"[{index}/{len(plans)}] Converting {source.name} -> {output.name}")
        temp = output.with_suffix(".partial.mov")
        temp.unlink(missing_ok=True)
        try:
            run(ffmpeg_command(source, temp, probe))
            os.replace(temp, output)
            preserve_file_dates(source, output)
            plan.status = "converted"
        except subprocess.CalledProcessError:
            temp.unlink(missing_ok=True)
            plan.status = "failed"
            raise SystemExit(f"ffmpeg conversion failed: {source}")



def parse_title_info(value: str | None) -> dict[str, Any]:
    """Parse iMovie HD's compact title settings string into useful fields."""
    if not value:
        return {}
    result: dict[str, Any] = {}
    for key, raw in re.findall(r"([A-Za-z][A-Za-z0-9]*)\(([^)]*)\)", value):
        normalized = {
            "fore": "foreground",
            "back": "background",
            "dir": "direction",
            "fontSizeScale": "font_size_scale",
            "hangTime": "hang_time",
            "overBlack": "over_black",
            "tvSafe": "tv_safe",
        }.get(key, key)
        if normalized in {"direction", "speed", "font_size_scale", "hang_time", "over_black", "tv_safe"}:
            try:
                result[normalized] = int(raw)
            except ValueError:
                result[normalized] = raw
        else:
            result[normalized] = raw
    return result


def _title_segment_from_item(item: dict[str, Any]) -> dict[str, Any] | None:
    plugin = str(item.get("plugin") or "")
    if not plugin.startswith("Title "):
        return None
    start = int(item.get("timeline_start_frame") or 0)
    frames = int(item.get("frames") or 0)
    if frames <= 0:
        return None
    underlying: list[str] = []
    for replaced in item.get("replaced") or []:
        name = replaced.get("name")
        if name and not str(replaced.get("plugin") or "").startswith("Title "):
            underlying.append(str(name))
    return {
        "plugin": plugin,
        "text": [str(x) for x in (item.get("title_block") or []) if str(x).strip()],
        "rendered_media": item.get("resolved_media"),
        "start": start,
        "end": start + frames,
        "underlying": underlying,
        "title_info": item.get("title_info"),
    }


def collect_titles(data: dict[str, Any]) -> list[TitlePlan]:
    """Consolidate title segments, including portions embedded in rendered transitions."""
    segments: list[dict[str, Any]] = []
    for item in data.get("timeline") or []:
        segment = _title_segment_from_item(item)
        if segment:
            segments.append(segment)
        item_start = int(item.get("timeline_start_frame") or 0)
        for replaced in item.get("replaced") or []:
            nested = _title_segment_from_item(replaced)
            if not nested:
                continue
            # A title nested in a rendered transition occupies that transition's timeline span.
            nested["start"] = item_start
            nested["end"] = item_start + int(item.get("frames") or 0)
            segments.append(nested)

    grouped: dict[tuple[str, str | None], dict[str, Any]] = {}
    for seg in segments:
        key = (seg["plugin"], seg["rendered_media"])
        group = grouped.setdefault(key, {
            "plugin": seg["plugin"],
            "text": [],
            "rendered_media": seg["rendered_media"],
            "start": seg["start"],
            "end": seg["end"],
            "underlying": [],
            "title_info": seg["title_info"],
        })
        group["start"] = min(group["start"], seg["start"])
        group["end"] = max(group["end"], seg["end"])
        for text in seg["text"]:
            if text not in group["text"]:
                group["text"].append(text)
        for name in seg["underlying"]:
            if name not in group["underlying"]:
                group["underlying"].append(name)
        if not group["title_info"] and seg["title_info"]:
            group["title_info"] = seg["title_info"]

    titles: list[TitlePlan] = []
    for group in sorted(grouped.values(), key=lambda x: x["start"]):
        parsed = parse_title_info(group["title_info"])
        titles.append(TitlePlan(
            plugin=group["plugin"],
            text=group["text"],
            rendered_media=group["rendered_media"],
            timeline_start_frame=group["start"],
            duration_frames=group["end"] - group["start"],
            timeline_end_frame=group["end"],
            underlying_clips=group["underlying"],
            font=parsed.get("font"),
            foreground=parsed.get("foreground"),
            background=parsed.get("background"),
            direction=parsed.get("direction"),
            speed=parsed.get("speed"),
            font_size_scale=parsed.get("font_size_scale"),
            hang_time=parsed.get("hang_time"),
            over_black=parsed.get("over_black"),
            tv_safe=parsed.get("tv_safe"),
            raw_title_info=group["title_info"],
        ))
    return titles


def write_title_report(path: Path, project_name: str, titles: list[TitlePlan]) -> None:
    lines = [
        f"iMovie HD Title Inventory — {project_name}",
        "=" * (27 + len(project_name)),
        "",
        "Rendered title clips remain unchanged in the FCPXML timeline.",
        "This report records metadata for later native-title reconstruction.",
        "",
        f"Titles found: {len(titles)}",
        "",
    ]
    if not titles:
        lines.append("No iMovie HD title plugins were detected.")
    for index, title in enumerate(titles, start=1):
        lines.extend([
            f"TITLE {index}",
            "-" * 40,
            f"Text: {' / '.join(title.text) if title.text else '(no title_block text)' }",
            f"Plugin: {title.plugin}",
            f"Start: frame {title.timeline_start_frame} ({title.timeline_start_frame / FPS:.2f} s)",
            f"End: frame {title.timeline_end_frame} ({title.timeline_end_frame / FPS:.2f} s)",
            f"Duration: {title.duration_frames} frames ({title.duration_frames / FPS:.2f} s)",
            f"Rendered media: {title.rendered_media or '(unknown)'}",
            f"Underlying clip(s): {', '.join(title.underlying_clips) if title.underlying_clips else '(not identified)'}",
            f"Font: {title.font or '(unknown)'}",
            f"Foreground: {title.foreground or '(unknown)'}",
            f"Background: {title.background or '(unknown)'}",
            f"Direction: {title.direction if title.direction is not None else '(unknown)'}",
            f"Speed: {title.speed if title.speed is not None else '(unknown)'}",
            f"Font size scale: {title.font_size_scale if title.font_size_scale is not None else '(unknown)'}",
            f"Hang time: {title.hang_time if title.hang_time is not None else '(unknown)'}",
            f"Over black: {title.over_black if title.over_black is not None else '(unknown)'}",
            f"TV safe: {title.tv_safe if title.tv_safe is not None else '(unknown)'}",
            f"Raw title info: {title.raw_title_info or '(none)'}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def collect_audio(data: dict[str, Any], converted_dir: Path, *, allow_missing: bool) -> list[AudioPlan]:
    plans: list[AudioPlan] = []
    for index, item in enumerate(data.get("music") or [], start=1):
        source_text = item.get("resolved_media")
        if not source_text:
            continue
        source = Path(source_text)
        exists = source.exists()
        if not exists and not allow_missing:
            raise SystemExit(f"Required soundtrack media is missing: {source}")
        probe = probe_media(source) if exists else Probe(path=str(source), error="missing")
        info = item.get("audio_info") or []
        # iMovie HD stores [timeline start in frames, duration in seconds, source start in seconds].
        timeline_start = int(round(float(info[0]))) if len(info) > 0 and info[0] is not None else 0
        duration_seconds = float(info[1]) if len(info) > 1 and info[1] is not None else (probe.duration_seconds or 0)
        source_start_seconds = float(info[2]) if len(info) > 2 and info[2] is not None else 0.0
        duration_frames = max(1, int(round(duration_seconds * FPS)))
        source_start_frame = max(0, int(round(source_start_seconds * FPS)))
        stem = safe_name(source.stem if source.suffix else source.name)
        digest = hashlib.sha1(str(source).encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
        output = converted_dir / f"{stem}-{digest}-audio.wav"
        plans.append(AudioPlan(
            source=str(source),
            output=str(output),
            asset_name=str(item.get("name") or source.stem or f"Soundtrack {index}"),
            uid=stable_uid("audio:" + str(source.resolve() if exists else source)),
            timeline_start_frame=timeline_start,
            source_start_frame=source_start_frame,
            duration_frames=duration_frames,
            probe=asdict(probe),
            status="missing" if not exists else "planned",
        ))
    return plans


def convert_audio_plans(plans: list[AudioPlan], *, force: bool) -> None:
    for index, plan in enumerate(plans, start=1):
        source = Path(plan.source)
        output = Path(plan.output)
        if plan.status == "missing":
            print(f"[audio {index}/{len(plans)}] MISSING {source}", file=sys.stderr)
            continue
        if output.exists() and not force:
            plan.status = "reused"
            print(f"[audio {index}/{len(plans)}] Reusing {output.name}")
            continue
        probe = Probe(**plan.probe)
        if not probe.has_audio:
            plan.status = "unsupported"
            print(f"[audio {index}/{len(plans)}] No audio stream; skipping {source}", file=sys.stderr)
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(".partial.wav")
        temp.unlink(missing_ok=True)
        print(f"[audio {index}/{len(plans)}] Converting {source.name} -> {output.name}")
        cmd = [
            "ffmpeg", "-hide_banner", "-y", "-i", str(source),
            "-map", "0:a:0", "-vn", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
            str(temp),
        ]
        try:
            run(cmd)
            os.replace(temp, output)
            preserve_file_dates(source, output)
            plan.status = "converted"
        except subprocess.CalledProcessError:
            temp.unlink(missing_ok=True)
            plan.status = "failed"
            raise SystemExit(f"Soundtrack conversion failed: {source}")


def indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + "    " * level
    child_pad = "\n" + "    " * (level + 1)
    if len(element):
        if not element.text or not element.text.strip():
            element.text = child_pad
        for child in element:
            indent(child, level + 1)
        if not element[-1].tail or not element[-1].tail.strip():
            element[-1].tail = pad
    if level and (not element.tail or not element.tail.strip()):
        element.tail = pad


def build_fcpxml(data: dict[str, Any], by_source: dict[str, MediaPlan], audio_plans: list[AudioPlan], project_name: str, event_name: str) -> ET.Element:
    timeline = data["timeline"]
    total_frames = max(
        (int(x.get("timeline_start_frame") or 0) + int(x.get("frames") or 0) for x in timeline),
        default=0,
    )
    audio_end_frames = max((a.timeline_start_frame + a.duration_frames for a in audio_plans if a.status not in {"missing", "unsupported", "failed"}), default=0)
    total_frames = max(total_frames, audio_end_frames)
    if total_frames <= 0:
        raise SystemExit("Timeline has zero duration")

    root = ET.Element("fcpxml", {"version": FCPXML_VERSION})
    resources = ET.SubElement(root, "resources")
    format_id = "r1"
    ET.SubElement(resources, "format", {
        "id": format_id,
        "name": "FFVideoFormatPAL",
        "frameDuration": FRAME_DURATION,
        "width": "720",
        "height": "576",
        "fieldOrder": "lower first",
        "colorSpace": "1-1-1 (Rec. 709)",
    })

    resource_refs: dict[str, str] = {}
    next_id = 2
    for source, plan in by_source.items():
        if plan.status in {"missing", "unsupported", "failed"}:
            continue
        output = Path(plan.output)
        if not output.exists():
            continue
        rid = f"r{next_id}"
        next_id += 1
        resource_refs[source] = rid
        converted_probe = probe_media(output)
        duration_frames = max(
            plan.max_required_frame,
            round((converted_probe.duration_seconds or 0) * FPS),
            1,
        )
        attrs = {
            "id": rid,
            "name": browser_asset_name(project_name, plan.asset_name),
            "start": "0s",
            "duration": frame_time(duration_frames),
            "hasVideo": "1",
            "format": format_id,
            "videoSources": "1",
        }
        if converted_probe.has_audio:
            attrs.update({
                "hasAudio": "1",
                "audioSources": "1",
                "audioChannels": str(converted_probe.audio_channels or 2),
                "audioRate": str(converted_probe.audio_rate or 48000),
            })
        asset = ET.SubElement(resources, "asset", attrs)
        ET.SubElement(asset, "media-rep", {
            "kind": "original-media",
            "sig": plan.uid,
            "src": file_url(output),
        })

    audio_refs: dict[str, str] = {}
    for plan in audio_plans:
        if plan.status in {"missing", "unsupported", "failed"}:
            continue
        output = Path(plan.output)
        if not output.exists():
            continue
        rid = f"r{next_id}"
        next_id += 1
        audio_refs[plan.source] = rid
        converted_probe = probe_media(output)
        duration_frames = max(plan.source_start_frame + plan.duration_frames, round((converted_probe.duration_seconds or 0) * FPS), 1)
        asset = ET.SubElement(resources, "asset", {
            "id": rid,
            "name": plan.asset_name,
            "uid": plan.uid,
            "start": "0s",
            "duration": frame_time(duration_frames),
            "hasAudio": "1",
            "audioSources": "1",
            "audioChannels": str(converted_probe.audio_channels or 2),
            "audioRate": str(converted_probe.audio_rate or 48000),
        })
        ET.SubElement(asset, "media-rep", {
            "kind": "original-media",
            "sig": plan.uid,
            "src": file_url(output),
        })

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": event_name})

    # Apple represents Browser media as asset-clip elements directly under the Event.
    # These clips and the timeline clips reference the same resource assets.
    browser_clips = 0
    for source, plan in by_source.items():
        rid = resource_refs.get(source)
        if not rid:
            continue
        output = Path(plan.output)
        if not output.exists():
            continue
        converted_probe = probe_media(output)
        duration_frames = max(
            plan.max_required_frame,
            round((converted_probe.duration_seconds or 0) * FPS),
            1,
        )
        attrs = {
            "ref": rid,
            "name": browser_asset_name(project_name, plan.asset_name),
            "duration": frame_time(duration_frames),
            "format": format_id,
            "tcFormat": "NDF",
        }
        if converted_probe.has_audio:
            attrs["audioRole"] = "dialogue"
        ET.SubElement(event, "asset-clip", attrs)
        browser_clips += 1

    for plan in audio_plans:
        rid = audio_refs.get(plan.source)
        if not rid:
            continue
        output = Path(plan.output)
        converted_probe = probe_media(output)
        duration_frames = max(plan.source_start_frame + plan.duration_frames, round((converted_probe.duration_seconds or 0) * FPS), 1)
        ET.SubElement(event, "asset-clip", {
            "ref": rid,
            "name": browser_asset_name(project_name, plan.asset_name),
            "duration": frame_time(duration_frames),
            "tcFormat": "NDF",
            "audioRole": "music",
        })
        browser_clips += 1

    if browser_clips == 0:
        raise SystemExit("No Event Browser clips could be emitted")

    project = ET.SubElement(event, "project", {"name": project_name})
    sequence = ET.SubElement(project, "sequence", {
        "format": format_id,
        "duration": frame_time(total_frames),
        "tcStart": "0s",
        "tcFormat": "NDF",
        "audioLayout": "stereo",
        "audioRate": "48k",
    })
    ET.SubElement(sequence, "note").text = (
        "Stage 6.5: Event Browser media, embedded clip audio, separate soundtrack, and title metadata inventory restored. Rendered transitions, effects, and title clips are preserved as media."
    )
    spine = ET.SubElement(sequence, "spine")

    emitted = 0
    first_timeline_clip: ET.Element | None = None
    for item in timeline:
        source = item.get("resolved_media")
        rid = resource_refs.get(source)
        frames = int(item.get("frames") or 0)
        if not rid or frames <= 0:
            continue
        attrs = {
            "ref": rid,
            "offset": frame_time(item.get("timeline_start_frame")),
            "name": str(item.get("name") or Path(source).name),
            "start": frame_time(item.get("in_frame")),
            "duration": frame_time(frames),
            "format": format_id,
            "tcFormat": "NDF",
        }
        converted_probe = probe_media(Path(by_source[source].output))
        if converted_probe.has_audio:
            attrs["audioRole"] = "dialogue"
        clip_element = ET.SubElement(spine, "asset-clip", attrs)
        if first_timeline_clip is None:
            first_timeline_clip = clip_element
        emitted += 1

    if emitted == 0:
        raise SystemExit("No timeline clips could be emitted")

    # Connected soundtrack clips use absolute sequence offsets and sit below the primary storyline.
    # Attaching them to the first primary clip is the standard FCPXML representation for connected media.
    connected_audio = 0
    if first_timeline_clip is not None:
        for plan in audio_plans:
            rid = audio_refs.get(plan.source)
            if not rid:
                continue
            attrs = {
                "ref": rid,
                "lane": "-1",
                "offset": frame_time(plan.timeline_start_frame),
                "name": plan.asset_name,
                "start": frame_time(plan.source_start_frame),
                "duration": frame_time(plan.duration_frames),
                "tcFormat": "NDF",
                "audioRole": "music",
            }
            ET.SubElement(first_timeline_clip, "asset-clip", attrs)
            connected_audio += 1

    # Match the useful default browser collections from a Final Cut export.
    sc = ET.SubElement(library, "smart-collection", {"name": "Projects", "match": "all"})
    ET.SubElement(sc, "match-clip", {"rule": "is", "type": "project"})
    sc = ET.SubElement(library, "smart-collection", {"name": "All Video", "match": "any"})
    ET.SubElement(sc, "match-media", {"rule": "is", "type": "videoOnly"})
    ET.SubElement(sc, "match-media", {"rule": "is", "type": "videoWithAudio"})
    sc = ET.SubElement(library, "smart-collection", {"name": "Audio Only", "match": "all"})
    ET.SubElement(sc, "match-media", {"rule": "is", "type": "audioOnly"})

    indent(root)
    return root


def write_xml(root: ET.Element, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent, prefix=".fcpxml-") as temp:
        temp.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n')
        ET.ElementTree(root).write(temp, encoding="utf-8", xml_declaration=False)
        temp.write(b"\n")
        temp_path = Path(temp.name)
    os.replace(temp_path, path)


def validate_result(xml_path: Path, plans: list[MediaPlan], audio_plans: list[AudioPlan]) -> list[str]:
    errors: list[str] = []
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as exc:
        return [f"XML is not well formed: {exc}"]
    root = tree.getroot()
    if root.tag != "fcpxml" or root.get("version") != FCPXML_VERSION:
        errors.append("Unexpected FCPXML root/version")
    clips = root.findall("./library/event/project/sequence/spine/asset-clip")
    if not clips:
        errors.append("No asset clips in sequence spine")
    browser_clips = root.findall("./library/event/asset-clip")
    if not browser_clips:
        errors.append("No asset clips directly inside Event for Browser population")
    resource_ids = {asset.get("id") for asset in root.findall("./resources/asset")}
    for clip in browser_clips + clips:
        if clip.get("ref") not in resource_ids:
            errors.append(f"Clip {clip.get('name')} references missing asset {clip.get('ref')}")
    for asset in root.findall("./resources/asset"):
        reps = asset.findall("media-rep")
        if len(reps) != 1 or not reps[0].get("src"):
            errors.append(f"Asset {asset.get('id')} has invalid media-rep")
    connected = root.findall("./library/event/project/sequence/spine/asset-clip/asset-clip")
    expected_connected = sum(1 for p in audio_plans if p.status in {"converted", "reused"})
    if expected_connected and len(connected) < expected_connected:
        errors.append("Expected connected soundtrack clips were not emitted")
    for plan in plans:
        if plan.status in {"converted", "reused"} and not Path(plan.output).exists():
            errors.append(f"Converted file missing: {plan.output}")
    for plan in audio_plans:
        if plan.status in {"converted", "reused"} and not Path(plan.output).exists():
            errors.append(f"Converted soundtrack missing: {plan.output}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcode iMovie HD timeline media and write Apple-style Event and timeline FCPXML 1.14"
    )
    parser.add_argument("timeline_json", type=Path, help="JSON produced by imoviehd_parser.py")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output folder; use the existing Stage 3 folder to reuse converted media")
    parser.add_argument("--project-name", help="Final Cut project name")
    parser.add_argument("--event-name", help="Final Cut Event name (defaults to project name)")
    parser.add_argument("--force", action="store_true", help="Reconvert existing outputs")
    parser.add_argument("--plan-only", action="store_true", help="Probe and write manifest only")
    parser.add_argument("--allow-missing", action="store_true", help="Continue while listing missing media")
    args = parser.parse_args()

    require_tools()
    data = load_timeline(args.timeline_json)
    source_name = Path(data.get("source") or args.timeline_json.stem).stem
    project_name = args.project_name or source_name or "iMovie HD Project"
    event_name = args.event_name or project_name
    output_dir = args.output_dir.expanduser().resolve()
    converted_dir = output_dir / "Converted Media"
    xml_path = output_dir / f"{safe_name(project_name)}-v1.fcpxml"
    title_report_path = output_dir / "title-inventory.txt"
    manifest_path = output_dir / "conversion-manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    plans, by_source = collect_media(data, converted_dir, allow_missing=args.allow_missing)
    audio_plans = collect_audio(data, converted_dir, allow_missing=args.allow_missing)
    title_plans = collect_titles(data)
    write_title_report(title_report_path, project_name, title_plans)
    manifest_path.write_text(json.dumps({
        "stage": "1.0-alpha",
        "project": project_name,
        "event": event_name,
        "timestamp_policy": "QuickTime creation_time + filesystem modified date; macOS creation date when SetFile is available",
        "timeline_json": str(args.timeline_json.expanduser().resolve()),
        "media": [asdict(p) for p in plans],
        "soundtrack": [asdict(p) for p in audio_plans],
        "titles": [asdict(p) for p in title_plans],
    }, indent=2), encoding="utf-8")

    print(f"Media assets: {len(plans)}")
    print(f"Separate soundtrack items: {len(audio_plans)}")
    print(f"Title items: {len(title_plans)}")
    print(f"Title inventory: {title_report_path}")
    print(f"Manifest: {manifest_path}")
    if args.plan_only:
        print("Plan-only mode: no media converted and no FCPXML written.")
        return

    convert_plans(plans, force=args.force)
    convert_audio_plans(audio_plans, force=args.force)
    # Rewrite manifest with conversion outcomes.
    manifest_path.write_text(json.dumps({
        "stage": "1.0-alpha",
        "project": project_name,
        "event": event_name,
        "timestamp_policy": "QuickTime creation_time + filesystem modified date; macOS creation date when SetFile is available",
        "timeline_json": str(args.timeline_json.expanduser().resolve()),
        "media": [asdict(p) for p in plans],
        "soundtrack": [asdict(p) for p in audio_plans],
        "titles": [asdict(p) for p in title_plans],
    }, indent=2), encoding="utf-8")

    root = build_fcpxml(data, by_source, audio_plans, project_name, event_name)
    write_xml(root, xml_path)
    errors = validate_result(xml_path, plans, audio_plans)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)

    converted = sum(p.status == "converted" for p in plans)
    reused = sum(p.status == "reused" for p in plans)
    skipped = sum(p.status in {"missing", "unsupported", "failed"} for p in plans)
    audio_converted = sum(p.status == "converted" for p in audio_plans)
    audio_reused = sum(p.status == "reused" for p in audio_plans)
    audio_skipped = sum(p.status in {"missing", "unsupported", "failed"} for p in audio_plans)
    print("\niMovieHD2FCP v1.0 alpha complete")
    print(f"Video converted: {converted}; reused: {reused}; skipped: {skipped}")
    print(f"Soundtrack converted: {audio_converted}; reused: {audio_reused}; skipped: {audio_skipped}")
    browser_count = len(root.findall("./library/event/asset-clip"))
    timeline_count = len(root.findall("./library/event/project/sequence/spine/asset-clip"))
    audio_count = sum(
        1 for asset in root.findall("./resources/asset") if asset.get("hasAudio") == "1"
    )
    connected_count = len(root.findall("./library/event/project/sequence/spine/asset-clip/asset-clip"))
    print(f"Browser clips: {browser_count}; timeline clips: {timeline_count}; audio assets: {audio_count}; connected soundtrack clips: {connected_count}")
    print(f"Titles inventoried: {len(title_plans)}")
    print(f"Title inventory: {title_report_path}")
    print(f"FCPXML: {xml_path}")
    print("Import this XML in Final Cut Pro with File > Import > XML.")


if __name__ == "__main__":
    main()
