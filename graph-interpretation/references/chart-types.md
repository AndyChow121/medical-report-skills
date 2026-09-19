# 8 类图表数据契约

所有解析器都从 JSON dict 读入，输出统一的 `StatisticalSummary`。
下面是每类图表的最小可用 JSON 结构（仅列出关键字段，缺失字段会被解析器忽略或填默认）。

## 1. kaplan_meier

```json
{
  "title": "OS by treatment",
  "hazard_ratio": 0.72,
  "hr_ci": [0.58, 0.89],
  "p_value": 0.003,
  "n_total": 480,
  "arms": [
    {"name": "Experimental", "median_survival": 19.6},
    {"name": "Control", "median_survival": 14.2}
  ],
  "at_risk": {"Experimental": [240, 220, 180, 120], "Control": [240, 200, 150, 90]},
  "schoenfeld_p": 0.42,
  "censoring_rate": 0.18
}
```

- `hazard_ratio` 或 `hr` 都可识别
- `schoenfeld_p > 0.05` 视为满足比例风险假设
- `at_risk` 为可选风险表（dict 或 list）

## 2. forest_plot

```json
{
  "title": "All-cause mortality",
  "measure": "OR",
  "model": "random",
  "i_squared": 32.5,
  "heterogeneity_p": 0.18,
  "overall_effect": 0.85,
  "overall_ci": [0.74, 0.98],
  "overall_p": 0.025,
  "studies": [
    {"name": "Study A", "effect": 0.78, "ci": [0.62, 0.98], "weight": 0.28, "n": 412}
  ],
  "eggers_p": 0.21,
  "publication_bias": "low"
}
```

- `measure` ∈ {`OR`, `HR`, `RR`, `MD`, `SMD`}，决定 CI 解读
- `model` ∈ {`fixed`, `random`}
- `weight` 总和通常 ≈ 1.0

## 3. roc_curve

```json
{
  "title": "Diagnostic model",
  "auc": 0.86,
  "auc_ci": [0.81, 0.91],
  "optimal_cutoff": 0.45,
  "sensitivity": 0.82,
  "specificity": 0.78,
  "delong_p": 0.012,
  "curves": [
    {"name": "Model A", "auc": 0.86, "ci": [0.81, 0.91], "points": [[0,0], [0.1,0.3], [1,1]]}
  ]
}
```

- 单条曲线可只填 `auc` + `auc_ci`
- 多条曲线比较时填 `curves`，并用 `delong_p` 报告显著性

## 4. box_plot

```json
{
  "title": "Expression levels",
  "groups": [
    {"name": "Control", "median": 1.2, "q1": 0.8, "q3": 1.7, "whisker_low": 0.3, "whisker_high": 2.4, "outliers": [3.1], "n": 24},
    {"name": "Treatment", "median": 2.1, "q1": 1.5, "q3": 2.8, "whisker_low": 0.9, "whisker_high": 3.5, "n": 25}
  ],
  "test": "Mann-Whitney U",
  "p_value": 0.004
}
```

## 5. scatter_plot

```json
{
  "title": "Biomarker correlation",
  "r": 0.72,
  "p_value": 0.001,
  "n": 96,
  "slope": 1.42,
  "intercept": 0.18,
  "ci_95": "shaded band",
  "outliers": ["sample_42"]
}
```

## 6. bar_chart

```json
{
  "title": "Tumor volume",
  "groups": [
    {"name": "Vehicle", "mean": 850, "error": 120, "error_type": "SEM", "n": 8},
    {"name": "Drug A",   "mean": 420, "error": 90,  "error_type": "SEM", "n": 8}
  ],
  "test": "two-way ANOVA + Tukey",
  "p_value": 0.012,
  "significance": ["**", "***"]
}
```

- `error_type` ∈ {`SD`, `SEM`, `CI`}，混用会被自动警告

## 7. heatmap

```json
{
  "title": "Differentially expressed genes",
  "rows": ["GATA1", "GATA2", "..."],
  "cols": ["Pt01", "Pt02", "..."],
  "scale": "z-score",
  "clustering_rows": "ward.D2",
  "clustering_cols": "none",
  "row_annotations": ["pathway"],
  "col_annotations": ["treatment"],
  "significance_threshold": 0.05,
  "colormap": "RdBu"
}
```

## 8. volcano_plot

```json
{
  "title": "DEGs treatment vs control",
  "fc_threshold": 1.0,
  "p_threshold": 0.05,
  "n_significant": 312,
  "n_up": 180,
  "n_down": 132,
  "fdr_method": "BH",
  "fdr_threshold": 0.05,
  "top_genes": ["TP53", "MYC", "EGFR", "VEGFA", "BCL2"]
}
```

## 通用约定

- 所有数字字段允许 `null`，会被解析器视为"未提供"
- 字符串字段会做 XML 转义（`&`/`<`/`>`）
- `notes` 字段是 free-form，会被 audiences/caption 自动引用

## SVG 数据格式差异

`render-svg` 还需要每条曲线/研究的原始坐标点：

| 图表 | 必填坐标字段 |
|------|--------------|
| KM | `arms[].times` + `arms[].events` + `arms[].survival` |
| Forest | `studies[].effect` + `studies[].ci` + `studies[].weight` |
| ROC | `points` 或 `curves[].points`（[(fpr, tpr), ...]） |

完整示例见 `scripts/sample_*.json`。
