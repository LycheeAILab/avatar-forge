# Workflow contract

## Inputs

- Portrait: JPG, PNG, or WebP depicting one authorized person.
- Reference voice: WAV or MP3 containing one authorized speaker with low background noise.
- Script: non-empty UTF-8 text to be spoken by the avatar.
- Optional presentation title for the bundled HyperFrames template.

## Stages

1. **Lab authorization** — exchange the user's signed-in Lab session for the user's revocable API Key through the loopback authorization flow.
2. **Voice cloning and speech synthesis** — the Lab gateway sends the reference voice and script to MiMo and obtains synthesized speech in the cloned voice.
3. **Digital-human generation** — the Lab gateway uploads the portrait and synthesized speech to the configured InfiniteTalk workflow on RunningHub and returns a task ID.
4. **Durable persistence** — the Lab gateway stores successful provider output in private Tencent COS and returns a short-lived signed result URL.
5. **Local presentation render** — the Skill downloads the raw MP4 and uses the bundled HyperFrames template to place the speaker in a visual mask, add script-derived captions and render the finished mouthpiece MP4.

Do not reorder stages 2 and 3: InfiniteTalk requires the synthesized speech before it can drive the portrait.

## Outputs

- `*-raw.mp4`: the unmodified digital-human video returned by the Lab gateway.
- The requested `--output`: the final HyperFrames-packaged mouthpiece video.
- The task ID printed to stdout so interrupted jobs can be resumed.

## Open-source boundary

The repository includes orchestration code, the Lab authentication client, API contracts, validation scripts, and the reusable HyperFrames template. It excludes provider credentials, the server-side credential vault, user API Keys, production data, validation portraits/voices, and generated media.
