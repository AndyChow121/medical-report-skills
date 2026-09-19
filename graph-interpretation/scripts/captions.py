"""期刊风格图注生成器（v1.2.0）。

支持的期刊风格：
- 英文：nature / lancet / jama / cell / nejm / generic
- 中文：
    - cma       中华医学会系列杂志（《中华医学杂志》《中华肿瘤杂志》等）
    - cslco     中国临床肿瘤学会（CSCO）指南类
    - cebm      《中国循证医学杂志》—— EBM/PICO 导向
    - zhcore    中文核心期刊通用学术格式

每种风格都给出：
- max_words：字数上限
- structure：段落顺序
- tone：语气预设
- _zh_blocks：中文学术段落模板（按结构填充）

支持中英双语输出。
"""
from __future__ import annotations

from parsers.base import StatisticalSummary, EffectEstimate


STYLE_GUIDE: dict[str, dict] = {
    # ----- 英文期刊 -----
    "nature": {
        "max_words": 200,
        "structure": ["title", "panel_description", "key_finding", "statistics", "meaning"],
        "tone": "concise, results-first",
    },
    "lancet": {
        "max_words": 250,
        "structure": ["title", "population", "finding", "statistics", "clinical_implication"],
        "tone": "clinical, PICO-aware",
    },
    "jama": {
        "max_words": 250,
        "structure": ["title", "setting", "design", "main_outcome", "statistics"],
        "tone": "structured, formal",
    },
    "cell": {
        "max_words": 220,
        "structure": ["title", "panel_description", "mechanism", "statistics", "biological_meaning"],
        "tone": "mechanistic",
    },
    "nejm": {
        "max_words": 180,
        "structure": ["title", "finding", "numbers", "clinical_decision"],
        "tone": "clinical-decision",
    },
    "generic": {
        "max_words": 250,
        "structure": ["title", "what_is_shown", "key_finding", "statistics", "interpretation"],
        "tone": "balanced",
    },

    # ----- 中文期刊 -----
    "cma": {
        "max_words": 300,
        "structure": ["title", "figure_intro", "methods_brief", "results",
                       "statistical_report", "interpretation"],
        "tone": "学术规范，结论稳健，'本文/本研究' 视角",
        "language": "zh",
    },
    "cslco": {
        "max_words": 360,
        "structure": ["title", "patient_population", "design_summary",
                       "results", "guideline_inclusion",
                       "recommendation", "interpretation"],
        "tone": "CSCO 指南语态：研究设计 + 结果 + 指南纳入 + 推荐级别",
        "language": "zh",
        "fields": ["patient_population_zh", "study_design", "chart_subtitle",
                   "csco_recommendation_level", "included_in_cslco_guideline",
                   "cslco_guideline_year", "nmpa_approved_drug", "fda_approved_drug"],
    },
    "cebm": {
        "max_words": 300,
        "structure": ["title", "pico", "results",
                       "evidence_quality", "applicability"],
        "tone": "循证医学，PICO 严谨",
        "language": "zh",
    },
    "zhcore": {
        "max_words": 280,
        "structure": ["title", "object", "methods", "results",
                       "statistical_report", "discussion"],
        "tone": "通用中文学术，结构完整",
        "language": "zh",
    },
}


# ----- 工具函数 -----

