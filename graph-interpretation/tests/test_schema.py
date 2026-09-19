"""JSON Schema 校验测试（v1.5.0 _schema.py）。

覆盖：
1. 全部 bundled sample 通过各自类型的 schema
2. 越界值 / 缺必填字段被正确拒绝
3. 8 类 schema 全部暴露
"""

import pytest

from _samples import load_bundled_sample
from _schema import SCHEMAS, validate_payload

CASES = [
    ("km", "kaplan_meier"),
    ("forest", "forest_plot"),
    ("roc", "roc_curve"),
    ("box", "box_plot"),
    ("scatter", "scatter_plot"),
    ("bar", "bar_chart"),
    ("heatmap", "heatmap"),
    ("volcano", "volcano_plot"),
    # 扩展场景：ML 与中文期刊样本走标准 parser 类型
    ("roc_ml", "roc_curve"),
    ("csco_km", "kaplan_meier"),
]


@pytest.mark.parametrize("alias,chart_type", CASES)
def test_sample_passes_own_schema(alias, chart_type):
    """bundled sample 是 schema 的事实标准，必须全部通过。"""
    data = load_bundled_sample(alias)
    ok, errors = validate_payload(data, chart_type)
    assert ok, f"{alias} 未通过 {chart_type} schema: {errors}"


@pytest.mark.parametrize(
    "bad,chart_type,needle",
    [
        # AUC 越界（0-1 之外）
        ({"title": "bad", "auc": 1.5}, "roc_curve", "auc"),
        # 缺必填字段 title
        ({"auc": 0.9}, "roc_curve", "title"),
        # forest 缺 studies
        ({"title": "x"}, "forest_plot", "studies"),
        # AUC 负数
        ({"title": "x", "auc": -0.1}, "roc_curve", "auc"),
    ],
)
def test_schema_rejects_invalid(bad, chart_type, needle):
    """越界值与缺必填字段都应收敛为校验失败，并在错误信息里点名字段。"""
    ok, errors = validate_payload(bad, chart_type)
    assert not ok, f"本应失败的用例却通过了: {bad}"
    assert any(needle in e for e in errors), (
        f"错误信息未点名字段 '{needle}': {errors}"
    )


def test_all_schemas_exposed():
    """8 类 schema 必须全部注册。"""
    required = {
        "kaplan_meier",
        "forest_plot",
        "roc_curve",
        "box_plot",
        "scatter_plot",
        "bar_chart",
        "heatmap",
        "volcano_plot",
    }
    assert required.issubset(set(SCHEMAS))


def test_unknown_schema_name_is_rejected():
    """传入未知 schema 名应报错而非静默通过。"""
    ok, errors = validate_payload({"title": "x"}, "no_such_chart")
    assert not ok
    assert errors
