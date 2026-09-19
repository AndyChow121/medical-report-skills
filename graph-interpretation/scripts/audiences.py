"""多受众说明生成器（v1.2.0）。

将 StatisticalSummary 渲染为面向不同受众的解读文本：
- researchers:    研究人员（完整统计学语言）
- clinicians:     临床医生（突出临床决策含义）
- patients:       患者（通俗比喻，避免专业术语）
- policy_makers:  政策制定者（卫生经济与人群视角）

新增 `locale='zh_CN'`：所有受众加入中国语境（医保/指南/中文术语）。
"""
from __future__ import annotations

from parsers.base import StatisticalSummary, EffectEstimate


def _fmt_p(p: float | None) -> str:
    if p is None:
        return "未提供"
    if p < 0.001:
        return "p<0.001"
    return f"p={p:.3f}"


def _fmt_effect(est: EffectEstimate | None) -> str:
    if est is None or est.value is None:
        return ""
    if est.measure in {"HR", "OR", "RR"}:
        return f"{est.measure}={est.value:.2f}"
    if est.measure == "AUC":
        return f"AUC={est.value:.3f}"
    if est.measure == "correlation":
        return f"r={est.value:.3f}"
    return f"{est.measure}={est.value:g}"


def _is_zh(locale: str) -> bool:
    return locale.lower().startswith("zh")


# ----- 研究人员 -----

def render_researchers(summary: StatisticalSummary, locale: str = "en") -> str:
    """研究人员视角：保留全部统计细节。"""
    zh = _is_zh(locale)
    lines = ["【研究型解读】" + ("" if zh else f" {summary.chart_type}")]
    if summary.title:
        lines.append(("标题" if zh else "Title") + f"：{summary.title}")
    if summary.primary:
        parts = [_fmt_effect(summary.primary)]
        if summary.primary.ci_str():
            parts.append(summary.primary.ci_str())
        if summary.primary.p_value is not None:
            parts.append(_fmt_p(summary.primary.p_value))
        if summary.primary.n:
            parts.append(f"n={summary.primary.n}")
        lines.append(("主要效应" if zh else "Primary effect") + "：" + "，".join(parts))
    if summary.notes:
        lines.append(("关键注释" if zh else "Key notes") + "：" + "；".join(summary.notes))
    return "\n".join(lines)


# ----- 临床医生 -----

def render_clinicians(summary: StatisticalSummary, locale: str = "en") -> str:
    """临床医生视角：突出决策含义（含中国语境时增加 CSCO/NCCN 双标、医保提示）。"""
    zh = _is_zh(locale)
    lines = ["【临床医生解读】"]
    est = summary.primary

    if est and est.measure == "HR" and est.value is not None:
        reduction = (1 - est.value) * 100
        sig = "具有统计学意义" if est.p_value is not None and est.p_value < 0.05 else "未达统计学显著"
        if zh:
            lines.append(
                f"治疗使事件风险下降 {reduction:.0f}%（{_fmt_effect(est)}，{sig}）。"
                f"对符合条件的患者可考虑该方案；同时建议关注 NCCN/CSCO 指南推荐级别更新。"
            )
        else:
            lines.append(
                f"Treatment reduces event risk by {reduction:.0f}% ({_fmt_effect(est)}, {sig})."
                f" Consider for eligible patients."
            )
    elif est and est.measure == "AUC" and est.value is not None:
        if est.value >= 0.8:
            quality = "判别力良好"
        elif est.value >= 0.7:
            quality = "判别力中等"
        else:
            quality = "判别力不足"
        if zh:
            lines.append(f"该诊断工具{quality}（{_fmt_effect(est)}），可在临床场景辅助决策。"
                        f"若涉及收费项目，建议核对该项目是否纳入医保目录。")
        else:
            lines.append(f"Diagnostic performance: {quality} ({_fmt_effect(est)}). "
                        f"Useful as clinical decision support.")
    elif est and est.measure == "OR" and est.value is not None:
        direction = "增加" if est.value > 1 else "降低"
        if zh:
            lines.append(f"该暴露/治疗使结局 odds {direction}约 {abs(est.value-1)*100:.0f}%。")
        else:
            lines.append(f"Odds {direction} by ~{abs(est.value-1)*100:.0f}% ({_fmt_effect(est)}).")
    else:
        if zh:
            lines.append(f"{summary.chart_type} 关键数值：" + "; ".join(summary.notes[:3]))
        else:
            lines.append(f"{summary.chart_type} key numbers: " + "; ".join(summary.notes[:3]))
    return "\n".join(lines)


# ----- 患者 -----

