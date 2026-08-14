#!/usr/bin/env python3
"""Static no-spend assertions for Avatar Forge's zeroshot delivery contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


require('f"{base_url}/api/avatar-forge/generate"' not in SCRIPT, "Legacy black-box generate route must not be used")
require('f"{base_url}/api/avatar-forge/template"' in SCRIPT, "Internal template stage is missing")
require('f"{base_url}/api/avatar-forge/avatar/clone"' in SCRIPT, "Fast-clone stage is missing")
require('f"{base_url}/api/avatar-forge/avatar/infer"' in SCRIPT, "Zeroshot stage is missing")

template_position = SCRIPT.index("Preparing internal motion template")
voice_position = SCRIPT.index("MiMo creates the formal target speech", template_position)
clone_position = SCRIPT.index('f"{base_url}/api/avatar-forge/avatar/clone"', voice_position)
infer_position = SCRIPT.index('f"{base_url}/api/avatar-forge/avatar/infer"', clone_position)
require(template_position < voice_position < clone_position < infer_position, "Stage order must be template -> MiMo -> v2clone -> zeroshot")

require("template_file.unlink()" in SCRIPT, "Internal template must be deleted after fast clone")
require('state["inferenceRequestId"]' in SCRIPT, "Zeroshot request ID must be saved for resume")
require("Saved zeroshot video" in SCRIPT, "The final output must be named zeroshot video")
require("template-only" not in SCRIPT, "Template-only delivery mode must not exist")
require("clone-only" not in SCRIPT, "Clone-only delivery mode must not exist")
require("package-only" not in SCRIPT, "Secondary package delivery mode must not replace zeroshot")
require("Return only the final MP4" in SKILL, "SKILL.md must enforce the zeroshot-only delivery contract")
require("RunningHub has no role after" in WORKFLOW, "Workflow must prohibit RunningHub after template creation")

print("Avatar Forge contract OK: internal template -> MiMo -> v2clone -> zeroshot; only zeroshot MP4 is delivered.")