def _stats_clause(summary: StatisticalSummary) -> str:
    """统一统计量子句（中英共用）。"""
    est = summary.primary
    if est is None or est.value is None:
        return ""
    parts = [f"{est.measure}={est.value:g}"]
    if est.ci_str():
        parts.append(est.ci_str())
    if est.p_value is not None:
        parts.append("p<0.001" if est.p_value < 0.001 else f"p={est.p_value:.3f}")
    if est.n:
        parts.append(f"n={est.n}")
    return "（" + "，".join(parts) + "）"


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def _effect_in_plain_words(summary: StatisticalSummary) -> str:
    """用自然中文描述主要效应。"""
    est = summary.primary
    if est is None or est.value is None:
        return "见统计摘要"
    if est.measure == "HR":
        direction = "降低" if est.value < 1 else "升高"
        pct = abs(est.value - 1) * 100
        return f"HR={est.value:.2f}（事件风险{direction}{pct:.0f}%）"
    if est.measure == "OR":
        return f"OR={est.value:.2f}"
    if est.measure == "RR":
        return f"RR={est.value:.2f}"
    if est.measure == "AUC":
        level = "良好" if est.value >= 0.8 else ("中等" if est.value >= 0.7 else "欠佳")
        return f"AUC={est.value:.3f}（判别力{level}）"
    if est.measure == "correlation":
        strength = ("强" if abs(est.value) >= 0.7 else
                    "中等" if abs(est.value) >= 0.4 else "弱")
        return f"r={est.value:.3f}（{strength}相关）"
    return f"{est.measure}={est.value:g}"


def _evidence_phrase(summary: StatisticalSummary) -> str:
    """基于 p 值生成证据等级短语（CSCO 风格用）。"""
    est = summary.primary
    if est is None or est.p_value is None:
        return "证据等级待评估"
    if est.p_value < 0.001:
        return "高级别证据（p<0.001）"
    if est.p_value < 0.01:
        return "较高级别证据（p<0.01）"
    if est.p_value < 0.05:
        return "中等证据（p<0.05）"
    return "证据尚不充分（p≥0.05）"


# ----- 英文 block 模板 -----

_EN_BLOCKS = {
    "title": "Figure {fid}. {title}.",
    "panel_description": "Chart type: {ct}.",
    "key_finding": "Key finding: {notes}.",
    "statistics": "Statistics: {stats}.",
    "meaning": "Interpretation: see discussion.",
    "population": "Population details in Methods.",
    "clinical_implication": "Clinical implication: see text.",
    "setting": "Setting described in the original article.",
    "design": "Design described in the original article.",
    "main_outcome": "Primary outcome reported above.",
    "mechanism": "Mechanistic interpretation: see Discussion.",
    "biological_meaning": "Biological meaning discussed in text.",
    "clinical_decision": "Clinical decision impact: see text.",
    "numbers": "Numbers: {stats}.",
    "finding": "Finding: {notes}.",
    "what_is_shown": "Content described in text.",
    "interpretation": "Interpretation discussed in text.",
}


# ----- 中文 block 模板（CMA 风格：稳健、规范） -----

_ZH_CMA_BLOCKS = {
    "title": "图{fid} {title}",
    "figure_intro": "本研究通过{ct}对数据进行可视化呈现。",
    "methods_brief": "研究对象及检测方法见正文。",
    "results": "结果显示，{effect}。",
    "statistical_report": "统计量：{stats}。",
    "interpretation": "上述结果提示，{notes_first}{notes_rest}",
}


# ----- 中文 block 模板（CSCO 风格：指南语态） -----

_ZH_CSLCO_BLOCKS = {
    "title": "图{fid} {title}",
    "patient_population": "研究人群：{patient_population}。",
    "design_summary": "研究设计：{design_summary}。",
    "results": "结果发现，{stats}。",
    "guideline_inclusion": "指南纳入：{guideline_inclusion}。",
    "recommendation": "CSCO 推荐意见：{recommendation}。",
    "interpretation": "{notes_first}{notes_rest}",
}


# ----- 中文 block 模板（CEBM 风格：循证医学 PICO） -----

_ZH_CEBM_BLOCKS = {
    "title": "图{fid} {title}",
    "pico": "P（人群）= {pop}；I（干预）= {intervention}；C（对照）= {comparison}；O（结局）= {outcome}。",
    "results": "研究结果显示，{effect}（{stats}）。",
    "evidence_quality": "证据质量：{evidence}。",
    "applicability": "适用人群与推广性：{notes_first}",
}


