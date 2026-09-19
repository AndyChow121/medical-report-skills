# Medical Literature Report · 医学文献解读报告

> 中文 | English

## 简介 / Introduction

**中文** — 面向临床（内科/外科/检验/护理/药学/公卫）与生物医学科研的英文医学文献一站式解读流水线：检索筛选 → 全文与补充材料合法核验 → 专业中文翻译 → 研究设计与统计方法解读 → 批判性评价与证据边界标注 → 实践启示 → 图文汇报 PPT → 文件归档。内置报告自检引擎（verify_report.py，9 道可运行关卡）与 GRADE 证据摘要、PRISMA 流程图、患者导向证据（NNT/NNH）、自我批判叙述等辅助生成器，并可端到端驱动 graph-interpretation 生成图注与 TRIPOD-AI 雷达图。

**English** — A one-stop pipeline for interpreting English medical literature in clinical (medicine/surgery/lab/nursing/pharmacy/public-health) and biomedical research contexts: search & screening, lawful full-text/supplement verification, professional Chinese translation, study-design & statistical-method interpretation, critical appraisal with evidence-boundary labeling, practice implications, illustrated PPT reporting, and archiving. Ships a self-check engine (verify_report.py, 9 runnable gates) plus GRADE Summary-of-Findings, PRISMA flow, patient-evidence (NNT/NNH), and self-critique generators, and can orchestrate graph-interpretation end-to-end for legends and TRIPOD-AI radar charts.

## 核心能力 / Key Features

- 全流程编排：检索→翻译→解读→报告→PPT — End-to-end orchestration: search → translate → interpret → report → PPT
- 自检门禁：9 道可机器化关卡(JSON+Markdown) — Self-check gate: 9 automatable gates (JSON + Markdown output)
- 图解读端到端编排(调用 graph-interpretation) — Figure-interpretation orchestration (drives graph-interpretation)
- 多受众输出：科室学习/组会/教学查房/科研汇报 — Multi-audience output: ward teaching / group meeting / journal club / research report

## 适用场景 / Use Cases

- 按专业方向/关键词/DOI/PMID 查找并比较文献
- 科室业务学习、研究生组会、文献精读、教学查房
- 把一篇英文论文快速变成中文解读 + 汇报 PPT

## 快速开始 / Quick Start

- 中文：在 WorkBuddy 中说「解读这篇文献 / 做一份医学文献报告」并附 PDF 或 PMID；或直接调用 Skill `medical-literature-report`。
- English：In WorkBuddy say "interpret this paper / make a medical literature report" with a PDF or PMID, or invoke Skill `medical-literature-report`.

## 安装 / Install

把本目录复制到 WorkBuddy 的 skills 目录：

```
# Windows
%USERPROFILE%\.workbuddy\skills\medical-literature-report

# macOS / Linux
~/.workbuddy/skills/medical-literature-report
```

## 许可 / License

MIT
