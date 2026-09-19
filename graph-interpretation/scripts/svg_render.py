"""图表 → SVG 重绘（8 类医学图表）。

输入：结构化数据字典。
输出：完整 SVG 字符串（无需外部依赖，纯 Python）。

约定：viewBox="0 0 680 480"，与 show_widget 内嵌尺寸兼容。
- KM / Forest / ROC / Box / Scatter / Bar 使用 680×480
- Heatmap 根据矩阵高度自适应
- Volcano 使用 680×480
"""
from __future__ import annotations

from typing import Any


# ---------- 共享工具 ----------

def _xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def _svg_header(width: int = 680, height: int = 480, title: str = "") -> list[str]:
    """公共 SVG 开头：背景 + 标题。"""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="Arial, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2:.0f}" y="22" text-anchor="middle" font-size="16" fill="#222">{_xml(title)}</text>',
    ]


def _cartesian_axes(
    parts: list[str],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    margin_l: int,
    margin_t: int,
    plot_w: int,
    plot_h: int,
    x_label: str = "",
    y_label: str = "",
    x_ticks: int = 6,
    y_ticks: list[float] | None = None,
    y_invert: bool = False,
) -> tuple[Any, Any]:
    """绘制直角坐标系 + 返回 x/y 坐标转换函数。

    y_invert=True 时 y 值向上递增（用于 Fold Change 这种"越大越显著"的场景）。
    """
    if y_ticks is None:
        y_ticks = [y_min + (y_max - y_min) * i / 5 for i in range(6)]

    def x(v: float) -> float:
        return margin_l + (v - x_min) / (x_max - x_min) * plot_w

    def y(v: float) -> float:
        if y_invert:
            return margin_t + (v - y_min) / (y_max - y_min) * plot_h
        return margin_t + (1 - (v - y_min) / (y_max - y_min)) * plot_h

    # 网格 + y 刻度
    for t in y_ticks:
        parts.append(f'<line x1="{margin_l}" y1="{y(t):.1f}" x2="{margin_l+plot_w}" y2="{y(t):.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{margin_l-8}" y="{y(t)+4:.1f}" text-anchor="end" font-size="11" fill="#444">{t:g}</text>')

    # x 刻度
    for i in range(x_ticks + 1):
        xt = x_min + (x_max - x_min) * i / x_ticks
        parts.append(f'<text x="{x(xt):.1f}" y="{margin_t+plot_h+18}" text-anchor="middle" font-size="11" fill="#444">{xt:g}</text>')

    # 轴线
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t+plot_h}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t+plot_h}" x2="{margin_l+plot_w}" y2="{margin_t+plot_h}" stroke="#333"/>')

    # 轴标签
    if x_label:
        parts.append(f'<text x="{margin_l+plot_w/2:.1f}" y="{margin_t+plot_h+44}" text-anchor="middle" font-size="12" fill="#222">{_xml(x_label)}</text>')
    if y_label:
        parts.append(f'<text transform="translate(20,{margin_t+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">{_xml(y_label)}</text>')

    return x, y


# ---------- Kaplan-Meier ----------

