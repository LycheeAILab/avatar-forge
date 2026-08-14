# Zeroshot delivery workflow

## Output invariant

The normal complete and avatar-only workflows have exactly one user-facing output: the MP4 returned by zeroshot inference.

Internal template media is transient implementation state. Do not copy it to the requested output path, return its URL, open it for the user, package it, or describe it as the finished digital human.

## Complete workflow

| Stage | Input | Service boundary | Persist for recovery | User deliverable |
| --- | --- | --- | --- | --- |
| Internal template | portrait + template-driving audio | Lab `/template` (internally RunningHub) | `assetId`, `templateTaskId`, hidden template until clone succeeds | No |
| Target speech | reference voice + full script | Lab `/voice/file` (MiMo) | chunk files and combined WAV | No, unless voice-only requested |
| Fast clone | internal template | Lab `/avatar/clone` → Lychee `v2clone` | `cloneRequestId`, `playerId` | No |
| Final inference | `playerId` + MiMo target WAV | Lab `/avatar/infer` → Lychee `zeroshot` | `inferenceRequestId` | Yes: zeroshot MP4 |

RunningHub has no role after the internal-template stage.

Template-driving audio and formal target speech are separate roles. Prefer `--driver-audio` when a dedicated motion driver is available. Otherwise the reference voice may provide template timing only; MiMo still generates the formal target speech used by zeroshot.

## Existing-input variants

- Existing finished audio: skip MiMo; still create the internal template, fast-clone, then zeroshot using that same finished audio.
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

MiMo currently accepts at most 500 characters per server request. The client splits longer scripts at Chinese or English sentence punctuation with a target maximum of 480 characters, generates each chunk, and concatenates WAV chunks. It must verify that normalized concatenated chunk text matches the complete source script.

## Billing protection

- Never infer failure from an HTTP timeout.
- Never automatically use `--reset-state`.
- Never restart template generation to recover clone or zeroshot.
- Store every task/request ID before polling.
