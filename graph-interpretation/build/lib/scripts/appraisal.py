"""批判性评价 checklist（Cochrane / GRADE / STARD / CONSORT 框架）。

v1.2.0 新增 TRIPOD-AI：当图表对应 ML/DL 预测模型时自动追加 14 条 AI 专属评价。
v1.3.0：AppraisalResult / ChecklistItem 转移到 models.py，对外从 models 导入。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from parsers.base import StatisticalSummary
from models import AppraisalResult, ChecklistItem  # noqa: F401 (re-export)


# v1.2.0: ML 模型自动追加 TRIPOD-AI 条目
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from tripod_ai_checklist import evaluate_tripod_ai
    _TRIPOD_AI_AVAILABLE = True
except Exception:
    evaluate_tripod_ai = None
    _TRIPOD_AI_AVAILABLE = False


# ---------- per-chart-type checklists ----------

_KM_ITEMS = [
    ("KM-1", "是否报告中位生存期与 95% CI？", "CONSORT"),
    ("KM-2", "是否提供风险表（at-risk table）？", "CONSORT"),
    ("KM-3", "是否给出 log-rank p 值？", "CONSORT"),
    ("KM-4", "是否检验比例风险假设（Schoenfeld 残差）？", "Cochrane RoB 2"),
    ("KM-5", "是否报告删失率与删失原因？", "CONSORT"),
    ("KM-6", "随访时间是否足够（中位随访 ≥ 主要事件中位时间）？", "Cochrane RoB 2"),
    ("KM-7", "是否按意向治疗（ITT）原则分析？", "CONSORT"),
    ("KM-8", "HR 95% CI 是否过宽（＞2 倍中位比）？", "Cochrane"),
]

_FOREST_ITEMS = [
    ("FP-1", "是否预先注册检索策略与纳入排除标准？", "Cochrane"),
    ("FP-2", "是否评估各研究的偏倚风险（RoB 2 / ROBINS-I）？", "Cochrane RoB 2"),
    ("FP-3", "是否报告 I² 与异质性检验 p 值？", "Cochrane"),
    ("FP-4", "效应模型选择（fixed/random）是否有方法学依据？", "Cochrane"),
    ("FP-5", "是否绘制漏斗图或进行 Egger 检验？", "Cochrane"),
    ("FP-6", "是否进行敏感性分析 / 亚组分析？", "Cochrane"),
    ("FP-7", "GRADE 证据等级是否给出？", "GRADE"),
    ("FP-8", "I²>50% 时是否在讨论中明确解释？", "Cochrane"),
    ("FP-9", "小样本研究权重是否过大（个别研究 >40%）？", "Cochrane"),
]

_ROC_ITEMS = [
    ("ROC-1", "是否报告 AUC 与 95% CI？", "STARD"),
    ("ROC-2", "是否说明参考标准（gold standard）？", "STARD"),
    ("ROC-3", "是否避免 cut-off 优化导致的过度拟合（验证集独立）？", "STARD"),
    ("ROC-4", "是否报告敏感度、特异度、PPV、NPV？", "STARD"),
    ("ROC-5", "是否在盲法下评估诊断结果？", "STARD"),
    ("ROC-6", "样本量是否充分（事件数 ≥ 10 per covariate）？", "STARD"),
    ("ROC-7", "多模型 AUC 是否做 DeLong 检验比较？", "STARD"),
    ("ROC-8", "最优 cut-off 是否在外部验证集中验证？", "STARD"),
    ("TRI-1", "是否声明研究类型（开发 / 验证 / 两者）？", "TRIPOD"),
    ("TRI-2", "discrimination 是否报告 C 统计量或 AUC + 95% CI？", "TRIPOD"),
    ("TRI-3", "calibration 是否评估（calibration plot / Hosmer-Lemeshow / slope+intercept）？", "TRIPOD"),
    ("TRI-4", "是否报告完整模型规格（公式 / 截距 / 系数）？", "TRIPOD"),
    ("TRI-5", "内验证是否实施（bootstrap / cross-validation / split）？", "TRIPOD"),
    ("TRI-6", "外部验证是否有独立队列？", "TRIPOD"),
    ("TRI-7", "临床效用是否评估（decision curve / NRI / IDI）？", "TRIPOD"),
]

_BOX_ITEMS = [
    ("BOX-1", "是否标注样本量 n？", "CONSORT"),
    ("BOX-2", "误差/离散度描述是否清楚（IQR/SD/range）？", "CONSORT"),
    ("BOX-3", "离群值是否被定义与说明？", "CONSORT"),
    ("BOX-4", "统计检验是否与数据类型匹配（参数 vs 非参数）？", "Cochrane"),
    ("BOX-5", "是否校正多重比较？", "Cochrane"),
    ("BOX-6", "组间基线是否齐性（年龄/性别/分期）？", "CONSORT"),
    ("BOX-7", "样本来源（独立 vs 技术重复）是否明确？", "MIAME"),
]

_SCATTER_ITEMS = [
    ("SC-1", "是否报告相关系数与 95% CI？", "STARD"),
    ("SC-2", "是否检验线性、正态性、方差齐性前提？", "Cochrane"),
    ("SC-3", "回归方程与预测带是否给出？", "CONSORT"),
    ("SC-4", "是否识别并说明离群点影响？", "Cochrane"),
    ("SC-5", "相关系数类型（Pearson / Spearman）是否与数据分布匹配？", "STARD"),
    ("SC-6", "样本量是否达到统计效能（一般 ≥ 30）？", "STARD"),
    # TRIPOD（calibration plot 通常用散点呈现）
    ("TRI-3c", "calibration plot：x=预测概率，y=实际概率，按十分位分组是否画出？", "TRIPOD"),
    ("TRI-8", "calibration slope 与 intercept 是否报告（理想线 y=x）？", "TRIPOD"),
    ("TRI-9", "Brier score 或平均绝对误差是否给出？", "TRIPOD"),
]

_BAR_ITEMS = [
    ("BAR-1", "误差棒类型是否明确（SD/SEM/CI）？", "CONSORT"),
    ("BAR-2", "y 轴是否从 0 起始或明确标注截断？", "CONSORT"),
    ("BAR-3", "样本量 n 与独立生物学重复数是否标注？", "CONSORT"),
    ("BAR-4", "统计检验与多重比较校正是否说明？", "Cochrane"),
    ("BAR-5", "每组独立生物学重复是否 ≥3？", "MIAME"),
    ("BAR-6", "数据分布假设（正态/方差齐）是否检验？", "Cochrane"),
]

_HEATMAP_ITEMS = [
    ("HM-1", "归一化方法（z-score / TPM / FPKM）是否明确？", "MIAME"),
    ("HM-2", "聚类方法（hierarchical / k-means）与距离度量是否说明？", "MIAME"),
    ("HM-3", "色板是否双向发散（适用于差异表达）？", "MIAME"),
    ("HM-4", "样本与基因的生物学重复是否足够（≥3）？", "MIAME"),
    ("HM-5", "缺失值处理方法是否说明（NA / 0 填充 / 插补）？", "MIAME"),
    ("HM-6", "样本独立性 / 是否混批（batch effect）是否评估？", "MIAME"),
]

_VOLCANO_ITEMS = [
    ("VOL-1", "是否明确阈值（|log2FC| 与 p/FDR）？", "CONSORT"),
    ("VOL-2", "多重比较校正方法是否说明（BH / Bonferroni）？", "Cochrane"),
    ("VOL-3", "效应量与显著性是否被同时报告？", "CONSORT"),
    ("VOL-4", "是否标注 top 基因与原始 counts？", "MIAME"),
    ("VOL-5", "样本量是否满足 power 估计（DESeq 推荐 ≥ 12）？", "MIAME"),
    ("VOL-6", "差异基因分布是否对称（避免仅上调偏向）？", "MIAME"),
]

_ITEMS_BY_TYPE: dict[str, list[tuple[str, str, str]]] = {
    "kaplan_meier": _KM_ITEMS,
    "forest_plot": _FOREST_ITEMS,
    "roc_curve": _ROC_ITEMS,
    "box_plot": _BOX_ITEMS,
    "scatter_plot": _SCATTER_ITEMS,
    "bar_chart": _BAR_ITEMS,
    "heatmap": _HEATMAP_ITEMS,
    "volcano_plot": _VOLCANO_ITEMS,
}

_FRAMEWORK_BY_TYPE: dict[str, str] = {
    "kaplan_meier": "CONSORT + Cochrane RoB 2",
    "forest_plot": "Cochrane + GRADE",
    "roc_curve": "STARD + TRIPOD",
    "box_plot": "CONSORT + Cochrane",
    "scatter_plot": "STARD + Cochrane + TRIPOD（calibration）",
    "bar_chart": "CONSORT + Cochrane",
    "heatmap": "MIAME",
    "volcano_plot": "MIAME + Cochrane",
}


def auto_evaluate(summary: StatisticalSummary) -> AppraisalResult:
    """基于 StatisticalSummary 自动评估可机器判定的项。

    判定策略：
    - raw 中显式给出 True/False 字段 → 直接采用
    - raw 中有可计算信号 → 派生判定 + 写 note
    - 字段缺失 → 保留为 None（待人工评估）
    """
    chart_type = summary.chart_type
    triples = _ITEMS_BY_TYPE.get(chart_type, [])
    framework = _FRAMEWORK_BY_TYPE.get(chart_type, "Generic")
    items = [ChecklistItem(id=i, question=q, framework=f) for i, q, f in triples]

    raw = summary.raw or {}

    def _resolve(item: ChecklistItem, key: str) -> bool | None:
        """从 raw 取字段：
        - bool/int/float 直接转 bool
        - 非空字符串 → True（视为已记录）
        - 否则 None（未评估）
        """
        if key in raw:
            v = raw[key]
            if isinstance(v, bool):
                item.note = f"{key}={v}"
                return v
            if isinstance(v, (int, float)):
                item.note = f"{key}={v}"
                return bool(v)
            if isinstance(v, str) and v.strip():
                item.note = f"{key}={v[:30]}"
                return True
        return None

    # ---------- KM ----------
    if chart_type == "kaplan_meier":
        for item in items:
            if item.id == "KM-2":
                item.passed = bool(raw.get("at_risk"))
                if item.passed:
                    item.note = "at_risk 已给出"
            elif item.id == "KM-3" and summary.primary:
                item.passed = summary.primary.p_value is not None
            elif item.id == "KM-4":
                ph = raw.get("schoenfeld_p") or raw.get("ph_test_p")
                if ph is not None:
                    item.passed = float(ph) > 0.05
                    item.note = f"Schoenfeld p={ph}"
            elif item.id == "KM-5":
                if "censoring_rate" in raw:
                    item.passed = bool(raw.get("censoring_rate"))
                    item.note = f"censoring_rate={raw['censoring_rate']}"
            elif item.id == "KM-7":
                v = _resolve(item, "itt_analysis")
                if v is not None:
                    item.passed = v
            elif item.id == "KM-8":
                if summary.primary and summary.primary.ci_lower and summary.primary.ci_upper:
                    width = summary.primary.ci_upper - summary.primary.ci_lower
                    eff = abs(summary.primary.value or 1.0) or 1.0
                    # CI 宽度 / |effect| > 2 即视为过宽
                    item.passed = (width / max(eff, 0.05)) <= 2.0
                    item.note = f"CI 宽度/效应={width/eff:.2f}"

    # ---------- Forest ----------
    if chart_type == "forest_plot":
        i2 = raw.get("i_squared")
        for item in items:
            if item.id == "FP-3":
                item.passed = (i2 is not None) or any("I²" in n for n in summary.notes)
                if i2 is not None:
                    item.note = f"I²={i2}%"
            elif item.id == "FP-4":
                item.passed = "model" in raw
            elif item.id == "FP-5":
                item.passed = bool(raw.get("funnel_plot") or raw.get("egger_p") is not None)
            elif item.id == "FP-8":
                # I²>50% 时若文中明确解释则通过；否则标记为未通过
                if i2 is not None and float(i2) > 50:
                    item.passed = bool(raw.get("heterogeneity_discussed"))
                    item.note = f"I²={i2}%（>50%）"
                else:
                    item.passed = True   # 不需要讨论
            elif item.id == "FP-9":
                # 单研究权重 > 40% 视为风险
                max_w = max((s.get("weight", 0) for s in raw.get("studies", [])), default=0)
                if max_w:
                    item.passed = max_w <= 0.4
                    item.note = f"最大权重={max_w*100:.1f}%"

    # ---------- ROC ----------
    if chart_type == "roc_curve":
        for item in items:
            if item.id == "ROC-1" and summary.primary:
                item.passed = summary.primary.ci_lower is not None
            elif item.id == "ROC-2":
                v = _resolve(item, "gold_standard")
                if v is not None:
                    item.passed = bool(v)
            elif item.id == "ROC-3":
                # cut-off 在训练集优化是常见偏倚：检查 explicit 报告或已独立验证
                v = _resolve(item, "external_validation") or _resolve(item, "cutoff_validation")
                if v is not None:
                    item.passed = bool(v)
            elif item.id == "ROC-4":
                item.passed = any("敏感度" in n or "特异度" in n for n in summary.notes)
            elif item.id == "ROC-5":
                v = _resolve(item, "blinded")
                if v is not None:
                    item.passed = bool(v)
            elif item.id == "ROC-6":
                epp = raw.get("events_per_predictor")
                if epp is not None:
                    item.passed = float(epp) >= 10
                    item.note = f"EPP={epp}"
            elif item.id == "ROC-7":
                item.passed = raw.get("delong_p") is not None
                if item.passed:
                    item.note = f"DeLong p={raw['delong_p']}"
            elif item.id == "ROC-8":
                v = _resolve(item, "external_validation")
                if v is not None:
                    item.passed = bool(v)
            # ---------- TRIPOD ----------
            elif item.id == "TRI-1":
                rt = raw.get("study_type") or raw.get("model_phase")
                if rt is not None:
                    item.passed = str(rt).lower() in {"development", "validation", "both"}
                    item.note = f"study_type={rt}"
            elif item.id == "TRI-2":
                # 与 ROC-1 重叠：discrimination 必有 C 统计量
                if summary.primary and summary.primary.ci_lower is not None:
                    item.passed = True
            elif item.id == "TRI-3":
                keys = ("calibration_plot", "calibration_slope", "hosmer_lemeshow_p",
                        "calibration_intercept", "calibration")
                present = [k for k in keys if raw.get(k) is not None]
                item.passed = bool(present)
                if present:
                    item.note = f"{present[0]}={raw[present[0]]}"
            elif item.id == "TRI-4":
                keys = ("model_coefficients", "model_intercept", "model_equation",
                        "coefficients", "beta")
                item.passed = any(k in raw for k in keys)
            elif item.id == "TRI-5":
                keys = ("internal_validation", "bootstrap_iters", "cv_folds", "split_sample")
                present = [k for k in keys if k in raw]
                item.passed = bool(present)
                if present:
                    item.note = f"{present[0]}={raw[present[0]]}"
            elif item.id == "TRI-6":
                v = _resolve(item, "external_validation") or _resolve(item, "external_cohort")
                if v is not None:
                    item.passed = bool(v)
            elif item.id == "TRI-7":
                keys = ("decision_curve", "nri", "idi", "clinical_utility")
                present = [k for k in keys if k in raw]
                item.passed = bool(present)
                if present:
                    item.note = f"{present[0]}={raw[present[0]]}"

    # ---------- Box ----------
    if chart_type == "box_plot":
        for item in items:
            if item.id == "BOX-1":
                groups = raw.get("groups", [])
                item.passed = all(g.get("n") is not None for g in groups)
            elif item.id == "BOX-3":
                item.passed = any(
                    "outlier" in str(k).lower() or "outliers" in g
                    for g in raw.get("groups", []) for k in g
                )
            elif item.id == "BOX-6":
                v = _resolve(item, "baseline_balanced")
                if v is not None:
                    item.passed = v
            elif item.id == "BOX-7":
                v = _resolve(item, "sample_independent")
                if v is not None:
                    item.passed = v

    # ---------- Scatter ----------
    if chart_type == "scatter_plot":
        for item in items:
            if item.id == "SC-1":
                item.passed = summary.primary is not None
            elif item.id == "SC-5":
                method = raw.get("correlation_method")
                if method:
                    item.passed = method in {"pearson", "spearman"}
                    item.note = f"method={method}"
            elif item.id == "SC-6":
                n = raw.get("n") or (len(raw.get("points", [])) if raw.get("points") else None)
                if n is not None:
                    item.passed = n >= 30
                    item.note = f"n={n}"
            # ---------- TRIPOD 散点专用（calibration plot） ----------
            elif item.id == "TRI-3c":
                item.passed = bool(raw.get("calibration_plot"))
                if item.passed:
                    item.note = "calibration plot 已绘制"
            elif item.id == "TRI-8":
                keys = ("calibration_slope", "calibration_intercept")
                present = [k for k in keys if k in raw]
                item.passed = len(present) == 2
                if item.passed:
                    item.note = f"slope={raw['calibration_slope']}, intercept={raw['calibration_intercept']}"
            elif item.id == "TRI-9":
                keys = ("brier_score", "mean_absolute_error", "mae")
                present = [k for k in keys if k in raw]
                item.passed = bool(present)
                if present:
                    item.note = f"{present[0]}={raw[present[0]]}"

    # ---------- Bar ----------
    if chart_type == "bar_chart":
        for item in items:
            if item.id == "BAR-2":
                item.passed = not any("截断" in n or "⚠" in n for n in summary.notes)
            elif item.id == "BAR-3":
                item.passed = bool(raw.get("groups"))
            elif item.id == "BAR-4":
                v = _resolve(item, "p_adjustment")
                if v is not None:
                    item.passed = v
                else:
                    # 若 raw 中给出 p_adjustment_method 则算通过
                    if raw.get("p_adjustment_method"):
                        item.passed = True
                        item.note = f"method={raw['p_adjustment_method']}"
            elif item.id == "BAR-5":
                rep = raw.get("min_replicates_per_group")
                if rep is not None:
                    item.passed = rep >= 3
                    item.note = f"min_replicates={rep}"
            elif item.id == "BAR-6":
                v = _resolve(item, "normality_tested")
                if v is not None:
                    item.passed = v

    # ---------- Heatmap ----------
    if chart_type == "heatmap":
        for item in items:
            if item.id == "HM-1":
                item.passed = raw.get("scale") in {"z-score", "minmax", "tpm", "fpkm", "log2"}
            elif item.id == "HM-2":
                item.passed = bool(raw.get("clustering_method") or raw.get("clustering_rows"))
            elif item.id == "HM-3":
                item.passed = (raw.get("colormap", "").lower() in {"rdbu", "bwr", "rdgy", "seismic", "coolwarm"})
            elif item.id == "HM-4":
                reps = raw.get("min_biological_replicates")
                if reps is not None:
                    item.passed = reps >= 3
                    item.note = f"min_reps={reps}"
            elif item.id == "HM-5":
                v = _resolve(item, "missing_value_method")
                if v is not None:
                    item.passed = v
            elif item.id == "HM-6":
                v = _resolve(item, "batch_effect_assessed")
                if v is not None:
                    item.passed = v

    # ---------- Volcano ----------
    if chart_type == "volcano_plot":
        for item in items:
            if item.id == "VOL-1":
                item.passed = ("fc_threshold" in raw) and ("p_threshold" in raw)
            elif item.id == "VOL-2":
                item.passed = any("FDR" in n or "BH" in n or "Bonferroni" in n for n in summary.notes)
            elif item.id == "VOL-5":
                n_samp = raw.get("n_samples") or (len(raw.get("groups", [])) if raw.get("groups") else None)
                if n_samp is not None:
                    item.passed = n_samp >= 12
                    item.note = f"n_samples={n_samp}"
            elif item.id == "VOL-6":
                up = raw.get("n_up"); down = raw.get("n_down")
                if up is not None and down is not None and (up + down) > 0:
                    ratio = max(up, down) / max(min(up, down), 1)
                    item.passed = ratio <= 3.0
                    item.note = f"up/down={up}:{down}（max/min={ratio:.1f}）"

    # ---------- v1.2.0: TRIPOD-AI 追加（仅 ROC / Scatter） ----------
    # 触发条件：图表承载预测模型评估功能（ROC/Scatter 必然）
    if _TRIPOD_AI_AVAILABLE and chart_type in {"roc_curve", "scatter_plot"}:
        triggered, ai_items = evaluate_tripod_ai(summary)
        if triggered:
            # 即便 ai_items 仅有 sentinel "TRIPOD-AI-0"，也展示
            items.extend(ai_items)
            if "TRIPOD-AI" not in framework:
                framework = framework + " + TRIPOD-AI"

    return AppraisalResult(chart_type=chart_type, framework=framework, items=items)


def manual_set(result: AppraisalResult, item_id: str, passed: bool, note: str = "") -> None:
    """手工标记某条目。"""
    for item in result.items:
        if item.id == item_id:
            item.passed = passed
            if note:
                item.note = note
            return


def checklist(chart_type: str) -> list[tuple[str, str, str]]:
    """返回空 checklist（供手工评估使用）。"""
    return _ITEMS_BY_TYPE.get(chart_type, [])
