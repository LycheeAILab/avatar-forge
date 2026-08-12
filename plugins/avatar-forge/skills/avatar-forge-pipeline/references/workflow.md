# Composable workflow contract

## Select modules from the requested outcome

| User outcome | Required input | Optional next module |
| --- | --- | --- |
| Use a public avatar | public model choice, speech audio or script | packaging |
| Animate a portrait | approved portrait, speech audio | packaging |
| Lip-sync an existing video | approved video, speech audio | packaging |
| Clone/synthesize a voice | approved reference voice, script | portrait animation, video lip sync, or audio delivery |
| Package an existing video | video, script/captions, style direction | none |
| Full talking-avatar video | inputs required by the selected modules | packaging |

Do not collect inputs for modules the user did not select.

## Portrait preflight gate

Before every portrait animation submission:

1. Show the Chinese quality notice from `SKILL.md`.
2. Inspect face clarity, complete visibility, occlusion, crop, exposure, tilt, and subject scale.
3. Record either a pass or a specific rejection reason.
4. Obtain user confirmation before a potentially charged submission.

## Composition rules

- Voice synthesis must precede animation or lip sync only when the user does not already have final speech audio.
- Existing video must bypass portrait generation.
- Packaging must accept an existing result and must not trigger regeneration.
- Save task IDs and resume interrupted paid jobs instead of duplicating them.
- Preserve intermediate audio and raw video when they are useful to the user.

## Current client boundary

The bundled CLI currently documents the protected complete-creation route and local HyperFrames packaging. Standalone capabilities may be available through LycheeAILab product surfaces before separate public API routes are added. Never infer endpoint names. Consult `api-contracts.md`, and surface the boundary honestly.
