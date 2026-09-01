#!/usr/bin/env python3
"""Transcribe a local video with the optional local Faster-Whisper dependency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--segments-output", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compute-type", default="default")
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file() or video.stat().st_size == 0:
        parser.error(f"video is missing or empty: {video}")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(
            "ERROR: local transcription requires the optional dependency: "
            "python -m pip install -r requirements-transcription.txt",
            file=sys.stderr,
        )
        return 2

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments_iter, info = model.transcribe(
        str(video),
        language=None if args.language == "auto" else args.language,
        vad_filter=True,
    )
    segments = [
        {"start": round(item.start, 3), "end": round(item.end, 3), "text": item.text.strip()}
        for item in segments_iter
        if item.text.strip()
    ]
    transcript = "".join(item["text"] for item in segments).strip()
    if not transcript:
        print("ERROR: transcription produced no text", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(transcript + "\n", encoding="utf-8")
    if args.segments_output:
        args.segments_output.parent.mkdir(parents=True, exist_ok=True)
        args.segments_output.write_text(
            json.dumps(
                {"language": info.language, "duration": info.duration, "segments": segments},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
