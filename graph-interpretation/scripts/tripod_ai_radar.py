"""TRIPOD-AI 14 维雷达图生成器（v1.3.0）。

纯 Python，无依赖；输出 SVG 字符串，便于嵌入 docx / PPT / HTML。
- 通过（True）→ 绿色
- 不通过（False）→ 红色
- 未评估（None）→ 灰色

用法：

    from appraisal import auto_evaluate
    from parsers import PARSERS
    from tripod_ai_radar import render_tripod_ai_radar

    summary = PARSERS["roc_curve"].parse(ml_data)
    result = auto_evaluate(summary)
    svg = render_tripod_ai_radar(result)
    Path("radar.svg").write_text(svg, encoding="utf-8")
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from models import AppraisalResult, ChecklistItem


# 雷达图配色（暗色主题友好）
_FILL_PASS = "rgba(80, 200, 120, 0.35)"     # 通过：半透明绿
_STROKE_PASS = "#50C878"
_FILL_FAIL = "rgba(255, 99, 99, 0.35)"     # 不通过：半透明红
_STROKE_FAIL = "#FF6363"
_FILL_UNCHECKED = "rgba(180, 180, 180, 0.25)"
_STROKE_UNCHECKED = "#B4B4B4"
_TEXT = "#E8E8E8"
_GRID = "rgba(255, 255, 255, 0.15)"
_AXIS = "rgba(255, 255, 255, 0.35)"
_BG = "#1E1E1E"


def _polygon(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def render_tripod_ai_radar(
    result: AppraisalResult,
    width: int = 560,
    height: int = 560,
    *,
    title: str | None = None,
) -> str:
    """渲染 TRIPOD-AI 评价结果为雷达图 SVG。"""
    items = [it for it in result.items if it.id.startswith("TRIPOD-AI")]
    if not items:
        # 雷达图只画 TRIPOD-AI 子集；其他条目不适合极坐标
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 680 680">'
            f'<rect width="680" height="680" fill="{_BG}"/>'
            f'<text x="340" y="340" text-anchor="middle" fill="{_TEXT}" '
            f'font-size="18">未检测到 TRIPOD-AI 条目（输入非 ML 预测模型？）</text>'
            f"</svg>"
        )

    n = len(items)
    cx, cy = 340, 340
    radius_outer = 250
    radius_label = radius_outer + 28

    title_text = title or "TRIPOD-AI 14 维评价雷达"

    # 1. 网格圈层（5 圈）
    grid = []
    for r_pct in (0.25, 0.5, 0.75, 1.0):
        r = radius_outer * r_pct
        pts = []
        for i in range(n):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        grid.append(
            f'<polygon points="{_polygon(pts)}" fill="none" stroke="{_GRID}" '
            f'stroke-width="1" stroke-dasharray="3 3"/>'
        )

    # 2. 轴线 + 标签
    axes = []
    labels = []
    for i, item in enumerate(items):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        x_outer = cx + radius_outer * math.cos(angle)
        y_outer = cy + radius_outer * math.sin(angle)
        x_label = cx + radius_label * math.cos(angle)
        y_label = cy + radius_label * math.sin(angle)
        axes.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x_outer:.2f}" y2="{y_outer:.2f}" '
            f'stroke="{_AXIS}" stroke-width="1"/>'
        )
        # 文本锚点：右半圈左对齐，左半圈右对齐，顶/底居中
        if abs(math.cos(angle)) < 0.1:
            anchor = "middle"
            dy = "-0.2em" if math.sin(angle) < 0 else "1em"
        elif math.cos(angle) > 0:
            anchor = "start"
            dy = "0.3em"
        else:
            anchor = "end"
            dy = "0.3em"
        labels.append(
            f'<text x="{x_label:.2f}" y="{y_label:.2f}" fill="{_TEXT}" '
            f'font-size="12" text-anchor="{anchor}" dy="{dy}" '
            f'font-family="Microsoft YaHei, Arial, sans-serif">'
            f'{item.id.replace("TRIPOD-AI-", "")} · '
            f'{"✓" if item.passed else "✗" if item.passed is False else "·"}'
            f"</text>"
        )

    # 3. 多边形填充：分三组（通过 / 不通过 / 未评估）映射到 0.33/0/0.66 半径
    def _pts_for(values: list[float]) -> list[tuple[float, float]]:
        pts = []
        for i, v in enumerate(values):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            r = radius_outer * v
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return pts

    # 通过 / 不通过 / 未评 → 半径（视觉直观：半透明绿在外环、红在内环、灰在中环）
    pass_radii = [1.0 if it.passed else 0.0 for it in items]
    fail_radii = [0.6 if it.passed is False else 0.0 for it in items]
    unchecked_radii = [0.45 if it.passed is None else 0.0 for it in items]

    polygons = []
    if any(p > 0 for p in pass_radii):
        polygons.append(
            f'<polygon points="{_polygon(_pts_for(pass_radii))}" '
            f'fill="{_FILL_PASS}" stroke="{_STROKE_PASS}" stroke-width="2"/>'
        )
    if any(f > 0 for f in unchecked_radii):
        polygons.append(
            f'<polygon points="{_polygon(_pts_for(unchecked_radii))}" '
            f'fill="{_FILL_UNCHECKED}" stroke="{_STROKE_UNCHECKED}" '
            f'stroke-width="1.5" stroke-dasharray="5 3"/>'
        )
    if any(f > 0 for f in fail_radii):
        polygons.append(
            f'<polygon points="{_polygon(_pts_for(fail_radii))}" '
            f'fill="{_FILL_FAIL}" stroke="{_STROKE_FAIL}" stroke-width="2"/>'
        )

    # 4. 数据点（每个 item 一个点）
    markers = []
    for i, item in enumerate(items):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        if item.passed is True:
            r = radius_outer * 1.0
            color = _STROKE_PASS
        elif item.passed is False:
            r = radius_outer * 0.6
            color = _STROKE_FAIL
        else:
            r = radius_outer * 0.45
            color = _STROKE_UNCHECKED
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        markers.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" '
            f'stroke="{_BG}" stroke-width="1.5"/>'
        )

    # 5. 标题 + 图例
    passed = sum(1 for it in items if it.passed is True)
    failed = sum(1 for it in items if it.passed is False)
    unchecked = sum(1 for it in items if it.passed is None)

    header = (
        f'<text x="340" y="30" text-anchor="middle" fill="{_TEXT}" '
        f'font-size="18" font-weight="bold" '
        f'font-family="Microsoft YaHei, Arial, sans-serif">{title_text}</text>'
        f'<text x="340" y="52" text-anchor="middle" fill="#999" font-size="12">'
        f'通过 {passed} / 不通过 {failed} / 未评估 {unchecked}（共 {len(items)} 条）'
        f"</text>"
    )
    legend = (
        f'<g transform="translate(20, 615)">'
        f'<rect x="0" y="-12" width="14" height="14" fill="{_FILL_PASS}" stroke="{_STROKE_PASS}"/>'
        f'<text x="20" y="0" fill="{_TEXT}" font-size="12">通过</text>'
        f'<rect x="80" y="-12" width="14" height="14" fill="{_FILL_FAIL}" stroke="{_STROKE_FAIL}"/>'
        f'<text x="100" y="0" fill="{_TEXT}" font-size="12">不通过</text>'
        f'<rect x="180" y="-12" width="14" height="14" fill="{_FILL_UNCHECKED}" stroke="{_STROKE_UNCHECKED}"/>'
        f'<text x="200" y="0" fill="{_TEXT}" font-size="12">未评估</text>'
        f"</g>"
    )

    # viewBox 必须是 "0 0 680 " 开头（show_widget 约束）
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 680 680">'
        f'<rect width="680" height="680" fill="{_BG}"/>'
        + header
        + "".join(grid)
        + "".join(axes)
        + "".join(polygons)
        + "".join(markers)
        + "".join(labels)
        + legend
        + "</svg>"
    )
    return svg


def tripod_ai_score_summary(result: AppraisalResult) -> dict[str, int]:
    """输出 TRIPOD-AI 评分汇总（用于其他模块）。"""
    items = [it for it in result.items if it.id.startswith("TRIPOD-AI")]
    return {
        "n_items": len(items),
        "passed": sum(1 for it in items if it.passed is True),
        "failed": sum(1 for it in items if it.passed is False),
        "unchecked": sum(1 for it in items if it.passed is None),
    }


# ---------- CSV 导出 (v1.4.0) ----------

import csv
from io import StringIO


def export_tripod_ai_csv(
    result: AppraisalResult,
    csv_path: str | Path | None = None,
    summary = None,           # 可选：graph-interpretation 的 StatisticalSummary
    include_bom: bool = True,
) -> str:
    """把 TRIPOD-AI 14 条评价导出为 CSV（utf-8-sig，Excel 中文友好）。

    Columns:
      - id          e.g. TRIPOD-AI-1
      - question    原始问题
      - status      通过 / 不通过 / 未评估
      - note        取自 ChecklistItem.note
      - raw_value   直接取自 summary.raw[raw_field]，便于审计追溯
    """
    items = [it for it in result.items if it.id.startswith("TRIPOD-AI")]
    raw_dict = (summary.raw if summary is not None else {}) or {}

    # raw_field 映射从 _TRIPOD_AI_ITEMS 取
    field_map = {}
    try:
        from tripod_ai_checklist import _TRIPOD_AI_ITEMS  # type: ignore
        for def_id, _, _, raw_field, _ in _TRIPOD_AI_ITEMS:
            field_map[def_id] = raw_field
    except Exception:
        pass

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "question", "status", "note", "raw_value"])

    for it in items:
        if it.passed is True:
            status = "通过"
        elif it.passed is False:
            status = "不通过"
        else:
            status = "未评估"

        note = it.note or ""
        field = field_map.get(it.id)
        raw_value = ""
        if field:
            v = raw_dict.get(field)
            if v is not None:
                raw_value = str(v)
            elif note and "=" in note:
                # fall back to note suffix
                raw_value = note.split("=", 1)[1].strip()
        writer.writerow([it.id, it.question, status, note, raw_value])

    content = buf.getvalue()
    if csv_path:
        Path(csv_path).write_text(
            ("\ufeff" + content) if include_bom else content,
            encoding="utf-8",
        )
    return content
