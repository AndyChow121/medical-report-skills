# Graph Interpretation · 医学科研图表解读器

> 中文 | English

## 简介 / Introduction

**中文** — 解读医学/生命科学图表与数据可视化。覆盖 8 类核心图表（ROC、KM、森林图、热图、散点、箱线、条形、显微镜图像等）的结构化统计解析、多受众说明、中英文期刊风格图注（cma/cslco/cebm/zhcore），以及批判性评价（含 TRIPOD / TRIPOD-AI 14 项）、SVG 重绘与 OCR 反向提取、TRIPOD-AI 14 维雷达图与 CSV 导出。自带自包含 samples，支持 demo / verify / validate / HTML 报告，可用于 CI 自动校验。

**English** — Interpret medical / life-science figures and data visualizations. Covers structured statistical parsing, multi-audience explanation, and CN/EN journal-style figure legends (cma/cslco/cebm/zhcore) for 8 core chart types (ROC, KM, forest, heatmap, scatter, box, bar, microscopy, etc.), plus critical appraisal (TRIPOD / TRIPOD-AI 14 items), SVG redraw & OCR reverse-extraction, and TRIPOD-AI 14-dimension radar chart with CSV export. Ships self-contained samples and supports demo / verify / validate / HTML reports for CI gating.

## 核心能力 / Key Features

- 8 类核心图表的结构化统计解析 — Structured statistical parsing for 8 core chart types
- 中英文期刊风格图注(cma/cslco/cebm/zhcore) — CN/EN journal-style legends (cma/cslco/cebm/zhcore)
- TRIPOD-AI 14 维雷达图 + CSV 导出 — TRIPOD-AI 14-dimension radar chart + CSV export
- verify / validate 自检，可接入 CI — verify / validate self-checks, CI-ready

## 适用场景 / Use Cases

- 学术论文图注撰写与图表批判性评价
- 临床研究数据解读、ML 预测模型评级
- 研究生带教、组会汇报的图表精讲

## 快速开始 / Quick Start

- 中文：调用 Skill `graph-interpretation`，上传图表数据(JSON/SVG/图片)即可生成图注与评级。
- English：Invoke Skill `graph-interpretation` with chart data (JSON/SVG/image) to generate legends and appraisal.

## 安装 / Install

把本目录复制到 WorkBuddy 的 skills 目录：

```
# Windows
%USERPROFILE%\.workbuddy\skills\graph-interpretation

# macOS / Linux
~/.workbuddy/skills/graph-interpretation
```

## 许可 / License

MIT
