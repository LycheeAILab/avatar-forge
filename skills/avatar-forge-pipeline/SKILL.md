---
name: avatar-forge-pipeline
description: Create a finished talking-avatar video from a portrait, reference voice, and script. Use when Codex should authenticate with LycheeAILab, clone and synthesize speech with MiMo, drive a digital human with InfiniteTalk, resume a RunningHub task, or package the result with the bundled HyperFrames masked-video template.
---

# Avatar Forge Pipeline

## Run the complete workflow

1. Confirm that the user is authorized to use the portrait, reference voice, and script.
2. Require three inputs: one portrait image, one WAV/MP3 reference voice, and a UTF-8 script file.
3. Run the login check. If no valid local Lab API Key exists, let the helper open the LycheeAILab login/registration page. Never ask the user for provider credentials.
4. Submit the three inputs to the protected Lab gateway. The gateway performs MiMo voice cloning and speech synthesis, then sends the portrait and generated speech to InfiniteTalk on RunningHub.
5. Poll the returned task ID until `SUCCESS` or `FAILED`. Resume the same task after interruption; never create a duplicate paid task.
6. Download the raw digital-human MP4 and render it through the bundled HyperFrames mouthpiece template. Return the packaged MP4 and retain the raw MP4 beside it.

```powershell
python scripts/run_pipeline.py `
  --image input/person.png `
  --voice input/reference.wav `
  --script-file input/script.txt `
  --output output/final-mouthpiece.mp4
```

Use `--skip-hyperframes` only when the user explicitly wants the raw InfiniteTalk result. When resuming, pass both `--resume-task-id TASK_ID` and the original `--script-file` so the final captions can be rebuilt without another paid submission.

## Authenticate safely

Avatar Forge is an Agent Skill, not a web application. Run:

```powershell
python scripts/run_pipeline.py --login-only
```

The browser login occurs on `https://lab.lycheeai.com.cn`. A randomized `127.0.0.1` callback receives only the signed-in user's revocable `lych_live_...` API Key. MiMo, RunningHub, HyperFrames hosting, and Tencent COS credentials remain in the encrypted server-side credential library and must never be returned, logged, or committed.

## Load references when needed

- Read [references/workflow.md](references/workflow.md) before changing stage order, inputs, or output behavior.
- Read [references/api-contracts.md](references/api-contracts.md) before changing Lab request or response handling.
- Read [references/verification-gates.md](references/verification-gates.md) before claiming that a generated video passed validation.

## Verify without spending

- `GET /api/skill-auth/me` must return 200 for a valid user API Key.
- An unauthenticated Avatar Forge request must return 401.
- Validate the bundled template and scripts without submitting a real MiMo or RunningHub job.
- Run `python scripts/scan_secrets.py .` before publishing.
- Never include portraits, voices, generated videos, API Keys, signed URLs, task payloads, or provider credentials in the open-source package.
