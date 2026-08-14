<div align="center">
  <a href="https://lab.lycheeai.com.cn/">
    <img src=".github/assets/logo.svg" width="80" alt="Avatar Forge" />
  </a>

  # Avatar Forge

  **让一张照片，成为可以开口表达的数字人。**

  面向 AI Agent 的开源数字人视频工作流。<br />
  从人物图片、参考声音和口播稿出发，生成完整的数字人口播视频。

  [![License: MIT](https://img.shields.io/badge/License-MIT-111111?style=flat-square)](LICENSE)
  [![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-111111?style=flat-square)](#安装)
  [![LycheeAILab](https://img.shields.io/badge/Built%20by-LycheeAILab-3157D5?style=flat-square)](https://lab.lycheeai.com.cn/)
</div>

<br />

## 它能做什么

Avatar Forge 将目标声音生成、内部动作模板、人物快速克隆与最终视频推理串成一条可恢复流水线。默认只向用户交付数字人平台 zeroshot 推理得到的最终 MP4。

| 能力 | 输入 | 输出 |
| --- | --- | --- |
| 声音克隆 | 参考声音 + 文案 | WAV 口播音频 |
| 内部模板 | 人物图片 + 模板驱动音频 | 仅供快速克隆使用，不对外交付 |
| 数字人快速克隆 | 内部模板 | 可复用的数字人身份 |
| zeroshot 推理 | 数字人身份 + MiMo 目标音频 | 唯一默认交付的口播视频 |

## 安装

### 让 Codex 帮你安装

在 Codex 桌面端新建任务，发送下面这句话：

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/main/INSTALL.md，帮我安装 Avatar Forge。

### 手动安装

```powershell
codex plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git --ref main
codex plugin add avatar-forge@avatar-forge
```

安装后请新建一个 Codex 任务，使插件在新会话中加载。

## 开始创作

把拥有合法使用权的素材交给 Codex，然后直接描述目标：

> 使用 Avatar Forge，把这张人物图片、参考声音和口播稿制作成一条完整的数字人口播视频。

首次使用时，Avatar Forge 会打开 LycheeAILab 登录授权页。完成登录后，Codex 会自动执行任务并在各阶段之间安全传递结果。RunningHub 仅在内部模板阶段使用；快速克隆与最终推理全部调用 LycheeAILab 数字人平台，最终只返回 zeroshot 视频。

模板驱动音频只服务于内部动作模板；MiMo 根据参考声音与文案生成的正式目标口播音频，只用于最终 zeroshot 推理。两者不会混为同一个产物。

也可以只使用某一项能力：

```text
使用 Avatar Forge，根据参考声音和这段文案生成口播音频。
使用 Avatar Forge，用这张人物图片和已有音频生成最终 zeroshot 数字人视频。
使用 Avatar Forge，让这个已有数字人使用指定音频执行 zeroshot 推理。
```

## 设计原则

- **明确交付**：完整流程只把 zeroshot MP4 作为最终结果，内部模板不对外输出。
- **可恢复**：长任务在本地隐藏状态中保留阶段进度，重新运行相同命令即可继续。
- **凭据隔离**：供应商密钥只保存在 LycheeAILab 服务端的加密凭据库。
- **阶段隔离**：RunningHub 只生成内部模板；快速克隆和 zeroshot 推理不经过 RunningHub。
- **Agent 原生**：无需额外操作页面，由 Agent 理解目标并选择正确流程。

## 安全与授权

Avatar Forge 通过 LycheeAILab 账户完成身份验证。插件本地只保存用户可撤销的 API Key，不会获取或暴露 MiMo、RunningHub、数字人服务和对象存储的供应商凭据。

请仅上传已获得合法授权的人物图片、声音、视频和文案。不得利用本项目冒充他人、误导公众或生成违法违规内容。

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。

<br />

<div align="center">
  <sub>Built with care by <a href="https://lab.lycheeai.com.cn/">LycheeAILab</a></sub>
</div>
