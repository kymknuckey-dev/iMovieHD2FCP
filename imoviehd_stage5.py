#!/usr/bin/env python3
"""iMovie HD -> modern media + import-safe FCPXML (Stage 5).

Stage 5 builds on the stable Stage 3 import. It mirrors Apple-generated FCPXML by
placing one asset-clip for every converted asset directly inside the Event, before the
Project. Timeline clips reference the same asset resources. Embedded source audio is
left to Final Cut to infer naturally. Background music, sound effects, editable
transitions, and titles remain disabled for this stage.

Requirements:
    ffmpeg and ffprobe on PATH

Example:
    python3 imoviehd_stage5.py \
      "output/Small World-timeline.json" \
      --output-dir "output/Small World Stage 5"
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

    # Stage 5 targets PAL SD. Preserve interlacing and lower-field-first DV behaviour.
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

    cmd += ["-movflags", "+faststart", str(output)]
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
            plan.status = "converted"
        except subprocess.CalledProcessError:
            temp.unlink(missing_ok=True)
            plan.status = "failed"
            raise SystemExit(f"ffmpeg conversion failed: {source}")


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


def build_fcpxml(data: dict[str, Any], by_source: dict[str, MediaPlan], project_name: str) -> ET.Element:
    timeline = data["timeline"]
    total_frames = max(
        (int(x.get("timeline_start_frame") or 0) + int(x.get("frames") or 0) for x in timeline),
        default=0,
    )
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
            "name": plan.asset_name,
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

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": "iMovie HD Imports"})

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
            "name": plan.asset_name,
            "duration": frame_time(duration_frames),
            "format": format_id,
            "tcFormat": "NDF",
        }
        if converted_probe.has_audio:
            attrs["audioRole"] = "dialogue"
        ET.SubElement(event, "asset-clip", attrs)
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
        "Stage 5: Apple-style Event Browser clips enabled; embedded clip audio preserved; background music, sound effects, titles, and editable transitions disabled."
    )
    spine = ET.SubElement(sequence, "spine")

    emitted = 0
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
        ET.SubElement(spine, "asset-clip", attrs)
        emitted += 1

    if emitted == 0:
        raise SystemExit("No timeline clips could be emitted")

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


def validate_result(xml_path: Path, plans: list[MediaPlan]) -> list[str]:
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
    for plan in plans:
        if plan.status in {"converted", "reused"} and not Path(plan.output).exists():
            errors.append(f"Converted file missing: {plan.output}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcode iMovie HD timeline media and write Apple-style Event and timeline FCPXML 1.14"
    )
    parser.add_argument("timeline_json", type=Path, help="JSON produced by imoviehd_parser.py")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output folder; use the existing Stage 3 folder to reuse converted media")
    parser.add_argument("--project-name", help="Final Cut project name")
    parser.add_argument("--force", action="store_true", help="Reconvert existing outputs")
    parser.add_argument("--plan-only", action="store_true", help="Probe and write manifest only")
    parser.add_argument("--allow-missing", action="store_true", help="Continue while listing missing media")
    args = parser.parse_args()

    require_tools()
    data = load_timeline(args.timeline_json)
    source_name = Path(data.get("source") or args.timeline_json.stem).stem
    project_name = args.project_name or source_name or "iMovie HD Project"
    output_dir = args.output_dir.expanduser().resolve()
    converted_dir = output_dir / "Converted Media"
    xml_path = output_dir / f"{safe_name(project_name)}-Stage5.fcpxml"
    manifest_path = output_dir / "conversion-manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    plans, by_source = collect_media(data, converted_dir, allow_missing=args.allow_missing)
    manifest_path.write_text(json.dumps({
        "stage": 4,
        "project": project_name,
        "timeline_json": str(args.timeline_json.expanduser().resolve()),
        "media": [asdict(p) for p in plans],
    }, indent=2), encoding="utf-8")

    print(f"Media assets: {len(plans)}")
    print(f"Manifest: {manifest_path}")
    if args.plan_only:
        print("Plan-only mode: no media converted and no FCPXML written.")
        return

    convert_plans(plans, force=args.force)
    # Rewrite manifest with conversion outcomes.
    manifest_path.write_text(json.dumps({
        "stage": 4,
        "project": project_name,
        "timeline_json": str(args.timeline_json.expanduser().resolve()),
        "media": [asdict(p) for p in plans],
    }, indent=2), encoding="utf-8")

    root = build_fcpxml(data, by_source, project_name)
    write_xml(root, xml_path)
    errors = validate_result(xml_path, plans)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)

    converted = sum(p.status == "converted" for p in plans)
    reused = sum(p.status == "reused" for p in plans)
    skipped = sum(p.status in {"missing", "unsupported", "failed"} for p in plans)
    print("\nStage 5 complete")
    print(f"Converted: {converted}; reused: {reused}; skipped: {skipped}")
    browser_count = len(root.findall("./library/event/asset-clip"))
    timeline_count = len(root.findall("./library/event/project/sequence/spine/asset-clip"))
    audio_count = sum(
        1 for asset in root.findall("./resources/asset") if asset.get("hasAudio") == "1"
    )
    print(f"Browser clips: {browser_count}; timeline clips: {timeline_count}; assets with embedded audio: {audio_count}")
    print(f"FCPXML: {xml_path}")
    print("Import this XML in Final Cut Pro with File > Import > XML.")


if __name__ == "__main__":
    main()
