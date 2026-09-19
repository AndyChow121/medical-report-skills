# graph-interpretation Changelog

## v1.6.0 — 2026-09-05

### 新增
- **`graph-interp diff` 子命令**：左右两个 appraisal JSON 对照，输出 `added / removed / changed / unchanged` 集合
  - 支持 `--type X --format {table,markdown,json}`
  - 自动类型推断（bundled sample 无 `chart_type` 字段时从别名推断）
  - 自然排序修复（`TRIPOD-AI-10` 不再排到 `TRIPOD-AI-2` 前）
  - 跨类型比对告警（如 `km vs roc_ml`）
  - CLI 子命令 + Python API `scripts._diff.diff_appraisals(left, right)`
- **HTML 报告 dark mode + 响应式**：
  - CSS 变量体系（`--bg / --fg / --accent / --border / --pass / --fail / --skip` 等 15 个）
  - `prefers-color-scheme: dark` 自动适配 + `<html data-theme="...">` 强制覆盖
  - `theme: {auto, light, dark}` 三档可选（CLI `--theme`）
  - `@media (max-width: 720px)` 移动端响应式
  - `@media print` 打印样式
  - `.figure-row` 双图并排（calibration 子图）
- **`graph-interp verify` CI 阈值**：
  - `--fail-on-low-score FLOAT`：得分低于阈值的样本视为失败
  - `--fail-on-missing INT`：缺失字段 ≥ N 的样本视为失败
  - 退出码 = 失败样本数（CI 可直接基于退出码 fail-pass）
  - 输出按得分升序汇总表，便于瓶颈定位
- **GitHub Actions CI**：
  - `.github/workflows/ci.yml`，Python 矩阵 3.10 / 3.11 / 3.12 / 3.13
  - 六阶段：install `.[all]` → pytest → verify → validate（8 类 schema 循环） → diff 冒烟 → build wheel
  - YAML 经 PyYAML 校验
- **calibration 子图**（ML 评估补全）：
  - `scripts/svg_render.py` 新增 `render_calibration(data, title="Calibration plot")`
  - 优先用 `calibration_points`（实测分位点）；缺失时用 `calibration_slope / intercept / brier_score` 按 Cox 校准回归 `logit(obs) = intercept + slope × logit(pred)` 合成
  - slope < 0.9 标"overfitted"，> 1.1 标"underfitted"
  - 无 calibration 数据返回空串，自动跳过
  - `to_legend_docx` 集成：ML 触发时 ROC + Calibration 并排 `.figure-row` 网格
  - 非 ML 场景（KM/Forest/Box/Bar/Heatmap/Volcano/非 ML scatter）不误添加
- **pytest 测试套件**（70 测试全过 / 0.47s）：
  - `tests/conftest.py`：`SAMPLES_DIR` 路径、bundled sample 列表 fixture
  - `tests/test_parsers.py`：8 类 parser 解析正确性
  - `tests/test_schema.py`：8 类 JSON Schema 校验
  - `tests/test_diff.py`：diff 算法（added/removed/changed/unchanged + 类型推断 + 自然排序）
  - `tests/test_end_to_end.py`：to-legend docx/HTML 端到端链路
- **`references/verify-recipe.md` 新增 v1.6.0 CI 章节**：fail-on-low-score / fail-on-missing 用法 + GitHub Actions 集成示例

### 改进
- **`models.py` `__version__` → 1.6.0**
- **`pyproject.toml` version → 1.6.0** + description 增补 v1.6.0 特性
- **`SKILL.md`**：14 子命令清单、v1.6.0 安装章节、6 个新特性加粗
- **HTML CSS 重构**：从行内样式集中到 `_HTML_CSS`，便于 dark/responsive/print 维护
- **`verify` 子命令输出**：新增按得分排序的汇总表（含平均分 / 字段完整度）

### CLI 子命令（v1.6.0，14 个）

