# Avatar Forge Codex Plugin install guide

This document is an execution guide for Codex agents. If the request is coming from a user, complete the steps instead of merely describing them.

## Host gate

Installation must run in the Codex desktop app on the user's local machine. A web or isolated cloud conversation cannot install into the desktop plugin directory. In that case, ask the user to open Codex desktop and paste:

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/main/INSTALL.md，帮我安装或升级 Avatar Forge 插件并创建一个新任务。

## Remove the legacy name collision

Before installing, inspect `${CODEX_HOME}/skills/avatar-forge-pipeline` or `~/.codex/skills/avatar-forge-pipeline`. This is the legacy standalone Skill and conflicts with the plugin Skill of the same name.

If it exists:

1. Verify that its `SKILL.md` declares `name: avatar-forge-pipeline` and that it contains `scripts/run_pipeline.py`. Do not move an unrelated or user-authored directory.
2. Move the entire directory to a timestamped backup under `~/.codex/legacy-skill-backups/`. Do not delete it or move any other Skill.
3. Record the backup path in the final response.

The backup step is required even when the old Skill appears functional. Leaving both copies active makes Codex select capabilities nondeterministically.

## Install or upgrade

Locate the Codex CLI bundled with the desktop app. Do not use an unrelated standalone CLI. Verify it with `"<BUNDLED_CODEX>" --version`, then run:

```text
"<BUNDLED_CODEX>" plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git
"<BUNDLED_CODEX>" plugin marketplace list
"<BUNDLED_CODEX>" plugin list --marketplace avatar-forge
"<BUNDLED_CODEX>" plugin add avatar-forge@avatar-forge
```

The default marketplace intentionally follows the official repository so future manifest version bumps can be discovered. Release ZIPs remain pinned and checksummed for reproducible WorkBuddy installs.

If the marketplace is already configured without a fixed `ref`, upgrade it before reinstalling:

```text
"<BUNDLED_CODEX>" plugin marketplace upgrade avatar-forge
"<BUNDLED_CODEX>" plugin add avatar-forge@avatar-forge
```

If the existing marketplace was originally added with a fixed tag such as `--ref v2.0.0` or `--ref v2.1.0`, a normal upgrade remains on that tag. Remove only the `avatar-forge` plugin and marketplace registration, add the official repository again without `--ref`, and reinstall the plugin. Do not modify unrelated marketplaces or plugins.

## Authenticate and verify

Avatar Forge uses an interactive LycheeAILab login on first use. Verify the installation first:

```text
"<BUNDLED_CODEX>" plugin list --marketplace avatar-forge --json
```

The result must show `avatar-forge@avatar-forge` as installed and enabled at version `2.1.1`. Also run the installed Skill's local `doctor.py`; it must return top-level `"version": "2.1.1"` and `"ok": true`. Do not claim setup succeeded from GitHub prose, successful authentication, or an old conversation summary.

## Required final step

Newly installed plugin skills are available only in a new Codex task. Create and open a new task yourself, preserving the current project context when possible, with this Chinese initial prompt:

```text
Avatar Forge 2.1.1 插件已经安装并通过 doctor 验证，旧的同名独立 Skill 已移出活动目录。请以插件内 VERSION 文件为版本依据。它既可以独立处理“上传视频或有权使用的抖音链接 -> 提取原文案 -> 改写新口播稿”，也可以生成数字人视频；文案任务完成后必须停止，除非我明确要求继续。抖音下载能力随 Skill 安装，不能要求我另装 douyindownload；如需读取本机浏览器登录态，必须先征得同意，绝不能索要、打印或保存 Cookie。数字人完整流程使用人物图片、已授权参考声音或现有 LycheeTTS speaker_id，以及口播稿；只有参考声音时，通过 Lab 网关克隆一次，将返回的 requestId 自动作为 speakerId 保存并继续生成。插件只能使用用户的 Lab API Key，绝不能索要或暴露供应商密钥。模板阶段必须使用 Skill 内置固定短音频。只返回 zeroshot 最终 MP4，不要返回内部模板、任务 ID、中间音频或供应商链接。如果需要上传人物图片，先提示并确认：人物脸部清晰、没有遮挡、完整露出且人物比例适中，否则会影响效果。未经我确认，不要提交可能产生费用的生成任务。
```

Use the host's task creation and navigation tools. Setup is complete only when the plugin is verified and the new task contains this prompt.

If installation or verification fails, create a recovery task containing the exact failed command and error, instructing it to reread this guide and resume from that step.
