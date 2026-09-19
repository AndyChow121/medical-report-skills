# 图解读接入（graph-interpretation v1.3.0）

在文献报告流水线中遇到数据图表（KM/Forest/ROC/Box/Scatter/Bar/Heatmap/Volcano）时，通过 `graph-interpretation` 技能做结构化解析、批判性评价与受众化解读，再把结果回填到翻译、PPT、图注。

> **v1.3.0 新增能力**：ML/DL 预测模型论文自动追加 **TRIPOD-AI 14 条**；`--all` 一次性输出四档；`models.py` 公开数据模型；CSCO 真实风格 cslco caption；14 维雷达图。

## 调用时机

满足下列**任意**条件时调用：

- 用户提供了 PDF 全文，且内有 ≥1 张核心结果图（KM/Forest/ROC 等）；
- 用户显式要求"解读图 X"、"评估这张森林图的偏倚"；
- 准备 PPT 时需要为图表生成图注、受众解读或质量评价；
- 论文为 **机器学习预测模型**（含神经网络 / XGBoost / Transformer 等），需追加 TRIPOD-AI 评价。

## 调用方式

`graph-interpretation` 工作目录：`~/.workbuddy/skills/graph-interpretation/`

### 1. ML/DL 论文自动追加 TRIPOD-AI（v1.2.0+）

在 ROC / Scatter 图的 JSON 数据中，只要声明 `model_type` 字段含 ML 关键词
（`XGBoost / LightGBM / CatBoost / Random Forest / neural_network / ResNet / Transformer / BERT / LogisticRegression` 等），`auto_evaluate` 会自动追加 14 条 TRIPOD-AI 评价：

```bash
python ~/.workbuddy/skills/graph-interpretation/scripts/main.py \
  appraise --type roc --data sample_roc_ml.json
# 框架自动变为 "STARD + TRIPOD + TRIPOD-AI"，共 8 + 7 + 14 = 29 条
```

完整 ML 字段示例（参考 `sample_roc_ml.json`）：

```json
{
  "model_type": "XGBoost",
  "data_source": "MIMIC-IV (2008-2019)",
  "events_per_predictor": 18.5,
  "split_strategy": "temporal (train: 2008-2014, test: 2015-2019)",
  "internal_validation": "10-fold CV",
  "external_validation_temporal": true,
  "external_validation_geographic": true,
  "calibration_slope": 0.98,
  "calibration_intercept": 0.01,
  "brier_score": 0.078,
  "explainability_method": "SHAP",
  "fairness_assessed": true,
  "decision_curve": true,
  "code_availability": "github.com/.../icu-xgb",
  "model_version_pinned": true,
  "bias_assessed": true
}
```

### 2. 端到端一次性四档（v1.3.0 `--all`）

```bash
python ~/.workbuddy/skills/graph-interpretation/scripts/main.py \
  all --type roc --data sample_roc_ml.json \
  --style cma --language zh --locale zh_CN --figure-id "图3" \
  --out all_outputs.json
```

输出 JSON 结构（13KB 示例）：

```json
{
  "chart_type": "roc_curve",
  "figure_id": "图3",
  "style": "cma",
  "language": "zh",
  "locale": "zh_CN",
  "interpret": { ...StatisticalSummary... },
  "caption": "图3 中文图注...",
  "audiences": {
    "researchers": "...",
    "clinicians": "...",
    "patients": "...",
    "policy_makers": "..."
  },
  "appraisal": { ...AppraisalResult 含 29 条 TRIPOD+TRIPOD-AI... }
}
```

### 3. 中文学术图注（4 套）

```bash
# CMA 中华医学会风格
python main.py caption --type roc --data sample_roc_ml.json --style cma --language zh

# CSCO 指南风格（v1.2.0+ 真实中国语境；要求数据含 patient_population_zh / study_design /
#                    csco_recommendation_level / included_in_cslco_guideline / 等等）
python main.py caption --type km --data sample_csco_gastric_km.json \
  --style cslco --language zh --figure-id "图1"
# 输出示例：
# 图1 Apatinib vs Placebo for Pretreated Advanced Gastric Cancer: Overall Survival
# 研究人群：既往二线化疗失败的转移性/局部晚期胃腺癌或胃食管结合部腺癌。
# 研究设计：Phase III 双盲 RCT，多中心（中国 32 家中心）。
# 结果发现，（HR=0.71，95% CI 0.54-0.93，p=0.014，n=273）。
# 指南纳入：已纳入《CSCO 胃癌诊疗指南》2023 版；治疗药物已获 NMPA 批准；FDA 已批准该适应证。
# CSCO 推荐意见：Ⅰ级推荐 / 1A 类证据；亚组分析未发现显著异质性。

# 中国循证医学杂志风格（PICO 结构）
python main.py caption --type km --data sample_km.json --style cebm --language zh

# 中文核心通用兜底
python main.py caption --type roc --data sample_roc.json --style zhcore --language zh
```

### 4. SVG 重绘 + 雷达图（v1.3.0）

