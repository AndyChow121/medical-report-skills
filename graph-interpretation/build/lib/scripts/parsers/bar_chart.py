"""Bar Chart 解析器。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class BarChartParser(BaseParser):
    """Bar Chart：抽取均值、误差棒类型、显著性符号。"""

    chart_type = "bar_chart"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        groups = data.get("groups", [])
        primary = EffectEstimate(measure="mean_diff")
        notes: list[str] = []

        for g in groups:
            err = g.get("error")
            err_type = g.get("error_type", "SD")
            notes.append(
                f"{g.get('name', 'group')}: 均值={g.get('mean')}, "
                f"{err_type}={err}, n={g.get('n')}"
            )

        test = data.get("test")
        p = data.get("p_value")
        if test and p is not None:
            primary.p_value = float(p)
            primary.n = sum(g.get("n", 0) or 0 for g in groups) or None
            notes.append(f"{test} p={p}")

        # 显著性符号
        sigs = data.get("significance", [])
        if sigs:
            notes.append(f"显著性符号: {sigs}")

        # 误差棒类型提示
        error_types = {g.get("error_type", "SD") for g in groups}
        if "SEM" in error_types and "SD" in error_types:
            notes.append("⚠️ 误差棒类型不一致（SD vs SEM），请核实")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Bar chart"),
            primary=primary,
            notes=notes,
            raw={"groups": groups},
        )
