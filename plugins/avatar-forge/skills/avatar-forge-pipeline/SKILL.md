---
name: avatar-forge-pipeline
description: Create a final zeroshot talking-avatar video or prepare its script from a reference video. Use when an agent should accept an uploaded video or authorized Douyin link, transcribe and rewrite spoken copy, authenticate with LycheeAILab, clone an authorized voice, synthesize LycheeTTS speech, build an internal motion template, fast-clone a digital human, run zeroshot inference, or resume an interrupted job.
---

# Avatar Forge Pipeline

## Enforce the delivery contract

Return only the final MP4 produced by LycheeAILab zeroshot inference unless the user explicitly requests standalone LycheeTTS audio.

- Never return, present, or call a RunningHub template the final digital-human video.
- Never stop after the internal template task.
- Never use RunningHub for fast clone or zeroshot inference.
- Never expose a RunningHub URL, task ID, payload, or internal template file to the user.
- Never replace the zeroshot result with a secondary packaged render.
- Delete the local internal template after fast clone succeeds.

## Choose a capability

- Complete: portrait + authorized reference voice or existing LycheeTTS `speaker_id` + script → internal template → target speech → fast clone → zeroshot MP4.
- Avatar only: portrait + finished WAV/MP3 → internal template → fast clone → zeroshot MP4.
- Zeroshot only: ready `asset_id` + `player_id` + finished WAV/MP3 → zeroshot MP4.
- Clone voice: authorized reference audio → LycheeTTS clone through Lab. Normalize the returned `requestId` as `speakerId` when no explicit `speakerId` is present; this is the identifier accepted by LycheeTTS inference.
- Voice only: existing `speaker_id` + script → LycheeTTS MP3 through Lab. Use only when the user explicitly asks for audio.
- Reference-video script: uploaded video or authorized Douyin URL → local video → original transcript → rewritten speaking script. Stop there unless the user asks to continue into voice or avatar generation.

Do not offer template-only or clone-only output as a finished user deliverable.

## Run the complete workflow

1. Confirm the user is authorized to use the portrait, reference voice, and script.
2. Require one portrait image, one UTF-8 script file, and either one WAV/MP3 reference voice or an existing `speaker_id`.
3. Authenticate through LycheeAILab. Never ask for provider credentials.
4. Run the command below once. The script stores hidden recovery state beside the output and resumes the exact stage after interruption.
5. Verify that the delivered MP4 has video and audio streams and positive duration.
6. Return only the zeroshot MP4 path. For failures, report only the failed stage and a sanitized error; never expose internal provider IDs, URLs, payloads, or media.

```powershell
python scripts/run_pipeline.py `
  --image input/person.png `
  --voice input/reference.wav `
  --script-file input/script.txt `
  --output output/avatar-zeroshot.mp4
```

Resolve `scripts/`, `assets/`, and `references/` relative to this `SKILL.md`. On WorkBuddy, `${CODEBUDDY_SKILL_DIR}` points to this directory; on Codex, use the installed Skill directory supplied by the host.

Always use the bundled `assets/template-driver.wav` for the internal motion template. Do not ask the user for template text or template-driving audio. Never send the user's script, reference voice, finished audio, or LycheeTTS target speech to the template stage.

Before submitting any portrait, show this notice and obtain confirmation:

> 请确认人物脸部清晰、没有遮挡、完整露出，且人物在画面中的比例适中。模糊、遮脸、面部超出画面或人物过大/过小都会影响数字人效果。

Inspect the image when possible. Reject or request a replacement when facial features are unclear, important facial areas are obscured, the face is cropped, exposure is unusable, or subject scale is unsuitable.

## Prepare a script from video

Read [references/video-recreation.md](references/video-recreation.md) before downloading, transcribing, or rewriting a reference video.

The downloader is declared in `requirements.txt`. If `python scripts/doctor.py` reports `ytDlp` missing, install that file automatically before continuing; do not require the user to locate or install a separate downloader project.

For an uploaded/local video:

```powershell
python scripts/prepare_video_source.py --video input/reference.mp4
```

For an authorized Douyin link, use the downloader installed with this Skill:

```powershell
python scripts/prepare_video_source.py `
  --douyin-url "https://v.douyin.com/..." `
  --output output/reference.mp4
```

If Douyin requires a login session, first ask for permission, then add `--cookies-from-browser edge` (or `chrome`/`firefox`). Never ask the user to paste cookies, and never print, copy, or save cookie values.

Prefer a trusted transcription tool already available to the agent. For fully local transcription, install the optional dependency only when needed and run:

```powershell
python -m pip install -r requirements-transcription.txt
python scripts/transcribe_video.py input/reference.mp4 --output output/transcript-original.txt
```

Rewrite the transcript as a new spoken script and save it separately as `script-rewritten.txt`. Preserve the original transcript, factual meaning, names, and numbers; change structure, hook, pacing, transitions, and conclusion rather than only replacing synonyms. Never fabricate claims. Ask for the desired platform, duration, audience, tone, or call to action only when those cannot be reasonably inferred.

The internal order is fixed:

1. Use the portrait and bundled fixed short audio to create one internal motion template.
2. If only a reference voice is supplied, clone it once through Lab, save the returned `requestId` as `speakerId`, then use the protected Lab voice endpoint to generate target speech. Retry transient “voice preparing” responses with bounded backoff. The client must send only the user's Lab bearer token; the LycheeTTS API Key remains encrypted in the Lab database.
3. Send the internal template to LycheeAILab fast clone (`v2clone`) and obtain `player_id`.
4. Send `player_id` and the LycheeTTS target speech to LycheeAILab zeroshot inference.

Submit a reference voice separately when cloning is needed:

```powershell
python scripts/run_pipeline.py --clone-voice --voice input/reference.wav
```

The clone response may contain only `requestId`. LycheeTTS accepts that identifier as `speakerId`; continue automatically and never ask the user to retrieve it manually. Do not invent a clone-status endpoint.
5. Download and return only the zeroshot MP4.

RunningHub is allowed only behind step 1. Steps 3 and 4 must use the LycheeAILab digital-human platform.

## Resume safely

- Re-run the same command with the same `--output`; the hidden `.avatar-forge/<output-stem>/state.json` resumes saved stages.
- Do not use `--reset-state` after a timeout unless the user explicitly authorizes a new paid workflow.
- A timeout is not failure. Query the saved template, clone, or inference ID.
- Never resubmit the internal template because fast clone or zeroshot is still processing.
- Never resubmit fast clone after `player_id` is stored.
- Never resubmit zeroshot after its request ID is stored.

## Authenticate safely

Run `python scripts/run_pipeline.py --login-only` when authentication is needed. The browser uses `https://lab.lycheeai.com.cn`; a randomized loopback callback returns only the user's revocable Lab API Key. LycheeTTS, RunningHub, and digital-human provider credentials remain server-side.

## Load references when needed

- Read [references/workflow.md](references/workflow.md) before changing stage order, outputs, or recovery behavior.
- Read [references/api-contracts.md](references/api-contracts.md) before changing Lab requests.
- Read [references/verification-gates.md](references/verification-gates.md) before claiming success.
- Read [references/video-recreation.md](references/video-recreation.md) for video acquisition, transcription, and rewriting.

## Verify without spending

- Run `python -m py_compile scripts/run_pipeline.py scripts/prepare_video_source.py scripts/transcribe_video.py scripts/test_pipeline_no_spend.py`.
- Run `python scripts/test_workflow_contract.py`, `python scripts/test_pipeline_no_spend.py`, `python scripts/test_video_source_no_network.py`, and the secret scan.
- Do not submit a real provider task solely to test installation or documentation.
