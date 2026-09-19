"""端到端链路测试：interpret → caption → audiences → appraise → render-svg。

对应 `graph-interp verify` 每类样本跑的 6 步中的前 5 步
（第 6 步 to-legend docx 需要 python-docx，在此跳过）。
"""

import pytest

import svg_render
from _samples import load_bundled_sample
from appraisal import auto_evaluate
from audiences import render_all
from captions import generate_caption
from parsers import PARSERS

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

SVG_FN = {
    "kaplan_meier": svg_render.render_km,
    "forest_plot": svg_render.render_forest,
    "roc_curve": svg_render.render_roc,
    "box_plot": svg_render.render_box,
    "scatter_plot": svg_render.render_scatter,
    "bar_chart": svg_render.render_bar,
    "heatmap": svg_render.render_heatmap,
    "volcano_plot": svg_render.render_volcano,
}

EXPECTED_AUDIENCES = 4  # researchers / clinicians / patients / policy_makers


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_full_pipeline(alias, chart_type):
    """5 步链路应逐步产出非空结果。"""
    data = load_bundled_sample(alias)
    summary = PARSERS[chart_type].parse(data)

    # 2. caption（中文期刊风格）
    cap = generate_caption(summary, style="cma", language="zh", figure_id="图1")
    assert isinstance(cap, str) and cap.strip()

    # 3. audiences（四档受众）
    aud = render_all(summary, locale="zh_CN")
    assert len(aud) >= EXPECTED_AUDIENCES

    # 4. appraise
    ap = auto_evaluate(summary)
    assert ap.n_items > 0
    assert ap.framework
    # 通过 + 未通过 + 未评估 = 总条目
    assert ap.n_passed + ap.n_failed + ap.n_unchecked == ap.n_items

    # 5. render-svg
    svg = SVG_FN[chart_type](data, title=data.get("title", ""))
    assert "<svg" in svg


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_appraisal_score_in_range(alias, chart_type):
    """overall_score 必须在 0-1 之间，或为 None（无已评估条目）。"""
    data = load_bundled_sample(alias)
    ap = auto_evaluate(PARSERS[chart_type].parse(data))

    s = ap.overall_score
    if s is not None:
        assert 0.0 <= s <= 1.0


def test_ml_sample_triggers_tripod_ai():
    """完整 ML 样本必须触发 TRIPOD-AI 框架（roc_ml 是主要卖点）。"""
    data = load_bundled_sample("roc_ml")
    ap = auto_evaluate(PARSERS["roc_curve"].parse(data))

    assert "TRIPOD-AI" in ap.framework
    assert ap.n_items >= 14  # STARD + TRIPOD + TRIPOD-AI


def test_non_ml_sample_does_not_trigger_tripod_ai():
    """普通 KM 样本不应触发 TRIPOD-AI。"""
    data = load_bundled_sample("km")
    ap = auto_evaluate(PARSERS["kaplan_meier"].parse(data))

    assert "TRIPOD-AI" not in ap.framework


def test_caption_differs_by_style():
    """不同期刊风格应产出不同图注（避免模板串台）。"""
    data = load_bundled_sample("km")
    summary = PARSERS["kaplan_meier"].parse(data)

    cma = generate_caption(summary, style="cma", language="zh", figure_id="图1")
    cslco = generate_caption(summary, style="cslco", language="zh", figure_id="图1")

    assert cma != cslco
