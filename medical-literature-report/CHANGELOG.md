# Changelog · medical-literature-report

## v1.2.0 — 2026-09-18 · 五大辅助生成器（"自我进化"第二步）

在 v1.1.0 自检引擎基础上，新增 5 个零依赖、各自带 `--self-test` 的辅助生成器，覆盖
证据合成、检索汇报、患者沟通、图解读编排与批判起稿：

- **`scripts/grade_sof.py`** (+ `references/grade-sof.md`)：GRADE Summary of Findings 证据摘要表，
  支持质量评级（高/中/低/极低）、降级理由、获益/伤害，可选 python-docx 导出。
- **`scripts/prisma_flow.py`** (+ `references/prisma-flow.md`)：PRISMA 2020 检索漏斗流程图
  （手工绘制 SVG，无 cairosvg 依赖）+ Markdown 文本漏斗。
- **`scripts/patient_evidence.py`** (+ `references/patient-evidence.md`)：患者导向证据换算，
  由 CER/EER 或 RR/OR/HR 计算 ARR/RRR/NNT/NNH 与患者友好表述。
- **`scripts/orchestrate_figures.py`** (+ `references/orchestrate-figures.md`)：端到端驱动
  `graph-interpretation` 生成图注/docx/SVG/TRIPOD-AI 雷达图并回填 `figures_generated/`；
  区别于 `verify_report --delegate-graphint`（仅校验），本器真正产出图解读素材。
- **`scripts/self_critique.py`** (+ `references/self-critique.md`)：从研究设计属性规则化生成
  优势/局限/适用性叙述与可编辑批判小结。
- SKILL.md：路由清单、新增「Auxiliary Generators」节、脚本命令区均接入 5 个生成器。
- 全量 `--self-test` 回归：6 个脚本（含 v1.1.0 的 verify_report）均 PASS。

## v1.1.0 — 2026-09-18 · 报告自检引擎（"自我进化"第一步）

- **新增 `scripts/verify_report.py`**：把 SKILL.md 的 Completion Gate 中可机器化的条目
  落地为 9 项质量关卡（G1–G9），零第三方依赖，输出 JSON（CI）+ Markdown（人读）。
  - G1 必备交付物齐全 / G2 文献身份与设计并核验 / G3 图表溯源完整
  - G4 证据标签与推理分离 / G5 证据规则越界启发式 / G6 PPTX 完整性与媒体
  - G7 交付物哈希一致（复用 `package_inventory.json`）/ G8 ML 论文 TRIPOD-AI 强制
  - G9 可选委托 `graph-interpretation` 做图解读级校验
- **新增 `references/verify-report.md`**：自检工作流、命令、目录约定、关卡明细、评分判定。
- **集成**：SKILL.md 路由清单、集成工作流第 16 步、脚本命令区、Completion Gate 均接入自检引擎。
- **自测**：`--self-test` 自带合成「合格/踩雷」样本，证明关卡可区分（good=0 fail / bad=4 fail）。
- 说明：本引擎无视觉能力，PPTX 排版/溢出/对比度等仍需人工视觉复核（已显式标注）。

## v1.0.0 — 初版

- 临床医学/检验/护理/药学/公卫/生物医学文献检索、合法全文核验、专业中文翻译、
  研究设计与统计方法解读、批判性评价、证据边界、专业实践启示、图文汇报 PPT、文件归档。
- 子能力路由：`literature-screening` / `source-acquisition` / `medical-translation` /
  `study-design-appraisal` / `figures-interpretation`（接 `graph-interpretation`）/
  `evidence-and-practice-interpretation`。
- 交付物脚本：`article_inventory.py` / `package_deliverables.py`。
