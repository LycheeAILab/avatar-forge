#!/usr/bin/env python3
"""Resolve a local video or download an authorized Douyin video with yt-dlp."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
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


def download_douyin(url: str, output: Path, browser: str | None) -> Path:
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
    if browser:
        options["cookiesfrombrowser"] = (browser,)
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            requested = info.get("requested_downloads") or []
            paths = [item.get("filepath") for item in requested if item.get("filepath")]
            paths.extend([info.get("filepath"), downloader.prepare_filename(info)])
    except DownloadError as exc:
        hint = (
            " Update yt-dlp first. If Douyin requires a login session, rerun with "
            "--cookies-from-browser edge|chrome|firefox only after the user approves local browser access."
        )
        raise SourceError(f"Douyin download failed.{hint}") from exc

    candidates = [Path(path) for path in paths if path]
    candidates.extend(sorted(output.parent.glob(f"{output.stem}.*")))
    for candidate in candidates:
        if candidate.suffix.lower() in VIDEO_SUFFIXES and candidate.is_file():
            return validate_video(candidate)
    raise SourceError("Douyin download completed but no readable video file was produced")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path, help="Uploaded or existing local video")
    source.add_argument("--douyin-url", help="Authorized Douyin share or canonical URL")
    parser.add_argument("--output", type=Path, help="Stable output path; required for Douyin")
    parser.add_argument(
        "--cookies-from-browser",
        choices=("edge", "chrome", "firefox"),
        help="Use local browser cookies only with explicit user approval",
    )
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
        video = download_douyin(args.douyin_url, args.output, args.cookies_from_browser)
        source_type = "douyin"

    print(json.dumps({"video": str(video), "sourceType": source_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
