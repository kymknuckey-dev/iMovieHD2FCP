#!/usr/bin/env python3
"""Create a first-pass Final Cut Pro XML file from iMovie HD parser JSON."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

FPS = 25

def t(frames: int | None) -> str:
    return f"{int(frames or 0)}/25s"

def file_url(path: Path) -> str:
    return "file://" + quote(str(path.expanduser().resolve()), safe="/:")

def probe_frames(path: Path) -> int | None:
    try:
        p = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ], check=True, capture_output=True, text=True)
        return max(1, round(float(p.stdout.strip()) * FPS))
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None

def indent(el: ET.Element, level: int = 0) -> None:
    i = "\n" + "  " * level
    j = "\n" + "  " * (level + 1)
    if len(el):
        if not el.text or not el.text.strip(): el.text = j
        for child in el: indent(child, level + 1)
        if not el[-1].tail or not el[-1].tail.strip(): el[-1].tail = i
    if level and (not el.tail or not el.tail.strip()): el.tail = i

def load(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f: data = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Timeline JSON does not exist: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON: {e}")
    if not isinstance(data.get("timeline"), list):
        raise SystemExit("JSON has no timeline list")
    return data

def build(data: dict, project_name: str) -> ET.Element:
    timeline = data.get("timeline", [])
    music = data.get("music", [])
    total = max((int(x.get("timeline_start_frame") or 0) + int(x.get("frames") or 0) for x in timeline), default=0)
    if total <= 0: raise SystemExit("Timeline has no duration")

    root = ET.Element("fcpxml", {"version": "1.10"})
    resources = ET.SubElement(root, "resources")
    fmt = "r1"
    ET.SubElement(resources, "format", {
        "id": fmt, "name": "FFVideoFormatPAL", "frameDuration": "1/25s",
        "width": "720", "height": "576", "fieldOrder": "lower first"
    })

    media = {}
    for item in timeline:
        p = item.get("resolved_media")
        if p and item.get("media_exists", True):
            media.setdefault(p, {"name": item.get("name") or Path(p).name,
                                 "duration": max(int(item.get("out_frame") or 0), int(item.get("frames") or 0), 1),
                                 "video": True})
    for item in music:
        p = item.get("resolved_media")
        if p and item.get("media_exists", True):
            media.setdefault(p, {"name": item.get("name") or Path(p).name,
                                 "duration": probe_frames(Path(p)) or total,
                                 "video": False})

    refs = {}
    for n, (p, m) in enumerate(media.items(), start=2):
        rid = f"r{n}"; refs[p] = rid
        attrs = {"id": rid, "name": str(m["name"]), "src": file_url(Path(p)),
                 "start": "0s", "duration": t(m["duration"]), "hasAudio": "1",
                 "audioSources": "1", "audioChannels": "2", "audioRate": "48k"}
        if m["video"]:
            attrs.update({"format": fmt, "hasVideo": "1"})
        ET.SubElement(resources, "asset", attrs)

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": "iMovie HD Imports"})
    project = ET.SubElement(event, "project", {"name": project_name})
    sequence = ET.SubElement(project, "sequence", {
        "format": fmt, "duration": t(total), "tcStart": "0s", "tcFormat": "NDF",
        "audioLayout": "stereo", "audioRate": "48k"
    })
    spine = ET.SubElement(sequence, "spine")
    first = None
    for item in timeline:
        p = item.get("resolved_media")
        if not p or p not in refs:
            print(f"Warning: skipped {item.get('name','Unnamed')}", file=sys.stderr); continue
        dur = int(item.get("frames") or 0)
        if dur <= 0: continue
        clip = ET.SubElement(spine, "asset-clip", {
            "name": str(item.get("name") or Path(p).name), "ref": refs[p],
            "offset": t(item.get("timeline_start_frame")), "start": t(item.get("in_frame")),
            "duration": t(dur), "format": fmt, "tcFormat": "NDF", "audioRole": "dialogue"
        })
        if first is None: first = clip

    if first is not None:
        for item in music:
            p = item.get("resolved_media")
            if not p or p not in refs: continue
            dur = min(probe_frames(Path(p)) or total, total)
            ET.SubElement(first, "asset-clip", {
                "name": str(item.get("name") or Path(p).name), "ref": refs[p], "lane": "-1",
                "offset": "0s", "start": t(item.get("in_frame")), "duration": t(dur),
                "audioRole": "music"
            })
    indent(root)
    return root

def main() -> None:
    ap = argparse.ArgumentParser(description="Convert iMovie HD timeline JSON to first-pass FCPXML")
    ap.add_argument("timeline_json", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--project-name")
    args = ap.parse_args()
    data = load(args.timeline_json)
    source = Path(data.get("source") or args.timeline_json.stem)
    name = args.project_name or (source.stem if source.suffix == ".iMovieProj" else source.name) or "iMovie HD Project"
    out = args.output or Path("output") / f"{name}.fcpxml"
    out.parent.mkdir(parents=True, exist_ok=True)
    root = build(data, name)
    with out.open("wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n')
        ET.ElementTree(root).write(f, encoding="utf-8", xml_declaration=False)
        f.write(b"\n")
    print(f"Wrote FCPXML: {out.resolve()}")
    print("Import in Final Cut Pro with File > Import > XML")

if __name__ == "__main__": main()
