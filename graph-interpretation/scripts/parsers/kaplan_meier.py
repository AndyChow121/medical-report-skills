"""Kaplan-Meier 生存曲线解析器。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class KaplanMeierParser(BaseParser):
    """KM 曲线：抽取 HR / 中位生存期 / log-rank p 值 / 风险表样本量。"""

    chart_type = "kaplan_meier"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        arms = data.get("arms", [])
        primary = EffectEstimate(measure="HR")
        notes: list[str] = []

        # 中位生存期
        medians: dict[str, float | None] = {}
        for arm in arms:
            name = arm.get("name", "arm")
            medians[name] = arm.get("median_survival")
            notes.append(f"{name} 中位生存期: {arm.get('median_survival')}")

        # HR 提取
        hr = data.get("hazard_ratio")
        if hr is not None:
            primary.value = float(hr)
            ci = data.get("hr_ci") or data.get("ci_95")
            if ci and len(ci) == 2:
                primary.ci_lower, primary.ci_upper = float(ci[0]), float(ci[1])
            primary.p_value = data.get("p_value") or data.get("logrank_p")
            primary.n = data.get("n_total")

        # 风险表（at-risk table）
        at_risk = data.get("at_risk", {})
        if at_risk:
            notes.append(f"风险表: {at_risk}")

        # 比例风险假设检验（可选）
        ph_test = data.get("schoenfeld_p") or data.get("ph_test_p")
        if ph_test is not None:
            notes.append(f"比例风险假设检验 p={ph_test}（>0.05 表示满足）")

        # 删失说明
        censoring = data.get("censoring_rate")
        if censoring is not None:
            notes.append(f"删失率 {censoring*100:.1f}%")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Kaplan-Meier survival"),
            primary=primary,
            notes=notes,
            raw={
                "arms": arms,
                "medians": medians,
                "at_risk": at_risk,
                "schoenfeld_p": ph_test,
                "censoring_rate": censoring,
                "n_total": data.get("n_total"),
                "censoring_reasons": data.get("censoring_reasons"),
                "median_followup": data.get("median_followup"),
                "itt_analysis": data.get("itt_analysis"),
                # v1.3.0: 透传 CSCO 专属字段
                "patient_population_zh": data.get("patient_population_zh"),
                "study_design": data.get("study_design"),
                "chart_subtitle": data.get("chart_subtitle"),
                "csco_recommendation_level": data.get("csco_recommendation_level"),
                "included_in_cslco_guideline": data.get("included_in_cslco_guideline"),
                "cslco_guideline_year": data.get("cslco_guideline_year"),
                "fda_approved_drug": data.get("fda_approved_drug"),
                "nmpa_approved_drug": data.get("nmpa_approved_drug"),
                "trial_registration": data.get("trial_registration"),
                "pre_registered": data.get("pre_registered"),
                "funding_source": data.get("funding_source"),
                "subgroup_p_interaction": data.get("subgroup_p_interaction"),
                "followup_adequate": data.get("followup_adequate"),
                "blinded": data.get("blinded"),
            },
        )
