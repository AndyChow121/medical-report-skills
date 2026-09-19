"""Volcano Plot 解析器（差异分析）。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class VolcanoPlotParser(BaseParser):
    """Volcano Plot：抽取显著基因数、阈值、上下调分布。"""

    chart_type = "volcano_plot"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        primary = EffectEstimate(measure="n_significant")
        notes: list[str] = []

        fc_threshold = data.get("fc_threshold", 1.0)  # log2FC 阈值
        p_threshold = data.get("p_threshold", 0.05)
        notes.append(f"阈值: |log2FC| ≥ {fc_threshold} 且 p ≤ {p_threshold}")

        sig = data.get("n_significant", 0)
        up = data.get("n_up", 0)
        down = data.get("n_down", 0)
        primary.value = float(sig)
        primary.ci_lower = float(down)
        primary.ci_upper = float(up)

        notes.append(f"显著基因: {sig}（上调 {up}，下调 {down}）")

        if data.get("fdr_method"):
            notes.append(f"FDR 校正: {data['fdr_method']}")
        if data.get("fdr_threshold") is not None:
            notes.append(f"FDR 阈值: {data['fdr_threshold']}")

        # top 基因
        top = data.get("top_genes", [])
        if top:
            notes.append(f"Top 基因: {top[:5]}")

        # 多重比较校正提醒
        if not data.get("fdr_method"):
            notes.append("⚠️ 未说明多重比较校正方法")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Volcano plot"),
            primary=primary,
            notes=notes,
            raw={
                "fc_threshold": fc_threshold,
                "p_threshold": p_threshold,
                "n_up": up,
                "n_down": down,
            },
        )
