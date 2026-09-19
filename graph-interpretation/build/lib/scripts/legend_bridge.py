"""graph-interpretation → figure-legend-gen 桥接层。

把 StatisticalSummary 转成 figure-legend-gen 的字段输入。

约定：figure-legend-gen 的输入是 {placeholder: value}，
模板（见 figure-legend-gen/scripts/main.py TEMPLATES）里的占位符
会被自动替换为 value。详见其 SKILL.md。

用法（程序化）：
    from parsers import PARSERS
    from legend_bridge import to_legend_fields
    summary = PARSERS["kaplan_meier"].parse(data)
    fields  = to_legend_fields(summary)
    # fields["groups"], fields["n"], fields["primary_measure"] ...

然后调用者把 fields 喂给 figure-legend-gen.main 的模板填充逻辑即可。
"""
from __future__ import annotations

from typing import Any

from parsers.base import StatisticalSummary


# graph-interpretation → figure-legend-gen 类型映射
_TYPE_MAP = {
    "kaplan_meier": "line",      # KM 曲线归类为 line
    "forest_plot": "bar",        # 森林图通常用条形表示
    "roc_curve": "scatter",      # ROC 点序列，归为 scatter
    "box_plot": "box",
    "scatter_plot": "scatter",
    "bar_chart": "bar",
    "heatmap": "heatmap",
    "volcano_plot": "scatter",   # 火山图本质是点云
}


def to_legend_type(gi_chart_type: str) -> str:
    """graph-interpretation 类型 → figure-legend-gen 类型。"""
    return _TYPE_MAP.get(gi_chart_type, "scatter")


def _fmt_primary(summary: StatisticalSummary) -> str:
    p = summary.primary
    if not p or p.value is None:
        return ""
    parts = [f"{p.measure}={p.value:g}"]
    if p.ci_lower is not None and p.ci_upper is not None:
        parts.append(f"{int(p.ci_level*100)}% CI {p.ci_lower:g}-{p.ci_upper:g}")
    if p.p_value is not None:
        parts.append(f"p={p.p_value:g}")
    return "，".join(parts)


def _fmt_sample_size(raw: dict[str, Any]) -> int | None:
    return raw.get("n_total") or raw.get("n") or (
        sum(g.get("n", 0) for g in raw.get("groups", [])) if raw.get("groups") else None
    )


