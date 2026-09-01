#!/usr/bin/env python3
"""Offline contract tests for the isolated DouK-derived downloader."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
HELPER = ROOT / "douk_downloader" / "download.py"
sys.path.insert(0, str(HELPER.parent))
spec = importlib.util.spec_from_file_location("avatar_forge_douk_download", HELPER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.is_allowed_douyin_url("https://v.douyin.com/example/")
assert module.is_allowed_douyin_url("https://www.douyin.com/video/7517243795256249640")
assert not module.is_allowed_douyin_url("http://v.douyin.com/example/")
assert not module.is_allowed_douyin_url("https://douyin.com.example.org/video/7517243795256249640")
assert module.extract_authorized_url("复制 https://v.douyin.com/example/ 打开抖音") == "https://v.douyin.com/example/"

detail = {
    "video": {
        "bit_rate": [
            {
                "FPS": 25,
                "bit_rate": 1000,
                "play_addr": {
                    "height": 720,
                    "width": 1280,
                    "data_size": 100,
                    "url_list": ["https://media.example/low-a", "https://media.example/low-b"],
                },
            },
            {
                "FPS": 30,
                "bit_rate": 2000,
                "play_addr": {
                    "height": 1080,
                    "width": 1920,
                    "data_size": 200,
                    "url_list": ["https://media.example/high-a", "https://media.example/high-b"],
                },
            },
        ]
    }
}
assert module.select_video_url(detail) == "https://media.example/high-b"

print("Douyin downloader contract OK: trusted URL gate and highest-quality selection work offline.")
