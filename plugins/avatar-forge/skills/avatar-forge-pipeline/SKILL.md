---
name: avatar-forge-pipeline
description: Create or edit digital-human media with composable Avatar Forge capabilities. Use when Codex should choose a public avatar, animate an authorized portrait, match lip movement for an existing video, clone or synthesize an authorized voice, resume a generation task, or combine selected stages into a packaged talking-avatar video with HyperFrames or ChatCut.
---

# Avatar Forge

## Compose only what the user needs

Do not force every request through the full portrait + voice + script pipeline. First identify the requested outcome and select only the relevant modules:

1. **Public avatar** — choose a suitable public digital-human model and generate speech-driven video.
2. **Portrait animation** — turn one authorized portrait plus speech audio into a digital-human video.
3. **Existing-video lip sync** — match an existing authorized video to supplied or synthesized speech; preserve the source video unless the user requests other edits.
4. **Voice clone / speech synthesis** — use one authorized reference voice and a script to produce speech audio without requiring an image or video.
5. **Video packaging** — package an existing digital-human video with HyperFrames or ChatCut; do not regenerate the avatar.
6. **Complete creation** — combine only the modules needed for an end-to-end result.

Ask for missing inputs module by module. Never require a portrait for voice-only work, a reference voice when the user already has usable speech audio, or regeneration when the user already has a video.

Before a paid or irreversible external submission, summarize the selected modules, inputs, expected outputs, and possible charge, then obtain the user's confirmation.

## Mandatory portrait check

Before accepting or submitting any portrait-driven task, show this notice and obtain confirmation:

> 请确认人物脸部清晰、没有遮挡、完整露出，且人物在画面中的比例适中。模糊、遮脸、面部超出画面或人物过大/过小都会影响数字人效果。

Inspect the image when possible. Confirm all of the following:

- exactly one intended primary person;
- face is sharp enough to identify facial features;
- eyes, nose, mouth, jawline, and full face are visible;
- no hands, hair, masks, glasses glare, objects, or crop obscure important facial areas;
- head and body are not cut off in a way that conflicts with the requested framing;
- subject scale is moderate, with useful space around the head and body;
- image is not severely tilted, distorted, underexposed, or overexposed.

If any item is doubtful, explain the specific issue and ask for a better image. Do not submit merely because a file exists. If inspection is unavailable, ask the user to explicitly confirm the notice.

## Authenticate safely

Run `python scripts/run_pipeline.py --login-only` when authentication is needed. The browser login occurs on `https://lab.lycheeai.com.cn`; never ask the user for provider credentials.

Use only documented LycheeAILab endpoints. Read [references/api-contracts.md](references/api-contracts.md) before making a request. If a requested standalone module is not exposed by the installed client contract, do not invent an endpoint or silently run the full pipeline. Explain the limitation and use the current LycheeAILab product entry that exposes that capability, or ask the user whether to use an available composition.

## Execute and resume

For the currently documented complete creation route:

```powershell
python scripts/run_pipeline.py `
  --image input/person.png `
  --voice input/reference.wav `
  --script-file input/script.txt `
  --output output/final-mouthpiece.mp4
```

Use `--skip-hyperframes` for a raw digital-human result. Resume an interrupted paid task with its original task ID instead of submitting a duplicate.

For packaging only, use `scripts/render_mouthpiece.py` with the user's existing video and script; do not invoke avatar generation.

## Load references when needed

- Read [references/workflow.md](references/workflow.md) to select and compose modules.
- Read [references/api-contracts.md](references/api-contracts.md) before calling LycheeAILab.
- Read [references/verification-gates.md](references/verification-gates.md) before claiming output quality.

## Safety and publishing

- Confirm authorization for every portrait, video, voice, and script.
- Never expose or commit API keys, provider credentials, user media, task payloads, or signed URLs.
- Run `python scripts/scan_secrets.py .` before publishing.
