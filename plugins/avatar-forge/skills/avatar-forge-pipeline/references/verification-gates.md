# Verification gates

Do not claim complete/avatar-only success until every applicable gate passes:

1. Confirm inputs exist and the user is authorized to use them.
2. Confirm Lab authentication without exposing credentials.
3. Confirm the template request used the bundled fixed `template-driver.wav`; reject a missing or hash-mismatched asset.
4. Confirm the template request did not include user text, reference voice, finished target audio, or LycheeTTS output.
5. Confirm hidden recovery state records the internal template task before polling.
6. Confirm LycheeTTS inference went through the Lab gateway, used the intended `speaker_id`, complete script, speed, volume, and sample rate, and returned a non-empty downloaded audio file.
7. Confirm fast clone succeeded and returned `player_id` from Lychee `v2clone`.
8. Confirm zeroshot succeeded and returned a final video URL from Lychee `zeroshot`.
9. Download the zeroshot MP4 to the requested output path.
10. Use FFprobe to confirm positive duration plus video and audio streams.
11. Confirm the local internal template was removed after clone.
12. Return only the zeroshot MP4. Do not return a template MP4, RunningHub URL/task ID, clone request ID, or intermediate WAV.

Run `scripts/scan_secrets.py` before publishing. Never save authorization headers, user API Keys, provider credentials, reference-audio Base64, signed URLs, or provider payloads.
