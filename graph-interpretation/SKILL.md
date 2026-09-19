---
name: graph-interpretation
description: 解读医学/生命科学图表与数据可视化：8 类核心图表的结构化统计解析、多受众说明、中英文期刊风格图注（含 cma/cslco/cebm/zhcore）、批判性评价（含 TRIPOD/TRIPOD-AI 14 项）、SVG 重绘与 OCR 反向提取、TRIPOD-AI 14 维雷达图、TRIPOD-AI 14 维 CSV 导出、pip install . 安装形态、figure-legend-gen 跨 Skill 共享 StatisticalSummary、bundled samples 自包含 demo / verify / validate / HTML 报告、TRIPOD-AI 字段缺失警示 docx。用于学术论文图注撰写、临床研究数据解读、研究生带教与组会汇报、ML 预测模型评级、CI 自动化校验。
allowed-tools: "Read Write Bash Edit Bash"
license: MIT
metadata:
  skill-author: AIPOCH
  version: "1.6.0"
  displayName: "医学科研图表解读器"
  slug: graph-interpretation
  updated: "2026-09-05"
---

# 医学科研图表解读器 v1.6.0

覆盖 8 类核心图表的结构化解析、多受众说明（支持中文语境）、中英文期刊风格图注（CMA / CSCO / CEBM / Nature / Lancet / JAMA / Cell / NEJM / 中文核心）、Cochrane/GRADE/STARD/CONSORT/MIAME + TRIPOD/TRIPOD-AI 共 67+14 项评价、8 类图表数据→SVG 重绘、PNG/JPG/PDF 反向 OCR 抽取、端到端 .docx 输出（支持嵌入 SVG）、`--all` 端到端四档 JSON、`models.py` 公开数据模型、TRIPOD-AI 14 维雷达图可视化、`export-csv` Excel 中文友好、`pip install .` 安装形态（CLI 入口 `graph-interp`）、bundled samples（21 个打入 wheel）、`demo` 一键跑通、`verify` CI 自检、`validate` JSON Schema 校验、HTML 单文件报告、TRIPOD-AI sentinel docx 字段缺失警示、**`diff` 子命令（左右样本对照）**、**HTML dark mode + 响应式 + print**、**`verify --fail-on-low-score` / `--fail-on-missing` CI 阈值**、**GitHub Actions CI（pytest 70 + verify/validate/diff 冒烟）**、**calibration 子图（ML 评估并排）**。

## 安装（v1.6.0）

```bash
cd ~/.workbuddy/skills/graph-interpretation
pip install .              # 真实安装，依赖 python-docx
pip install -e .           # 开发模式
pip install .[all]         # 含 pdfplumber + cairosvg + pillow
```

安装后 `graph-interp --help` 注册命令，**14 个子命令**：
`interpret / caption / audiences / appraise / render-svg / ocr / to-legend / demo / verify / validate / export-csv / all / check / diff`。

无 pip 环境下，也可保持原 `python scripts/main.py ...` 调用方式。

## 新增子命令速查（v1.5.0）

```bash
# 1. demo: 跑通 bundled samples（pip install 后无需外网数据）
graph-interp demo                          # 8 类基础 sample 摘要
graph-interp demo --type roc_ml            # ML 场景深度 demo（额外 render-svg + docx）
graph-interp demo --type csco_km --out-dir ./out

# 2. verify: CI 自检（10 sample × 6 步链路）
graph-interp verify --cleanup              # 跑完后自动清理
graph-interp verify --work-dir artifacts   # 保留产物

# 3. validate: JSON Schema 校验
graph-interp validate --list-schemas
graph-interp validate --show-schema roc_curve
graph-interp validate --data data.json --type km
graph-interp validate --data data.json --type roc_ml

# 4. to-legend --mode html: 单文件 HTML 报告
graph-interp to-legend --type roc_ml --mode html --with-svg \
    --figure-number 1 --language zh --style cma --out fig.html

# 5. to-legend --mode docx --ai-sentinel: TRIPOD-AI 字段缺失警示
graph-interp to-legend --type roc --data sample_roc_partial_ml.json \
    --mode docx --style cma --language zh \
    --ai-sentinel auto    # auto/force/off
# 自动生成 *_sentinel.docx 警示（ML 触发 + 字段 < 7 时）
```

## 数据模型（v1.3.0+ 稳定）

```python
from models import (
    StatisticalSummary,     # 统一统计摘要（含 raw 字段字典）
    EffectEstimate,         # 点估计 + 区间估计 + p 值
    ChecklistItem,          # 单条评价项
    AppraisalResult,        # 评价汇总（n_items/n_passed/overall_score/to_dict()）
)
```

`figure-legend-gen` 已接入同一份模型：`LegendGenerator.from_statistical_summary(summary, figure_number)` 直接接收 KM/Forest/ROC/Box/Scatter/Bar/Heatmap/Volcano 的输出渲染分子生物图注。

## bundled samples（v1.5.0，21 个打入 wheel）

通过 `importlib.resources` 在 wheel 安装态可读，`pip install .` 后无需下载外网数据。

