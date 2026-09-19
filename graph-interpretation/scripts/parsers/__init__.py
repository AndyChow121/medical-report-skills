"""8 类图表解析器集合。"""
from .base import BaseParser, StatisticalSummary, EffectEstimate
from .kaplan_meier import KaplanMeierParser
from .forest_plot import ForestPlotParser
from .roc_curve import RocCurveParser
from .box_plot import BoxPlotParser
from .scatter_plot import ScatterPlotParser
from .bar_chart import BarChartParser
from .heatmap import HeatmapParser
from .volcano_plot import VolcanoPlotParser

PARSERS: dict[str, BaseParser] = {
    p.chart_type: p for p in [
        KaplanMeierParser(),
        ForestPlotParser(),
        RocCurveParser(),
        BoxPlotParser(),
        ScatterPlotParser(),
        BarChartParser(),
        HeatmapParser(),
        VolcanoPlotParser(),
    ]
}

__all__ = [
    "BaseParser",
    "StatisticalSummary",
    "EffectEstimate",
    "PARSERS",
    "KaplanMeierParser",
    "ForestPlotParser",
    "RocCurveParser",
    "BoxPlotParser",
    "ScatterPlotParser",
    "BarChartParser",
    "HeatmapParser",
    "VolcanoPlotParser",
]
