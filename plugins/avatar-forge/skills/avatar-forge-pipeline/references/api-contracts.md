# Protected API contracts

## Credentials

- Every client request uses only the user's revocable LycheeAILab bearer token.
- Never request, store, or expose the LycheeTTS `api_key`. The Lab gateway reads it from the encrypted `provider_credentials` table.
- Never store credentials in the repository, command examples, logs, state files, or output.

## LycheeAILab avatar stages

Base URL: `https://lab.lycheeai.com.cn`

Person-video clone input policy: MP4, at most 100 MiB, 120 seconds, 25fps (both average and nominal rates), long edge ≤1920 and short edge ≤1080. Skill preflight and Lab server validate independently. Reject unknown/over-limit metadata; never silently trim. This is separate from the 300-second final speech limit.

- `POST /api/avatar-forge/voice/clone`: authorized reference audio in multipart field `voice`; returns `requestId`, `speakerId`, and status. For compatibility with older gateways, use `requestId` as `speakerId` when the explicit field is absent. Do not invent a clone-status endpoint.
- `POST /api/avatar-forge/voice/file`: form fields `speakerId`, `script`, `speed`, `volume`, `sampleRate`; returns downloaded LycheeTTS MP3 bytes.
- `POST /api/avatar-forge/template`: authorized portrait plus bundled fixed `assets/template-driver.wav`; returns `assetId` and `taskId`.
- `GET /api/avatar-forge/task/:taskId`: poll the internal template until `SUCCESS` or `FAILED`; never return this MP4 as the final output.
- `POST /api/avatar-forge/avatar/clone`: multipart `video`, optional `assetId`; returns `assetId`, `requestId`, status. Image mode sends internal template plus its assetId. Person-video mode sends the authorized MP4 with no assetId; Lab creates the owned asset. Persist both returned IDs before polling. Never invent an assetId or call RunningHub for this path.
- `POST /api/avatar-forge/avatar/infer`: target audio plus `assetId` and `playerId`; returns `inferenceId` and `requestId`.
- `GET /api/avatar-forge/digital-task/:requestId`: poll until `INFER.SUCCESS` or `INFER.FAIL`; `body.data` from successful final inference is the normal user-facing MP4 URL.

Do not use the legacy `/api/avatar-forge/generate` route. Never return provider credentials, internal task IDs, signed internal template URLs, or internal template media.