def to_legend_fields(summary: StatisticalSummary) -> dict[str, Any]:
    """把 StatisticalSummary 转成 figure-legend-gen 可消费的字段。

    返回的 dict 同时附带一个 ``_gi_chart_type`` 与 ``_legend_chart_type`` 供调用方判断。
    """
    raw = summary.raw or {}
    notes = summary.notes or []
    primary = summary.primary

    # 通用字段
    fields: dict[str, Any] = {
        "metric": primary.measure if primary else "",
        "groups": "",
        "sample_description": "",
        "sample_unit": "sample",
        "n": _fmt_sample_size(raw) or "",
        "x_var": "",
        "y_var": "",
        "r_value": "",
        "p_value": primary.p_value if primary and primary.p_value is not None else "",
        "time_range": "",
        "condition": "",
        "value_range": "",
        "normalization_method": raw.get("scale") or "z-score",
        "clustering_method": raw.get("clustering_method") or "hierarchical clustering",
        "test": "",
        "staining": "",
        "sample_type": "",
        "stains": "",
        "scale_bar": "",
        "microscope_type": "",
        "primary_stat": _fmt_primary(summary),
        "_gi_chart_type": summary.chart_type,
        "_legend_chart_type": to_legend_type(summary.chart_type),
        "_notes": " | ".join(notes),
    }

    chart_type = summary.chart_type

    # KM：折线（生存曲线）
    if chart_type == "kaplan_meier":
        arms = raw.get("arms") or [a.get("name") for a in raw.get("arms", [])]
        if arms:
            arm_names = [a if isinstance(a, str) else a.get("name", "") for a in arms]
            fields["groups"] = " vs ".join([n for n in arm_names if n]) or "treatment arms"
            fields["condition"] = fields["groups"]
            fields["metric"] = "Overall survival"
        fields["time_range"] = "follow-up time"
        fields["test"] = "log-rank test"
        fields["sample_description"] = f"{fields['n']} participants" if fields["n"] else ""

    # Forest：分类条形
    elif chart_type == "forest_plot":
        studies = raw.get("studies", [])
        if studies:
            fields["groups"] = "pooled meta-analysis"
            fields["sample_description"] = f"{len(studies)} studies, {fields['n']} participants" if fields['n'] else f"{len(studies)} studies"
        fields["test"] = f"{raw.get('model', 'random')}-effects model"
        fields["metric"] = primary.measure if primary else "pooled effect"

    # ROC：散点
    elif chart_type == "roc_curve":
        fields["x_var"] = "1 - Specificity (FPR)"
        fields["y_var"] = "Sensitivity (TPR)"
        fields["metric"] = f"ROC curve (AUC={primary.value:g})" if primary and primary.value else "ROC curve"
        fields["sample_description"] = f"{fields['n']} cases" if fields['n'] else ""

    # Box
    elif chart_type == "box_plot":
        groups = raw.get("groups", [])
        if groups:
            names = [g.get("name", f"G{i+1}") for i, g in enumerate(groups)]
            fields["groups"] = ", ".join(names)
        fields["sample_unit"] = "subjects per group"
        fields["test"] = "Mann-Whitney U test / Kruskal-Wallis"

    # Scatter
    elif chart_type == "scatter_plot":
        fields["x_var"] = raw.get("x_label", "X")
        fields["y_var"] = raw.get("y_label", "Y")
        reg = raw.get("regression", {})
        if reg.get("r_squared") is not None:
            fields["r_value"] = f"{reg['r_squared']:.3f}"
        if primary and primary.p_value is not None:
            fields["p_value"] = primary.p_value

    # Bar
    elif chart_type == "bar_chart":
        cats = raw.get("categories") or [f"Cat{i+1}" for i in range(len(raw.get("groups", [])))]
        fields["groups"] = ", ".join(str(c) for c in cats)
        fields["sample_description"] = "comparison groups"
        fields["test"] = "ANOVA / Student's t-test"

    # Heatmap
    elif chart_type == "heatmap":
        rows = raw.get("row_labels", [])
        cols = raw.get("col_labels", [])
        fields["dimensions"] = f"{len(rows)} features × {len(cols)} samples"
        all_vals = [v for row in raw.get("matrix", []) for v in row if v is not None]
        if all_vals:
            fields["value_range"] = f"{min(all_vals):.2f} to {max(all_vals):.2f}"

    # Volcano
    elif chart_type == "volcano_plot":
        fields["x_var"] = "log₂ fold change"
        fields["y_var"] = "−log₁₀ (p-value)"
        fields["sample_description"] = f"{fields['n']} samples" if fields['n'] else ""
        n_sig = raw.get("n_significant")
        if n_sig:
            fields["metric"] = f"differentially expressed genes (n={n_sig})"
        fields["test"] = raw.get("fdr_method") and f"with {raw['fdr_method']} FDR correction" or "with FDR correction"

    return fields


def render_legend_context(
    summary: StatisticalSummary,
    figure_id: str = "Figure 1",
    style: str = "generic",
    language: str = "en",
) -> str:
    """生成一段可读 markdown 上下文文档，便于人工或 figure-legend-gen
    把 graph-interpretation 的结构化输出直接落到图注里。

    本质是 ``to_legend_fields`` 的人类可读形式。
    """
    fields = to_legend_fields(summary)
    lines = [
        f"<!-- graph-interpretation → figure-legend-gen bridge -->",
        f"<!-- chart_type: {summary.chart_type} → {fields['_legend_chart_type']} -->",
        f"<!-- style={style}, language={language}, figure_id={figure_id} -->",
        "",
        f"## {figure_id}. {summary.title}",
        "",
        f"- **Type**: {fields['_legend_chart_type']}",
        f"- **Primary effect**: {fields['primary_stat'] or 'see raw data'}",
        f"- **Sample size (n)**: {fields['n'] or '未报告'}",
        f"- **Statistical test**: {fields['test'] or '未说明'}",
        f"- **Notes**: {fields['_notes'] or '—'}",
        "",
        "<!-- figure-legend-gen fields（可直接作模板输入） -->",
        "```yaml",
    ]
    for k, v in fields.items():
        if k.startswith("_") and k not in {"_notes"}:
            continue
        lines.append(f"  {k}: {v!r}")
    lines.append("```")
    return "\n".join(lines)
