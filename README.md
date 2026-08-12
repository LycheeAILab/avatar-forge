<div align="center">
  <img src=".github/assets/logo.svg" width="72" alt="Avatar Forge logo" />

  # Avatar Forge

  **让每个人都能拥有自己的数字人。**

  上传一张图片、一段声音和一份文案，即可生成自然开口的数字人视频。

  [![License: MIT](https://img.shields.io/badge/License-MIT-111827.svg)](LICENSE)
  [![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-7257E8.svg)](#一句话安装)
</div>

---

Avatar Forge 是一个面向 AI Agent 的可组合数字人视频插件。你可以只使用其中一项能力，也可以按需组合，无需每次执行完整流水线。

## 核心能力

### 丰富的公共模型

无需准备人物素材，直接选择合适的公共数字人，用于产品介绍、知识分享、资讯播报等内容。

### 创建你的专属数字人

上传一张已获授权的人物图片、一段参考声音和一份口播文案，即可创建拥有相似形象与音色的数字人视频。

上传前请确认人物脸部清晰、没有遮挡、完整露出，且人物在画面中的比例适中；否则会影响生成效果。

### 已有视频匹配口型

如果你已经有视频，可以直接为视频匹配新的语音和口型，无需重新生成角色。

### 单独克隆声音

只上传已获授权的参考声音和文案即可生成克隆语音，不要求同时提供人物图片或视频。

### 制作完整口播成片

与 [HyperFrames](https://github.com/HyperCrowdAI/hyperframes) 或 ChatCut 搭配，为数字人口播添加字幕、标题、素材画面、动态包装和镜头节奏。

## 一句话安装

在 Codex 桌面端新建任务并发送：

> 阅读 https://raw.githubusercontent.com/LycheeAILab/avatar-forge/main/INSTALL.md，帮我安装 Avatar Forge 插件并创建一个新的数字人视频任务。

Codex 会自动完成 Marketplace 添加、插件安装、安装验证，并为你打开第一个数字人视频任务。首次制作时会引导你完成 LycheeAILab 登录授权，再根据你的目标选择所需能力。

## 手动安装

```powershell
codex plugin marketplace add https://github.com/LycheeAILab/avatar-forge.git --ref main
codex plugin add avatar-forge@avatar-forge
```

安装后请新建 Codex 任务，让插件能力在新会话中加载。

## 适合用来做什么

- 产品介绍与营销视频
- 知识科普与课程内容
- 新闻、资讯与每日播报
- 自媒体口播与短视频
- 多语言数字人内容
- 品牌 IP 与虚拟主播

## 素材授权

请仅上传你拥有合法使用权的人物图片、声音和文案，并遵守适用的法律、平台规则与内容政策。提交可能产生费用的生成任务前，Agent 应获得你的确认。

## License

本项目基于 [MIT License](LICENSE) 开源。

<div align="center">
  Built by <a href="https://lab.lycheeai.com.cn/">LycheeAILab</a>
</div>
