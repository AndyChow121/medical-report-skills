# Find Paper References · 参考文献检索插入

> 中文 | English

## 简介 / Introduction

**中文** — 自动为论文 Markdown 查找参考文献：识别需引用的知识点（流行病学数据、机制描述、已有结论等），经 PubMed 检索 3–5 篇最相关文献，在句末插入 [PMID:xxxx] 标记，并生成候选参考文献列表。后续排版交给 format-references-endnote / format-references-zotero。

**English** — Auto-find references for a paper Markdown: identify citable claims (epidemiology, mechanisms, prior findings), PubMed-search 3–5 most relevant papers, insert [PMID:xxxx] markers at sentence ends, and emit a candidate reference list. Hand formatting to format-references-endnote / format-references-zotero.

## 核心能力 / Key Features

- 按知识点检索 3–5 篇文献 — 3–5 papers per citable claim
- 句末插入 [PMID:xxxx] 标记 — Inline [PMID:xxxx] markers
- 产出候选文献列表 — Candidate reference list

## 适用场景 / Use Cases

- 给初稿补引用
- 核实论点所需文献

## 快速开始 / Quick Start

- 中文：调用 Skill `find-paper-references`，附论文 Markdown。
- English：Invoke Skill `find-paper-references` with the paper Markdown.

## 安装 / Install

把本目录复制到 WorkBuddy 的 skills 目录：

```
# Windows
%USERPROFILE%\.workbuddy\skills\find-paper-references

# macOS / Linux
~/.workbuddy/skills/find-paper-references
```

## 许可 / License

未声明 (Unspecified) — 默认 MIT / Default MIT
