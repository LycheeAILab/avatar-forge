#!/usr/bin/env python3
"""Run local, no-spend readiness checks for Avatar Forge."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "assets" / "template-driver.wav"
EXPECTED_DRIVER_SHA256 = "73c9cc8dde3ee0f4fe0d39b3720bbc4453ab22b3ede2a9068183d0e1c55d3d0b"


def main() -> int:
    checks = {
        "python": {
            "ok": sys.version_info >= (3, 9),
            "value": platform.python_version(),
            "required": ">=3.9",
        },
        "requests": {
            "ok": importlib.util.find_spec("requests") is not None,
            "required": "requests>=2.31,<3",
        },
        "ytDlp": {
            "ok": importlib.util.find_spec("yt_dlp") is not None,
            "required": "yt-dlp>=2025.1.1",
        },
        "pipeline": {"ok": (ROOT / "scripts" / "run_pipeline.py").is_file()},
        "videoSource": {"ok": (ROOT / "scripts" / "prepare_video_source.py").is_file()},
        "localTranscriptionScript": {"ok": (ROOT / "scripts" / "transcribe_video.py").is_file()},
        "videoRecreationGuide": {"ok": (ROOT / "references" / "video-recreation.md").is_file()},
        "templateDriver": {
            "ok": DRIVER.is_file() and sha256(DRIVER.read_bytes()).hexdigest() == EXPECTED_DRIVER_SHA256,
            "sha256": sha256(DRIVER.read_bytes()).hexdigest() if DRIVER.is_file() else None,
        },
        "skill": {"ok": (ROOT / "SKILL.md").is_file()},
    }
    optional = {
        "fasterWhisper": {
            "ok": importlib.util.find_spec("faster_whisper") is not None,
            "required": False,
            "install": "python -m pip install -r requirements-transcription.txt",
        }
    }
    ok = all(item["ok"] for item in checks.values())
    print(json.dumps({"ok": ok, "mode": "no-spend", "checks": checks, "optional": optional}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