| alias | chart_type | 场景 |
|-------|------------|------|
| `km` / `kaplan_meier` / `kaplan` | kaplan_meier | OS by treatment arm（HR=0.72） |
| `forest` / `forest_plot` | forest_plot | 4 研究 OR 汇总（I²=32%） |
| `roc` / `roc_curve` | roc_curve | 诊断模型（AUC=0.86） |
| `roc_ml` / `roc_curve_ml` | roc_curve | ICU XGBoost 死亡风险预测（AUC=0.91，TRIPOD-AI 14 项齐全） |
| `roc_partial_ml` / `roc_curve_partial_ml` | roc_curve | XGBoost + 仅超参，触发 sentinel docx |
| `box` / `box_plot` | box_plot | Tumor size by genotype |
| `scatter` / `scatter_plot` | scatter_plot | Calibration plot |
| `bar` / `bar_chart` | bar_chart | Expression by treatment |
| `heatmap` | heatmap | Gene expression 5×5 matrix |
| `volcano` / `volcano_plot` | volcano_plot | Differential expression（10 基因） |
| `csco_km` / `csco_gastric_km` | kaplan_meier | CSCO 胃癌 apatinib III 期 RCT（中国语境） |
| `km_svg` | kaplan_meier | KM 数据 + 现成 SVG 路径 |

```bash
graph-interp demo                       # 跑遍 8 类基础 sample
graph-interp demo --type roc_ml         # 单类深度 demo（额外 render-svg + docx）
python -m scripts._samples              # 自检 21 个 sample
```

## TRIPOD-AI sentinel docx（v1.5.0）

自动检测逻辑：`_is_ml_model(raw)` + 14 项标准字段已报告数 < 7（即阈值 `_SENTINEL_THRESHOLD = 7`）。

触发时自动生成 `<主docx>_sentinel.docx`，含：
- 橙色标题"⚠️ TRIPOD-AI 字段缺失警示"
- ML 触发方式（model_type / methodology / 超参字段）
- 缺失字段清单（红色）
- 已报告字段清单（绿色）
- 14 项空白模板（待人工补全的 3 列表格）
- 5 步后续建议

CLI 控制：`--ai-sentinel {auto,force,off}`，默认 `auto`。

## 评价清单数（v1.5.0）

| 图表 | 主框架 | 自动评价数 | 触发 TRIPOD-AI 时 |
|------|--------|------------|-------------------|
| KM | CONSORT + Cochrane RoB 2 | 8 | – |
| Forest | Cochrane + GRADE | 9 | – |
| ROC | STARD + TRIPOD | 15 | +14（AI 模型时） |
| Scatter | STARD + TRIPOD-calibration | 9 | +14 |
| Box | CONSORT + Cochrane | 7 | – |
| Bar | CONSORT + Cochrane | 7 | – |
| Heatmap | MIAME + Cochrane | 6 | – |
| Volcano | MIAME + Cochrane | 6 | – |

## 常用 CLI 速查

```bash
# 快速评价 + 雷达图
graph-interp appraise --type roc --data sample_roc_ml.json
graph-interp render-svg --type roc --data sample_roc_ml.json --out radar.svg

# TRIPOD-AI 14 条 → CSV（Excel 中文友好，自带 UTF-8 BOM）
graph-interp export-csv --type roc --data sample_roc_ml.json --out t_ai.csv

# 中文期刊图注 + 中国语境受众 + 端到端 docx
graph-interp to-legend --type roc --data sample_roc_ml.json --mode docx \
    --with-svg --style cma --language zh --figure-id "图3" \
    --out figure_3.docx

# 一次性四档
graph-interp all --type roc --data sample_roc_ml.json \
    --style cma --language zh --locale zh_CN --figure-id "图3" --out all.json

# 单文件 HTML 报告（含雷达图）
graph-interp to-legend --type roc_ml --mode html --with-svg \
    --style cma --language zh --figure-number 3 --out fig3.html

# JSON Schema 校验
graph-interp validate --list-schemas
graph-interp validate --data sample_km.json --type km

# 自检
graph-interp check
graph-interp verify --cleanup
```

## 跨 Skill 桥接

- **`medical-literature-report`**：`references/figures-interpretation.md` 指引把图解读节点接入；PDF/SVG 双链路；支持 TRIPOD-AI / 中文 caption / 雷达图
- **`figure-legend-gen`**：`LegendGenerator.from_statistical_summary()` 直接接收 `StatisticalSummary`（KM → LINE / ROC → SCATTER / Forest → LINE / Box → BOX / Bar → BAR / Heatmap → HEATMAP / Volcano → BAR）

## JSON Schema（v1.5.0）

8 类图表 schema + 手写轻量校验器（无第三方依赖）：

- 类型 + 必填字段 + 数字范围（minimum/maximum）
- 数组长度（minItems/maxItems）+ 元素子 schema
- enum 限定（如 measure ∈ {OR, RR, HR, MD, SMD}）
- 多描述形式支持（box 五数概括/values；bar series[]/values；volcano gene/name）

```python
from _schema import validate_payload
ok, errors = validate_payload(data_dict, "roc_curve")
```

## 已知限制

- cairo/cairosvg 在 Windows 默认未安装，`to-legend --with-svg` 会降级为 docx 文本块
- TRIPOD-AI EPP 推荐 ≥10 来自 Riley et al. 2019，可在 `references/guidelines.md` 中查阅
- 编辑模式下 `pip install -e .` 修了 `scripts/` 后需重启 Python 进程
- HTML 报告嵌入雷达图依赖 `tripod_ai_radar.render_tripod_ai_radar(appraisal)`；非 ML 模型时不渲染雷达图

详细 SKILL 说明与历史命令见 `scripts/main.py --help` 与 `references/`、`CHANGELOG.md`。