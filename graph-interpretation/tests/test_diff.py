"""v1.6.0 diff 模块测试。

核心不变量：
1. 自比无差异（added = removed = changed = 0，score_delta = 0）
2. 缺字段 → 完整是净改善；反向则是净退化（方向敏感性）
3. 三档渲染格式都产出非空结果，且 json 档可被解析
"""

import json

import pytest

from _diff import diff_appraisals, render_diff
from _samples import load_bundled_sample
from appraisal import auto_evaluate
from parsers import PARSERS


def _appraise(alias: str, chart_type: str):
    return auto_evaluate(PARSERS[chart_type].parse(load_bundled_sample(alias)))


@pytest.fixture(scope="module")
def ml_pair():
    """(缺字段 ML, 完整 ML) 两个评价结果。"""
    return (
        _appraise("roc_partial_ml", "roc_curve"),
        _appraise("roc_ml", "roc_curve"),
    )


def test_self_diff_has_no_changes(ml_pair):
    """同一结果自比：无新增 / 无移除 / 无变化 / 得分差为 0。"""
    full, _ = ml_pair
    d = diff_appraisals(full, full, "same", "same")

    assert d["n_added"] == 0
    assert d["n_removed"] == 0
    assert d["n_changed"] == 0
    assert d["score_delta"] == 0


def test_partial_to_full_is_net_improvement(ml_pair):
    """缺字段 → 完整：净改善，新增 TRIPOD-AI 条目，得分上升。"""
    partial, full = ml_pair
    d = diff_appraisals(partial, full, "partial", "full")

    assert d["n_added"] > 0, "完整版应带来新增评价条目"
    assert d["n_improved"] >= d["n_regressed"]
    assert d["score_delta"] > 0


def test_reverse_diff_is_net_regression(ml_pair):
    """完整 → 缺字段：方向反转，应判为退化（diff 非对称）。"""
    partial, full = ml_pair
    d = diff_appraisals(full, partial, "full", "partial")

    assert d["n_removed"] > 0
    assert d["n_regressed"] > 0
    assert d["score_delta"] < 0


def test_changed_items_carry_direction_metadata(ml_pair):
    """变化的条目必须带 symbol 与 meaning，便于报告直接展示。"""
    partial, full = ml_pair
    d = diff_appraisals(partial, full, "partial", "full")

    assert d["n_changed"] > 0
    for rec in d["changed"]:
        assert rec["symbol"], f"{rec['id']} 缺少变化符号"
        assert rec["meaning"], f"{rec['id']} 缺少变化语义"
        assert rec["from_passed"] != rec["to_passed"]


def test_added_ids_sorted_naturally(ml_pair):
    """自然排序：TRIPOD-AI-2 必须排在 TRIPOD-AI-10 之前。"""
    partial, full = ml_pair
    d = diff_appraisals(partial, full, "partial", "full")

    ids = [r["id"] for r in d["added"]]
    ai_ids = [i for i in ids if i.startswith("TRIPOD-AI-")]
    if len(ai_ids) >= 2:
        assert ai_ids[0] == "TRIPOD-AI-2", (
            f"自然排序失效，实际顺序: {ai_ids}"
        )


@pytest.mark.parametrize("fmt", ["table", "markdown", "json"])
def test_render_formats_produce_output(ml_pair, fmt):
    """三档输出格式都应产出非空字符串。"""
    partial, full = ml_pair
    out = render_diff(diff_appraisals(partial, full), fmt=fmt)

    assert isinstance(out, str)
    assert len(out) > 100


def test_json_format_is_parseable(ml_pair):
    """json 档必须可被 json.loads 解析（程序消费场景）。"""
    partial, full = ml_pair
    out = render_diff(diff_appraisals(partial, full), fmt="json")
    payload = json.loads(out)

    assert "n_added" in payload
    assert "changed" in payload
    assert "score_delta" in payload


def test_verbose_adds_unchanged_detail(ml_pair):
    """verbose 模式下 json 档应包含 unchanged 明细，否则仅保留摘要。"""
    partial, full = ml_pair
    d = diff_appraisals(partial, full)

    brief = json.loads(render_diff(d, fmt="json", verbose=False))
    full_out = json.loads(render_diff(d, fmt="json", verbose=True))

    # 精简模式把 unchanged 压成 {id, passed}
    assert all(set(r) <= {"id", "passed"} for r in brief["unchanged"])
    # verbose 模式保留完整字段
    assert any("question" in r for r in full_out["unchanged"])
