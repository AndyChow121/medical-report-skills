#!/usr/bin/env python3
"""
图注生成器 - 为科学图表生成标准化图注。

用法：
    python main.py --input <image_path> --type <chart_type> [options]

支持的图表类型：
    bar, line, scatter, box, heatmap, microscopy, flow, western
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ChartType(Enum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    BOX = "box"
    HEATMAP = "heatmap"
    MICROSCOPY = "microscopy"
    FLOW = "flow"
    WESTERN = "western"


@dataclass
class LegendTemplate:
    """用于生成图注的模板。"""
    title_template: str
    description_template: str
    data_template: str
    stat_template: str
    notes_template: str


TEMPLATES = {
    ChartType.BAR: LegendTemplate(
        title_template="Comparison of {metric} across {groups}",
        description_template="Bar chart showing {metric} in {sample_description}.",
        data_template="Data are presented as mean ± SEM from n={n} independent experiments.",
        stat_template="Statistical significance was determined by {test}; *p<0.05, **p<0.01, ***p<0.001.",
        notes_template="Error bars represent standard error of the mean (SEM)."
    ),
    ChartType.LINE: LegendTemplate(
        title_template="Time course of {metric} in {condition}",
        description_template="Line graph showing {metric} over {time_range} in {sample_description}.",
        data_template="Data points represent mean ± SEM from n={n} replicates per time point.",
        stat_template="Significance compared to control: *p<0.05, **p<0.01.",
        notes_template="Shaded areas indicate standard error of the mean."
    ),
    ChartType.SCATTER: LegendTemplate(
        title_template="Correlation between {x_var} and {y_var}",
        description_template="Scatter plot showing the relationship between {x_var} and {y_var} in {sample_description}.",
        data_template="Each point represents an individual {sample_unit}. n={n}.",
        stat_template="Correlation coefficient (r) = {r_value}, p = {p_value}.",
        notes_template="Solid line indicates linear regression fit."
    ),
    ChartType.BOX: LegendTemplate(
        title_template="Distribution of {metric} across {groups}",
        description_template="Box plot showing {metric} distribution in {sample_description}.",
        data_template="Boxes represent interquartile range (IQR), lines indicate median, whiskers show 1.5×IQR. n={n} per group.",
        stat_template="Mann-Whitney U test; *p<0.05, **p<0.01.",
        notes_template="Outliers are shown as individual points."
    ),
    ChartType.HEATMAP: LegendTemplate(
        title_template="{metric} matrix across {dimensions}",
        description_template="Heatmap displaying {metric} values across {dimensions}.",
        data_template="Color scale indicates {value_range}. Data normalized by {normalization_method}.",
        stat_template="Hierarchical clustering performed using {clustering_method}.",
        notes_template=""
    ),
    ChartType.MICROSCOPY: LegendTemplate(
        title_template="{staining} staining of {sample_type}",
        description_template="Representative confocal microscopy images of {sample_type} stained with {stains}.",
        data_template="Scale bar: {scale_bar}. Images acquired with {microscope_type}.",
        stat_template="",
        notes_template="DAPI (blue) indicates nuclei."
    ),
    ChartType.FLOW: LegendTemplate(
        title_template="Flow cytometry analysis of {marker}",
        description_template="FACS plots showing {marker} expression in {cell_type}.",
        data_template="{percent_positive}% of cells were positive for {marker}. n={n} experiments.",
        stat_template="Gating strategy shown in supplementary figure.",
        notes_template=""
    ),
    ChartType.WESTERN: LegendTemplate(
        title_template="Western blot analysis of {protein}",
        description_template="Immunoblot showing {protein} expression in {sample_description}.",
        data_template="{loading_control} served as loading control. Representative of n={n} experiments.",
        stat_template="Quantification shown in adjacent bar graph.",
        notes_template="Molecular weight markers (kDa) indicated on left."
    ),
}


class LegendGenerator:
    """科学图注生成器。

    v1.4.0 新增：
      - 类方法 `from_statistical_summary(summary)` 桥接 graph-interpretation 输出，
        自动把 KM/Forest/ROC/Box/Scatter/Bar/Heatmap/Volcano 的 `StatisticalSummary`
        转换为分子生物图注模板（BAR/LINE/SCATTER/BOX/HEATMAP）。
    """

    def __init__(self, chart_type: ChartType, language: str = "en"):
        self.chart_type = chart_type
        self.language = language
        self.template = TEMPLATES.get(chart_type, TEMPLATES[ChartType.BAR])

    @classmethod
    def from_statistical_summary(
        cls,
        summary,             # graph-interpretation 的 StatisticalSummary
        figure_number: str = "1",
    ):
        """从 graph-interpretation 的 StatisticalSummary 自动选择模板并填充字段。

        支持 chart_type → LegendGenerator template 的映射：
          kaplan_meier / forest_plot  → LINE（time-to-event 描述）
          roc_curve / scatter_plot   → SCATTER（关联/校准点）
          box_plot                   → BOX
          bar_chart / volcano_plot   → BAR
          heatmap                    → HEATMAP
        """
        ct = (getattr(summary, "chart_type", "") or "").lower()
        primary = getattr(summary, "primary", None)
        notes_raw = list(getattr(summary, "notes", []) or [])
        notes = [n for n in notes_raw if isinstance(n, str) and n.strip()]
        raw = getattr(summary, "raw", {}) or {}
        title = getattr(summary, "title", "") or ct.replace("_", " ").title()

        # 主效应量
        metric = primary.measure if primary and getattr(primary, "measure", None) else "experimental values"
        groups = raw.get("arms") or raw.get("groups") or raw.get("comparison") or "experimental groups"
        if isinstance(groups, list):
            groups = " vs ".join(str(g.get("name", g) if isinstance(g, dict) else g) for g in groups)[:60]
        sample_description = raw.get("sample_description") or raw.get("sample_unit") or "tested samples"

        # 样本量：KM/Box 用 n_total；Forest/Volcano 从 studies/n_de 求和
        n = raw.get("n_total") or raw.get("n") or raw.get("sample_size")
        if not n and isinstance(raw.get("studies"), list):
            n = sum(s.get("n_total") or 0 for s in raw["studies"] if isinstance(s, dict))
        if not n and isinstance(raw.get("groups"), list):
            n = sum(g.get("n") or 0 for g in raw["groups"] if isinstance(g, dict))
        if not n or (isinstance(n, str) and not n.isdigit()):
            n = 3

        # 模板选择
        ALIAS = {
            "kaplan_meier": ChartType.LINE,
            "forest_plot": ChartType.LINE,
            "roc_curve": ChartType.SCATTER,
            "scatter_plot": ChartType.SCATTER,
            "box_plot": ChartType.BOX,
            "bar_chart": ChartType.BAR,
            "volcano_plot": ChartType.BAR,
            "heatmap": ChartType.HEATMAP,
        }
        gen = cls(ALIAS.get(ct, ChartType.BAR))

        # 抽取模板专用字段
        # KM/Forest/ROC 不是经典 scatter/bar，给出专用 description 覆盖
        ct_lower = ct
        if ct_lower in ("roc_curve",):
            description_override = (
                "Receiver operating characteristic (ROC) curve for "
                "{sample_description}; AUC = {auc_str}; cutoff = {cutoff}; "
                "sensitivity = {sens}, specificity = {spec}."
            )
            x_var = "1 − specificity"
            y_var = "sensitivity"
            r_value = "AUC"
            p_value = raw.get("p_value") or "see primary measure"
        elif ct_lower == "forest_plot":
            description_override = (
                "Forest plot of pooled {metric} ({n} subjects across "
                "{k_studies} studies). Markers show point estimates; "
                "horizontal bars indicate 95% CIs. Heterogeneity (I²) reported in notes."
            )
            x_var = raw.get("x_var") or raw.get("measure", "Effect size")
            y_var = "Study"
            r_value = primary.measure if primary and getattr(primary, "measure", None) else "OR"
            p_value = (f"{primary.p_value:.4f}" if primary and getattr(primary, "p_value", None) is not None
                        else raw.get("p_value") or "reported")
        elif ct_lower == "kaplan_meier":
            description_override = (
                "Kaplan-Meier estimates of {outcome} for {sample_description} "
                "(n={n} subjects in {k_arms} arms)."
            )
            x_var = "Time (months)"
            y_var = "Survival probability"
            r_value = (f"{primary.value:.3f}" if primary and getattr(primary, "value", None) is not None
                        else "HR")
            p_value = (f"{primary.p_value:.4f}" if primary and getattr(primary, "p_value", None) is not None
                        else raw.get("p_value") or "reported")
        elif ct_lower == "volcano_plot":
            description_override = (
                "Volcano plot of {n} features comparing {groups}. Red points mark "
                "statistically significant features after multiple-testing correction."
            )
            x_var = "log2(fold change)"
            y_var = "−log10(p-value)"
            r_value = "log2(FC)"
            p_value = "FDR-adjusted"
        else:
            description_override = None
            x_var = raw.get("x_var") or "X"
            y_var = raw.get("y_var") or "Y"
            r_value = (f"{primary.value:.3f}" if primary and getattr(primary, "value", None) is not None
                        else raw.get("r_value") or "computed")
            p_value = (f"{primary.p_value:.4f}" if primary and getattr(primary, "p_value", None) is not None
                        else raw.get("p_value") or "reported")
        # 样本/统计基础信息已通过 kwargs 传入；notes 走末尾追加

        # 拼成 stat 字符串
        stat = ""
        if primary is not None and getattr(primary, "value", None) is not None:
            stat = f"{primary.measure} = {primary.value:.3f}"
            if getattr(primary, "ci_str", lambda: '')():
                stat += f" ({primary.ci_str()})"
            if getattr(primary, "p_value", None) is not None:
                stat += f", p = {primary.p_value:.4f}"

        md = gen.generate(
            figure_number=figure_number,
            metric=metric,
            groups=str(groups),
            sample_description=str(sample_description),
            n=int(n) if str(n).isdigit() else 3,
            x_var=x_var,
            y_var=y_var,
            r_value=r_value,
            p_value=p_value,
            sample_unit=raw.get("sample_unit") or "sample",
            condition=raw.get("condition") or "the experiment",
            time_range=raw.get("time_range") or "follow-up",
            test=raw.get("test") or "appropriate statistical test",
            value_range=raw.get("value_range") or "normalized values",
            normalization_method=raw.get("normalization_method") or "z-score",
            clustering_method=raw.get("clustering_method") or "hierarchical",
            dimensions=raw.get("dimensions") or "samples × features",
        )

        # 若有 description_override 则覆写第二段（紧跟 **Figure N.** title 的那一段）
        if description_override is not None:
            try:
                override_str = description_override.format(
                    sample_description=str(sample_description),
                    n=int(n) if str(n).isdigit() else 3,
                    groups=str(groups),
                    metric=metric,
                    k_studies=len(raw.get("studies", []) or []) or 3,
                    k_arms=len(raw.get("arms", []) or []) or 2,
                    auc_str=(f"{primary.value:.3f} (95% CI {primary.ci_lower:g}-{primary.ci_upper:g})"
                             if primary and getattr(primary, "value", None) is not None else "computed"),
                    cutoff=str(raw.get("optimal_cutoff", "computed")),
                    sens=str(raw.get("sensitivity", "computed")),
                    spec=str(raw.get("specificity", "computed")),
                    outcome=raw.get("outcome") or "overall survival",
                )
            except (KeyError, IndexError):
                override_str = None
            if override_str:
                # markdown 结构：**Figure N.** title \n {description} \n Data...
                lines = md.split("\n")
                # 找到 title 行（包含 **Figure N.**）的下一个非空行
                for i, line in enumerate(lines):
                    if line.startswith("**Figure") and i + 1 < len(lines):
                        # i+1 应该是空行，再后是 description
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == "":
                                continue
                            lines[j] = override_str
                            break
                        break
                md = "\n".join(lines)

        # 附加 statistical summary 注解
        if stat:
            md += f"\n\n**Statistical summary**: {stat}\n"
        if notes:
            md += "\n".join(f"- {n_}" for n_ in notes[:3])
        return md

    def generate(
        self,
        figure_number: str = "1",
        metric: str = "experimental values",
        groups: str = "experimental groups",
        sample_description: str = "tested samples",
        n: int = 3,
        **kwargs
    ) -> str:
        """生成完整的图注。"""

        # 构建图注各部分
        sections = []

        # 图编号和标题
        title = self.template.title_template.format(
            metric=metric,
            groups=groups,
            **kwargs
        )
        sections.append(f"**Figure {figure_number}.** {title}")
        sections.append("")

        # 主要描述
        description = self.template.description_template.format(
            metric=metric,
            sample_description=sample_description,
            **kwargs
        )
        sections.append(description)

        # 数据细节
        data_detail = self.template.data_template.format(
            n=n,
            **kwargs
        )
        sections.append(data_detail)

        # 统计信息
        if self.template.stat_template:
            stats = self.template.stat_template.format(**kwargs)
            if stats:
                sections.append(stats)

        # 附加说明
        if self.template.notes_template:
            notes = self.template.notes_template.format(**kwargs)
            if notes:
                sections.append(notes)

        return "\n".join(sections)

    def analyze_image(self, image_path: Path) -> Dict:
        """分析图像以提取图表元数据。"""
        # 图像分析的占位符
        # 在生产环境中，这里会使用PIL + OCR/视觉模型
        return {
            "detected_type": self.chart_type.value,
            "has_error_bars": True,
            "has_stats": True,
            "dimensions": "detected"
        }


def detect_chart_type(image_path: Path) -> Optional[ChartType]:
    """尝试从图像中检测图表类型。"""
    # 基于文件命名或基本分析的简化检测
    name_lower = image_path.stem.lower()

    type_hints = {
        "bar": ChartType.BAR,
        "line": ChartType.LINE,
        "scatter": ChartType.SCATTER,
        "box": ChartType.BOX,
        "heatmap": ChartType.HEATMAP,
        "microscopy": ChartType.MICROSCOPY,
        "confocal": ChartType.MICROSCOPY,
        "flow": ChartType.FLOW,
        "facs": ChartType.FLOW,
        "western": ChartType.WESTERN,
        "wb": ChartType.WESTERN,
    }

    for hint, ctype in type_hints.items():
        if hint in name_lower:
            return ctype

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate standardized figure legends for scientific charts"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to chart image"
    )
    parser.add_argument(
        "--type", "-t",
        type=str,
        required=False,
        choices=[ct.value for ct in ChartType],
        help="Chart type (auto-detected if not specified)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="markdown",
        choices=["text", "markdown", "latex"],
        help="Output format"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="en",
        choices=["en", "zh"],
        help="Output language"
    )
    parser.add_argument(
        "--figure-number", "-n",
        type=str,
        default="1",
        help="Figure number"
    )

    args = parser.parse_args()

    # 验证输入
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 确定图表类型
    chart_type = None
    if args.type:
        chart_type = ChartType(args.type)
    else:
        chart_type = detect_chart_type(input_path)
        if not chart_type:
            print("Error: Could not auto-detect chart type. Please specify with --type", file=sys.stderr)
            sys.exit(1)
        print(f"Auto-detected chart type: {chart_type.value}", file=sys.stderr)

    # 生成图注
    generator = LegendGenerator(chart_type, args.language)

    # 所有图表类型的基本参数
    base_params = {
        "figure_number": args.figure_number,
        "metric": "measured values",
        "groups": "experimental conditions",
        "sample_description": "the tested samples",
        "n": 3,
        "test": "one-way ANOVA with Tukey's post-hoc test"
    }

    # 添加特定图表类型的默认参数
    type_specific_params = {
        ChartType.SCATTER: {
            "x_var": "independent variable",
            "y_var": "dependent variable",
            "r_value": "0.75",
            "p_value": "<0.001",
            "sample_unit": "sample"
        },
        ChartType.WESTERN: {
            "protein": "target protein",
            "loading_control": "β-actin"
        },
        ChartType.FLOW: {
            "marker": "CD marker",
            "cell_type": "cell population",
            "percent_positive": "45"
        },
        ChartType.HEATMAP: {
            "dimensions": "samples and features",
            "value_range": "normalized expression values",
            "normalization_method": "z-score",
            "clustering_method": "Ward's method"
        },
        ChartType.LINE: {
            "condition": "experimental condition",
            "time_range": "24 hours"
        },
        ChartType.MICROSCOPY: {
            "staining": "immunofluorescence",
            "sample_type": "cell culture",
            "stains": "DAPI and phalloidin",
            "scale_bar": "50 μm",
            "microscope_type": "confocal microscope"
        }
    }

    # 合并参数
    if chart_type in type_specific_params:
        base_params.update(type_specific_params[chart_type])

    legend = generator.generate(**base_params)

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(legend, encoding="utf-8")
        print(f"Legend saved to: {args.output}")
    else:
        print(legend)


if __name__ == "__main__":
    main()
