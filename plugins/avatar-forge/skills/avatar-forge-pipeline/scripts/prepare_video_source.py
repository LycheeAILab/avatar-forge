#!/usr/bin/env python3
"""Resolve a local video or download an authorized Douyin video without browser cookies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


class SourceError(RuntimeError):
    pass


def validate_video(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SourceError(f"Video file does not exist: {resolved}")
    if resolved.suffix.lower() not in VIDEO_SUFFIXES:
        raise SourceError(f"Unsupported video extension: {resolved.suffix}")
    if resolved.stat().st_size == 0:
        raise SourceError(f"Video file is empty: {resolved}")
    return resolved


def download_with_douk_direct(url: str, output: Path) -> Path:
    helper = Path(__file__).resolve().parent / "douk_downloader" / "download.py"
    result = subprocess.run(
        [sys.executable, str(helper), "--url", url, "--output", str(output)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        message = result.stderr.strip().splitlines()
        raise SourceError(message[-1] if message else "DouK direct downloader failed")
    try:
        payload = json.loads(result.stdout)
        return validate_video(Path(payload["video"]))
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SourceError("DouK direct downloader returned an invalid result") from exc


def download_with_ytdlp(url: str, output: Path) -> Path:
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError as exc:
        raise SourceError(
            "The video downloader is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    options = {
        "outtmpl": str(output.with_suffix(".%(ext)s")),
        "format": "b[ext=mp4]/b",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            requested = info.get("requested_downloads") or []
            paths = [item.get("filepath") for item in requested if item.get("filepath")]
            paths.extend([info.get("filepath"), downloader.prepare_filename(info)])
    except DownloadError as exc:
        raise SourceError("yt-dlp fallback failed") from exc

    candidates = [Path(path) for path in paths if path]
    candidates.extend(sorted(output.parent.glob(f"{output.stem}.*")))
    for candidate in candidates:
        if candidate.suffix.lower() in VIDEO_SUFFIXES and candidate.is_file():
            return validate_video(candidate)
    raise SourceError("Douyin download completed but no readable video file was produced")


def download_douyin(url: str, output: Path) -> tuple[Path, str]:
    errors = []
    try:
        return download_with_douk_direct(url, output), "douk-direct"
    except (SourceError, OSError) as exc:
        errors.append(str(exc))
    try:
        return download_with_ytdlp(url, output), "yt-dlp"
    except (SourceError, OSError) as exc:
        errors.append(str(exc))
    detail = "; ".join(item for item in errors if item)
    raise SourceError(
        "Douyin download failed in both cookie-free engines. "
        "No Edge/Chrome cookie or ChatGPT browser extension is required. "
        f"Details: {detail}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path, help="Uploaded or existing local video")
    source.add_argument("--douyin-url", help="Authorized Douyin share or canonical URL")
    parser.add_argument("--output", type=Path, help="Stable output path; required for Douyin")
    args = parser.parse_args()

    if args.video:
        video = validate_video(args.video)
        source_type = "local"
        if args.output:
            output = args.output.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            if output != video:
                shutil.copy2(video, output)
            video = validate_video(output)
    else:
        if not args.output:
            raise SourceError("--output is required with --douyin-url")
        video, engine = download_douyin(args.douyin_url, args.output)
        source_type = "douyin"

    payload = {"video": str(video), "sourceType": source_type}
    if source_type == "douyin":
        payload["engine"] = engine
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
