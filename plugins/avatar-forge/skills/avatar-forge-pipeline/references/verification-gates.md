# Verification gates

Do not claim complete/avatar-only success until every applicable gate passes:

1. Confirm inputs exist and the user is authorized to use them.
2. Confirm Lab authentication without exposing credentials.
3. Confirm hidden recovery state records the internal template task before polling.
4. Confirm MiMo generated every script chunk and the reconstructed text equals the complete source.
5. Confirm fast clone succeeded and returned `player_id` from Lychee `v2clone`.
6. Confirm zeroshot succeeded and returned a final video URL from Lychee `zeroshot`.
7. Download the zeroshot MP4 to the requested output path.
8. Use FFprobe to confirm positive duration plus video and audio streams.
9. Confirm the local internal template was removed after clone.
10. Return only the zeroshot MP4. Do not return a template MP4, RunningHub URL/task ID, clone request ID, or intermediate WAV.

Run `scripts/scan_secrets.py` before publishing. Never save authorization headers, user API Keys, provider credentials, reference-audio Base64, signed URLs, or provider payloads.
