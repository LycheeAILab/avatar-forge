# Avatar Forge WorkBuddy installation guide

This is an execution guide for WorkBuddy. If a user asks you to install Avatar Forge, perform the installation instead of only describing it.

## Safety gate

- Install release `v2.0.0` from the official `LycheeAILab/avatar-forge` GitHub repository.
- Verify the downloaded ZIP against the release `SHA256SUMS` file.
- Back up an existing installation; do not delete user data.
- Run only `doctor.py` after installation. Never submit a real or paid generation as an installation test.

## Windows

Run this from a local PowerShell terminal:

```powershell
$script = Join-Path $env:TEMP "install-avatar-forge-workbuddy.ps1"
Invoke-WebRequest "https://raw.githubusercontent.com/LycheeAILab/avatar-forge/v2.0.0/install-workbuddy.ps1" -OutFile $script
powershell -ExecutionPolicy Bypass -File $script -Version "2.0.0"
```

## macOS or Linux

Run this from a local terminal:

```bash
script="$(mktemp)"
curl -fsSL "https://raw.githubusercontent.com/LycheeAILab/avatar-forge/v2.0.0/install-workbuddy.sh" -o "$script"
sh "$script" "2.0.0"
```

## Verify in WorkBuddy

1. Reload WorkBuddy or start a new conversation so the installed Skill is discovered.
2. Confirm that `avatar-forge-pipeline` appears in installed Skills.
3. Run the local no-spend doctor from the installed Skill directory.
4. Do not claim installation succeeded unless the doctor returns `"ok": true`.

If WorkBuddy does not discover user Skills from `~/.workbuddy/skills`, use its Skills page to upload the downloaded `avatar-forge-workbuddy-2.0.0.zip`. Do not unpack the package into a project repository or expose any user/provider credential.

Authentication happens only when the user actually invokes Avatar Forge. The login browser opens LycheeAILab and returns to a randomized local `127.0.0.1` callback owned by the installer process. Never replace that callback with a public URL and never ask for LycheeTTS, RunningHub, digital-human, or COS provider keys.