def render_patients(summary: StatisticalSummary, locale: str = "en") -> str:
    """患者视角：通俗类比，避免术语（中国语境加入就诊沟通语气）。"""
    zh = _is_zh(locale)
    lines = ["【通俗解读】" if zh else "[Patient-facing summary]"]
    est = summary.primary

    if est and est.measure == "HR" and est.value is not None:
        if est.value < 0.8:
            benefit_text_zh = (
                "这种治疗能明显延长生存，约每 10 个人里有 3 个人能从治疗中得到明显帮助。"
            )
            benefit_text_en = (
                "This treatment meaningfully extends survival — about 3 of every 10 people "
                "benefit clearly."
            )
            lines.append(benefit_text_zh if zh else benefit_text_en)
        elif est.value < 1.0:
            lines.append("这种治疗有一定帮助，但获益不算特别大。" if zh else
                         "The treatment helps a little but the benefit is modest.")
        else:
            lines.append("现有数据看不出明显获益。" if zh else
                         "The current data does not show a clear benefit.")
    elif est and est.measure == "AUC" and est.value is not None:
        if est.value >= 0.8:
            lines.append("这个检查比较靠谱，能比较好地区分有病和没病。" if zh else
                         "This test is reasonably accurate at telling disease from non-disease.")
        else:
            lines.append("这个检查只能提供一定参考，不能仅凭它下结论。" if zh else
                         "This test only gives partial information; don't rely on it alone.")
    elif est and est.measure in {"OR", "RR"} and est.value is not None:
        if est.value > 2:
            lines.append("这个因素会显著增加风险，需要重视。" if zh else
                         "This factor substantially increases risk — pay close attention.")
        elif est.value > 1:
            lines.append("这个因素可能略增风险，但效应不算很大。" if zh else
                         "This factor may slightly raise risk but the effect is small.")
        else:
            lines.append("这个因素看起来没有增加风险。" if zh else
                         "This factor does not appear to raise risk.")
    else:
        lines.append("这是一张统计图表，建议结合医生讲解来理解其含义。" if zh else
                     "This is a statistical figure; ask your clinician to walk you through it.")

    if zh:
        lines.append("（以上内容仅供了解参考，不替代医生面诊，请结合临床实际情况判断；具体治疗方案请遵医嘱。）")
    else:
        lines.append("(This summary is for general understanding and does not replace a clinical consultation.)")
    return "\n".join(lines)


# ----- 政策制定者 -----

def render_policy_makers(summary: StatisticalSummary, locale: str = "en") -> str:
    """政策制定者视角：人群层面含义（含医保/集采/指南等）。"""
    zh = _is_zh(locale)
    lines = ["【政策视角解读】" if zh else "[Policy-maker summary]"]
    est = summary.primary

    if est and est.measure == "HR" and est.value is not None:
        nnt_needed = abs(1 / (est.value - 1)) if est.value and est.value != 1 else None
        if nnt_needed:
            if zh:
                lines.append(
                    f"按当前效应推算，约每 {nnt_needed:.1f} 人接受治疗可减少 1 例不良事件，"
                    f"在人群层面值得纳入医保目录或指南评估。"
                )
            else:
                lines.append(
                    f"Approximately 1 in {nnt_needed:.1f} treated patients avoids 1 adverse event. "
                    f"Population-scale impact may merit coverage/guideline review."
                )
    elif est and est.measure == "AUC" and est.value is not None:
        if est.value >= 0.8:
            if zh:
                lines.append(
                    "该诊断工具达到筛查/早诊技术门槛，已具备大规模推广的技术可行性。"
                    "若涉及新增收费项目，可考虑纳入医保谈判议程。"
                )
            else:
                lines.append(
                    "Diagnostic test meets screening/early-detection performance thresholds; "
                    "feasible for population-scale deployment."
                )
        else:
            lines.append(
                "该工具尚不具备人群筛查条件，建议先在小范围试点验证。" if zh else
                "Test does not yet meet population-screening criteria; pilot validation recommended."
            )
    elif est and est.measure in {"OR", "RR"} and est.value is not None:
        if zh:
            lines.append(
                f"人群归因风险约为 {abs(est.value-1)*100:.0f}%，"
                f"可作为公共卫生干预或医保政策制定的依据。"
            )
        else:
            lines.append(
                f"Population-attributable risk ≈ {abs(est.value-1)*100:.0f}%; "
                f"useful for public-health planning."
            )
    else:
        lines.append(
            "建议结合 GRADE 证据评级和成本效益评估后纳入决策。" if zh else
            "Combine with GRADE rating and cost-effectiveness evaluation before policy use."
        )
    return "\n".join(lines)


AUDIENCE_RENDERERS = {
    "researchers": render_researchers,
    "clinicians": render_clinicians,
    "patients": render_patients,
    "policy_makers": render_policy_makers,
}


def render_all(summary: StatisticalSummary, locale: str = "en") -> dict[str, str]:
    """一次性生成全部受众版本。"""
    return {audience: fn(summary, locale=locale) for audience, fn in AUDIENCE_RENDERERS.items()}
