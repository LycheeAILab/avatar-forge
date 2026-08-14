# Avatar Forge Codex Plugin install guide

This document is an execution guide for Codex agents. If the request is coming from a user, complete the steps instead of merely describing them.

## Host gate

Installation must run in the Codex desktop app on the user's local machine. A web or isolated cloud conversation cannot install into the desktop plugin directory. In that case, ask the user to open Codex desktop and paste:

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/main/INSTALL.md，帮我安装 Avatar Forge 插件并创建一个新的数字人视频任务。

## Install

Locate the Codex CLI bundled with the desktop app. Do not use an unrelated standalone CLI. Verify it with `"<BUNDLED_CODEX>" --version`, then run:

```text
"<BUNDLED_CODEX>" plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git --ref main
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
Avatar Forge 插件已经安装好了。请先引导我完成 LycheeAILab 登录授权。完整流程需要人物图片、参考声音和口播稿；如果我有专用模板驱动音频，也一并接收并仅用于内部动作模板。流程内部依次完成动作模板、MiMo 目标口播、数字人快速克隆和 zeroshot 推理。只向我返回 zeroshot 推理生成的最终 MP4，不要返回内部模板、任务 ID、中间音频或供应商链接。也可以按我的明确要求只生成 MiMo 音频，或者使用已有 assetId、playerId 和音频执行 zeroshot 推理。如果需要上传人物图片，先提示并确认：人物脸部清晰、没有遮挡、完整露出且人物比例适中，否则会影响效果。未经我确认，不要提交可能产生费用的生成任务。
```

Use the host's task creation and navigation tools. Setup is complete only when the plugin is verified and the new task contains this prompt.

If installation or verification fails, create a recovery task containing the exact failed command and error, instructing it to reread this guide and resume from that step.