```bash
graph-interp interpret / caption / audiences / appraise
graph-interp all --type X --data Y --out all.json
graph-interp export-csv --type X --data Y --out t.csv
graph-interp render-svg --type {km,forest,roc,box,scatter,bar,heatmap,volcano}
graph-interp ocr --image / --pdf / --text
graph-interp to-legend --mode {context,fields,docx,html}   # +html dark mode
graph-interp check
graph-interp demo [--type alias]
graph-interp verify [--no-ml] [--no-zh] [--fail-on-low-score F] [--fail-on-missing N]
graph-interp validate [--list-schemas / --show-schema X / --data X.json]
graph-interp diff left.json right.json [--type X] [--format {table,markdown,json}]   # v1.6.0 NEW
```

### 端到端产物示例（v1.6.0）

- `demo_v150.html` / `demo_v160_dark.html`：dark mode + 响应式 HTML 报告
- `demo_sentinel.docx` / `demo_sentinel_sentinel.docx`：TRIPOD-AI 警示 docx
- `.github/workflows/ci.yml`：CI 工作流（70 pytest + verify/validate/diff 冒烟）

### 已知限制

- cairo/cairosvg 在 Windows 默认未安装，`to-legend --with-svg` 会降级为 docx 文本块
- TRIPOD-AI EPP 推荐 ≥10 来自 Riley et al. 2019
- `pip install -e .` 修了 `scripts/` 后需重启 Python 进程
- `--cleanup` 标志触发批量删除保护时建议改用 `--work-dir .vtest` 自管理临时目录

---

## v1.5.0 — 2026-09-05

### 新增
- **Bundled samples 打包**：21 个 sample_*.json / sample_*.svg 打入 wheel，`graph-interp demo` 直接用，无需外网下载
- **`graph-interp demo` 子命令**：跑遍 bundled samples（8 类基础 + ML + 中文）；支持 `--type <alias>` 单类深度 demo（额外 render-svg + to-legend docx）
- **TRIPOD-AI sentinel docx**：自动检测 ML 触发但标准字段 < 7 时，并行输出橙色警示 docx，含缺失字段清单、已报告字段清单、14 项空白模板、自动建议
  - CLI：`--ai-sentinel {auto,force,off}`，默认 auto
  - 阈值：`_SENTINEL_THRESHOLD = 7`
- **`graph-interp verify` 子命令**：CI 友好的全样本端到端自检（10 sample × 6 步链路：interpret + caption + audiences + appraise + render-svg + to-legend docx）
  - `--no-ml` / `--no-zh` 关闭部分场景
  - `--work-dir` / `--cleanup` 控制产物目录
  - 退出码 = 失败样本数（0 = 全部通过）
  - 详见 `references/verify-recipe.md`
- **HTML 单文件报告**：`graph-interp to-legend --mode html` 输出自包含 HTML（inline CSS + SVG + 雷达图），可直接浏览器/微信分享
  - 自动检测 ML 时内嵌 TRIPOD-AI 14 维雷达图
  - `--with-svg` 启用图表重绘 SVG
- **JSON Schema + `graph-interp validate`**：
  - 8 类图表 schema + 手写轻量校验器（无第三方依赖）
  - `--list-schemas` / `--show-schema <name>` / 校验 JSON 数据
  - 支持 schema 字段多种描述形式（box: q1/median/q3 五数概括；bar: series[].values；volcano: gene/name 双命名）
- **heatmap parser 修复**：v1.4.0 时只透传 `n_rows / n_cols`，v1.5.0 透传整个 data dict，使 `legend_bridge` 能拿到 `row_labels / col_labels / matrix`，修复 docx/HTML/verify 中的 heatmap 渲染
- **`references/verify-recipe.md`**：CI 接入 GitHub Actions / 本地 CI 完整配方

### 改进
- **`models.py` `__version__` → 1.5.0**
- **`_type_alias` 扩展**：新增 `roc_ml / roc_curve_ml / csco_km / csco_gastric_km / km_svg / scatter_ml` 映射到标准 8 类
- **`cmd_to_legend` 自动 bundled sample**：未提供 `--data` 时自动从 bundled sample 加载（特别是 `to-legend --type roc_ml` 直跑 ML 场景）
- **parser 兼容性**：`heatmap` 透传 data；`to_legend_docx.render_chart_legend` 给 heatmap 类型 kwargs 补 `dimensions` 默认值
- **MANIFEST.in / pyproject.toml `package-data`**：sample 数据同时支持 sdist 和 wheel 安装态

