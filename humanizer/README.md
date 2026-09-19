# Humanizer · 去 AI 写作痕迹

> 中文 | English

## 简介 / Introduction

**中文** — 识别并去除文本中的 AI 写作痕迹，让文字更自然、更像人写。基于 Wikipedia「Signs of AI writing」(WikiProject AI Cleanup) 维护的清单，可检测并修正 24 类模式：夸张象征、营销腔、表面化分析、含糊引用、破折号滥用、排比三连、AI 高频词、否定式对仗、过多连接词等。保留原意与语气。

**English** — Identify and remove signs of AI-generated text so writing sounds more natural and human. Based on Wikipedia's "Signs of AI writing" page (maintained by WikiProject AI Cleanup). Detects and fixes 24 pattern categories: inflated symbolism, promotional language, superficial analyses, vague attributions, em-dash overuse, rule of three, AI vocabulary words, negative parallelisms, excessive conjunctive phrases, and more. Preserves meaning and voice.

## 核心能力 / Key Features

- 模式识别：覆盖内容/语言/风格/沟通/填充 5 大类 24 种 AI 味 — Pattern detection: 24 smells across content/language/style/communication/filler
- 自然改写：用具体事实替换套路化表达 — Natural rewrite: replace stock phrases with concrete facts
- 保留原意与语气 — Preserves meaning and intended tone
- 附带前后对照示例 — Ships before/after examples

## 适用场景 / Use Cases

- 编辑/审校稿件，去掉机器生成的痕迹
- 论文、博客、营销文案、报告的人味打磨
- 与 `write` 配合做发布前终稿润色

## 快速开始 / Quick Start

- 中文：在 WorkBuddy 中说「去 AI 味 / 这段太 AI 了，改自然点」并附文本；或直接调用 Skill `humanizer`。
- English：In WorkBuddy say "humanize this / make it sound less AI" with the text, or invoke Skill `humanizer`.

## 安装 / Install

把本目录复制到 WorkBuddy 的 skills 目录：

```
# Windows
%USERPROFILE%\.workbuddy\skills\humanizer

# macOS / Linux
~/.workbuddy/skills/humanizer
```

## 许可 / License

MIT