# ----- 中文 block 模板（中文核心通用） -----

_ZH_ZHCORE_BLOCKS = {
    "title": "图{fid} {title}",
    "object": "本图旨在展示{ct}结果。",
    "methods": "数据来源与统计方法详见正文材料与方法部分。",
    "results": "结果如图所示：{effect}。",
    "statistical_report": "统计量：{stats}。",
    "discussion": "结合上述结果，{notes_first}",
}


_ZH_TEMPLATE_MAP: dict[str, dict[str, str]] = {
    "cma": _ZH_CMA_BLOCKS,
    "cslco": _ZH_CSLCO_BLOCKS,
    "cebm": _ZH_CEBM_BLOCKS,
    "zhcore": _ZH_ZHCORE_BLOCKS,
}


# ----- 推断辅助字段 -----

def _infer_population(summary: StatisticalSummary) -> str:
    """从 raw/notes 推断人群描述；缺失则使用占位。"""
    raw = summary.raw or {}
    pop = raw.get("population") or raw.get("cohort") or raw.get("population_description")
    if pop:
        return str(pop)
    notes = summary.notes or []
    for n in notes:
        if any(k in n for k in ("研究人群", "队列", "patients", "participants", "subjects")):
            return n
    return "本研究纳入的研究对象"


def _infer_intervention(summary: StatisticalSummary) -> str:
    raw = summary.raw or {}
    v = raw.get("intervention") or raw.get("treatment") or raw.get("exposure")
    return str(v) if v else "研究中施加的干预/暴露因素"


def _infer_comparison(summary: StatisticalSummary) -> str:
    raw = summary.raw or {}
    v = raw.get("comparison") or raw.get("control")
    return str(v) if v else "对照/常规处理"


def _infer_outcome(summary: StatisticalSummary) -> str:
    raw = summary.raw or {}
    v = raw.get("outcome") or raw.get("endpoint") or raw.get("primary_endpoint")
    if v:
        return str(v)
    est = summary.primary
    if est and est.measure:
        return f"主要结局指标（{est.measure}）"
    return "本研究关注的主要结局"


def _infer_recommendation(summary: StatisticalSummary) -> str:
    """基于 effect 大小生成推荐语。"""
    est = summary.primary
    if est is None or est.value is None:
        return "在临床决策中可结合患者具体情况权衡使用"
    if est.measure == "HR":
        if est.value < 0.8 and est.p_value is not None and est.p_value < 0.05:
            return "可考虑在符合条件的患者中应用"
        if est.value < 1.0:
            return "可作为备选，需进一步证据支持"
        return "不建议优先采用"
    if est.measure == "AUC":
        if est.value >= 0.8:
            return "可用于辅助临床诊断决策"
        if est.value >= 0.7:
            return "建议联合其他指标使用"
        return "不推荐单独应用于临床决策"
    return "可结合临床场景酌情参考"


# ----- 主入口 -----

