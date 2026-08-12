# LycheeAILab protected API

Base URL: `https://lab.lycheeai.com.cn`

## Authentication

- `POST /api/skill-auth/login`
  - JSON: `username`, `password`
  - Response: `accessToken`, `tokenType`, `expiresIn`
- `POST /api/skill-auth/exchange`
  - Requires an existing same-origin LycheeAILab login cookie.
  - Response: the signed-in user's `apiKey`, its prefix, and basic user metadata.
  - The authorization page sends the key by POST to a randomized loopback callback. Never put the key in a URL or log it.
- `GET /api/skill-auth/me`
  - Header: `Authorization: Bearer <userApiKey>`
- `POST /api/skill-auth/logout`
  - Header: `Authorization: Bearer <accessToken>`

The Skill stores only the revocable user API Key. MiMo, RunningHub, and Tencent COS credentials remain server-side.

## Avatar Forge

- `POST /api/avatar-forge/generate`
  - Header: `Authorization: Bearer <userApiKey>`
  - Multipart: `image`, `voice`, `script`
  - Response: `taskId`, `status`
- `GET /api/avatar-forge/task/:taskId`
  - Header: `Authorization: Bearer <userApiKey>`
  - Poll until `SUCCESS` or `FAILED`
  - On success, use the returned signed MP4 URL immediately.

Never call provider APIs directly from the Skill and never return provider keys from the Lab API.
