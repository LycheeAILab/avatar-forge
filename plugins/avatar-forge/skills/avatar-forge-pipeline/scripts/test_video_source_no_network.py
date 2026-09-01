#!/usr/bin/env python3
"""Verify local-video preparation without network access or provider spending."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).resolve().with_name("prepare_video_source.py")


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "reference.mp4"
    output = root / "stable" / "reference.mp4"
    source.write_bytes(b"local-video-contract-test")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--video", str(source), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(result.stdout)
    assert payload["sourceType"] == "local"
    assert Path(payload["video"]) == output.resolve()
    assert output.read_bytes() == source.read_bytes()

print("Video source contract OK: local upload resolves and copies without network access.")
