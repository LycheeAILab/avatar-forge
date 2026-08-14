---
name: avatar-forge-pipeline
description: Create a final zeroshot talking-avatar video from a portrait, reference voice or finished audio, and script. Use when Codex should authenticate with LycheeAILab, generate target speech with MiMo, build an internal motion template, fast-clone a digital human, run zeroshot inference, or resume an interrupted avatar job.
---

# Avatar Forge Pipeline

## Enforce the delivery contract

Return only the final MP4 produced by LycheeAILab zeroshot inference unless the user explicitly requests a standalone MiMo WAV.

- Never return, present, or call a RunningHub template the final digital-human video.
- Never stop after the internal template task.
- Never use RunningHub for fast clone or zeroshot inference.
- Never expose a RunningHub URL, task ID, payload, or internal template file to the user.
- Never replace the zeroshot result with a secondary packaged render.
- Delete the local internal template after fast clone succeeds.

## Choose a capability

- Complete: portrait + reference voice + script → internal template → MiMo speech → fast clone → zeroshot MP4.
- Avatar only: portrait + finished WAV/MP3 → internal template → fast clone → zeroshot MP4.
- Zeroshot only: ready `asset_id` + `player_id` + finished WAV/MP3 → zeroshot MP4.
- Voice only: reference voice + script → MiMo WAV. Use only when the user explicitly asks for audio.

Do not offer template-only or clone-only output as a finished user deliverable.

## Run the complete workflow

1. Confirm the user is authorized to use the portrait, reference voice, and script.
2. Require one portrait image, one WAV/MP3 reference voice, and one UTF-8 script file.
3. Authenticate through LycheeAILab. Never ask for provider credentials.
4. Run the command below once. The script stores hidden recovery state beside the output and resumes the exact stage after interruption.
5. Verify that the delivered MP4 has video and audio streams and positive duration.
6. Return only the zeroshot MP4 path. For failures, report only the failed stage and a sanitized error; never expose internal provider IDs, URLs, payloads, or media.

```powershell
python scripts/run_pipeline.py `
  --image input/person.png `
  --voice input/reference.wav `
  --driver-audio input/template-driver.wav `
  --script-file input/script.txt `
  --output output/avatar-zeroshot.mp4
```

`--driver-audio` is an optional dedicated template driver and is never used as the formal target speech. If it is omitted, the reference voice is used only to provide motion timing for the internal template. The MiMo output remains the sole formal target speech passed to zeroshot.

The internal order is fixed:

1. Use the portrait and template-driving audio to create one internal motion template.
2. Use MiMo to clone the reference voice and generate the complete target speech. Scripts over the server's single-request limit are split on sentence boundaries and concatenated without dropping text.
3. Send the internal template to LycheeAILab fast clone (`v2clone`) and obtain `player_id`.
4. Send `player_id` and the MiMo target speech to LycheeAILab zeroshot inference.
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

Run `python scripts/run_pipeline.py --login-only` when authentication is needed. The browser uses `https://lab.lycheeai.com.cn`; a randomized loopback callback returns only the user's revocable Lab API Key. Provider credentials remain server-side.

## Load references when needed

- Read [references/workflow.md](references/workflow.md) before changing stage order, outputs, or recovery behavior.
- Read [references/api-contracts.md](references/api-contracts.md) before changing Lab requests.
- Read [references/verification-gates.md](references/verification-gates.md) before claiming success.

## Verify without spending

- Run `python -m py_compile scripts/run_pipeline.py scripts/test_pipeline_no_spend.py`.
- Run `python scripts/test_workflow_contract.py`, `python scripts/test_pipeline_no_spend.py`, and the secret scan.
- Do not submit a real provider task solely to test installation or documentation.
