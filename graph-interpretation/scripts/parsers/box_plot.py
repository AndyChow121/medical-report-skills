"""Box Plot 解析器。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class BoxPlotParser(BaseParser):
    """Box Plot：抽取中位数、IQR、离群值、组间检验。"""

    chart_type = "box_plot"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        groups = data.get("groups", [])
        primary = EffectEstimate(measure="median_diff")
        notes: list[str] = []

        for g in groups:
            notes.append(
                f"{g.get('name', 'group')}: 中位={g.get('median')}, "
                f"IQR={g.get('q1')}-{g.get('q3')}, "
                f"须线={g.get('whisker_low')}-{g.get('whisker_high')}"
            )
            outliers = g.get("outliers", [])
            if outliers:
                notes.append(f"  离群值: {outliers}")

        test = data.get("test")
        p = data.get("p_value")
        if test and p is not None:
            notes.append(f"{test} 检验 p={p}")
            primary.p_value = float(p)
            primary.n = sum(g.get("n", 0) or 0 for g in groups) or None

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Box plot"),
            primary=primary,
            notes=notes,
            raw={"groups": groups},
        )
