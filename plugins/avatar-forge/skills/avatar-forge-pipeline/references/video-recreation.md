# Reference-video script workflow

Use this workflow when the user supplies a local video or an authorized Douyin link and wants its spoken content extracted or rewritten.

## Source acquisition

- Treat an attached/uploaded video as the preferred source; do not download it again.
- For a Douyin URL, confirm the user is permitted to download and reuse the content.
- Invoke `scripts/prepare_video_source.py`. It uses the Skill's declared `yt-dlp` dependency, so users do not need a separate downloader project.
- If Douyin requires a login session, obtain permission before using `--cookies-from-browser`. Never ask the user to paste cookies, and never print, copy, or save cookie values.

## Transcription

- Preserve the raw transcript in `transcript-original.txt`.
- Prefer an available trusted transcription tool. Otherwise use `scripts/transcribe_video.py`; its optional local dependency is listed in `requirements-transcription.txt`.
- Do not invent inaudible words. Mark uncertain passages or ask the user to review them.
- Remove obvious recognition artifacts, but keep facts, numbers, names, and claims unchanged in the original transcript.

## Rewrite

Before rewriting, ask for a target only when it is not reasonably inferable: platform, desired duration, audience, tone, or call to action.

Produce `script-rewritten.txt` separately from the original transcript. The rewrite should:

- preserve verifiable meaning unless the user explicitly asks to change the message;
- reorganize the hook, pacing, transitions, and conclusion instead of merely swapping synonyms;
- avoid copying distinctive phrasing more closely than necessary;
- flag factual, medical, financial, legal, or promotional claims that need verification;
- fit the requested speaking duration and sound natural when read aloud;
- never fabricate product results, testimonials, prices, or statistics.

Return both files and summarize the main structural changes. Continue into voice or avatar generation only when the user asks.
