#!/usr/bin/env python3
"""Render a raw digital-human MP4 with the bundled HyperFrames mouthpiece template."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


class RenderError(RuntimeError):
    pass


def duration_seconds(video: Path) -> float:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        value = float(json.loads(result.stdout)["format"]["duration"])
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RenderError("Unable to read the raw video duration with ffprobe") from exc
    if value <= 0:
        raise RenderError("Raw video duration is invalid")
    return round(value, 3)


def caption_chunks(script: str, maximum: int = 18) -> list[str]:
    normalized = " ".join(script.split())
    if not normalized:
        raise RenderError("Script text is empty")
    chunks: list[str] = []
    sentences = [part.strip() for part in re.findall(r".*?(?:[。！？!?；;]|$)", normalized) if part.strip()]
    for sentence in sentences:
        while len(sentence) > maximum:
            cut = maximum
            if len(sentence) - cut < 5:
                cut = (len(sentence) + 1) // 2
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            chunks.append(sentence)
    return chunks


def prepare_project(template_dir: Path, raw_video: Path, script: str, title: str, workdir: Path) -> None:
    shutil.copytree(template_dir, workdir, dirs_exist_ok=True)
    shutil.copy2(raw_video, workdir / "avatar.mp4")
    duration = duration_seconds(raw_video)
    chunks = caption_chunks(script)
    segment = duration / len(chunks)
    timing = [
        {"start": round(index * segment, 3), "end": round(min(duration, (index + 1) * segment), 3)}
        for index in range(len(chunks))
    ]
    caption_html = "".join(f'<div id="caption-{index}" class="caption">{html.escape(text)}</div>' for index, text in enumerate(chunks))
    template = (workdir / "index.template.html").read_text(encoding="utf-8")
    rendered = (template
        .replace("__DURATION_LABEL__", f"{duration:.2f}")
        .replace("__DURATION__", str(duration))
        .replace("__TITLE__", html.escape(title))
        .replace("__CAPTION_HTML__", caption_html)
        .replace("__CAPTION_DATA__", json.dumps(timing, ensure_ascii=False)))
    (workdir / "index.html").write_text(rendered, encoding="utf-8")
    (workdir / "index.template.html").unlink()


def render(raw_video: Path, script_file: Path, output: Path, title: str, keep_project: Path | None = None) -> None:
    template_dir = Path(__file__).resolve().parent.parent / "assets" / "mouthpiece-template"
    script = script_file.read_text(encoding="utf-8").strip()
    if keep_project:
        keep_project.mkdir(parents=True, exist_ok=True)
        prepare_project(template_dir, raw_video, script, title, keep_project)
        project = keep_project
        cleanup = None
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="avatar-forge-hyperframes-")
        project = Path(cleanup.name)
        prepare_project(template_dir, raw_video, script, title, project)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["npx.cmd", "--yes", "hyperframes@0.7.105", "check"], cwd=project, check=True)
        subprocess.run(["npx.cmd", "--yes", "hyperframes@0.7.105", "render", "--output", str(output.resolve())], cwd=project, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RenderError("HyperFrames validation or rendering failed") from exc
    finally:
        if cleanup:
            cleanup.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--script-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="YOUR STORY")
    parser.add_argument("--keep-project", type=Path)
    args = parser.parse_args()
    render(args.video, args.script_file, args.output, args.title, args.keep_project)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RenderError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
