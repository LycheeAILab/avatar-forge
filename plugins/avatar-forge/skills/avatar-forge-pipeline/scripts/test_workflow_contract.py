#!/usr/bin/env python3
"""Static no-spend assertions for Avatar Forge's zeroshot delivery contract."""

from hashlib import sha256
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
FIXED_DRIVER = ROOT / "assets" / "template-driver.wav"
FIXED_DRIVER_SHA256 = "73c9cc8dde3ee0f4fe0d39b3720bbc4453ab22b3ede2a9068183d0e1c55d3d0b"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


require('f"{base_url}/api/avatar-forge/generate"' not in SCRIPT, "Legacy black-box generate route must not be used")
require('f"{base_url}/api/avatar-forge/template"' in SCRIPT, "Internal template stage is missing")
require('f"{base_url}/api/avatar-forge/avatar/clone"' in SCRIPT, "Fast-clone stage is missing")
require('f"{base_url}/api/avatar-forge/avatar/infer"' in SCRIPT, "Zeroshot stage is missing")
require("--driver-audio" not in SCRIPT, "User-selectable template-driving audio must not exist")
require('"assets" / "template-driver.wav"' in SCRIPT, "Bundled fixed template-driving audio is not wired")
require(FIXED_DRIVER.is_file(), "Bundled fixed template-driving audio is missing")
require(sha256(FIXED_DRIVER.read_bytes()).hexdigest() == FIXED_DRIVER_SHA256, "Bundled fixed template-driving audio changed")

template_position = SCRIPT.index("Preparing internal motion template")
voice_position = SCRIPT.index("LycheeTTS creates the formal target speech", template_position)
clone_position = SCRIPT.index('f"{base_url}/api/avatar-forge/avatar/clone"', voice_position)
infer_position = SCRIPT.index('f"{base_url}/api/avatar-forge/avatar/infer"', clone_position)
require(template_position < voice_position < clone_position < infer_position, "Stage order must be template -> LycheeTTS -> v2clone -> zeroshot")
require('/api/avatar-forge/voice/clone' in SCRIPT, "Protected LycheeTTS clone endpoint is missing")
require('/api/avatar-forge/voice/file' in SCRIPT, "Protected LycheeTTS inference endpoint is missing")
require("voice.lycheeai.com.cn" not in SCRIPT, "The client must not call LycheeTTS directly")
require("LYCHEE_VOICE_API_KEY" not in SCRIPT and "LYCHEE_TTS_API_KEY" not in SCRIPT, "Provider API keys must remain server-side")
require(re.search(r"sk_[A-Za-z0-9]{16,}", SCRIPT) is None, "A voice API key appears to be embedded in the client")

require("template_file.unlink()" in SCRIPT, "Internal template must be deleted after fast clone")
require('state["inferenceRequestId"]' in SCRIPT, "Zeroshot request ID must be saved for resume")
require("Saved zeroshot video" in SCRIPT, "The final output must be named zeroshot video")
require("template-only" not in SCRIPT, "Template-only delivery mode must not exist")
require("clone-only" not in SCRIPT, "Clone-only delivery mode must not exist")
require("package-only" not in SCRIPT, "Secondary package delivery mode must not replace zeroshot")
require("Return only the final MP4" in SKILL, "SKILL.md must enforce the zeroshot-only delivery contract")
require("RunningHub has no role after" in WORKFLOW, "Workflow must prohibit RunningHub after template creation")

print("Avatar Forge contract OK: fixed driver -> LycheeTTS through Lab -> v2clone -> zeroshot; only zeroshot MP4 is delivered.")
