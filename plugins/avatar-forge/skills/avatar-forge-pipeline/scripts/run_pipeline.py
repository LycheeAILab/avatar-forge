#!/usr/bin/env python3
"""Authenticate with LycheeAILab and create a zeroshot talking-avatar video."""

from __future__ import annotations

import argparse
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode
import webbrowser

import requests


DEFAULT_BASE_URL = "https://lab.lycheeai.com.cn"
TERMINAL_TEMPLATE = {"SUCCESS", "FAILED"}
SUCCESS_DIGITAL = "INFER.SUCCESS"
FAILED_DIGITAL = "INFER.FAIL"


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
        ".mp4": "video/mp4",
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
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "Avatar-Forge-Skill/2.0"})
    response = session.get(f"{base_url}/api/skill-auth/me", timeout=20)
    if response.status_code == 401 and not force_login:
        token = browser_login(base_url)
        session.headers["Authorization"] = f"Bearer {token}"
        response = session.get(f"{base_url}/api/skill-auth/me", timeout=20)
    if not response.ok:
        raise PipelineError(f"LycheeAILab authorization failed (HTTP {response.status_code})")
    return session


def require_json(response: requests.Response, stage: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise PipelineError(f"{stage} returned non-JSON HTTP {response.status_code}: {response.text[:300]}") from exc
    if not response.ok:
        raise PipelineError(f"{stage} failed (HTTP {response.status_code}): {json.dumps(payload, ensure_ascii=False)[:500]}")
    return payload


def download(session: requests.Session, url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with output.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    if output.stat().st_size == 0:
        raise PipelineError(f"Downloaded an empty file: {output}")


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def workflow_fingerprint(paths: list[Path], script: str) -> str:
    digest = sha256()
    for path in paths:
        digest.update(file_hash(path).encode("ascii"))
    digest.update(script.encode("utf-8"))
    return digest.hexdigest()


def split_script(script: str, limit: int = 480) -> list[str]:
    if not script:
        raise PipelineError("Script text is empty")
    sentences = [part.strip() for part in re.findall(r"[^。！？!?]+[。！？!?]?", script, flags=re.S) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > limit:
            for offset in range(0, len(sentence), limit):
                piece = sentence[offset:offset + limit]
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(piece)
            continue
        if current and len(current) + len(sentence) > limit:
            chunks.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    if "".join(chunks) != re.sub(r"\s+", "", script):
        if re.sub(r"\s+", "", "".join(chunks)) != re.sub(r"\s+", "", script):
            raise PipelineError("Script splitting changed the source text")
    return chunks


def poll_template(session: requests.Session, base_url: str, task_id: str, poll_seconds: int, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        payload = require_json(session.get(f"{base_url}/api/avatar-forge/task/{task_id}", timeout=60), "Internal template query")
        status = str(payload.get("status", "UNKNOWN"))
        print(f"Internal template status: {status}", flush=True)
        if status in TERMINAL_TEMPLATE:
            if status != "SUCCESS":
                raise PipelineError(payload.get("errorMessage") or "Internal template generation failed")
            return payload
        if time.monotonic() >= deadline:
            raise PipelineError("Internal template timed out. Re-run the same command to resume without resubmitting.")
        time.sleep(poll_seconds)


def poll_digital(session: requests.Session, base_url: str, request_id: str, stage: str, poll_seconds: int, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        payload = require_json(session.get(f"{base_url}/api/avatar-forge/digital-task/{request_id}", timeout=60), f"{stage} query")
        event = str(payload.get("event_type", "UNKNOWN"))
        print(f"{stage} status: {event}", flush=True)
        if event == SUCCESS_DIGITAL:
            return payload
        if event == FAILED_DIGITAL:
            raise PipelineError(f"{stage} failed: {json.dumps(payload, ensure_ascii=False)[:700]}")
        if time.monotonic() >= deadline:
            raise PipelineError(f"{stage} timed out. Re-run the same command to resume without resubmitting.")
        time.sleep(poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("LYCHEE_LAB_URL", DEFAULT_BASE_URL))
    parser.add_argument("--image", type=Path)
    parser.add_argument("--voice", type=Path)
    parser.add_argument("--driver-audio", type=Path, help="Optional dedicated audio used only to create the internal motion template")
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--script-file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("avatar-forge-zeroshot.mp4"))
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--login-only", action="store_true")
    parser.add_argument("--force-login", action="store_true")
    parser.add_argument("--reset-state", action="store_true", help="Discard the hidden recovery state and start a new paid workflow")
    parser.add_argument("--voice-only", action="store_true", help="Explicitly generate only MiMo speech")
    parser.add_argument("--avatar-only", action="store_true", help="Use a portrait and existing audio to return only the final zeroshot MP4")
    parser.add_argument("--infer-only", action="store_true", help="Use an existing ready asset/player and audio to return a zeroshot MP4")
    parser.add_argument("--asset-id")
    parser.add_argument("--player-id")
    return parser.parse_args()


def generate_mimo_audio(session: requests.Session, base_url: str, voice: Path, script: str, workspace: Path, state: dict, save_state) -> Path:
    chunks = split_script(script)
    chunk_files: list[Path] = []
    generated = state.setdefault("mimoChunks", {})
    for index, chunk in enumerate(chunks, start=1):
        chunk_file = workspace / f"mimo-{index:03d}.wav"
        if str(index) not in generated or not chunk_file.is_file() or chunk_file.stat().st_size == 0:
            print(f"Generating target speech with MiMo: part {index}/{len(chunks)}", flush=True)
            with voice.open("rb") as source:
                response = session.post(
                    f"{base_url}/api/avatar-forge/voice/file",
                    files={"voice": (voice.name, source, media_type(voice))},
                    data={"script": chunk},
                    timeout=300,
                )
            if not response.ok:
                raise PipelineError(f"MiMo speech part {index} failed (HTTP {response.status_code}): {response.text[:300]}")
            chunk_file.write_bytes(response.content)
            if chunk_file.stat().st_size == 0:
                raise PipelineError(f"MiMo speech part {index} is empty")
            generated[str(index)] = {"characters": len(chunk), "file": str(chunk_file)}
            save_state()
        chunk_files.append(chunk_file)

    final_audio = workspace / "target-speech.wav"
    if len(chunk_files) == 1:
        shutil.copyfile(chunk_files[0], final_audio)
    else:
        concat_file = workspace / "mimo-concat.txt"
        concat_file.write_text("".join(f"file '{path.as_posix()}'\n" for path in chunk_files), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(final_audio)], check=True)
    if not final_audio.is_file() or final_audio.stat().st_size == 0:
        raise PipelineError("Combined MiMo target speech is empty")
    state["targetAudioReady"] = True
    save_state()
    return final_audio


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
        workspace = args.output.parent / ".avatar-forge" / f"{args.output.stem}-voice"
        workspace.mkdir(parents=True, exist_ok=True)
        state: dict = {}
        audio = generate_mimo_audio(session, base_url, args.voice, script, workspace, state, lambda: None)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(audio, args.output)
        print(f"Saved explicitly requested MiMo speech: {args.output}")
        return 0

    if args.infer_only:
        if args.audio is None or not args.audio.is_file() or not args.asset_id or not args.player_id:
            raise PipelineError("--infer-only requires --audio, --asset-id and --player-id")
        with args.audio.open("rb") as audio:
            submitted = require_json(session.post(
                f"{base_url}/api/avatar-forge/avatar/infer",
                files={"audio": (args.audio.name, audio, media_type(args.audio))},
                data={"assetId": args.asset_id, "playerId": args.player_id},
                timeout=300,
            ), "Zeroshot submission")
        result = poll_digital(session, base_url, str(submitted["requestId"]), "Zeroshot inference", args.poll_seconds, args.timeout_seconds)
        url = result.get("body", {}).get("data")
        if not url:
            raise PipelineError("Zeroshot inference returned no MP4")
        download(session, str(url), args.output)
        print(f"Saved zeroshot video: {args.output}")
        return 0

    if args.image is None or not args.image.is_file():
        raise PipelineError("A portrait --image is required")
    if args.driver_audio is not None and not args.driver_audio.is_file():
        raise PipelineError("--driver-audio does not exist")
    if args.avatar_only:
        if args.audio is None or not args.audio.is_file():
            raise PipelineError("--avatar-only requires --image and final --audio")
        driver_audio = args.driver_audio or args.audio
        target_audio = args.audio
        script = ""
        fingerprint_inputs = [args.image, driver_audio, target_audio]
    else:
        if args.voice is None or not args.voice.is_file() or args.script_file is None or not args.script_file.is_file():
            raise PipelineError("Complete workflow requires --image, --voice and --script-file")
        driver_audio = args.driver_audio or args.voice
        target_audio = None
        script = args.script_file.read_text(encoding="utf-8").strip()
        if not script:
            raise PipelineError("Script text is empty")
        fingerprint_inputs = [args.image, driver_audio, args.voice]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    workspace = args.output.parent / ".avatar-forge" / args.output.stem
    if args.reset_state and workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    state_file = workspace / "state.json"
    fingerprint = workflow_fingerprint(fingerprint_inputs, script)
    state: dict = {}
    if state_file.is_file():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("fingerprint") != fingerprint:
            raise PipelineError("Recovery state belongs to different inputs. Choose a different --output or explicitly pass --reset-state.")
    state.setdefault("fingerprint", fingerprint)
    state.setdefault("flow", ["internal-template", "mimo-target-speech" if not args.avatar_only else "existing-target-speech", "v2clone", "zeroshot"])
    state["finalOutputType"] = "zeroshot-mp4"

    def save_state() -> None:
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    save_state()

    # RunningHub is isolated to this internal template stage. Its result is never returned to the user.
    if not state.get("templateTaskId"):
        print("Preparing internal motion template", flush=True)
        with args.image.open("rb") as image, driver_audio.open("rb") as audio:
            template_submit = require_json(session.post(
                f"{base_url}/api/avatar-forge/template",
                files={
                    "image": (args.image.name, image, media_type(args.image)),
                    "audio": (driver_audio.name, audio, media_type(driver_audio)),
                },
                timeout=300,
            ), "Internal template submission")
        state["assetId"] = template_submit["assetId"]
        state["templateTaskId"] = template_submit["taskId"]
        save_state()

    template_file = workspace / "internal-template.mp4"
    if not state.get("cloneRequestId"):
        if not state.get("templateReady") or not template_file.is_file():
            template_result = poll_template(session, base_url, str(state["templateTaskId"]), args.poll_seconds, args.timeout_seconds)
            result = next((item for item in template_result.get("results", []) if str(item.get("outputType", "")).lower() == "mp4"), None)
            if not result or not result.get("url"):
                raise PipelineError("Internal template completed without an MP4")
            download(session, str(result["url"]), template_file)
            state["templateReady"] = True
            save_state()

    # MiMo creates the formal target speech only after the internal template is ready.
    if not args.avatar_only:
        target_audio = generate_mimo_audio(session, base_url, args.voice, script, workspace, state, save_state)
    assert target_audio is not None

    if not state.get("cloneRequestId"):
        print("Submitting fast digital-human clone", flush=True)
        with template_file.open("rb") as video:
            clone_submit = require_json(session.post(
                f"{base_url}/api/avatar-forge/avatar/clone",
                files={"video": (template_file.name, video, "video/mp4")},
                data={"assetId": state["assetId"]},
                timeout=300,
            ), "Fast clone submission")
        state["cloneRequestId"] = clone_submit["requestId"]
        save_state()

    if not state.get("playerId"):
        clone_result = poll_digital(session, base_url, str(state["cloneRequestId"]), "Fast clone", args.poll_seconds, args.timeout_seconds)
        player_id = clone_result.get("body", {}).get("player_id")
        if not player_id:
            raise PipelineError("Fast clone returned no player_id")
        state["playerId"] = player_id
        save_state()
    if template_file.exists():
        template_file.unlink()

    if not state.get("inferenceRequestId"):
        print("Submitting zeroshot inference", flush=True)
        with target_audio.open("rb") as audio:
            infer_submit = require_json(session.post(
                f"{base_url}/api/avatar-forge/avatar/infer",
                files={"audio": (target_audio.name, audio, media_type(target_audio))},
                data={"assetId": state["assetId"], "playerId": state["playerId"]},
                timeout=300,
            ), "Zeroshot submission")
        state["inferenceId"] = infer_submit.get("inferenceId")
        state["inferenceRequestId"] = infer_submit["requestId"]
        save_state()

    infer_result = poll_digital(session, base_url, str(state["inferenceRequestId"]), "Zeroshot inference", args.poll_seconds, args.timeout_seconds)
    final_url = infer_result.get("body", {}).get("data")
    if not final_url:
        raise PipelineError("Zeroshot inference returned no MP4")
    download(session, str(final_url), args.output)
    state["completed"] = True
    state["output"] = str(args.output)
    save_state()
    print(f"Saved zeroshot video: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PipelineError, requests.RequestException, subprocess.CalledProcessError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
