# LycheeAILab protected API

Base URL: `https://lab.lycheeai.com.cn`

## Authentication

- `POST /api/skill-auth/exchange`: exchange a same-origin Lab browser session for the signed-in user's API Key.
- `GET /api/skill-auth/me`: validate `Authorization: Bearer <userApiKey>`.

The Skill stores only the revocable user API Key. Provider credentials remain server-side.

## Internal template — only allowed RunningHub boundary

- `POST /api/avatar-forge/template`
  - Multipart: user-authorized `image`, bundled fixed `assets/template-driver.wav` as `audio`.
  - Never send user script text, reference voice, finished target audio, or MiMo output to this endpoint.
  - Returns internal `assetId`, `taskId`, `status`.
- `GET /api/avatar-forge/task/:taskId`
  - Poll until `SUCCESS` or `FAILED`.
  - The returned MP4 is an internal template only. Never return it as the final output.

Do not use the legacy `/api/avatar-forge/generate` route in the Skill. Explicit stage calls are required for correct recovery and final-output semantics.

## MiMo target speech

- `POST /api/avatar-forge/voice/file`
  - Multipart: `voice`, `script`.
  - Returns WAV bytes.
  - A single server call accepts at most 500 characters; split complete scripts safely and concatenate every chunk.

## Fast clone — never RunningHub

- `POST /api/avatar-forge/avatar/clone`
  - Multipart: internal template `video`, `assetId`.
  - Server calls Lychee digital-human `v2clone`.
  - Returns `requestId`; poll it with `/digital-task/:requestId` until it returns `player_id`.

## Zeroshot final inference — never RunningHub

- `POST /api/avatar-forge/avatar/infer`
  - Multipart: target `audio`, `assetId`, `playerId`.
  - Server calls Lychee digital-human `zeroshot`.
  - Returns `inferenceId`, `requestId`.
- `GET /api/avatar-forge/digital-task/:requestId`
  - Poll until `INFER.SUCCESS` or `INFER.FAIL`.
  - For inference success, `body.data` is the only normal user-facing final video URL.

Never return provider credentials, internal task IDs, signed internal template URLs, or internal template media to the user.
