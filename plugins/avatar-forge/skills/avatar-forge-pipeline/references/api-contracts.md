# Protected API contracts

## Credentials

- Every client request uses only the user's revocable LycheeAILab bearer token.
- Never request, store, or expose the LycheeTTS `api_key`. The Lab gateway reads it from the encrypted `provider_credentials` table.
- Never store credentials in the repository, command examples, logs, state files, or output.

## LycheeAILab avatar stages

Base URL: `https://lab.lycheeai.com.cn`

- `POST /api/avatar-forge/voice/clone`: authorized reference audio in multipart field `voice`; returns `requestId`, optional `speakerId`, and status. The upstream contract currently provides no clone-status endpoint, so never invent one or treat `requestId` as `speakerId`.
- `POST /api/avatar-forge/voice/file`: form fields `speakerId`, `script`, `speed`, `volume`, `sampleRate`; returns downloaded LycheeTTS MP3 bytes.
- `POST /api/avatar-forge/template`: authorized portrait plus bundled fixed `assets/template-driver.wav`; returns `assetId` and `taskId`.
- `GET /api/avatar-forge/task/:taskId`: poll the internal template until `SUCCESS` or `FAILED`; never return this MP4 as the final output.
- `POST /api/avatar-forge/avatar/clone`: internal template video plus `assetId`; returns `requestId`.
- `POST /api/avatar-forge/avatar/infer`: target audio plus `assetId` and `playerId`; returns `inferenceId` and `requestId`.
- `GET /api/avatar-forge/digital-task/:requestId`: poll until `INFER.SUCCESS` or `INFER.FAIL`; `body.data` from successful final inference is the normal user-facing MP4 URL.

Do not use the legacy `/api/avatar-forge/generate` route. Never return provider credentials, internal task IDs, signed internal template URLs, or internal template media.
