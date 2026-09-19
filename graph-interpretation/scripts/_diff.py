"""v1.6.0: 评价结果差异对比。

用途：同一张图在两版之间（如审稿前 / 补充数据后、或两个候选模型）
各自的评价清单对比，快速定位「新增了哪些条目、哪些条目由未通过转为通过、
哪些条目反而退化」。

设计要点
--------
* 条目以 `id` 为主键对齐（TRI-3、TRIPOD-AI-7 等跨框架唯一）
* 通过状态是三态：True=通过 / False=未通过 / None=未评估
  因此「未评估 → 通过」也算变化（信息补全，记为 improved）
* 输出三档：table（终端）/ markdown（贴报告）/ json（程序消费）

无第三方依赖。
"""

from __future__ import annotations

import json
import re
from typing import Any

__all__ = [
    "STATUS_LABEL",
    "diff_appraisals",
    "render_diff_table",
    "render_diff_markdown",
    "render_diff_json",
    "render_diff",
]

# 三态显示标签
STATUS_LABEL: dict[bool | None, str] = {
    True: "PASS",
    False: "FAIL",
    None: "  ? ",
}

# 变化方向 → (符号, 语义)
_DELTA_META = {
    (None, True): ("+", "补全（未评估 → 通过）"),
    (False, True): ("^", "改善（未通过 → 通过）"),
    (True, False): ("v", "退化（通过 → 未通过）"),
    (True, None): ("!", "丢失（通过 → 未评估）"),
    (None, False): ("x", "暴露（未评估 → 未通过）"),
    (False, None): ("-", "搁置（未通过 → 未评估）"),
}


def _natkey(s: str) -> list[Any]:
    """自然排序 key：让 TRIPOD-AI-2 排在 TRIPOD-AI-10 之前。

    纯字符串排序会把 '10' 排到 '2' 前面，读起来很反直觉。
    """
    return [
        int(t) if t.isdigit() else t.lower()
        for t in re.split(r"(\d+)", s or "")
    ]


def _status(passed: bool | None) -> str:
    return STATUS_LABEL.get(passed, "  ? ")


def _item_record(item: Any) -> dict[str, Any]:
    """ChecklistItem → 可序列化 dict。"""
    return {
        "id": item.id,
        "question": item.question,
        "framework": item.framework,
        "passed": item.passed,
        "note": item.note,
    }


