<div align="center">
  <a href="https://lab.lycheeai.com.cn/">
    <img src=".github/assets/logo.svg" width="80" alt="Avatar Forge" />
  </a>

  # Avatar Forge

  **让一张照片，成为可以开口表达的数字人。**

  面向 AI Agent 的开源数字人视频工作流。<br />
  从参考视频提炼新文案，或从人物图片、参考声音和口播稿生成完整数字人口播视频。

  [![License: MIT](https://img.shields.io/badge/License-MIT-111111?style=flat-square)](LICENSE)
  [![Version](https://img.shields.io/badge/version-2.1.0-3157D5?style=flat-square)](https://github.com/LycheeAILab/avatar-forge/releases/tag/v2.1.0)
  [![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-111111?style=flat-square)](#codex)
  [![WorkBuddy Skill](https://img.shields.io/badge/WorkBuddy-Skill-111111?style=flat-square)](#workbuddy)
  [![LycheeAILab](https://img.shields.io/badge/Built%20by-LycheeAILab-3157D5?style=flat-square)](https://lab.lycheeai.com.cn/)
</div>

<br />

## 它能做什么

Avatar Forge 将目标声音生成、内部动作模板、人物快速克隆与最终视频推理串成一条可恢复流水线。默认只向用户交付数字人平台 zeroshot 推理得到的最终 MP4。

| 能力 | 输入 | 输出 |
| --- | --- | --- |
| 视频文案再创作 | 上传视频或有权使用的抖音链接 | 原文案 + 独立保存的改写口播稿 |
| 声音克隆 | 已授权参考声音 | 自动获得并保存 `speaker_id` |
| 语音生成 | `speaker_id` + 文案 | LycheeTTS MP3 口播音频 |
| 内部模板 | 人物图片 + Skill 内置固定短音频 | 仅供快速克隆使用，不对外交付 |
| 数字人快速克隆 | 内部模板 | 可复用的数字人身份 |
| zeroshot 推理 | 数字人身份 + LycheeTTS 目标音频 | 唯一默认交付的口播视频 |

## 安装

### Codex

#### 让 Codex 帮你安装

在 Codex 桌面端新建任务，发送下面这句话：

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/v2.1.0/INSTALL.md，帮我安装 Avatar Forge。

#### 手动安装

```powershell
codex plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git --ref v2.1.0
codex plugin add avatar-forge@avatar-forge
```

安装后请新建一个 Codex 任务，使插件在新会话中加载。

### WorkBuddy

在 WorkBuddy 中发送下面这句话：

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/v2.1.0/WORKBUDDY_INSTALL.md，帮我安装 Avatar Forge 2.1.0；安装后只运行本地 doctor，不要提交任何生成任务。

也可以从 [2.1.0 Release](https://github.com/LycheeAILab/avatar-forge/releases/tag/v2.1.0) 下载 `avatar-forge-workbuddy-2.1.0.zip`，在 WorkBuddy 的 Skills 页面上传。安装包与 Codex 插件共享同一套运行脚本，平台适配层不会复制业务流程。

## 开始创作

把拥有合法使用权的素材交给 Codex，然后直接描述目标：

> 使用 Avatar Forge，下载这个我有权使用的抖音视频，提取原文案，并改写成一版新的口播稿。先不要生成数字人视频。

也可以直接上传本地视频。Avatar Forge 会保留原始转写稿，并把改写稿单独保存；改写会调整开头、结构、节奏、转场和结尾，而不是简单替换同义词。只有你明确要求时，才会继续生成声音或数字人视频。

> 使用 Avatar Forge，把这张人物图片、已授权参考声音和口播稿制作成一条完整的数字人口播视频。

首次使用时，Avatar Forge 会打开 LycheeAILab 登录授权页。完成登录后，Codex 会自动执行任务并在各阶段之间安全传递结果。RunningHub 仅在内部模板阶段使用；快速克隆与最终推理全部调用 LycheeAILab 数字人平台，最终只返回 zeroshot 视频。

模板阶段始终使用 Skill 内置的固定短音频，不读取用户口播稿，也不使用用户参考声音、已有目标音频或 LycheeTTS 生成音频。LycheeTTS 根据 `speaker_id` 与文案生成的正式目标口播，只用于最终 zeroshot 推理。

语音克隆与合成由 LycheeAILab 网关调用 LycheeTTS。插件只保存用户本人可撤销的 Lab API Key；LycheeTTS 公共 Key 加密保存在 Lab 数据库，不进入用户电脑、仓库或日志。克隆接口返回的 `request_id` 会被自动登记为后续推理使用的 `speaker_id`，音色尚未就绪时会有限重试，无需用户手动复制 ID。

也可以只使用某一项能力：

```text
使用 Avatar Forge，提交这段已授权参考声音进行声音克隆。
使用 Avatar Forge，根据这个 speaker_id 和文案生成口播音频。
使用 Avatar Forge，用这张人物图片和已有音频生成最终 zeroshot 数字人视频。
使用 Avatar Forge，让这个已有数字人使用指定音频执行 zeroshot 推理。
使用 Avatar Forge，提取这个视频的口播文案并改写，完成后停止。
```

## 设计原则

- **明确交付**：完整流程只把 zeroshot MP4 作为最终结果，内部模板不对外输出。
- **可恢复**：长任务在本地隐藏状态中保留阶段进度，重新运行相同命令即可继续。
- **凭据隔离**：供应商密钥只保存在 LycheeAILab 服务端的加密凭据库。
- **阶段隔离**：RunningHub 只生成内部模板；快速克隆和 zeroshot 推理不经过 RunningHub。
- **Agent 原生**：无需额外操作页面，由 Agent 理解目标并选择正确流程。

## 安全与授权

Avatar Forge 通过 LycheeAILab 账户完成身份验证。插件不会获取或暴露 LycheeTTS、RunningHub、数字人服务和对象存储的公共供应商凭据；这些凭据只存在于 Lab 服务端的加密凭据库。

请仅上传已获得合法授权的人物图片、声音、视频和文案。不得利用本项目冒充他人、误导公众或生成违法违规内容。

抖音下载能力由随 Skill 安装的 `yt-dlp` 提供，用户无需预先安装其他下载项目。如果平台要求登录态，Avatar Forge 必须先获得许可，且只允许从本机浏览器读取；不得要求用户粘贴、打印或保存 Cookie。

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。

<br />

<div align="center">
  <sub>Built with care by <a href="https://lab.lycheeai.com.cn/">LycheeAILab</a></sub>
</div>
