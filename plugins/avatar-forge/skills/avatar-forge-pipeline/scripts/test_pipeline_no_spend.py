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
        self.voice_failures_remaining = 0

    def post(self, url: str, **kwargs):
        self.posts.append(url)
        if url.endswith("/api/avatar-forge/voice/clone"):
            assert "voice" in kwargs["files"]
            return FakeResponse(payload={"requestId": "voice-clone-1", "speakerId": None, "status": "QUEUED"})
        if url.endswith("/api/avatar-forge/template"):
            audio_name, audio_source, _media_type = kwargs["files"]["audio"]
            self.template_audio_name = audio_name
            position = audio_source.tell()
            self.template_audio_sha256 = sha256(audio_source.read()).hexdigest()
            audio_source.seek(position)
            return FakeResponse(payload={"assetId": "asset-1", "taskId": "template-1"})
        if url.endswith("/api/avatar-forge/voice/file"):
            assert kwargs["data"]["speakerId"] in {"speaker-1", "voice-clone-1"}
            assert kwargs["data"]["script"] == "这是一次不产生真实费用的流程测试。"
            if self.voice_failures_remaining:
                self.voice_failures_remaining -= 1
                return FakeResponse(payload={"message": "voice is preparing"}, status_code=502)
            return FakeResponse(content=b"LYCHEE_TTS_TARGET")
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
                "--speaker-id", "speaker-1",
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
                "--speaker-id", "speaker-1",
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

        clone_fake = FakeSession()
        try:
            PIPELINE.authorized_session = lambda *_args, **_kwargs: clone_fake
            sys.argv = [str(SCRIPT), "--base-url", "https://lab.test", "--clone-voice", "--voice", str(voice)]
            clone_result = PIPELINE.main()
        finally:
            PIPELINE.authorized_session = original_session
            sys.argv = original_argv
        assert clone_result == 0
        assert clone_fake.posts == ["https://lab.test/api/avatar-forge/voice/clone"]
        clone_contract = PIPELINE.clone_voice(clone_fake, "https://lab.test", voice)
        assert clone_contract["speakerId"] == clone_contract["requestId"] == "voice-clone-1"

        voice_fake = FakeSession()
        voice_output = root / "voice-only.mp3"
        try:
            PIPELINE.authorized_session = lambda *_args, **_kwargs: voice_fake
            sys.argv = [
                str(SCRIPT), "--base-url", "https://lab.test", "--voice-only",
                "--speaker-id", "speaker-1", "--script-file", str(script), "--output", str(voice_output),
            ]
            voice_result = PIPELINE.main()
        finally:
            PIPELINE.authorized_session = original_session
            sys.argv = original_argv
        assert voice_result == 0
        assert voice_fake.posts == ["https://lab.test/api/avatar-forge/voice/file"]
        assert voice_output.read_bytes() == b"LYCHEE_TTS_TARGET"

        # A complete workflow can clone a reference voice and continue without a manual speaker ID.
        auto_fake = FakeSession()
        auto_fake.voice_failures_remaining = 1
        auto_output = root / "result-auto.mp4"
        original_sleep = PIPELINE.time.sleep
        try:
            PIPELINE.authorized_session = lambda *_args, **_kwargs: auto_fake
            PIPELINE.time.sleep = lambda *_args, **_kwargs: None
            sys.argv = [
                str(SCRIPT), "--base-url", "https://lab.test",
                "--image", str(image), "--voice", str(voice),
                "--script-file", str(script), "--output", str(auto_output),
                "--poll-seconds", "0",
            ]
            auto_result = PIPELINE.main()
        finally:
            PIPELINE.authorized_session = original_session
            PIPELINE.time.sleep = original_sleep
            sys.argv = original_argv
        assert auto_result == 0
        assert auto_fake.posts == [
            "https://lab.test/api/avatar-forge/template",
            "https://lab.test/api/avatar-forge/voice/clone",
            "https://lab.test/api/avatar-forge/voice/file",
            "https://lab.test/api/avatar-forge/voice/file",
            "https://lab.test/api/avatar-forge/avatar/clone",
            "https://lab.test/api/avatar-forge/avatar/infer",
        ]
        assert auto_output.read_bytes() == b"ZEROSHOT_FINAL_ONLY"
        print("No-spend pipeline test passed: only the zeroshot MP4 was delivered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