def diff_appraisals(
    a: Any,
    b: Any,
    label_a: str = "A",
    label_b: str = "B",
) -> dict[str, Any]:
    """对比两个 AppraisalResult，返回结构化差异。

    Parameters
    ----------
    a, b : AppraisalResult
        A = 基线（旧版），B = 对比（新版）
    label_a, label_b : str
        便于报告展示的来源标签

    Returns
    -------
    dict
        added / removed / changed / unchanged 四组条目
        + score_a / score_b / score_delta 汇总
    """
    a_map = {it.id: it for it in a.items}
    b_map = {it.id: it for it in b.items}

    # 新增（B 有 A 无）与移除（A 有 B 无）
    added = [
        _item_record(b_map[i]) for i in b_map if i not in a_map
    ]
    removed = [
        _item_record(a_map[i]) for i in a_map if i not in b_map
    ]

    # 共有条目：状态是否变化
    changed: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    for i in a_map:
        if i not in b_map:
            continue
        ai, bi = a_map[i], b_map[i]
        symbol, meaning = _DELTA_META.get(
            (ai.passed, bi.passed), ("=", "无变化")
        )
        rec = {
            "id": i,
            "question": bi.question or ai.question,
            "framework": bi.framework or ai.framework,
            "from_passed": ai.passed,
            "to_passed": bi.passed,
            "from_note": ai.note,
            "to_note": bi.note,
            "symbol": symbol,
            "meaning": meaning,
        }
        (changed if ai.passed != bi.passed else unchanged).append(rec)

    # 保持稳定输出顺序：按 id 自然排序（TRIPOD-AI-2 先于 TRIPOD-AI-10）
    added.sort(key=lambda r: _natkey(r["id"]))
    removed.sort(key=lambda r: _natkey(r["id"]))
    changed.sort(key=lambda r: _natkey(r["id"]))
    unchanged.sort(key=lambda r: _natkey(r["id"]))

    def _score(r: Any) -> float | None:
        s = r.overall_score
        return None if s is None else round(s, 4)

    sa, sb = _score(a), _score(b)
    delta = None if (sa is None or sb is None) else round(sb - sa, 4)

    # 变化分类计数（仅 changed 内）
    n_improved = sum(
        1 for r in changed if r["symbol"] in ("+", "^")
    )
    n_regressed = sum(
        1 for r in changed if r["symbol"] in ("v", "!", "x")
    )

    return {
        "label_a": label_a,
        "label_b": label_b,
        "chart_type": b.chart_type or a.chart_type,
        "framework_a": a.framework,
        "framework_b": b.framework,
        "score_a": sa,
        "score_b": sb,
        "score_delta": delta,
        "n_a": a.n_items,
        "n_b": b.n_items,
        "n_passed_a": a.n_passed,
        "n_passed_b": b.n_passed,
        "n_added": len(added),
        "n_removed": len(removed),
        "n_changed": len(changed),
        "n_unchanged": len(unchanged),
        "n_improved": n_improved,
        "n_regressed": n_regressed,
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def _pct(v: float | None) -> str:
    if v is None:
        return "n/a"
    return f"{v * 100:.0f}%"


def render_diff_table(diff: dict[str, Any], verbose: bool = False) -> str:
    """终端友好表格。verbose=True 时连 unchanged 条目也列出。"""
    la, lb = diff["label_a"], diff["label_b"]
    lines: list[str] = []

    lines.append("=" * 68)
    lines.append(f"评价差异对比   {la}  ->  {lb}")
    lines.append("=" * 68)
    lines.append(
        f"图表类型   : {diff['chart_type']}"
    )
    if diff["framework_a"] != diff["framework_b"]:
        lines.append(
            f"评价框架   : {diff['framework_a']}  ->  {diff['framework_b']}"
        )
    else:
        lines.append(f"评价框架   : {diff['framework_b']}")
    lines.append(
        f"条目数     : {diff['n_a']}  ->  {diff['n_b']}"
        f"   (+{diff['n_added']} / -{diff['n_removed']})"
    )
    lines.append(
        f"通过数     : {diff['n_passed_a']}  ->  {diff['n_passed_b']}"
    )
    d = diff["score_delta"]
    if d is None:
        delta_s = f"{_pct(diff['score_a'])}  ->  {_pct(diff['score_b'])}"
    else:
        arrow = "+" if d > 0 else ("" if d == 0 else "")
        delta_s = (
            f"{_pct(diff['score_a'])}  ->  {_pct(diff['score_b'])}"
            f"   ({arrow}{d * 100:.0f}%)"
        )
    lines.append(f"总体得分   : {delta_s}")
    lines.append(
        f"状态变化   : {diff['n_changed']} 条"
        f"   (改善 {diff['n_improved']} / 退化 {diff['n_regressed']})"
    )
    lines.append("")

    # 变化明细
    if diff["changed"]:
        lines.append(f"[状态变化] {diff['n_changed']} 条")
        lines.append(
            f"  {'ID':<16} {'变化':<4} {'从':<6} {'到':<6} 说明"
        )
        lines.append("  " + "-" * 64)
        for r in diff["changed"]:
            lines.append(
                f"  {r['id']:<16} {r['symbol']:<4} "
                f"{_status(r['from_passed']):<6} {_status(r['to_passed']):<6} "
                f"{r['meaning']}"
            )
        lines.append("")
    else:
        lines.append("[状态变化] 无")
        lines.append("")

    # 新增
    if diff["added"]:
        lines.append(f"[新增条目] {diff['n_added']} 条")
        for r in diff["added"]:
            lines.append(
                f"  + {r['id']:<16} {_status(r['passed']):<6} {r['question'][:38]}"
            )
        lines.append("")

    # 移除
    if diff["removed"]:
        lines.append(f"[移除条目] {diff['n_removed']} 条")
        for r in diff["removed"]:
            lines.append(
                f"  - {r['id']:<16} {_status(r['passed']):<6} {r['question'][:38]}"
            )
        lines.append("")

    # 未变化（仅 verbose）
    if verbose and diff["unchanged"]:
        lines.append(f"[未变化] {diff['n_unchanged']} 条")
        for r in diff["unchanged"]:
            lines.append(
                f"    {r['id']:<16} {_status(r['to_passed']):<6} "
                f"{r['question'][:38]}"
            )
        lines.append("")

    # 结论
    lines.append("-" * 68)
    if diff["n_regressed"] > diff["n_improved"]:
        verdict = "净退化：新版有条目由通过转为未通过，建议核查数据补录是否丢字段"
    elif diff["n_improved"] > diff["n_regressed"]:
        verdict = "净改善：新版补全了此前未评估 / 未通过的条目"
    elif diff["n_changed"] == 0 and diff["n_added"] == 0 and diff["n_removed"] == 0:
        verdict = "完全一致：两版评价结果无差异"
    else:
        verdict = "改善与退化持平，需人工判断"
    lines.append(f"结论: {verdict}")
    lines.append("=" * 68)

    return "\n".join(lines)


def render_diff_markdown(diff: dict[str, Any], verbose: bool = False) -> str:
    """Markdown 报告（可直接贴进审稿意见 / 补充材料）。"""
    la, lb = diff["label_a"], diff["label_b"]
    L: list[str] = []

    L.append(f"## 评价差异对比：{la} → {lb}")
    L.append("")
    L.append("| 指标 | %s | %s | 变化 |" % (la, lb))
    L.append("|---|---|---|---|")
    L.append(
        f"| 条目数 | {diff['n_a']} | {diff['n_b']} | "
        f"+{diff['n_added']} / -{diff['n_removed']} |"
    )
    L.append(
        f"| 通过数 | {diff['n_passed_a']} | {diff['n_passed_b']} | "
        f"{diff['n_passed_b'] - diff['n_passed_a']:+d} |"
    )
    L.append(
        f"| 总体得分 | {_pct(diff['score_a'])} | {_pct(diff['score_b'])} | "
        f"{_pct(diff['score_delta']) if diff['score_delta'] is not None else 'n/a'} |"
    )
    L.append(
        f"| 状态变化 | — | — | 改善 {diff['n_improved']} / "
        f"退化 {diff['n_regressed']} |"
    )
    L.append("")

    if diff["changed"]:
        L.append(f"### 状态变化（{diff['n_changed']} 条）")
        L.append("")
        L.append("| ID | 检查项 | 变化 | 从 | 到 | 说明 |")
        L.append("|---|---|---|---|---|---|")
        for r in diff["changed"]:
            q = (r["question"] or "").replace("|", "\\|")
            L.append(
                f"| `{r['id']}` | {q[:44]} | {r['symbol']} | "
                f"{_status(r['from_passed'])} | {_status(r['to_passed'])} | "
                f"{r['meaning']} |"
            )
        L.append("")

    if diff["added"]:
        L.append(f"### 新增条目（{diff['n_added']} 条）")
        L.append("")
        for r in diff["added"]:
            q = (r["question"] or "").replace("|", "\\|")
            L.append(f"- `{r['id']}` [{_status(r['passed'])}] {q}")
        L.append("")

    if diff["removed"]:
        L.append(f"### 移除条目（{diff['n_removed']} 条）")
        L.append("")
        for r in diff["removed"]:
            q = (r["question"] or "").replace("|", "\\|")
            L.append(f"- `{r['id']}` [{_status(r['passed'])}] {q}")
        L.append("")

    if verbose and diff["unchanged"]:
        L.append(f"### 未变化（{diff['n_unchanged']} 条）")
        L.append("")
        for r in diff["unchanged"]:
            q = (r["question"] or "").replace("|", "\\|")
            L.append(f"- `{r['id']}` [{_status(r['to_passed'])}] {q}")
        L.append("")

    return "\n".join(L)


def render_diff_json(diff: dict[str, Any], verbose: bool = False) -> str:
    """JSON 输出（程序消费）。verbose=False 时省略 unchanged 明细。"""
    payload = {k: v for k, v in diff.items()}
    if not verbose:
        payload["unchanged"] = [
            {"id": r["id"], "passed": r["to_passed"]}
            for r in diff["unchanged"]
        ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_diff(
    diff: dict[str, Any],
    fmt: str = "table",
    verbose: bool = False,
) -> str:
    """按格式分发渲染。"""
    if fmt == "json":
        return render_diff_json(diff, verbose=verbose)
    if fmt == "markdown":
        return render_diff_markdown(diff, verbose=verbose)
    return render_diff_table(diff, verbose=verbose)


# ---------- 自检 ----------
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    from parsers import PARSERS  # type: ignore
    from appraisal import auto_evaluate  # type: ignore

    def _run(rel: str, ctype: str) -> Any:
        data = json.loads(
            (Path(__file__).parent / rel).read_text(encoding="utf-8")
        )
        summary = PARSERS[ctype].parse(data)
        return auto_evaluate(summary)

    print("=== _diff.py 自检 ===")
    print()

    # 场景 1：完整 ML vs 缺字段 ML（应大量「补全」= 退化方向）
    full = _run("sample_roc_ml.json", "roc_curve")
    partial = _run("sample_roc_partial_ml.json", "roc_curve")

    d1 = diff_appraisals(partial, full, "partial_ml", "full_ml")
    print(render_diff_table(d1))
    print()

    # 场景 2：自己跟自己比（应完全一致）
    d2 = diff_appraisals(full, full, "full_ml", "full_ml")
    print(
        f"[场景2] 自比: n_changed={d2['n_changed']} "
        f"n_added={d2['n_added']} n_removed={d2['n_removed']}"
    )
    print()

    # 场景 3：三档格式输出长度
    for fmt in ("table", "markdown", "json"):
        out = render_diff(d1, fmt=fmt)
        print(f"[场景3] {fmt:<9} 输出 {len(out)} 字符")

    print()
    print("=== 自检通过 ===")
