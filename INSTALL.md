# Avatar Forge Codex Plugin install guide

This document is an execution guide for Codex agents. If the request is coming from a user, complete the steps instead of merely describing them.

## Host gate

Installation must run in the Codex desktop app on the user's local machine. A web or isolated cloud conversation cannot install into the desktop plugin directory. In that case, ask the user to open Codex desktop and paste:

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/v2.1.0/INSTALL.md，帮我安装 Avatar Forge 插件并创建一个新任务。

## Install

Locate the Codex CLI bundled with the desktop app. Do not use an unrelated standalone CLI. Verify it with `"<BUNDLED_CODEX>" --version`, then run:

```text
"<BUNDLED_CODEX>" plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git --ref v2.1.0
"<BUNDLED_CODEX>" plugin marketplace list
"<BUNDLED_CODEX>" plugin list --marketplace avatar-forge
"<BUNDLED_CODEX>" plugin add avatar-forge@avatar-forge
```

If the marketplace is already configured, upgrade it before installing:

```text
"<BUNDLED_CODEX>" plugin marketplace upgrade avatar-forge
```

## Authenticate and verify

Avatar Forge uses an interactive LycheeAILab login on first use. Verify the installation first:

```text
"<BUNDLED_CODEX>" plugin list --marketplace avatar-forge --json
```

The result must show `avatar-forge@avatar-forge` as installed and enabled. Do not claim setup succeeded without this evidence.

## Required final step

Newly installed plugin skills are available only in a new Codex task. Create and open a new task yourself, preserving the current project context when possible, with this Chinese initial prompt:

```text
Avatar Forge 插件已经安装好了。它既可以独立处理“上传视频或有权使用的抖音链接 -> 提取原文案 -> 改写新口播稿”，也可以生成数字人视频；文案任务完成后必须停止，除非我明确要求继续。抖音下载能力随 Skill 安装，不能要求我另装 douyindownload；如需读取本机浏览器登录态，必须先征得同意，绝不能索要、打印或保存 Cookie。数字人完整流程使用人物图片、已授权参考声音或现有 LycheeTTS speaker_id，以及口播稿；只有参考声音时，通过 Lab 网关克隆一次，将返回的 requestId 自动作为 speakerId 保存并继续生成，音色未就绪时有限重试，禁止要求用户手动查找 ID。插件只能使用用户的 Lab API Key，绝不能索要或暴露供应商密钥。模板阶段必须使用 Skill 内置固定短音频。只返回 zeroshot 最终 MP4，不要返回内部模板、任务 ID、中间音频或供应商链接。如果需要上传人物图片，先提示并确认：人物脸部清晰、没有遮挡、完整露出且人物比例适中，否则会影响效果。未经我确认，不要提交可能产生费用的生成任务。
```

Use the host's task creation and navigation tools. Setup is complete only when the plugin is verified and the new task contains this prompt.

If installation or verification fails, create a recovery task containing the exact failed command and error, instructing it to reread this guide and resume from that step.
