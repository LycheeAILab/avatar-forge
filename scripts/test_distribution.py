#!/usr/bin/env python3
"""Validate Codex and WorkBuddy package contracts without spending or network calls."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.2.0"
ARCHIVE = ROOT / "dist" / f"avatar-forge-workbuddy-{VERSION}.zip"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    manifest = json.loads((ROOT / "plugins/avatar-forge/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
    require(manifest["version"] == VERSION, "Codex manifest version must match release")
    require(ARCHIVE.is_file(), "WorkBuddy archive has not been built")
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = set(archive.namelist())
        required = {
            "avatar-forge-pipeline/SKILL.md",
            "avatar-forge-pipeline/VERSION",
            "avatar-forge-pipeline/requirements.txt",
            "avatar-forge-pipeline/requirements-transcription.txt",
            "avatar-forge-pipeline/scripts/run_pipeline.py",
            "avatar-forge-pipeline/scripts/doctor.py",
            "avatar-forge-pipeline/scripts/prepare_video_source.py",
            "avatar-forge-pipeline/scripts/douk_downloader/download.py",
            "avatar-forge-pipeline/scripts/douk_downloader/a_bogus.py",
            "avatar-forge-pipeline/scripts/douk_downloader/LICENSE",
            "avatar-forge-pipeline/scripts/douk_downloader/NOTICE.md",
            "avatar-forge-pipeline/scripts/transcribe_video.py",
            "avatar-forge-pipeline/assets/template-driver.wav",
            "avatar-forge-pipeline/references/workflow.md",
            "avatar-forge-pipeline/references/api-contracts.md",
            "avatar-forge-pipeline/references/verification-gates.md",
            "avatar-forge-pipeline/references/video-recreation.md",
        }
        require(required <= names, f"WorkBuddy archive is missing: {sorted(required - names)}")
        require(not any("__pycache__" in name or name.endswith(".pyc") for name in names), "Archive contains cache files")
        require(not any("agents/" in name for name in names), "WorkBuddy archive contains Codex-only agent metadata")
        skill = archive.read("avatar-forge-pipeline/SKILL.md").decode("utf-8")
        packaged_version = archive.read("avatar-forge-pipeline/VERSION").decode("utf-8").strip()
        require(packaged_version == VERSION, "WorkBuddy VERSION marker must match release")
        require("${CODEBUDDY_SKILL_DIR}" in skill, "WorkBuddy directory variable is missing")
        require("Return only the final MP4" in skill, "Final zeroshot contract is missing")
        require("RunningHub is allowed only" in skill, "RunningHub boundary is missing")
    print("Distribution OK: Codex 2.2.0 plus self-contained WorkBuddy Skill package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