```bash
# KM/Forest/ROC 8 类重绘
python main.py render-svg --type roc --data sample_roc_ml.json --out fig.svg

# TRIPOD-AI 14 维雷达图（ML 模型）
python -c "
import sys; sys.path.insert(0, '~/.workbuddy/skills/graph-interpretation/scripts')
from appraisal import auto_evaluate
from parsers import PARSERS
from tripod_ai_radar import render_tripod_ai_radar
result = auto_evaluate(PARSERS['roc_curve'].parse(json_data))
Path('radar.svg').write_text(render_tripod_ai_radar(result), encoding='utf-8')
"

# 端到端 docx（含 SVG + 中文 caption + 评价清单）
python main.py to-legend --type roc --data sample_roc_ml.json \
  --mode docx --with-svg --style cma --language zh --out figure_3_zh_ai.docx
```

### 5. 公开数据模型（v1.3.0）

外部脚本直接复用 dataclass：

```python
from models import (
    StatisticalSummary, EffectEstimate,  # 数据契约
    ChecklistItem, AppraisalResult,       # 评价模型
)

# 实例化或从 appraisal.auto_evaluate() 拿到的就是 AppraisalResult
result.to_dict()                       # 序列化
result.by_framework()                  # 按框架分组
result.overall_score                   # 已评估条目通过率
```

## 三档产物（回填到 source fact sheet）

```markdown
### Figure X（按 graph-interpretation 输出）

- **Chart type**: kaplan_meier / forest_plot / ...
- **Primary effect**: HR=0.72 (95% CI 0.58-0.89), p=0.003, N=480
- **Statistical commentary**: 实验组 vs 对照组中位 OS 19.6 vs 14.2 个月，HR 0.72 代表死亡风险下降约 28%
- **Quality flags**:
  - KM-2 ✓ at-risk table
  - KM-3 ✓ log-rank p
  - KM-4 ✓ Schoenfeld p=0.42
  - KM-5 ✗ 未报告删失率（人工核实）
  - **TRIPOD-AI 触发**（如 model_type=XGBoost）：
    - TRIPOD-AI-6 时间外部验证 ✓
    - TRIPOD-AI-9 SHAP 可解释性 ✓
    - TRIPOD-AI-12 代码公开 ✓
- **Patient-friendly phrasing**: 每 100 人用药 1 年，多约 5 人避免主要终点事件
- **Reproducibility note**: 数据可在 main.py ocr --pdf 链路复现
- **Radar figure**（如适用）：见 `radar.svg`，可视化 14 维评分
```

## 与其它节点的衔接

| 节点 | 图解读产物用途 |
|------|---------------|
| 文献筛选（literature-screening） | Forest plot 的 I²/异质性 → 评价"纳入研究的代表性" |
| 全文获取（source-acquisition） | OCR 抽取失败 → 提示"需获取原始数据图" |
| 中文翻译（medical-translation） | StatisticalSummary 数字精度 → 翻译一致性校验 |
| 研究设计评价（study-design-appraisal） | 对 RCT/RWE/Diagnostic 的图表分别施加 CONSORT/STARD/PRISMA 检查；ML 论文额外触发 TRIPOD-AI |
| 报告与 PPT（report-standard） | caption / audiences / SVG / radar 图直接当 PPT 素材 |

## 数据契约

每个图表的最小 JSON 结构见 `~/.workbuddy/skills/graph-interpretation/references/chart-types.md`。
如果 PDF 抽取得到的关键数字与正文表格/文字冲突，把 conflict 写到 discrepancy log（图解读层级）。

## 反向链路（figure-legend-gen 重出图）

如果用户已有图解文件并希望重画：

```bash
# Step 1: OCR 读文字统计量
python graph-interpretation/scripts/main.py ocr --pdf article.pdf  > stats.json

# Step 2: 整理成可消费 JSON（按 stats.json 内容手动整理 sample_*.json 形式）

# Step 3: SVG 重绘
python graph-interpretation/scripts/main.py render-svg \
  --type forest --data sample_forest.json --out fig2.svg

# Step 4: 调 figure-legend-gen 把 SVG/截图生成图注
python ~/.workbuddy/skills/figure-legend-gen/scripts/main.py \
  --input fig2.svg --type bar --language zh
```

## ML/DL 论文特化流程

当论文为预测模型研究时，按以下流程跑：

1. `ocr --pdf` → 抽出 AUC / 置信区间 / 模型类型
2. 把 ML 字段（model_type / external_validation_* / calibration / SHAP / DCA / code_availability / bias_assessed 等）写入 JSON
3. `all --type roc --style cma --language zh --locale zh_CN --out all.json`
4. `to-legend --mode docx --with-svg` 生成 docx
5. 用 `tripod_ai_radar.render_tripod_ai_radar()` 生成 14 维雷达图
6. 把 docx + 雷达图 + all.json 三件套打包进交付

## 边界与依赖

- `graph-interpretation` 仅做**图表数据层**（数字、统计量、图注文字、SVG 重绘）。不替代研究设计层评价。
- 对诊断准确性研究，**STARD / TRIPOD** 等框架的"整体"质量评价仍归 `study-design-appraisal`；图表层级评价（ROC-1~8）由 graph-interpretation 提供。
- ML 论文的 **TRIPOD-AI 14 条**仅在 `model_type` 命中关键词时触发；其他条目同样适用。
- 集成时注意 `graph-interpretation` ≥ v1.3.0，本目录是其调用入口。
