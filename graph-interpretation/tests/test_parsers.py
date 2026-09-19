"""8 类图表解析器测试。

每类用 bundled sample 跑一遍，断言：
1. 返回带正确 chart_type / title 的 StatisticalSummary
2. to_dict() 产出 JSON 可序列化结构（verify / all 子命令依赖它）
3. 8 类解析器全部注册在 PARSERS 中
"""

import json

import pytest

from _samples import load_bundled_sample
from parsers import PARSERS

# bundled sample 别名 → 期望的 parser chart_type
CASES = [
    ("km", "kaplan_meier"),
    ("forest", "forest_plot"),
    ("roc", "roc_curve"),
    ("box", "box_plot"),
    ("scatter", "scatter_plot"),
    ("bar", "bar_chart"),
    ("heatmap", "heatmap"),
    ("volcano", "volcano_plot"),
]

ALL_PARSERS = {
    "kaplan_meier",
    "forest_plot",
    "roc_curve",
    "box_plot",
    "scatter_plot",
    "bar_chart",
    "heatmap",
    "volcano_plot",
}


def test_all_eight_parsers_registered():
    """8 类解析器必须全部注册，避免新增类型时漏挂 dispatch 表。"""
    assert ALL_PARSERS.issubset(set(PARSERS))


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_parser_returns_summary(alias, chart_type):
    """每类解析器都应返回带 chart_type / title 的 StatisticalSummary。"""
    data = load_bundled_sample(alias)
    summary = PARSERS[chart_type].parse(data)

    assert summary.chart_type == chart_type
    assert isinstance(summary.title, str) and summary.title
    assert isinstance(summary.raw, dict)


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_summary_to_dict_is_serializable(alias, chart_type):
    """to_dict() 必须 JSON 可序列化——all / verify 子命令直接依赖它。"""
    data = load_bundled_sample(alias)
    summary = PARSERS[chart_type].parse(data)

    payload = summary.to_dict()
    assert isinstance(payload, dict)
    json.dumps(payload, ensure_ascii=False)  # 不应抛异常


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_parser_is_deterministic(alias, chart_type):
    """同一输入重复解析应得到相同结果（无隐藏随机性 / 状态泄漏）。"""
    data = load_bundled_sample(alias)
    a = PARSERS[chart_type].parse(data)
    b = PARSERS[chart_type].parse(data)

    assert a.title == b.title
    assert a.to_dict() == b.to_dict()
