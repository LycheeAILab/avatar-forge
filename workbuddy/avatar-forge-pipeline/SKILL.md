---
name: avatar-forge-pipeline
description: Create a final zeroshot talking-avatar video or prepare its script from a reference video. Use when WorkBuddy should accept an uploaded video or authorized Douyin link, transcribe and rewrite spoken copy, authenticate with LycheeAILab, clone an authorized voice, synthesize target speech, build an internal motion template, fast-clone a digital human, run zeroshot inference, or resume an interrupted job.
---

# Avatar Forge Pipeline for WorkBuddy

## Identify the installed release

Read the adjacent `VERSION` file when asked which release is installed. Report that exact value instead of inferring a version from conversation history or documentation prose. This package is release `2.1.1`.

## Keep the final-output contract

Return only the final MP4 produced by LycheeAILab zeroshot inference unless the user explicitly requests standalone LycheeTTS audio.

- RunningHub is allowed only for the internal motion-template stage.
- Never return the RunningHub template, URL, task ID, payload, or file.
- Fast clone and zeroshot inference must use the LycheeAILab digital-human platform.
- Delete the internal template after fast clone succeeds.
- Never resubmit a paid stage when a saved task can be resumed.

## Select the requested capability

- Complete: portrait + authorized reference voice or existing LycheeTTS `speaker_id` + script -> internal template -> target speech -> fast clone -> zeroshot MP4.
- Avatar only: portrait + finished WAV/MP3 -> internal template -> fast clone -> zeroshot MP4.
- Zeroshot only: ready `asset_id` + `player_id` + finished WAV/MP3 -> zeroshot MP4.
- Clone voice: authorized reference audio -> LycheeTTS clone through Lab; normalize `requestId` as `speakerId` when needed.
- Voice only: existing `speaker_id` + script -> LycheeTTS MP3 through Lab, only when explicitly requested.
- Reference-video script: uploaded video or authorized Douyin URL -> local video -> original transcript -> rewritten speaking script. Stop unless the user asks to continue.

## Run from the Skill directory

WorkBuddy exposes the installed directory as `${CODEBUDDY_SKILL_DIR}`. Use absolute paths for all user inputs and outputs.

```powershell
python "${CODEBUDDY_SKILL_DIR}/scripts/run_pipeline.py" `
  --image "C:/absolute/input/person.png" `
  --voice "C:/absolute/input/reference.wav" `
  --script-file "C:/absolute/input/script.txt" `
  --output "C:/absolute/output/avatar-zeroshot.mp4"
```

On macOS or Linux:

```bash
python3 "${CODEBUDDY_SKILL_DIR}/scripts/run_pipeline.py" \
  --image "/absolute/input/person.png" \
  --voice "/absolute/input/reference.wav" \
  --script-file "/absolute/input/script.txt" \
  --output "/absolute/output/avatar-zeroshot.mp4"
```

Before any paid stage, confirm that the user is authorized to use the portrait, voice, and script. If authentication is missing, run:

```powershell
python "${CODEBUDDY_SKILL_DIR}/scripts/run_pipeline.py" --login-only
```

The browser must open `https://lab.lycheeai.com.cn`. The randomized `127.0.0.1` callback is local-only and returns the user's revocable Lab credential to the local process; it is not a web service address.

Before uploading a portrait, show this notice and obtain confirmation:

> 请确认人物脸部清晰、没有遮挡、完整露出，且人物在画面中的比例适中。模糊、遮脸、面部超出画面或人物过大/过小都会影响数字人效果。

Inspect the image when possible. Request a replacement if the face is unclear, obscured, cropped, unusably exposed, or poorly scaled.

## Prepare a script from video

Read `references/video-recreation.md` first. For a local or uploaded video:

The WorkBuddy installer installs `requirements.txt`, including the downloader. If the doctor reports `ytDlp` missing, install that requirements file before continuing; do not require a separate downloader project.

```powershell
python "${CODEBUDDY_SKILL_DIR}/scripts/prepare_video_source.py" --video "C:/absolute/input/reference.mp4"
```

For an authorized Douyin URL:

```powershell
python "${CODEBUDDY_SKILL_DIR}/scripts/prepare_video_source.py" `
  --douyin-url "https://v.douyin.com/..." `
  --output "C:/absolute/output/reference.mp4"
```

If Douyin requires a login session, first ask for permission, then add `--cookies-from-browser edge` (or `chrome`/`firefox`). Never ask the user to paste cookies, and never print, copy, or save cookie values.

Prefer an available trusted transcription tool. For optional fully local transcription:

```powershell
python -m pip install -r "${CODEBUDDY_SKILL_DIR}/requirements-transcription.txt"
python "${CODEBUDDY_SKILL_DIR}/scripts/transcribe_video.py" "C:/absolute/input/reference.mp4" --output "C:/absolute/output/transcript-original.txt"
```

Keep `transcript-original.txt` unchanged and save the rewrite separately as `script-rewritten.txt`. Preserve facts, names, and numbers; rewrite the hook, structure, pacing, transitions, and conclusion. Never fabricate claims. Do not continue into voice or avatar generation unless the user asks.

## Preserve the fixed stage order

1. Create the internal motion template from the portrait and bundled `assets/template-driver.wav`.
2. Clone the authorized reference voice when needed and save the returned `requestId` as `speakerId`.
3. Generate the formal target speech through the protected LycheeAILab LycheeTTS endpoint.
4. Fast-clone the avatar through LycheeAILab and obtain `player_id`.
5. Run LycheeAILab zeroshot inference with `player_id` and the formal target speech.
6. Verify the MP4 has audio, video, and positive duration; return only that MP4.

Never use the user's script, reference voice, target audio, or LycheeTTS output to drive the template stage. Never ask for provider keys; the local client sends only the user's Lab credential.

## Resume instead of repeating

- Re-run the identical command and output path to resume from `.avatar-forge/<output-stem>/state.json`.
- A timeout is not a failure. Poll the saved template, clone, or inference request.
- Do not use `--reset-state` unless the user explicitly authorizes a new paid workflow.
- Do not resubmit template, fast-clone, or zeroshot stages whose task IDs are already saved.

## Verify without spending

After installation, run only the local doctor unless the user explicitly authorizes a real generation:

```powershell
python "${CODEBUDDY_SKILL_DIR}/scripts/doctor.py"
```

The doctor checks Python, `requests`, package files, and the fixed template-audio hash. It does not authenticate, upload media, or submit provider tasks.

## Read supporting contracts when needed

- Read `references/workflow.md` before changing or debugging stage order.
- Read `references/api-contracts.md` for Lab request and response fields.
- Read `references/verification-gates.md` before declaring a generated deliverable complete.
- Read `references/video-recreation.md` before downloading, transcribing, or rewriting a reference video.