### CLI 子命令（v1.5.0，13 个）

```bash
graph-interp interpret / caption / audiences / appraise
graph-interp all --type X --data Y --out all.json   # v1.3.0
graph-interp export-csv --type X --data Y --out t.csv  # v1.4.0
graph-interp render-svg --type {km,forest,roc,box,scatter,bar,heatmap,volcano}
graph-interp ocr --image / --pdf / --text
graph-interp to-legend --mode {context,fields,docx,html}   # v1.5.0 +html
graph-interp check
graph-interp demo [--type alias]   # v1.5.0 NEW
graph-interp verify [--no-ml] [--no-zh]   # v1.5.0 NEW
graph-interp validate [--list-schemas / --show-schema X / --data X.json]   # v1.5.0 NEW
```

### 端到端产物示例

- `figure_3_zh_ai_cma.docx`（39KB，CMA 风格 + 嵌入 SVG + 29 项评价）
- `figure_3_zh_ai_cma_sentinel.docx`（38KB，TRIPOD-AI 字段缺失警示，仅缺字段场景）
- `figure_3_zh_ai.html`（19.5KB，单文件 HTML 报告，含雷达图）
- `tripod_ai_demo.csv`（UTF-8 BOM Excel 中文友好）
- `tripod_ai_radar_ml.svg` / `tripod_ai_radar_partial.svg`（14 维雷达图）

### 已知限制

- cairo/cairosvg 在 Windows 默认未安装，`to-legend --with-svg` 会降级为 docx 文本块
- TRIPOD-AI EPP 推荐 ≥10 来自 Riley et al. 2019
- `pip install -e .` 修了 `scripts/` 后需重启 Python 进程
- heatmap docx 的 `dimensions` 默认值兜底仅在 `legend_bridge.to_legend_fields` 返回空时生效

---

## v1.4.0 — 2026-09-05

### 新增
- 60+ ML/DL/LLM 关键词（含 TabNet/causal_forest/federated/diffusion/RL + GPT-4/Claude/Qwen/Gemini/DeepSeek + Foundation model/fine-tuning/RAG/few-shot）
- 13 个超参字段（learning_rate/epochs/batch_size/loss_fn/optimizer 等）
- TRIPOD-AI CSV 导出（`graph-interp export-csv`，UTF-8 BOM）
- pip install . 打包形态（graph-interp CLI 入口）
- figure-legend-gen 跨 Skill 共享 `StatisticalSummary`（`LegendGenerator.from_statistical_summary`）

### 改进
- 模型定义单源化（models.py 导出 StatisticalSummary / EffectEstimate / ChecklistItem / AppraisalResult）
- sentinel "TRIPOD-AI-0" 自动兜底（ML 触发但 14 项无字段时）
- 完整修复合并入 v1.5.0 的 TRIPOD-AI sentinel docx

---

## v1.3.0 — 2026-09-04

### 新增
- `models.py` 公开数据模型
- CSCO 真实世界样本（sample_csco_gastric_km.json）
- `--all` 一次性输出 interpret + caption + audiences + appraisal 四档 JSON
- TRIPOD-AI 14 维雷达图（tripod_ai_radar.py）
- medical-literature-report skill 整合

---

## v1.2.0 — 2026-09-03

### 新增
- 中文期刊 caption 模板（cma / cslco / cebm / zhcore）
- China-context audiences（`--locale zh_CN`）
- TRIPOD-AI 评价框架（14 条 ML/DL）
- SVG 嵌入 docx（`--with-svg`）

---

## v1.1.0 — 2026-09-01

### 新增
- 多受众解读（researchers / clinicians / patients / policy_makers）
- 期刊风格 caption（Nature / Lancet / JAMA / Cell / NEJM）
- 评价清单（CONSORT / Cochrane RoB 2 / STARD / MIAME）

---

## v1.0.0 — 2026-08-28

### 初版
- 8 类核心图表解析器
- CSV / Excel 友好的中文 caption