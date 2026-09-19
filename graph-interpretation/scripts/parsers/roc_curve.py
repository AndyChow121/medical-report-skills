"""ROC 曲线解析器（诊断准确性研究）。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class RocCurveParser(BaseParser):
    """ROC 曲线：抽取 AUC、最佳截断值、敏感性、特异性、Youden 指数。"""

    chart_type = "roc_curve"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        primary = EffectEstimate(measure="AUC")
        secondary: list[EffectEstimate] = []
        notes: list[str] = []

        # AUC 与 CI
        auc = data.get("auc")
        if auc is not None:
            primary.value = float(auc)
            ci = data.get("auc_ci")
            if ci and len(ci) == 2:
                primary.ci_lower, primary.ci_upper = float(ci[0]), float(ci[1])
            primary.n = data.get("n")

        # 诊断能力判读
        if auc is not None:
            if auc >= 0.9:
                notes.append("AUC ≥0.9：优秀判别力")
            elif auc >= 0.8:
                notes.append("AUC 0.8-0.9：良好判别力")
            elif auc >= 0.7:
                notes.append("AUC 0.7-0.8：一般判别力")
            else:
                notes.append("AUC <0.7：判别力不足")

        # 最佳截断点（Youden）
        cutoff = data.get("optimal_cutoff")
        if cutoff is not None:
            sens = data.get("sensitivity")
            spec = data.get("specificity")
            youden = (sens or 0) + (spec or 0) - 1 if sens is not None and spec is not None else None
            secondary.append(EffectEstimate(
                measure="Youden",
                value=youden,
                n=primary.n,
            ))
            note = f"最佳截断值={cutoff}"
            if sens is not None:
                note += f"，敏感度={sens:.2f}"
            if spec is not None:
                note += f"，特异度={spec:.2f}"
            if youden is not None:
                note += f"，Youden={youden:.2f}"
            notes.append(note)

        # 多曲线比较
        curves = data.get("curves", [])
        if curves:
            notes.append(f"共 {len(curves)} 条 ROC 曲线")
            for c in curves:
                secondary.append(EffectEstimate(
                    measure="AUC",
                    value=c.get("auc"),
                    ci_lower=(c.get("ci") or [None, None])[0],
                    ci_upper=(c.get("ci") or [None, None])[1],
                    n=c.get("n"),
                ))

        # 比较检验（DeLong）
        delong_p = data.get("delong_p")
        if delong_p is not None:
            notes.append(f"DeLong 比较检验 p={delong_p}")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "ROC curve"),
            primary=primary,
            secondary=secondary,
            notes=notes,
            # v1.2.0: 先 copy 原 data 让 model_type/data_source 等 ML 标签透传；
            # 然后用 parser 加工过的字段覆盖（更权威）。
            raw={
                **data,
                "cutoff": cutoff,
                "curves": curves,
                "delong_p": data.get("delong_p"),
                "events_per_predictor": data.get("events_per_predictor"),
                "external_validation": data.get("external_validation"),
                "sensitivity": data.get("sensitivity"),
                "specificity": data.get("specificity"),
                "gold_standard": data.get("gold_standard"),
                "blinded": data.get("blinded"),
                # TRIPOD 字段
                "study_type": data.get("study_type") or data.get("model_phase"),
                "calibration_plot": data.get("calibration_plot"),
                "calibration_slope": data.get("calibration_slope"),
                "calibration_intercept": data.get("calibration_intercept"),
                "hosmer_lemeshow_p": data.get("hosmer_lemeshow_p"),
                "model_coefficients": data.get("model_coefficients"),
                "model_intercept": data.get("model_intercept"),
                "model_equation": data.get("model_equation"),
                "internal_validation": data.get("internal_validation"),
                "bootstrap_iters": data.get("bootstrap_iters"),
                "cv_folds": data.get("cv_folds"),
                "split_sample": data.get("split_sample"),
                "external_cohort": data.get("external_cohort"),
                "decision_curve": data.get("decision_curve"),
                "nri": data.get("nri"),
                "idi": data.get("idi"),
                "brier_score": data.get("brier_score"),
            },
        )
