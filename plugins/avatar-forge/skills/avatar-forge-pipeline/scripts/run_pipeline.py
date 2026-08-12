#!/usr/bin/env python3
"""Authenticate with LycheeAILab and run Avatar Forge through its protected API."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlencode
import webbrowser
from pathlib import Path

import requests

DEFAULT_BASE_URL = "https://lab.lycheeai.com.cn"
TERMINAL = {"SUCCESS", "FAILED"}


class PipelineError(RuntimeError):
    pass


def media_type(path: Path) -> str:
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def token_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config"))
    return root / "LycheeAILab" / "avatar-forge-token.json"


def save_token(token: str) -> None:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"accessToken": token}), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_token() -> str | None:
    token = os.environ.get("LYCHEE_LAB_TOKEN")
    if token:
        return token.strip()
    try:
        return json.loads(token_path().read_text(encoding="utf-8"))["accessToken"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return None


def browser_login(base_url: str, timeout_seconds: int = 180) -> str:
    state = secrets.token_urlsafe(32)
    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/callback":
                self.send_error(404)
                return
            length = min(int(self.headers.get("Content-Length", "0")), 4096)
            fields = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
            received_state = fields.get("state", [""])[0]
            api_key = fields.get("api_key", [""])[0]
            if not secrets.compare_digest(received_state, state) or not api_key.startswith("lych_live_"):
                self.send_error(403)
                return
            result["api_key"] = api_key
            body = "<!doctype html><meta charset='utf-8'><title>Authorized</title><style>body{font-family:sans-serif;display:grid;place-items:center;height:100vh;margin:0}p{color:#555}</style><div><h2>Avatar Forge 已授权</h2><p>可以关闭此窗口并返回 Codex。</p></div><script>setTimeout(()=>window.close(),500)</script>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    server.timeout = timeout_seconds
    callback = f"http://127.0.0.1:{server.server_port}/callback"
    authorize_url = f"{base_url}/skill-auth?{urlencode({'callback': callback, 'state': state, 'skill': 'Avatar Forge'})}"
    print(f"Authorize Avatar Forge at:\n{authorize_url}", flush=True)
    webbrowser.open(authorize_url)
    server.handle_request()
    server.server_close()
    api_key = result.get("api_key")
    if not api_key:
        raise PipelineError("LycheeAILab browser authorization timed out or was rejected")
    save_token(api_key)
    return api_key


def authorized_session(base_url: str, force_login: bool = False) -> requests.Session:
    token = None if force_login else load_token()
    if not token:
        token = browser_login(base_url)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "Avatar-Forge-Skill/1.0"})
    response = session.get(f"{base_url}/api/skill-auth/me", timeout=20)
    if response.status_code == 401 and not force_login:
        token = browser_login(base_url)
        session.headers["Authorization"] = f"Bearer {token}"
        response = session.get(f"{base_url}/api/skill-auth/me", timeout=20)
    if not response.ok:
        raise PipelineError(f"LycheeAILab authorization failed (HTTP {response.status_code})")
    return session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("LYCHEE_LAB_URL", DEFAULT_BASE_URL))
    parser.add_argument("--image", type=Path)
    parser.add_argument("--voice", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--script-file", type=Path)
    parser.add_argument("--resume-task-id")
    parser.add_argument("--output", type=Path, default=Path("avatar-forge-result.mp4"))
    parser.add_argument("--raw-output", type=Path)
    parser.add_argument("--skip-hyperframes", action="store_true")
    parser.add_argument("--template-title", default="YOUR STORY")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--login-only", action="store_true")
    parser.add_argument("--force-login", action="store_true")
    parser.add_argument("--voice-only", action="store_true", help="Clone the reference voice and save a WAV without generating an avatar")
    parser.add_argument("--avatar-only", action="store_true", help="Generate an avatar from an image and an existing WAV/MP3")
    parser.add_argument("--template-only", action="store_true", help="Generate only the RunningHub template video")
    parser.add_argument("--clone-only", action="store_true", help="Clone a template video into a reusable digital human")
    parser.add_argument("--infer-only", action="store_true", help="Run a ready digital human with an existing audio file")
    parser.add_argument("--video", type=Path)
    parser.add_argument("--asset-id")
    parser.add_argument("--player-id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    session = authorized_session(base_url, args.force_login)
    if args.login_only:
        print("LycheeAILab authentication succeeded")
        return 0
    if args.voice_only:
        if args.voice is None or not args.voice.is_file() or args.script_file is None or not args.script_file.is_file():
            raise PipelineError("--voice-only requires --voice and --script-file")
        script = args.script_file.read_text(encoding="utf-8").strip()
        with args.voice.open("rb") as voice:
            response = session.post(f"{base_url}/api/avatar-forge/voice/file", files={"voice": (args.voice.name, voice, media_type(args.voice))}, data={"script": script}, timeout=300)
        if not response.ok:
            raise PipelineError(f"Voice cloning failed (HTTP {response.status_code}): {response.text[:300]}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(response.content)
        print(f"Saved cloned voice: {args.output}")
        return 0
    if args.clone_only:
        if args.video is None or not args.video.is_file():
            raise PipelineError("--clone-only requires --video")
        with args.video.open("rb") as video:
            response = session.post(f"{base_url}/api/avatar-forge/avatar/clone", files={"video": (args.video.name, video, "video/mp4")}, data={"assetId": args.asset_id or ""}, timeout=300)
        if not response.ok:
            raise PipelineError(f"Digital-human clone failed (HTTP {response.status_code}): {response.text[:300]}")
        data = response.json()
        print(json.dumps(data, ensure_ascii=False))
        return 0
    if args.infer_only:
        if args.audio is None or not args.audio.is_file() or not args.asset_id or not args.player_id:
            raise PipelineError("--infer-only requires --audio, --asset-id and --player-id")
        with args.audio.open("rb") as audio:
            response = session.post(f"{base_url}/api/avatar-forge/avatar/infer", files={"audio": (args.audio.name, audio, media_type(args.audio))}, data={"assetId": args.asset_id, "playerId": args.player_id}, timeout=300)
        if not response.ok:
            raise PipelineError(f"Digital-human inference failed (HTTP {response.status_code}): {response.text[:300]}")
        data = response.json()
        print(json.dumps(data, ensure_ascii=False))
        return 0
    if args.avatar_only or args.template_only:
        if args.image is None or not args.image.is_file() or args.audio is None or not args.audio.is_file():
            raise PipelineError("--avatar-only requires --image and --audio")
        with args.image.open("rb") as image, args.audio.open("rb") as audio:
            response = session.post(f"{base_url}/api/avatar-forge/template", files={"image": (args.image.name, image, media_type(args.image)), "audio": (args.audio.name, audio, media_type(args.audio))}, timeout=300)
        if not response.ok:
            raise PipelineError(f"Avatar submission failed (HTTP {response.status_code}): {response.text[:300]}")
        generated_payload = response.json()
        task_id = str(generated_payload.get("taskId", ""))
        if not task_id:
            raise PipelineError("Avatar generation returned no task ID")
        print(f"Submitted task {task_id}", flush=True)
    elif args.resume_task_id:
        task_id = args.resume_task_id
    elif not args.skip_hyperframes and (args.script_file is None or not args.script_file.is_file()):
        raise PipelineError("A script file is required to render the HyperFrames mouthpiece")
    else:
        for path in (args.image, args.voice, args.script_file):
            if path is None or not path.is_file():
                raise PipelineError(f"Missing input: {path}")
        script = args.script_file.read_text(encoding="utf-8").strip()
        if not script:
            raise PipelineError("Script text is empty")
        with args.image.open("rb") as image, args.voice.open("rb") as voice:
            response = session.post(
                f"{base_url}/api/avatar-forge/generate",
                files={"image": (args.image.name, image, media_type(args.image)), "voice": (args.voice.name, voice, media_type(args.voice))},
                data={"script": script},
                timeout=300,
            )
        if not response.ok:
            raise PipelineError(f"Avatar Forge submission failed (HTTP {response.status_code}): {response.text[:300]}")
        generated_payload = response.json()
        task_id = str(generated_payload.get("taskId", ""))
        if not task_id:
            raise PipelineError("Avatar Forge returned no task ID")
        print(f"Submitted task {task_id}", flush=True)

    deadline = time.monotonic() + args.timeout_seconds
    while True:
        response = session.get(f"{base_url}/api/avatar-forge/task/{task_id}", timeout=60)
        if not response.ok:
            raise PipelineError(f"Task query failed (HTTP {response.status_code}): {response.text[:300]}")
        data = response.json()
        status = str(data.get("status", "UNKNOWN"))
        print(f"task={task_id} status={status}", flush=True)
        if status in TERMINAL:
            break
        if time.monotonic() >= deadline:
            raise PipelineError(f"Timed out; resume with --resume-task-id {task_id}")
        time.sleep(args.poll_seconds)

    if status != "SUCCESS":
        raise PipelineError(data.get("errorMessage") or "Avatar Forge generation failed")
    result = next((item for item in data.get("results", []) if str(item.get("outputType", "")).lower() == "mp4"), None)
    if not result or not result.get("url"):
        raise PipelineError("Successful task returned no MP4")
    if not (args.avatar_only or args.template_only or args.resume_task_id):
        template_path = args.output.with_name(f"{args.output.stem}-template.mp4")
        with session.get(result["url"], stream=True, timeout=300) as download:
            download.raise_for_status()
            template_path.parent.mkdir(parents=True, exist_ok=True)
            with template_path.open("wb") as handle:
                for chunk in download.iter_content(1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        with template_path.open("rb") as video:
            clone = session.post(f"{base_url}/api/avatar-forge/avatar/clone", files={"video": (template_path.name, video, "video/mp4")}, data={"assetId": generated_payload.get("assetId", "")}, timeout=300)
        if not clone.ok:
            raise PipelineError(f"Digital-human clone failed (HTTP {clone.status_code}): {clone.text[:300]}")
        clone_data = clone.json()
        clone_request = clone_data["requestId"]
        while True:
            status_response = session.get(f"{base_url}/api/avatar-forge/digital-task/{clone_request}", timeout=60)
            status_response.raise_for_status()
            clone_result = status_response.json()
            if clone_result.get("event_type") == "INFER.SUCCESS":
                break
            if clone_result.get("event_type") == "INFER.FAIL":
                raise PipelineError(f"Digital-human clone failed: {clone_result}")
            time.sleep(args.poll_seconds)
        player_id = clone_result.get("body", {}).get("player_id")
        if not player_id:
            raise PipelineError("Digital-human clone returned no player_id")
        audio_url = generated_payload.get("audioUrl")
        if not audio_url:
            raise PipelineError("Complete workflow returned no generated audio URL")
        audio_path = args.output.with_name(f"{args.output.stem}-speech.wav")
        audio_download = session.get(audio_url, timeout=300)
        audio_download.raise_for_status()
        audio_path.write_bytes(audio_download.content)
        with audio_path.open("rb") as audio:
            infer = session.post(f"{base_url}/api/avatar-forge/avatar/infer", files={"audio": (audio_path.name, audio, "audio/wav")}, data={"assetId": generated_payload["assetId"], "playerId": player_id, "audioGenerationId": generated_payload.get("audioGenerationId", "")}, timeout=300)
        if not infer.ok:
            raise PipelineError(f"Digital-human inference failed (HTTP {infer.status_code}): {infer.text[:300]}")
        infer_request = infer.json()["requestId"]
        while True:
            status_response = session.get(f"{base_url}/api/avatar-forge/digital-task/{infer_request}", timeout=60)
            status_response.raise_for_status()
            infer_result = status_response.json()
            if infer_result.get("event_type") == "INFER.SUCCESS":
                break
            if infer_result.get("event_type") == "INFER.FAIL":
                raise PipelineError(f"Digital-human inference failed: {infer_result}")
            time.sleep(args.poll_seconds)
        result = {"url": infer_result.get("body", {}).get("data"), "outputType": "mp4"}
        if not result["url"]:
            raise PipelineError("Digital-human inference returned no video")
    raw_only = args.skip_hyperframes or args.avatar_only or args.template_only
    raw_output = args.output if raw_only else (args.raw_output or args.output.with_name(f"{args.output.stem}-raw.mp4"))
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    with session.get(result["url"], stream=True, timeout=300) as download:
        download.raise_for_status()
        with raw_output.open("wb") as handle:
            for chunk in download.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    print(f"Saved raw digital human: {raw_output}")
    if not raw_only:
        renderer = Path(__file__).with_name("render_mouthpiece.py")
        command = [sys.executable, str(renderer), "--video", str(raw_output), "--script-file", str(args.script_file), "--output", str(args.output), "--title", args.template_title]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            raise PipelineError(f"HyperFrames packaging failed; raw video is preserved at {raw_output}") from exc
        print(f"Saved packaged mouthpiece: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
