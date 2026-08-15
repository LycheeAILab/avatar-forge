#!/usr/bin/env python3
"""Exercise the complete workflow without calling any real provider or paid API."""

from __future__ import annotations

import importlib.util
from hashlib import sha256
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_pipeline.py")
SPEC = importlib.util.spec_from_file_location("avatar_forge_run_pipeline", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load run_pipeline.py")
PIPELINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PIPELINE)


class FakeResponse:
    def __init__(self, *, payload=None, content: bytes = b"", status_code: int = 200):
        self._payload = payload
        self.content = content
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.text = "" if payload is None else str(payload)

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, _size: int):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeSession:
    def __init__(self):
        self.posts: list[str] = []
        self.template_audio_name: str | None = None
        self.template_audio_sha256: str | None = None

    def post(self, url: str, **kwargs):
        self.posts.append(url)
        if url.endswith("/api/avatar-forge/template"):
            audio_name, audio_source, _media_type = kwargs["files"]["audio"]
            self.template_audio_name = audio_name
            position = audio_source.tell()
            self.template_audio_sha256 = sha256(audio_source.read()).hexdigest()
            audio_source.seek(position)
            return FakeResponse(payload={"assetId": "asset-1", "taskId": "template-1"})
        if url.endswith("/api/avatar-forge/voice/file"):
            return FakeResponse(content=b"MIMO_TARGET_AUDIO")
        if url.endswith("/api/avatar-forge/avatar/clone"):
            return FakeResponse(payload={"requestId": "clone-1"})
        if url.endswith("/api/avatar-forge/avatar/infer"):
            return FakeResponse(payload={"inferenceId": "infer-1", "requestId": "zeroshot-1"})
        raise AssertionError(f"Unexpected POST {url}")

    def get(self, url: str, **_kwargs):
        if url.endswith("/api/avatar-forge/task/template-1"):
            return FakeResponse(payload={"status": "SUCCESS", "results": [{"outputType": "mp4", "url": "https://internal.invalid/template.mp4"}]})
        if url.endswith("/api/avatar-forge/digital-task/clone-1"):
            return FakeResponse(payload={"event_type": "INFER.SUCCESS", "body": {"player_id": "player-1"}})
        if url.endswith("/api/avatar-forge/digital-task/zeroshot-1"):
            return FakeResponse(payload={"event_type": "INFER.SUCCESS", "body": {"data": "https://final.invalid/zeroshot.mp4"}})
        if url == "https://internal.invalid/template.mp4":
            return FakeResponse(content=b"INTERNAL_TEMPLATE_MUST_NOT_BE_DELIVERED")
        if url == "https://final.invalid/zeroshot.mp4":
            return FakeResponse(content=b"ZEROSHOT_FINAL_ONLY")
        raise AssertionError(f"Unexpected GET {url}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="avatar-forge-contract-") as directory:
        root = Path(directory)
        image = root / "portrait.png"
        voice = root / "voice.wav"
        script = root / "script.txt"
        output = root / "result.mp4"
        image.write_bytes(b"IMAGE")
        voice.write_bytes(b"VOICE")
        script.write_text("这是一次不产生真实费用的流程测试。", encoding="utf-8")

        fake = FakeSession()
        original_session = PIPELINE.authorized_session
        original_argv = sys.argv
        try:
            PIPELINE.authorized_session = lambda *_args, **_kwargs: fake
            sys.argv = [
                str(SCRIPT),
                "--base-url", "https://lab.test",
                "--image", str(image),
                "--voice", str(voice),
                "--script-file", str(script),
                "--output", str(output),
                "--poll-seconds", "0",
            ]
            result = PIPELINE.main()
        finally:
            PIPELINE.authorized_session = original_session
            sys.argv = original_argv

        expected_posts = [
            "https://lab.test/api/avatar-forge/template",
            "https://lab.test/api/avatar-forge/voice/file",
            "https://lab.test/api/avatar-forge/avatar/clone",
            "https://lab.test/api/avatar-forge/avatar/infer",
        ]
        assert result == 0
        assert fake.posts == expected_posts, fake.posts
        assert output.read_bytes() == b"ZEROSHOT_FINAL_ONLY"
        assert fake.template_audio_name == "template-driver.wav"
        assert fake.template_audio_sha256 == PIPELINE.FIXED_TEMPLATE_DRIVER_SHA256
        assert not (root / ".avatar-forge" / "result" / "internal-template.mp4").exists()
        assert all("/generate" not in url for url in fake.posts)

        # Repeating the exact command must resume state, not resubmit a paid stage.
        try:
            PIPELINE.authorized_session = lambda *_args, **_kwargs: fake
            sys.argv = [
                str(SCRIPT),
                "--base-url", "https://lab.test",
                "--image", str(image),
                "--voice", str(voice),
                "--script-file", str(script),
                "--output", str(output),
                "--poll-seconds", "0",
            ]
            resumed_result = PIPELINE.main()
        finally:
            PIPELINE.authorized_session = original_session
            sys.argv = original_argv
        assert resumed_result == 0
        assert fake.posts == expected_posts, "Resume unexpectedly submitted a paid task"
        assert output.read_bytes() == b"ZEROSHOT_FINAL_ONLY"
        print("No-spend pipeline test passed: only the zeroshot MP4 was delivered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
