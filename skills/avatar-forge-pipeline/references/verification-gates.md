# Verification gates

Do not claim end-to-end success until all applicable gates pass:

1. Confirm the portrait, reference voice, and script exist and are authorized for use.
2. Confirm Lab authentication succeeds with the user's API Key without exposing it.
3. Confirm the gateway returns a task ID after MiMo speech synthesis and InfiniteTalk submission.
4. Poll until `SUCCESS`; a timeout is not proof of failure and must not trigger automatic resubmission.
5. Confirm the signed result downloads as a non-empty MP4.
6. Use FFprobe to confirm positive duration and both video and audio streams in the raw MP4.
7. Run the bundled HyperFrames check and require zero lint, runtime, layout, motion, and contrast errors.
8. Confirm the packaged MP4 is 1080×1920, includes AAC audio, and matches the raw video's approximate duration.
9. Inspect frames near the beginning, middle, and end for a visible speaker, intact mask, readable captions, and no clipped layout.
10. Run `scripts/scan_secrets.py` against the Skill folder before publishing.

Preserve only the task ID and sanitized status metadata. Never save authorization headers, user API Keys, provider credentials, reference-audio Base64, or signed result URLs.
