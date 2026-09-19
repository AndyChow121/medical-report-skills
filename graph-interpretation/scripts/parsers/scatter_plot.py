"""Scatter Plot 解析器。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class ScatterPlotParser(BaseParser):
    """Scatter Plot：抽取相关系数、R²、回归系数、离群值。"""

    chart_type = "scatter_plot"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        primary = EffectEstimate(measure="correlation")
        notes: list[str] = []

        r = data.get("r") or data.get("pearson_r")
        if r is not None:
            primary.value = float(r)
            primary.p_value = data.get("p_value")
            primary.n = data.get("n")
            r2 = r ** 2
            notes.append(f"Pearson r={r:.3f}（R²={r2:.3f}），p={primary.p_value}")

        # 回归
        slope = data.get("slope")
        intercept = data.get("intercept")
        if slope is not None:
            notes.append(f"回归方程: y={slope:.3f}x+{intercept or 0:.3f}")

        # 离群
        outliers = data.get("outliers", [])
        if outliers:
            notes.append(f"离群点: {outliers}")

        # 95% 预测带
        ci = data.get("ci_95")
        if ci:
            notes.append(f"95% 预测带: {ci}")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Scatter plot"),
            primary=primary,
            notes=notes,
            # v1.2.0: 先 copy 原 data 让 model_type/data_source 等 ML 标签透传
            raw={
                **data,
                "slope": slope,
                "intercept": intercept,
                "n": data.get("n"),
                "correlation_method": data.get("correlation_method"),
                # TRIPOD calibration 字段
                "calibration_plot": data.get("calibration_plot"),
                "calibration_slope": data.get("calibration_slope"),
                "calibration_intercept": data.get("calibration_intercept"),
                "brier_score": data.get("brier_score"),
                "mean_absolute_error": data.get("mean_absolute_error"),
                "mae": data.get("mae"),
            },
        )
