# Zeroshot delivery workflow

## Output invariant

The normal complete and avatar-only workflows have exactly one user-facing output: the MP4 returned by zeroshot inference.

Internal template media is transient implementation state. Do not copy it to the requested output path, return its URL, open it for the user, package it, or describe it as the finished digital human.

## Complete workflow

| Stage | Input | Service boundary | Persist for recovery | User deliverable |
| --- | --- | --- | --- | --- |
| Internal template | portrait + bundled fixed short audio | Lab `/template` (internally RunningHub) | `assetId`, `templateTaskId`, hidden template until clone succeeds | No |
| Voice clone request | authorized reference voice | Lab `/voice/clone` → LycheeTTS | `requestId` normalized as `speakerId` | Internal only |
| Target speech | `speaker_id` + full script | Lab `/voice/file` → LycheeTTS | downloaded MP3 | No, unless voice-only requested |
| Fast clone | internal template | Lab `/avatar/clone` → Lychee `v2clone` | `cloneRequestId`, `playerId` | No |
| Final inference | `playerId` + LycheeTTS target audio | Lab `/avatar/infer` → Lychee `zeroshot` | `inferenceRequestId` | Yes: zeroshot MP4 |

RunningHub has no role after the internal-template stage.

The template-driving audio is always the bundled `assets/template-driver.wav` (SHA-256 `73c9cc8dde3ee0f4fe0d39b3720bbc4453ab22b3ede2a9068183d0e1c55d3d0b`). It is fixed internal input, not a user option. The user's script, reference voice, finished audio, and LycheeTTS target speech must never enter the template stage.

## Existing-input variants

- Existing finished audio: skip LycheeTTS; create the internal template with the bundled fixed audio, fast-clone, then use the user's finished audio only for zeroshot.
- Reference voice: clone once, persist the returned `speakerId` in recovery state, and continue automatically. Retry transient voice-readiness failures without resubmitting the clone.
- Existing ready `assetId/playerId`: skip template and fast clone; submit audio directly to zeroshot.
- Existing zeroshot MP4: return or reuse that zeroshot output; do not replace it with an internal template.

Do not collect or regenerate inputs for skipped stages.

## Recovery rules

The client stores hidden state under `.avatar-forge/<output-stem>/state.json` and fingerprints its inputs.

- Same inputs + same output: resume saved stage.
- Different inputs + same output: stop; require a different output or explicit `--reset-state`.
- Saved template task: query it; do not create another.
- Saved clone request: query it; do not call template or clone again.
- Saved `playerId`: skip clone.
- Saved inference request: query it; do not call any earlier stage.
- After fast clone succeeds, remove the transient local template.

Provider IDs are diagnostic state, not normal user-facing output.

## Script handling

The provided LycheeTTS contract does not specify a text-length limit. Submit the complete script once and surface any service validation error without silently truncating it.

## Billing protection

- Never infer failure from an HTTP timeout.
- Never automatically use `--reset-state`.
- Never restart template generation to recover clone or zeroshot.
- Store every task/request ID before polling.