def render_km(data: dict[str, Any], title: str = "Kaplan-Meier") -> str:
    """KM 曲线数据 → SVG。

    data 期望结构：
        {
          "arms": [
              {"name": "A", "times": [...], "events": [...], "survival": [...]},
              ...
          ],
          "x_max": float,
          "y_ticks": [0.0, 0.25, 0.5, 0.75, 1.0],
        }
    """
    arms = data.get("arms", [])
    x_max = float(data.get("x_max", max((max(a.get("times", [12]) or [12]) for a in arms), default=12)))
    y_ticks = data.get("y_ticks", [0.0, 0.25, 0.5, 0.75, 1.0])
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]

    margin_l, margin_r, margin_t, margin_b = 80, 40, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    def x(t: float) -> float:
        return margin_l + (t / x_max) * plot_w

    def y(s: float) -> float:
        return margin_t + (1 - s) * plot_h

    parts: list[str] = _svg_header(680, 480, title)

    # y 网格
    for t in y_ticks:
        parts.append(f'<line x1="{margin_l}" y1="{y(t):.1f}" x2="{margin_l+plot_w}" y2="{y(t):.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{margin_l-8}" y="{y(t)+4:.1f}" text-anchor="end" font-size="11" fill="#444">{t:.2f}</text>')

    # x 轴刻度
    n_ticks = 6
    for i in range(n_ticks + 1):
        xt = x_max * i / n_ticks
        parts.append(f'<text x="{x(xt):.1f}" y="{margin_t+plot_h+18}" text-anchor="middle" font-size="11" fill="#444">{xt:g}</text>')

    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t+plot_h}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t+plot_h}" x2="{margin_l+plot_w}" y2="{margin_t+plot_h}" stroke="#333"/>')
    parts.append(f'<text x="{margin_l+plot_w/2:.1f}" y="{margin_t+plot_h+44}" text-anchor="middle" font-size="12" fill="#222">Time</text>')
    parts.append(f'<text transform="translate(20,{margin_t+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">Survival probability</text>')

    for idx, arm in enumerate(arms):
        color = palette[idx % len(palette)]
        times = arm.get("times", [])
        events = arm.get("events", [])
        surv = arm.get("survival", [])
        if not surv:
            continue
        path_d: list[str] = []
        prev_x = x(times[0]) if times else margin_l
        prev_y = y(surv[0])
        path_d.append(f"M {prev_x:.1f} {prev_y:.1f}")
        for i in range(1, len(times)):
            seg_x = x(times[i])
            seg_y = y(surv[i])
            path_d.append(f"H {seg_x:.1f}")
            path_d.append(f"V {seg_y:.1f}")
            if i < len(events) and events[i] == 0:
                parts.append(f'<line x1="{seg_x:.1f}" y1="{seg_y-5:.1f}" x2="{seg_x:.1f}" y2="{seg_y+5:.1f}" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<path d="{" ".join(path_d)}" fill="none" stroke="{color}" stroke-width="2"/>')
        ly = margin_t + 16 + idx * 20
        parts.append(f'<rect x="{margin_l+plot_w-110}" y="{ly-10}" width="14" height="3" fill="{color}"/>')
        parts.append(f'<text x="{margin_l+plot_w-92}" y="{ly-6}" font-size="11" fill="#222">{_xml(arm.get("name", f"Arm {idx+1}"))}</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Forest Plot ----------

def render_forest(data: dict[str, Any], title: str = "Forest plot") -> str:
    """森林图数据 → SVG。

    data 期望结构：
        {
          "studies": [{"name", "effect", "ci", "weight", "n"}],
          "measure": "OR",
          "overall_effect", "overall_ci",
        }
    """
    studies = data.get("studies", [])
    measure = data.get("measure", "OR")
    overall_effect = data.get("overall_effect")
    overall_ci = data.get("overall_ci", [None, None])
    n = len(studies) + (1 if overall_effect is not None else 0)

    margin_l, margin_r, margin_t, margin_b = 60, 220, 40, 40
    row_h = 26
    plot_w = 680 - margin_l - margin_r
    plot_h = max(120, n * row_h + 30)
    height = margin_t + plot_h + margin_b

    all_vals: list[float] = []
    for s in studies:
        if s.get("effect") is not None:
            all_vals.append(s["effect"])
        if s.get("ci"):
            all_vals.extend([v for v in s["ci"] if v is not None])
    if overall_effect is not None:
        all_vals.append(overall_effect)
        if overall_ci:
            all_vals.extend([v for v in overall_ci if v is not None])
    if not all_vals:
        all_vals = [0.5, 1.5]
    vmin = min(all_vals) * 0.8
    vmax = max(all_vals) * 1.2

    def x(v: float) -> float:
        return margin_l + (v - vmin) / (vmax - vmin) * plot_w

    null_value = data.get("null_value", 1.0 if measure in {"OR", "HR", "RR"} else 0.0)

    parts: list[str] = _svg_header(680, height, title)

    nx = x(null_value)
    parts.append(f'<line x1="{nx:.1f}" y1="{margin_t}" x2="{nx:.1f}" y2="{margin_t + n * row_h}" stroke="#888" stroke-dasharray="4,3"/>')
    parts.append(f'<text x="{nx:.1f}" y="{margin_t - 6}" text-anchor="middle" font-size="11" fill="#666">null={null_value}</text>')

    ticks = 5
    for i in range(ticks + 1):
        v = vmin + (vmax - vmin) * i / ticks
        tx = x(v)
        parts.append(f'<line x1="{tx:.1f}" y1="{margin_t + n * row_h}" x2="{tx:.1f}" y2="{margin_t + n * row_h + 4}" stroke="#333"/>')
        parts.append(f'<text x="{tx:.1f}" y="{margin_t + n * row_h + 18}" text-anchor="middle" font-size="10" fill="#444">{v:.2f}</text>')

    parts.append(f'<text x="40" y="{margin_t-6}" font-size="11" fill="#444">Study</text>')
    parts.append(f'<text x="{margin_l+plot_w+10}" y="{margin_t-6}" font-size="11" fill="#444">{measure} [95% CI]</text>')
    parts.append(f'<text x="{margin_l+plot_w+90}" y="{margin_t-6}" font-size="11" fill="#444">Weight</text>')

    for i, s in enumerate(studies):
        y_top = margin_t + i * row_h + row_h / 2
        parts.append(f'<text x="40" y="{y_top+4:.1f}" font-size="11" fill="#222">{_xml(s.get("name", f"Study {i+1}"))}</text>')
        eff = s.get("effect")
        ci = s.get("ci", [None, None])
        weight = s.get("weight", 0.1)
        if eff is not None and ci and ci[0] is not None and ci[1] is not None:
            box_w = max(2, weight * 30)
            parts.append(f'<line x1="{x(ci[0]):.1f}" y1="{y_top:.1f}" x2="{x(ci[1]):.1f}" y2="{y_top:.1f}" stroke="#444" stroke-width="1.5"/>')
            parts.append(f'<rect x="{x(eff)-box_w/2:.1f}" y="{y_top-box_w/2:.1f}" width="{box_w:.1f}" height="{box_w:.1f}" fill="#1f77b4"/>')
            parts.append(f'<text x="{margin_l+plot_w+10}" y="{y_top+4:.1f}" font-size="10" fill="#222">{eff:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]</text>')
        parts.append(f'<text x="{margin_l+plot_w+90}" y="{y_top+4:.1f}" font-size="10" fill="#222">{weight*100:.1f}%</text>')

    if overall_effect is not None and overall_ci and overall_ci[0] is not None:
        y_top = margin_t + len(studies) * row_h + row_h / 2
        parts.append(f'<line x1="{x(overall_ci[0]):.1f}" y1="{y_top:.1f}" x2="{x(overall_ci[1]):.1f}" y2="{y_top:.1f}" stroke="#222" stroke-width="2"/>')
        cx = x(overall_effect)
        half = (x(overall_ci[1]) - x(overall_ci[0])) / 2
        parts.append(
            f'<polygon points="{cx:.1f},{y_top-7:.1f} {cx+half:.1f},{y_top:.1f} {cx:.1f},{y_top+7:.1f} {cx-half:.1f},{y_top:.1f}" '
            f'fill="#d62728" stroke="#222"/>'
        )
        parts.append(f'<text x="40" y="{y_top+4:.1f}" font-size="11" font-weight="bold" fill="#222">Overall</text>')
        parts.append(f'<text x="{margin_l+plot_w+10}" y="{y_top+4:.1f}" font-size="10" fill="#222">{overall_effect:.2f} [{overall_ci[0]:.2f}, {overall_ci[1]:.2f}]</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- ROC Curve ----------

def render_roc(data: dict[str, Any], title: str = "ROC curve") -> str:
    """ROC 曲线数据 → SVG。

    data 期望结构：
        {
          "points": [(fpr, tpr), ...],   # 单条曲线
          "curves": [{"name", "points", "auc", "ci"}],   # 多条曲线
          "auc": float,
          "auc_ci": [lo, hi],
        }
    """
    curves: list[dict[str, Any]] = []
    if "curves" in data and data["curves"]:
        curves = list(data["curves"])
    else:
        curves.append({
            "name": "Model",
            "points": data.get("points", []),
            "auc": data.get("auc"),
            "ci": data.get("auc_ci"),
        })
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]

    margin_l, margin_r, margin_t, margin_b = 70, 130, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    def x(v: float) -> float:
        return margin_l + v * plot_w

    def y(v: float) -> float:
        return margin_t + (1 - v) * plot_h

    parts: list[str] = _svg_header(680, 480, title)

    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        parts.append(f'<line x1="{x(v):.1f}" y1="{margin_t}" x2="{x(v):.1f}" y2="{margin_t+plot_h}" stroke="#eee"/>')
        parts.append(f'<line x1="{margin_l}" y1="{y(v):.1f}" x2="{margin_l+plot_w}" y2="{y(v):.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{x(v):.1f}" y="{margin_t+plot_h+16}" text-anchor="middle" font-size="10" fill="#444">{v:.2f}</text>')
        parts.append(f'<text x="{margin_l-8}" y="{y(v)+3:.1f}" text-anchor="end" font-size="10" fill="#444">{v:.2f}</text>')

    parts.append(f'<line x1="{x(0):.1f}" y1="{y(0):.1f}" x2="{x(1):.1f}" y2="{y(1):.1f}" stroke="#bbb" stroke-dasharray="4,3"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t+plot_h}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t+plot_h}" x2="{margin_l+plot_w}" y2="{margin_t+plot_h}" stroke="#333"/>')
    parts.append(f'<text x="{margin_l+plot_w/2:.1f}" y="{margin_t+plot_h+44}" text-anchor="middle" font-size="12" fill="#222">False Positive Rate (1-Specificity)</text>')
    parts.append(f'<text transform="translate(22,{margin_t+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">True Positive Rate (Sensitivity)</text>')

    for idx, c in enumerate(curves):
        color = palette[idx % len(palette)]
        pts = c.get("points", [])
        if not pts:
            continue
        path_d = " ".join(
            f"{('M' if i==0 else 'L')} {x(p[0]):.1f} {y(p[1]):.1f}"
            for i, p in enumerate(pts)
        )
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2"/>')
        closed = path_d + f" L {x(1):.1f} {y(0):.1f} Z"
        parts.append(f'<path d="{closed}" fill="{color}" fill-opacity="0.05"/>')
        ly = margin_t + 16 + idx * 38
        name = c.get("name", f"Model {idx+1}")
        auc = c.get("auc")
        ci = c.get("ci") or [None, None]
        auc_text = f"AUC={auc:.3f}" if auc is not None else ""
        if ci and ci[0] is not None:
            auc_text += f" [{ci[0]:.3f}-{ci[1]:.3f}]"
        parts.append(f'<rect x="{margin_l+plot_w+12}" y="{ly-12}" width="14" height="3" fill="{color}"/>')
        parts.append(f'<text x="{margin_l+plot_w+30}" y="{ly-6}" font-size="11" fill="#222">{_xml(name)}</text>')
        if auc_text:
            parts.append(f'<text x="{margin_l+plot_w+30}" y="{ly+8}" font-size="10" fill="#555">{auc_text}</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Calibration Plot (v1.6.0) ----------

def render_calibration(
    data: dict[str, Any],
    title: str = "Calibration plot",
    n_bins: int = 10,
) -> str:
    """v1.6.0: Calibration plot（预测概率 vs 实际观测率）。

    ML 预测模型除 discrimination（AUC/ROC）外，calibration 决定
    「预测 30% 风险的患者里，是不是真有约 30% 发生事件」。
    TRIPOD-AI-8 要求报告 slope / intercept / Brier，本图把它可视化。

    数据来源（任一即可）：
        1) ``calibration_points``: [[pred, obs], ...] 实测分位点（优先）
        2) ``calibration_slope`` + ``calibration_intercept``:
           按 Cox 校准回归 logit(obs) = intercept + slope * logit(pred) 合成曲线

    两者都缺失时返回空串，调用方据此跳过该子图。

    参考判读：
        slope = 1.0 / intercept = 0.0 为完美校准
        slope < 1 提示「过度拟合 / 预测过于极端」
        slope > 1 提示「预测过于保守」
    """
    import math

    slope = data.get("calibration_slope")
    intercept = data.get("calibration_intercept")
    brier = data.get("brier_score")

    # ---- 1) 优先用实测分位点 ----
    pts: list[tuple[float, float]] = []
    raw_pts = data.get("calibration_points")
    if raw_pts:
        try:
            pts = [(float(p[0]), float(p[1])) for p in raw_pts]
        except (TypeError, ValueError, IndexError):
            pts = []

    # ---- 2) 否则用 Cox 校准回归合成 ----
    if not pts and slope is not None:
        try:
            s = float(slope)
            b = float(intercept or 0.0)
        except (TypeError, ValueError):
            return ""
        for i in range(1, n_bins):
            p = i / n_bins
            lp = math.log(p / (1.0 - p))     # logit(预测概率)
            lo = b + s * lp                  # logit(观测率)
            obs = 1.0 / (1.0 + math.exp(-lo))
            pts.append((p, max(0.0, min(1.0, obs))))

    if not pts:
        return ""

    margin_l, margin_r, margin_t, margin_b = 70, 150, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    def x(v: float) -> float:
        return margin_l + v * plot_w

    def y(v: float) -> float:
        return margin_t + (1 - v) * plot_h

    parts: list[str] = _svg_header(680, 480, title)

    # 网格与刻度（0-1）
    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        parts.append(
            f'<line x1="{x(v):.1f}" y1="{margin_t}" x2="{x(v):.1f}" '
            f'y2="{margin_t+plot_h}" stroke="#eee"/>'
        )
        parts.append(
            f'<line x1="{margin_l}" y1="{y(v):.1f}" x2="{margin_l+plot_w}" '
            f'y2="{y(v):.1f}" stroke="#eee"/>'
        )
        parts.append(
            f'<text x="{x(v):.1f}" y="{margin_t+plot_h+16}" text-anchor="middle" '
            f'font-size="10" fill="#444">{v:.2f}</text>'
        )
        parts.append(
            f'<text x="{margin_l-8}" y="{y(v)+3:.1f}" text-anchor="end" '
            f'font-size="10" fill="#444">{v:.2f}</text>'
        )

    # 完美校准对角线（y = x）
    parts.append(
        f'<line x1="{x(0):.1f}" y1="{y(0):.1f}" x2="{x(1):.1f}" y2="{y(1):.1f}" '
        f'stroke="#bbb" stroke-dasharray="4,3"/>'
    )

    # 坐标轴
    parts.append(
        f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" '
        f'y2="{margin_t+plot_h}" stroke="#333"/>'
    )
    parts.append(
        f'<line x1="{margin_l}" y1="{margin_t+plot_h}" x2="{margin_l+plot_w}" '
        f'y2="{margin_t+plot_h}" stroke="#333"/>'
    )
    parts.append(
        f'<text x="{margin_l+plot_w/2:.1f}" y="{margin_t+plot_h+44}" '
        f'text-anchor="middle" font-size="12" fill="#222">'
        f'Predicted probability</text>'
    )
    parts.append(
        f'<text transform="translate(22,{margin_t+plot_h/2:.1f}) rotate(-90)" '
        f'text-anchor="middle" font-size="12" fill="#222">'
        f'Observed proportion</text>'
    )

    # 实际 calibration 曲线（点 + 连线）
    path_d = " ".join(
        f"{('M' if i == 0 else 'L')} {x(px):.1f} {y(py):.1f}"
        for i, (px, py) in enumerate(pts)
    )
    parts.append(
        f'<path d="{path_d}" fill="none" stroke="#1f77b4" stroke-width="2"/>'
    )
    for px, py in pts:
        parts.append(
            f'<circle cx="{x(px):.1f}" cy="{y(py):.1f}" r="3.5" fill="#1f77b4"/>'
        )

    # 图例区（右侧）
    lx = margin_l + plot_w + 14
    ly = margin_t + 16
    parts.append(f'<rect x="{lx}" y="{ly-12}" width="14" height="3" fill="#1f77b4"/>')
    parts.append(f'<text x="{lx+20}" y="{ly-6}" font-size="11" fill="#222">Model</text>')
    parts.append(
        f'<line x1="{lx}" y1="{ly+8}" x2="{lx+14}" y2="{ly+8}" '
        f'stroke="#bbb" stroke-dasharray="4,3"/>'
    )
    parts.append(
        f'<text x="{lx+20}" y="{ly+12}" font-size="11" fill="#555">Perfect</text>'
    )

    # 统计量
    stat_y = ly + 40
    if slope is not None:
        try:
            parts.append(
                f'<text x="{lx}" y="{stat_y}" font-size="10" fill="#555">'
                f'slope = {float(slope):.3f}</text>'
            )
            stat_y += 14
        except (TypeError, ValueError):
            pass
    if intercept is not None:
        try:
            parts.append(
                f'<text x="{lx}" y="{stat_y}" font-size="10" fill="#555">'
                f'intercept = {float(intercept):.3f}</text>'
            )
            stat_y += 14
        except (TypeError, ValueError):
            pass
    if brier is not None:
        try:
            parts.append(
                f'<text x="{lx}" y="{stat_y}" font-size="10" fill="#555">'
                f'Brier = {float(brier):.3f}</text>'
            )
            stat_y += 14
        except (TypeError, ValueError):
            pass

    # 判读提示（仅在有 slope 时给出，避免无依据的解读）
    if slope is not None:
        try:
            s_val = float(slope)
            if s_val < 0.9:
                hint = "slope<0.9: possibly overfitted"
            elif s_val > 1.1:
                hint = "slope>1.1: possibly underfitted"
            else:
                hint = "slope~1: well calibrated"
            parts.append(
                f'<text x="{margin_l}" y="{margin_t+plot_h+58}" '
                f'font-size="10" fill="#777">{_xml(hint)}</text>'
            )
        except (TypeError, ValueError):
            pass

    parts.append("</svg>")
    return "".join(parts)


# ---------- Box Plot ----------

def render_box(data: dict[str, Any], title: str = "Box plot") -> str:
    """Box-and-whisker 图数据 → SVG。

    data 期望结构：
        {
          "groups": [
              {"name": "A", "q1": ..., "median": ..., "q3": ..., "whisker_low": ..., "whisker_high": ..., "outliers": [...], "n": ...},
              ...
          ],
        }
    """
    groups = data.get("groups", [])
    if not groups:
        groups = []

    margin_l, margin_r, margin_t, margin_b = 70, 40, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b
    n = len(groups)

    # 自动计算 y 范围
    all_vals: list[float] = []
    for g in groups:
        for k in ("whisker_low", "q1", "median", "q3", "whisker_high"):
            if g.get(k) is not None:
                all_vals.append(g[k])
        all_vals.extend(g.get("outliers", []) or [])
    if not all_vals:
        all_vals = [0, 1]
    y_min = min(all_vals)
    y_max = max(all_vals)
    span = y_max - y_min if y_max > y_min else 1
    y_min -= span * 0.08
    y_max += span * 0.08

    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]

    parts: list[str] = _svg_header(680, 480, title)
    x, y = _cartesian_axes(
        parts,
        x_min=-0.5, x_max=n - 0.5, y_min=y_min, y_max=y_max,
        margin_l=margin_l, margin_t=margin_t, plot_w=plot_w, plot_h=plot_h,
        x_ticks=n, y_ticks=None,
    )

    # x 轴类别标签
    for i, g in enumerate(groups):
        parts.append(f'<text x="{x(i):.1f}" y="{margin_t+plot_h+38}" text-anchor="middle" font-size="12" fill="#222">{_xml(g.get("name", f"G{i+1}"))}</text>')

    box_w = min(40, plot_w / max(n, 4) * 0.6)

    for i, g in enumerate(groups):
        cx = x(i)
        color = palette[i % len(palette)]
        q1 = g.get("q1"); med = g.get("median"); q3 = g.get("q3")
        wl = g.get("whisker_low"); wh = g.get("whisker_high")
        # 须线
        if wl is not None:
            parts.append(f'<line x1="{cx:.1f}" y1="{y(wl):.1f}" x2="{cx:.1f}" y2="{y(q1):.1f}" stroke="{color}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{cx-box_w/3:.1f}" y1="{y(wl):.1f}" x2="{cx+box_w/3:.1f}" y2="{y(wl):.1f}" stroke="{color}" stroke-width="1.5"/>')
        if wh is not None:
            parts.append(f'<line x1="{cx:.1f}" y1="{y(q3):.1f}" x2="{cx:.1f}" y2="{y(wh):.1f}" stroke="{color}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{cx-box_w/3:.1f}" y1="{y(wh):.1f}" x2="{cx+box_w/3:.1f}" y2="{y(wh):.1f}" stroke="{color}" stroke-width="1.5"/>')
        # 箱体
        if q1 is not None and q3 is not None:
            parts.append(f'<rect x="{cx-box_w/2:.1f}" y="{y(q3):.1f}" width="{box_w:.1f}" height="{(y(q1)-y(q3)):.1f}" fill="{color}" fill-opacity="0.3" stroke="{color}" stroke-width="1.5"/>')
        # 中位数
        if med is not None:
            parts.append(f'<line x1="{cx-box_w/2:.1f}" y1="{y(med):.1f}" x2="{cx+box_w/2:.1f}" y2="{y(med):.1f}" stroke="{color}" stroke-width="2.5"/>')
        # 离群点
        for o in g.get("outliers", []) or []:
            parts.append(f'<circle cx="{cx:.1f}" cy="{y(o):.1f}" r="2.5" fill="{color}"/>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Scatter Plot ----------

def render_scatter(data: dict[str, Any], title: str = "Scatter plot") -> str:
    """散点图数据 → SVG（可含回归线与置信带）。

    data 期望结构：
        {
          "points": [{"x": ..., "y": ...}, ...],
          "x_label": ..., "y_label": ...,
          "regression": {"slope": ..., "intercept": ..., "r_squared": ...},
          "loess": False,   # 若 true 用 lowess 平滑（占位实现，复用 linear）
        }
    """
    points = [p for p in data.get("points", []) if p.get("x") is not None and p.get("y") is not None]
    if not points:
        points = []

    margin_l, margin_r, margin_t, margin_b = 70, 40, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    if not xs:
        return _svg_header(680, 480, title, )[0] + ''.join(_svg_header(680, 480, title)[1:]) + '<text x="340" y="240" text-anchor="middle" font-size="14" fill="#888">No points</text></svg>'

    x_min = min(xs); x_max = max(xs)
    y_min = min(ys); y_max = max(ys)
    x_span = x_max - x_min if x_max > x_min else 1
    y_span = y_max - y_min if y_max > y_min else 1
    x_min -= x_span * 0.05
    x_max += x_span * 0.05
    y_min -= y_span * 0.05
    y_max += y_span * 0.05

    parts: list[str] = _svg_header(680, 480, title)
    x, y = _cartesian_axes(
        parts,
        x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
        margin_l=margin_l, margin_t=margin_t, plot_w=plot_w, plot_h=plot_h,
        x_label=data.get("x_label", ""), y_label=data.get("y_label", ""),
    )

    # 散点
    for p in points:
        parts.append(f'<circle cx="{x(p["x"]):.1f}" cy="{y(p["y"]):.1f}" r="3" fill="#1f77b4" fill-opacity="0.6"/>')

    # 回归线
    reg = data.get("regression")
    if reg and reg.get("slope") is not None and reg.get("intercept") is not None:
        slope = reg["slope"]
        intercept = reg["intercept"]
        x1 = x_min + x_span * 0.05
        x2 = x_max - x_span * 0.05
        y1 = slope * x1 + intercept
        y2 = slope * x2 + intercept
        parts.append(f'<line x1="{x(x1):.1f}" y1="{y(y1):.1f}" x2="{x(x2):.1f}" y2="{y(y2):.1f}" stroke="#d62728" stroke-width="2"/>')
        rs = reg.get("r_squared")
        if rs is not None:
            parts.append(f'<text x="{margin_l+10}" y="{margin_t+20}" font-size="11" fill="#222">y = {slope:.3g}x + {intercept:.3g}, R²={rs:.3f}</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Bar Chart ----------

def render_bar(data: dict[str, Any], title: str = "Bar chart") -> str:
    """柱状图数据 → SVG（支持分组与误差棒）。

    data 期望结构（两种用法）：
        (1) 单系列：
        {
          "categories": ["A", "B", ...],
          "values": [...],
          "errors": [...],   # 可选
          "ylabel": ...,
        }
        (2) 多系列：
        {
          "categories": [...],
          "series": [{"name", "values", "errors"}, ...]
        }
    """
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    margin_l, margin_r, margin_t, margin_b = 70, 40, 40, 60
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    series: list[dict[str, Any]] = []
    if "series" in data and data["series"]:
        series = list(data["series"])
        categories = data.get("categories", [])
    else:
        series.append({
            "name": data.get("name", "Value"),
            "values": data.get("values", []),
            "errors": data.get("errors", []),
        })
        categories = data.get("categories", [])

    n_cat = len(categories)
    n_series = len(series)
    if n_cat == 0:
        n_cat = len(series[0].get("values", []))
        categories = [f"C{i+1}" for i in range(n_cat)]

    all_vals: list[float] = []
    for s in series:
        all_vals.extend(v for v in s.get("values", []) if v is not None)
    if not all_vals:
        all_vals = [0, 1]
    y_min = min(all_vals + [0]) - 0.1 * (max(all_vals) - min(all_vals) or 1)
    y_max = max(all_vals) + 0.1 * (max(all_vals) - min(all_vals) or 1)
    if y_min > 0:
        y_min = 0

    parts: list[str] = _svg_header(680, 480, title)
    x, y = _cartesian_axes(
        parts,
        x_min=-0.5, x_max=n_cat - 0.5, y_min=y_min, y_max=y_max,
        margin_l=margin_l, margin_t=margin_t, plot_w=plot_w, plot_h=plot_h,
        x_ticks=n_cat,
    )
    parts.append(f'<text transform="translate(20,{margin_t+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-size="12" fill="#222">{_xml(data.get("ylabel", ""))}</text>')

    group_w = plot_w / n_cat
    bar_w = min(36, group_w * 0.8 / n_series)

    # 类别标签
    for i, cat in enumerate(categories):
        parts.append(f'<text x="{x(i):.1f}" y="{margin_t+plot_h+38}" text-anchor="middle" font-size="11" fill="#222">{_xml(str(cat))}</text>')

    for si, s in enumerate(series):
        vals = s.get("values", [])
        errs = s.get("errors", [])
        for i, v in enumerate(vals):
            if v is None:
                continue
            color = palette[si % len(palette)]
            cx_center = x(i) + (si - (n_series - 1) / 2) * bar_w
            zero_y = y(0)
            top_y = y(v)
            top = min(zero_y, top_y)
            bot = max(zero_y, top_y)
            parts.append(f'<rect x="{cx_center-bar_w/2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{(bot-top):.1f}" fill="{color}" fill-opacity="0.7"/>')
            parts.append(f'<text x="{cx_center:.1f}" y="{(top - 4):.1f}" text-anchor="middle" font-size="9" fill="#222">{v:g}</text>')
            # 误差棒
            if i < len(errs) and errs[i] is not None:
                e = errs[i]
                ey_top = y(v + abs(e))
                ey_bot = y(v - abs(e))
                parts.append(f'<line x1="{cx_center:.1f}" y1="{ey_top:.1f}" x2="{cx_center:.1f}" y2="{ey_bot:.1f}" stroke="#222" stroke-width="1"/>')
                parts.append(f'<line x1="{cx_center-bar_w/3:.1f}" y1="{ey_top:.1f}" x2="{cx_center+bar_w/3:.1f}" y2="{ey_top:.1f}" stroke="#222" stroke-width="1"/>')
                parts.append(f'<line x1="{cx_center-bar_w/3:.1f}" y1="{ey_bot:.1f}" x2="{cx_center+bar_w/3:.1f}" y2="{ey_bot:.1f}" stroke="#222" stroke-width="1"/>')

    # 图例
    if n_series > 1:
        for si, s in enumerate(series):
            color = palette[si % len(palette)]
            ly = margin_t + 16 + si * 18
            parts.append(f'<rect x="{margin_l+plot_w-110}" y="{ly-10}" width="12" height="10" fill="{color}"/>')
            parts.append(f'<text x="{margin_l+plot_w-94}" y="{ly-1}" font-size="11" fill="#222">{_xml(s.get("name", f"S{si+1}"))}</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Heatmap ----------

def render_heatmap(data: dict[str, Any], title: str = "Heatmap") -> str:
    """热图数据 → SVG。

    data 期望结构：
        {
          "matrix": [[v11, v12, ...], ...],
          "row_labels": [...],
          "col_labels": [...],
          "colormap": "RdBu" | "viridis" | "Greys",
          "scale": "z-score" | "minmax" | "raw",
        }
    """
    matrix = data.get("matrix", [])
    row_labels = data.get("row_labels", [])
    col_labels = data.get("col_labels", [])
    if not matrix or not matrix[0]:
        parts = _svg_header(680, 480, title)
        parts.append('<text x="340" y="240" text-anchor="middle" font-size="14" fill="#888">Empty matrix</text>')
        parts.append('</svg>')
        return "".join(parts)

    n_rows = len(matrix)
    n_cols = len(matrix[0])
    all_vals = [v for row in matrix for v in row if v is not None]
    if not all_vals:
        vmin, vmax = 0, 1
    else:
        vmin, vmax = min(all_vals), max(all_vals)

    cmap = _resolve_colormap(data.get("colormap", "RdBu"))
    label_w = max(80, max((len(str(r)) for r in row_labels), default=4) * 7 + 16)
    col_label_h = max(40, max((len(str(c)) for c in col_labels), default=2) * 7)

    margin_t = 40 + col_label_h
    margin_b = 40
    margin_l = label_w + 20
    margin_r = 80   # 色条宽度

    cell_w = max(8, min(40, (680 - margin_l - margin_r) / n_cols))
    plot_w = cell_w * n_cols
    plot_h = max(120, min(360, cell_w * n_rows))   # 让 cell 接近正方形，但限制最大高度
    cell_h = plot_h / n_rows
    height = margin_t + plot_h + margin_b + 30
    width = margin_l + plot_w + margin_r

    parts: list[str] = _svg_header(width, height, title)

    # 单元格
    for ri, row in enumerate(matrix):
        for ci, v in enumerate(row):
            cx = margin_l + ci * cell_w
            cy = margin_t + ri * cell_h
            color = _color_for(cmap, v, vmin, vmax)
            parts.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{color}" stroke="#fff" stroke-width="0.5"/>')
            # 单元格数值
            if cell_w >= 24 and v is not None:
                text_color = "#fff" if _is_dark(color) else "#222"
                parts.append(f'<text x="{cx+cell_w/2:.1f}" y="{cy+cell_h/2+4:.1f}" text-anchor="middle" font-size="9" fill="{text_color}">{v:g}</text>')

    # 行标签
    for ri, r in enumerate(row_labels):
        cy = margin_t + ri * cell_h + cell_h / 2 + 4
        parts.append(f'<text x="{margin_l-8}" y="{cy:.1f}" text-anchor="end" font-size="11" fill="#222">{_xml(str(r))}</text>')

    # 列标签（旋转）
    for ci, c in enumerate(col_labels):
        cx = margin_l + ci * cell_w + cell_w / 2
        parts.append(f'<text transform="translate({cx:.1f},{margin_t-6:.1f}) rotate(-30)" text-anchor="start" font-size="11" fill="#222">{_xml(str(c))}</text>')

    # 色条
    cb_x = margin_l + plot_w + 20
    cb_y = margin_t
    cb_w = 16
    cb_h = plot_h
    for i in range(cb_h):
        ratio = 1 - i / cb_h
        v = vmin + ratio * (vmax - vmin)
        parts.append(f'<rect x="{cb_x:.1f}" y="{cb_y+i:.1f}" width="{cb_w}" height="1" fill="{_color_for(cmap, v, vmin, vmax)}"/>')
    parts.append(f'<text x="{cb_x+cb_w+4}" y="{cb_y+10:.1f}" font-size="10" fill="#222">{vmax:g}</text>')
    parts.append(f'<text x="{cb_x+cb_w+4}" y="{cb_y+cb_h:.1f}" font-size="10" fill="#222">{vmin:g}</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- Volcano Plot ----------

def render_volcano(data: dict[str, Any], title: str = "Volcano plot") -> str:
    """火山图数据 → SVG。

    data 期望结构：
        {
          "points": [{"gene": "...", "log2fc": ..., "neg_log10_p": ...}, ...],
          "fc_threshold": 1.0, "p_threshold": 0.05,
          "fdr_method": "BH",
        }
    """
    points = data.get("points", [])
    fc_t = float(data.get("fc_threshold", 1.0))
    p_t = float(data.get("p_threshold", 0.05))
    neg_log_p_t = -_log10(p_t) if 0 < p_t < 1 else 1.3

    x_min = data.get("x_min"); x_max = data.get("x_max")
    y_min_data = data.get("y_min"); y_max_data = data.get("y_max")
    if x_min is None or x_max is None:
        xs = [p["log2fc"] for p in points]
        x_min = min(xs + [-fc_t - 0.5])
        x_max = max(xs + [fc_t + 0.5])
    if y_min_data is None or y_max_data is None:
        ys = [p["neg_log10_p"] for p in points]
        y_min_data = 0
        y_max_data = max(ys + [neg_log_p_t + 1])

    margin_l, margin_r, margin_t, margin_b = 80, 40, 40, 70
    plot_w = 680 - margin_l - margin_r
    plot_h = 480 - margin_t - margin_b

    parts: list[str] = _svg_header(680, 480, title)
    x, y = _cartesian_axes(
        parts,
        x_min=x_min, x_max=x_max, y_min=y_min_data, y_max=y_max_data,
        margin_l=margin_l, margin_t=margin_t, plot_w=plot_w, plot_h=plot_h,
        x_label="log₂ Fold Change", y_label="-log₁₀(p-value)",
    )

    # 阈值线
    nx_left = x(-fc_t); nx_right = x(fc_t)
    ny = y(neg_log_p_t)
    parts.append(f'<line x1="{nx_left:.1f}" y1="{margin_t}" x2="{nx_left:.1f}" y2="{margin_t+plot_h}" stroke="#888" stroke-dasharray="4,3"/>')
    parts.append(f'<line x1="{nx_right:.1f}" y1="{margin_t}" x2="{nx_right:.1f}" y2="{margin_t+plot_h}" stroke="#888" stroke-dasharray="4,3"/>')
    parts.append(f'<line x1="{margin_l}" y1="{ny:.1f}" x2="{margin_l+plot_w}" y2="{ny:.1f}" stroke="#888" stroke-dasharray="4,3"/>')
    parts.append(f'<text x="{nx_left-4:.1f}" y="{margin_t+12:.1f}" text-anchor="end" font-size="10" fill="#666">FC=-{fc_t}</text>')
    parts.append(f'<text x="{nx_right+4:.1f}" y="{margin_t+12:.1f}" text-anchor="start" font-size="10" fill="#666">FC=+{fc_t}</text>')
    parts.append(f'<text x="{margin_l+plot_w-6}" y="{ny-4:.1f}" text-anchor="end" font-size="10" fill="#666">p={p_t}</text>')

    # 点（按显著性分色）
    n_up = n_down = n_ns = 0
    for p in points:
        l2fc = p["log2fc"]; nlp = p["neg_log10_p"]
        sig = abs(l2fc) > fc_t and nlp > neg_log_p_t
        if sig:
            color = "#d62728" if l2fc > 0 else "#1f77b4"
            size = 4
            if l2fc > 0:
                n_up += 1
            else:
                n_down += 1
        else:
            color = "#bbb"
            size = 2.5
            n_ns += 1
        parts.append(f'<circle cx="{x(l2fc):.1f}" cy="{y(nlp):.1f}" r="{size}" fill="{color}" fill-opacity="0.7"/>')

    # 图例
    lx = margin_l + plot_w - 150
    ly = margin_t + plot_h - 60
    parts.append(f'<circle cx="{lx+5}" cy="{ly+5}" r="4" fill="#d62728"/><text x="{lx+15}" y="{ly+8}" font-size="10" fill="#222">Up</text>')
    parts.append(f'<circle cx="{lx+5}" cy="{ly+22}" r="4" fill="#1f77b4"/><text x="{lx+15}" y="{ly+25}" font-size="10" fill="#222">Down</text>')
    parts.append(f'<circle cx="{lx+5}" cy="{ly+39}" r="2.5" fill="#bbb"/><text x="{lx+15}" y="{ly+42}" font-size="10" fill="#222">NS</text>')

    parts.append('</svg>')
    return "".join(parts)


# ---------- 颜色映射 ----------

_RDBU = [
    (0.0, (67, 147, 195)),
    (0.25, (199, 222, 240)),
    (0.5, (247, 247, 247)),
    (0.75, (244, 165, 130)),
    (1.0, (165, 0, 38)),
]
_VIRIDIS = [
    (0.0, (68, 1, 84)),
    (0.25, (59, 82, 139)),
    (0.5, (33, 145, 140)),
    (0.75, (94, 201, 98)),
    (1.0, (253, 231, 37)),
]
_GREYS = [
    (0.0, (240, 240, 240)),
    (0.5, (160, 160, 160)),
    (1.0, (20, 20, 20)),
]


def _resolve_colormap(name: str) -> list[tuple[float, tuple[int, int, int]]]:
    cmap = (name or "RdBu").lower()
    if "viridis" in cmap:
        return _VIRIDIS
    if "grey" in cmap:
        return _GREYS
    return _RDBU


def _color_for(cmap: list[tuple[float, tuple[int, int, int]]], v: float, vmin: float, vmax: float) -> str:
    if vmax == vmin:
        t = 0.5
    else:
        t = (v - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
    # 线性插值
    for i in range(len(cmap) - 1):
        t0, c0 = cmap[i]
        t1, c1 = cmap[i + 1]
        if t0 <= t <= t1:
            local = (t - t0) / (t1 - t0) if t1 > t0 else 0
            r = int(c0[0] + (c1[0] - c0[0]) * local)
            g = int(c0[1] + (c1[1] - c0[1]) * local)
            b = int(c0[2] + (c1[2] - c0[2]) * local)
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#ffffff"


def _is_dark(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return False
    r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
    return (r * 0.299 + g * 0.587 + b * 0.114) < 128


def _log10(x: float) -> float:
    """简单 log10，避免对数依赖。"""
    if x <= 0:
        return 0.0
    n = 0.0
    while x >= 10:
        x /= 10
        n += 1
    while x < 1:
        x *= 10
        n -= 1
    # 此时 1 <= x < 10
    import math
    return n + math.log10(x)