def generate_caption(
    summary: StatisticalSummary,
    style: str = "generic",
    language: str = "en",
    figure_id: str = "1",
) -> str:
    """生成符合期刊风格的图注。

    中文期刊风格（cma/cslco/cebm/zhcore）会自动切换 language='zh'，
    并使用相应学术段落模板。
    """
    style = style.lower()
    spec = STYLE_GUIDE.get(style)
    if spec is None:
        style = "generic"
        spec = STYLE_GUIDE["generic"]

    # 中文期刊强制切到中文
    if spec.get("language") == "zh":
        language = "zh"

    if language == "zh" and style not in _ZH_TEMPLATE_MAP:
        style = "zhcore"
        spec = STYLE_GUIDE["zhcore"]

    title = summary.title or summary.chart_type.replace("_", " ").title()
    effect = _effect_in_plain_words(summary)
    stats = _stats_clause(summary).strip("（）")
    if stats:
        stats = "（" + stats + "）"
    evidence = _evidence_phrase(summary)
    notes = summary.notes[:3]
    notes_first = notes[0] if notes else "该结果支持研究假设，详见正文讨论。"
    notes_rest = ("；" + "；".join(notes[1:])) if len(notes) > 1 else ""
    pop = _infer_population(summary)
    intervention = _infer_intervention(summary)
    comparison = _infer_comparison(summary)
    outcome = _infer_outcome(summary)
    recommendation = _infer_recommendation(summary)

    # v1.3.0: CSCO 风格专属字段（中国语境硬指标）
    raw = summary.raw or {}
    if language == "zh" and style == "cslco":
        patient_population = raw.get("patient_population_zh") or pop
        design_summary = (
            raw.get("study_design")
            or raw.get("chart_subtitle")
            or raw.get("design_summary")
            or "见正文研究设计"
        )
        rec_level = raw.get("csco_recommendation_level")
        if rec_level:
            # CSCO 硬指标优先；额外挂载补充说明
            extra = ""
            if raw.get("subgroup_p_interaction") is not None and raw.get("subgroup_p_interaction") >= 0.1:
                extra = "亚组分析未发现显著异质性"
            elif raw.get("pre_registered") and raw.get("blinded"):
                extra = "研究方法学严谨"
            recommendation = f"{rec_level}" + (f"；{extra}" if extra else "")
        if raw.get("included_in_cslco_guideline") and raw.get("cslco_guideline_year"):
            guideline_inclusion = (
                f"已纳入《CSCO 胃癌诊疗指南》{raw.get('cslco_guideline_year')} 版"
            )
        elif raw.get("included_in_cslco_guideline"):
            guideline_inclusion = "已纳入 CSCO 系列指南"
        else:
            guideline_inclusion = "暂未纳入 CSCO 系列指南"
        if raw.get("nmpa_approved_drug"):
            guideline_inclusion += "；治疗药物已获 NMPA 批准"
        if raw.get("fda_approved_drug"):
            guideline_inclusion += "；FDA 已批准该适应证"
    else:
        patient_population = pop
        design_summary = ""
        guideline_inclusion = ""

    # 中文时把 "Figure N" / "Fig. N" 自动转成 "N"
    if language == "zh":
        import re as _re
        m = _re.search(r"\d+", figure_id or "")
        fid_disp = m.group(0) if m else "1"
    else:
        fid_disp = figure_id

    if language == "zh":
        blocks_def = _ZH_TEMPLATE_MAP[style]
        rendered: dict[str, str] = {}
        for key, tmpl in blocks_def.items():
            rendered[key] = tmpl.format(
                fid=fid_disp,
                title=title,
                ct=summary.chart_type,
                effect=effect,
                stats=stats,
                notes_first=notes_first,
                notes_rest=notes_rest,
                pop=pop,
                intervention=intervention,
                comparison=comparison,
                outcome=outcome,
                evidence=evidence,
                recommendation=recommendation,
                # v1.3.0 cslco 专属字段
                patient_population=patient_population,
                design_summary=design_summary,
                guideline_inclusion=guideline_inclusion,
            )
    else:
        rendered = {k: v.format(
            fid=figure_id, title=title, ct=summary.chart_type,
            stats=_stats_clause(summary), notes=("; ".join(notes) or "see summary"),
        ) for k, v in _EN_BLOCKS.items()}

    parts = [rendered.get(s, "") for s in spec["structure"]]
    parts = [p for p in parts if p]
    caption = "".join(parts) if language == "zh" else " ".join(parts)
    caption = _truncate(caption, spec["max_words"] * 6)
    return caption


def list_styles() -> list[str]:
    return list(STYLE_GUIDE.keys())


def list_zh_styles() -> list[str]:
    return [k for k, v in STYLE_GUIDE.items() if v.get("language") == "zh"]
