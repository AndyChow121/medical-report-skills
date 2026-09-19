# Style & Journal Rewrite · 文风与期刊格式适配

> 中文 | English

## 简介 / Introduction

**中文** — 按目标文风或目标期刊格式改写初稿。当用户说「改成 XX 风格」「仿照这个味道」「按 XX 期刊格式整理」「参考这篇格式改」时触发；输入可为 .docx / .md / .txt 或对话文本。可套用期刊体例（摘要结构、参考文献格式、标题层级）与作者个人文风，不改事实与核心内容。

**English** — Rewrite a draft to match a target writing style or target journal's format. Triggers when the user says "make it sound like X", "match this tone", "format for journal X", or "restyle based on this sample". Input can be .docx / .md / .txt or chat text. Applies journal conventions (abstract structure, reference style, heading levels) and author voice without altering facts or core content.

## 核心能力 / Key Features

- 文风迁移：仿写指定作者/平台语气 — Style transfer: mimic a specified author/platform voice
- 期刊格式适配：摘要/参考文献/层级套模板 — Journal formatting: abstract / references / heading templates
- 多格式输入：DOCX / MD / TXT / 对话文本 — Multi-format input: DOCX / MD / TXT / chat text
- 依赖 python-docx 处理 .docx 视觉格式 — Uses python-docx for .docx visual formatting

## 适用场景 / Use Cases

- 把稿件改成 Nature / NEJM / 某中文核心期刊的体例
- 仿照某篇范文重写自己的段落
- 统一多篇投稿的参考文献与标题规范

## 快速开始 / Quick Start

- 中文：在 WorkBuddy 中说「按 XX 期刊格式整理这篇」「改成 XX 风格」并附文本/文档；或直接调用 Skill `style-journal-rewrite`。
- English：In WorkBuddy say "format this for journal X / rewrite in the style of X" with the text or doc, or invoke Skill `style-journal-rewrite`.

## 安装 / Install

把本目录复制到 WorkBuddy 的 skills 目录：

```
# Windows
%USERPROFILE%\.workbuddy\skills\style-journal-rewrite

# macOS / Linux
~/.workbuddy/skills/style-journal-rewrite
```

> 处理 .docx 格式需先安装 `python-docx`：`pip install python-docx`

## 许可 / License

MIT
