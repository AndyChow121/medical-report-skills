"""Forest Plot 解析器（荟萃分析）。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class ForestPlotParser(BaseParser):
    """Forest Plot：抽取各研究的效应量、CI、异质性 I²、汇总效应。"""

    chart_type = "forest_plot"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        studies = data.get("studies", [])
        primary = EffectEstimate(measure=data.get("measure", "OR"))
        notes: list[str] = []

        # 异质性
        i2 = data.get("i_squared") or data.get("heterogeneity_i2")
        if i2 is not None:
            level = "低" if i2 < 25 else "中" if i2 < 75 else "高"
            notes.append(f"I²={i2}%（{level}异质性）")
        het_p = data.get("heterogeneity_p")
        if het_p is not None:
            notes.append(f"异质性检验 p={het_p}")

        # 汇总效应
        overall = data.get("overall_effect")
        if overall is not None:
            primary.value = float(overall)
            ci = data.get("overall_ci")
            if ci and len(ci) == 2:
                primary.ci_lower, primary.ci_upper = float(ci[0]), float(ci[1])
            primary.p_value = data.get("overall_p")
            primary.n = sum(s.get("n", 0) or 0 for s in studies) or None

        # 个体研究作为二级条目
        secondary: list[EffectEstimate] = []
        for s in studies:
            eff = EffectEstimate(
                measure=primary.measure,
                value=s.get("effect"),
                ci_lower=(s.get("ci") or [None, None])[0],
                ci_upper=(s.get("ci") or [None, None])[1],
                p_value=s.get("p"),
                n=s.get("n"),
            )
            secondary.append(eff)

        # 偏倚提示
        if data.get("publication_bias"):
            notes.append(f"发表偏倚: {data['publication_bias']}")
        if data.get("eggers_p") is not None:
            notes.append(f"Egger 检验 p={data['eggers_p']}")

        # 模型选择
        model = data.get("model", "fixed")
        notes.append(f"效应模型: {model}（{'固定' if model=='fixed' else '随机'}效应）")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Forest plot"),
            primary=primary,
            secondary=secondary,
            notes=notes,
            raw={
                "studies": studies,
                "i_squared": i2,
                "model": model,
                "n_total": primary.n,
                "n_studies": len(studies),
                "heterogeneity_discussed": data.get("heterogeneity_discussed"),
                "egger_p": data.get("eggers_p") or data.get("egger_p"),
                "funnel_plot": data.get("funnel_plot"),
                "grade": data.get("grade"),
                "prospero": data.get("prospero_id"),
                "rob_per_study": data.get("rob_per_study"),
            },
        )
