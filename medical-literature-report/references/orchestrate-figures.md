# graph-interpretation 端到端编排

`verify_report.py --delegate-graphint` 只是「委托校验」。本编排器更进一步：自动调用
`graph-interpretation` 把每张结果图**生成图注文档 / SVG / TRIPOD-AI 雷达图**，并回填到
报告目录，供 PPT 直接嵌入。

## 作业清单（报告目录下的 `figure_jobs.json`）

```json
[
  {"type": "roc_ml", "data": "sample_roc_ml.json", "figure_id": "图3",
   "style": "cma", "language": "zh", "with_svg": true, "radar": true},
  {"type": "km", "data": "sample_csco_gastric_km.json", "style": "cslco",
   "language": "zh", "figure_id": "图1"}
]
```

`data` 支持：绝对路径 / 报告目录内相对路径 / `graph-interpretation/scripts/` 下的
bundled sample 文件名（自动查找）。

## 命令

```bash
python scripts/orchestrate_figures.py <报告目录> --out orch_summary.json
python scripts/orchestrate_figures.py --self-test
```

## 每图执行步骤（best-effort，单步失败不中断）

1. `all` → `<图号>_all.json`（四档：interpret/caption/audiences/appraisal），核心步骤；
2. `to-legend --mode docx --with-svg` → `<图号>.docx`（需 python-docx，缺失则降级跳过）；
3. `render-svg` → `<图号>.svg`（需 cairosvg，缺失则降级跳过）；
4. ML 图追加 **TRIPOD-AI 雷达图** `<图号>_radar.svg`。

产物落在 `<报告目录>/figures_generated/`，PPT 制作时直接引用。

## 回填到 PPT

- 把 `<图号>.svg` / `<图号>_radar.svg` 作为原始证据对象嵌入对应结果页；
- 把 `<图号>.docx` / `<图号>_all.json` 的 caption + audiences 文本贴入「图注/受众解读」区；
- 在「批判性评价」页引用 appraisal 的 TRIPOD/TRIPOD-AI 条目与雷达图。

## 边界

- 本编排器**不替代** graph-interpretation 的图数据解析；它只负责调度与回填。
- 子技能未安装时优雅跳过，仅输出规划摘要（不报错）。
- docx/SVG 的依赖（python-docx / cairosvg）缺失时对应步骤失败但不阻断整体。
