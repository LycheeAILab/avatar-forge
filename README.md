<div align="center">
  <img src=".github/assets/logo.svg" width="72" alt="Avatar Forge logo" />

  # Avatar Forge

  **让每个人都能拥有自己的数字人。**

  上传一张图片、一段声音和一份文案，即可生成自然开口的数字人视频。

  [![License: MIT](https://img.shields.io/badge/License-MIT-111827.svg)](LICENSE)
  [![Agent Skill](https://img.shields.io/badge/Agent-Skill-7257E8.svg)](#安装)
</div>

---

Avatar Forge 是一个面向 AI Agent 的数字人视频 Skill。

你可以从丰富的公共数字人形象中直接选择，也可以使用自己的图片和声音，快速创建专属数字人。只需告诉 Agent 你想说什么，剩下的交给 Avatar Forge。

## 核心能力

### 丰富的公共模型

无需准备人物素材，直接从公共数字人形象中挑选适合你的角色，快速生成产品介绍、知识分享、新闻播报等内容。

### 克隆你的专属数字人

上传一张已获授权的人物图片和一段参考声音，即可生成拥有相似形象与音色的数字人视频。

- 一张人物图片
- 一段参考声音
- 一份口播文案
- 一个会自然开口的专属数字人

### 一句话完成口播视频

Avatar Forge 可以与 [HyperFrames](https://github.com/HyperCrowdAI/hyperframes) 或 ChatCut 搭配使用，在数字人口播的基础上继续添加字幕、标题、画面素材、动态包装与镜头节奏，完成适合社交媒体发布的口播成片。

## 适合用来做什么

- 产品介绍与营销视频
- 知识科普与课程内容
- 新闻、资讯与每日播报
- 自媒体口播与短视频
- 多语言数字人内容
- 品牌 IP 与虚拟主播

## 使用方式

安装后，直接在 Codex 中描述你的需求即可：

> 用这个人物和这段声音，生成一条介绍新产品的数字人口播视频。

或者：

> 从公共模型里选一个专业、亲和的主播，制作这份文案的口播视频，再用 HyperFrames 包装成竖屏短视频。

Agent 会引导你准备所需素材并完成生成。

## 安装

```powershell
git clone https://github.com/LycheeAILab/avatar-forge.git
Copy-Item `
  avatar-forge\skills\avatar-forge-pipeline `
  "$env:USERPROFILE\.codex\skills\avatar-forge-pipeline" `
  -Recurse
```

重新打开一个 Codex 任务后，`avatar-forge-pipeline` 即可被自动发现。首次使用时，Skill 会引导你完成 LycheeAILab 登录授权。

## 关于素材授权

请仅上传你拥有合法使用权的人物图片、声音和文案，并在发布生成内容时遵守适用的法律、平台规则与内容政策。

## License

本项目基于 [MIT License](LICENSE) 开源。

<div align="center">
  Built by <a href="https://lab.lycheeai.com.cn/">LycheeAILab</a>
</div>
