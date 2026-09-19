"""端到端：graph-interpretation → figure-legend-gen → .docx（v1.2.0，新增 SVG 嵌入）。

从一张 KM / Forest / ROC 等图表的结构化 JSON 出发：
1. graph-interpretation 解析为 StatisticalSummary
2. legend_bridge 转成 figure-legend-gen 模板可消费的字段
3. 调用 figure-legend-gen 的 LegendGenerator 填充模板
4. 用 python-docx 渲染为 .docx 工件
5. （可选）自动调用 svg_render 把数据重绘为 SVG，嵌入 .docx 中

用法：
    python to_legend_docx.py --type km --data sample_km.json --out figure_legend.docx
    python to_legend_docx.py --type km --data sample_km.json --with-svg --svg-width 6.0 --out figure_with_svg.docx
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tempfile
from pathlib import Path

# 把同目录与 figure-legend-gen scripts 都加进路径
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path("C:/Users/Chow1/.workbuddy/skills/figure-legend-gen/scripts")))

from parsers import PARSERS
from legend_bridge import to_legend_fields, to_legend_type

from main import ChartType, LegendGenerator  # figure-legend-gen scripts/main.py

# 可选：SVG 渲染依赖本目录的 svg_render
try:
    import svg_render as _svg_render  # type: ignore
    _SVG_AVAILABLE = True
except Exception:
    _svg_render = None
    _SVG_AVAILABLE = False


_TYPE_ALIAS = {
    "km": "kaplan_meier",
    "kaplan_meier": "kaplan_meier",
    "forest": "forest_plot",
    "forest_plot": "forest_plot",
    "roc": "roc_curve",
    "roc_curve": "roc_curve",
    "box": "box_plot",
    "box_plot": "box_plot",
    "scatter": "scatter_plot",
    "scatter_plot": "scatter_plot",
    "bar": "bar_chart",
    "bar_chart": "bar_chart",
    "heatmap": "heatmap",
    "volcano": "volcano_plot",
    "volcano_plot": "volcano_plot",
}


# ---------- Markdown → docx 渲染 ----------

def _parse_md_to_blocks(text: str) -> list[tuple[str, str]]:
    """极简 markdown → (kind, text) 序列。"""
    blocks: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            blocks.append(("blank", ""))
            continue
        if line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            blocks.append(("bold", line.strip("*")))
        else:
            blocks.append(("p", line))
    return blocks


def _svg_to_png_bytes(svg_text: str) -> bytes | None:
    """尝试用 cairosvg 把 SVG 转 PNG；若不可用则返回 None，回退到 docx 直接嵌入 SVG。

    python-docx 本身不支持 SVG（只支持 PNG/JPEG 等位图），所以必须转 PNG。
    """
    try:
        import cairosvg  # type: ignore
        png = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"),
                                output_width=1600)  # ~高 DPI
        return png
    except Exception:
        return None


def _svg_render_for_type(chart_type: str, data: dict) -> str | None:
    """根据 chart_type 调用 svg_render 对应函数。"""
    if not _SVG_AVAILABLE or _svg_render is None:
        return None
    try:
        if chart_type == "kaplan_meier":
            return _svg_render.render_km(data, title=data.get("title", ""))
        if chart_type == "forest_plot":
            return _svg_render.render_forest(data, title=data.get("title", ""))
        if chart_type == "roc_curve":
            return _svg_render.render_roc(data, title=data.get("title", ""))
        if chart_type == "box_plot":
            return _svg_render.render_box(data, title=data.get("title", ""))
        if chart_type == "scatter_plot":
            return _svg_render.render_scatter(data, title=data.get("title", ""))
        if chart_type == "bar_chart":
            return _svg_render.render_bar(data, title=data.get("title", ""))
        if chart_type == "heatmap":
            return _svg_render.render_heatmap(data, title=data.get("title", ""))
        if chart_type == "volcano_plot":
            return _svg_render.render_volcano(data, title=data.get("title", ""))
    except Exception as e:
        print(f"[svg] 渲染 {chart_type} 失败：{e}")
    return None


def _embed_svg(doc, svg_text: str, width_inches: float = 6.0) -> None:
    """把 SVG 文本嵌入 docx：优先转 PNG，自动加图说。

    若 cairosvg 不可用，则把 SVG 文本作为代码块附在 figure 后面（降级）。
    """
    from docx.shared import Inches

    png_bytes = _svg_to_png_bytes(svg_text)
    if png_bytes is not None:
        try:
            doc.add_picture(io.BytesIO(png_bytes), width=Inches(width_inches))
            # 居中
            last_para = doc.paragraphs[-1]
            last_para.alignment = 1   # WD_ALIGN_PARAGRAPH.CENTER
            return
        except Exception as e:
            print(f"[svg] PNG 嵌入失败：{e}")

    # 降级：把 SVG 作为代码段附在 figure 后面
    p = doc.add_paragraph()
    p.alignment = 1
    p.add_run("[SVG 嵌入失败；以下是原始 SVG 文本]").italic = True
    code_p = doc.add_paragraph()
    code_p.add_run(svg_text[:800] + ("…" if len(svg_text) > 800 else "")).font.size = None


def write_docx(
    legend_text: str,
    output_path: Path,
    title: str,
    svg_text: str | None = None,
    svg_width: float = 6.0,
) -> None:
    """把图注 markdown + 可选 SVG 渲染成 .docx。"""
    from docx import Document

    doc = Document()

    # 顶部：文档标题与生成来源
    h = doc.add_heading(title, level=0)
    p_meta = doc.add_paragraph()
    p_meta.add_run("Generated by: graph-interpretation → figure-legend-gen bridge").italic = True

    # --- 嵌入 SVG（如果有）---
    if svg_text:
        _embed_svg(doc, svg_text, width_inches=svg_width)
        # 紧跟一个图说明标题
        cap = doc.add_paragraph()
        cap.alignment = 1   # center
        cap.add_run("图 | Figure  ").italic = True
        cap.add_run("(auto-rendered from raw data)").italic = True

    blocks = _parse_md_to_blocks(legend_text)
    cur_p = None

    for kind, text in blocks:
        if kind == "blank":
            if cur_p is not None:
                cur_p = None
            continue
        if kind == "h2":
            doc.add_heading(text, level=1)
            cur_p = None
        elif kind == "h3":
            doc.add_heading(text, level=2)
            cur_p = None
        elif kind == "bold":
            if cur_p is None:
                cur_p = doc.add_paragraph()
            cur_p.add_run(text).bold = True
            cur_p.add_run(" ")
        else:  # "p"
            p = doc.add_paragraph()
            parts = re.split(r"(\*\*[^*]+\*\*)", text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    p.add_run(part.strip("*")).bold = True
                else:
                    p.add_run(part)
            cur_p = p

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"[docx] 已写入 {output_path}{' (含 SVG)' if svg_text else ''}")


def render_chart_legend(data: dict, chart_type: str,
                        figure_number: str = "1",
                        figure_id: str | None = None,
                        language: str = "en",
                        style: str = "generic") -> str:
    """端到端核心：从原始图表数据 → markdown 图注。

    v1.2.0：当 style 为中文期刊（cma/cslco/cebm/zhcore），优先走 graph-interpretation
    内置的 caption 模板，而不是 figure-legend-gen 默认模板。
    """
    gi_type = _TYPE_ALIAS.get(chart_type)
    if gi_type not in PARSERS:
        raise ValueError(f"不支持的 chart type: {chart_type}")
    summary = PARSERS[gi_type].parse(data)

    fields = to_legend_fields(summary)
    chart_enum = ChartType(fields["_legend_chart_type"])

    # ---------- 1) 优先用 graph-interpretation 内置 caption（支持中文期刊风格） ----------
    from captions import generate_caption
    caption_text = generate_caption(
        summary,
        style=style,
        language=language,
        figure_id=f"图{figure_number}" if language == "zh" else f"Figure {figure_number}",
    )

    # ---------- 2) 走 figure-legend-gen 默认模板作为补充 ----------
    gen = LegendGenerator(chart_enum, language=language)
    kwargs = {
        "figure_number": figure_number,
        "metric": fields["metric"] or "experimental values",
        "groups": fields["groups"] or "experimental groups",
        "sample_description": fields["sample_description"] or "the tested samples",
        "n": fields["n"] if isinstance(fields["n"], int) else 3,
        "test": fields["test"] or "appropriate statistical test",
        "x_var": fields.get("x_var") or "X",
        "y_var": fields.get("y_var") or "Y",
        "r_value": fields.get("r_value") or "computed",
        "p_value": fields.get("p_value") or "reported",
        "sample_unit": fields.get("sample_unit") or "sample",
        "condition": fields.get("condition") or "the experiment",
        "time_range": fields.get("time_range") or "follow-up",
        "value_range": fields.get("value_range") or "normalized values",
        "normalization_method": fields.get("normalization_method") or "z-score",
        "clustering_method": fields.get("clustering_method") or "hierarchical",
        "dimensions": fields.get("dimensions") or f"{len(fields.get('row_labels', []))} features × {len(fields.get('col_labels', []))} samples",
    }
    figure_legend_md = gen.generate(**kwargs)

    # 拼接：caption（学术风格）+ figure-legend-gen 默认段
    legend_md = f"\n\n{('### ' + ('中文学术图注' if language == 'zh' else 'Caption'))}: \n{caption_text}\n"
    if language != "zh" or style not in {"cma", "cslco", "cebm", "zhcore"}:
        # 英文或非中文风格时用 figure-legend-gen 默认段为主
        legend_md = f"\n\n### {'学术图注 / Caption'} ({style})\n{caption_text}\n"
    legend_md += f"\n\n### {'模板段落 / Template' if language == 'zh' else 'Default template'}\n{figure_legend_md}\n"

    # 追加：原始效应量 + graph-interpretation notes
    if fields.get("primary_stat"):
        legend_md += f"\n**Primary effect**: {fields['primary_stat']}\n"
    if fields.get("_notes"):
        legend_md += f"\n**Notes from graph-interpretation**: {fields['_notes']}\n"

    # 中文受众补充（从 audiences 模块）
    if language == "zh":
        try:
            from audiences import render_all
            audiences_md_parts = []
            for aud_name, aud_text in render_all(summary, locale="zh_CN").items():
                audiences_md_parts.append(f"\n### 受众 / {aud_name}\n{aud_text}\n")
            legend_md += "\n".join(audiences_md_parts) + "\n"
        except Exception:
            pass

    # 评价清单补充
    try:
        from appraisal import auto_evaluate
        result = auto_evaluate(summary)
        legend_md += f"\n### {'批判性评价清单'} ({result.framework})\n"
        legend_md += f"总条目: {result.n_items}（通过 {result.n_passed}，未通过 {result.n_failed}，未评估 {result.n_unchecked}）\n"
        if result.overall_score is not None:
            legend_md += f"整体得分: {result.overall_score*100:.1f}%\n"
        for it in result.items:
            mark = {True: "✓", False: "✗", None: "·"}[it.passed]
            legend_md += f"- [{mark}] **{it.id}** {it.question}"
            if it.note:
                legend_md += f"  ({it.note})"
            legend_md += "\n"
    except Exception:
        pass

    return legend_md


# ---------- v1.5.0: HTML 单文件报告 ----------

# ---------- v1.6.0: 主题变量 + 响应式 + 打印样式 ----------

_LIGHT_VARS = """\
    --bg: #fafbfc;      --fg: #1c1c1c;
    --accent: #3498db;  --h1: #2c3e50;  --h2: #34495e;  --h3: #5d6d7e;
    --meta: #7f8c8d;    --card-bg: #ffffff;  --card-border: #e1e4e8;
    --code-bg: #ecf0f1; --row-alt: #f6f8fa;
    --pass: #27ae60;    --fail: #c0392b;     --skip: #7f8c8d;
    --th-bg: #3498db;   --th-fg: #ffffff;    --footer: #95a5a6;
    --shadow: 0 1px 3px rgba(0,0,0,0.06);
"""

_DARK_VARS = """\
    --bg: #16181d;      --fg: #e3e3e3;
    --accent: #5dade2;  --h1: #ecf0f1;  --h2: #d5dbdb;  --h3: #aab7c4;
    --meta: #95a5a6;    --card-bg: #1e2127;  --card-border: #2f343d;
    --code-bg: #23272e; --row-alt: #22262d;
    --pass: #48c78e;    --fail: #f14668;     --skip: #7a8290;
    --th-bg: #2b6cb0;   --th-fg: #ffffff;    --footer: #6b7280;
    --shadow: 0 1px 3px rgba(0,0,0,0.4);
"""

_BASE_RULES = """\
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
         "Microsoft YaHei", "Segoe UI", sans-serif;
         max-width: 920px; margin: 0 auto; padding: 24px;
         background: var(--bg); color: var(--fg); line-height: 1.65; }
  h1 { color: var(--h1); border-bottom: 3px solid var(--accent);
       padding-bottom: 8px; font-size: 1.7em; }
  h2 { color: var(--h2); margin-top: 32px; border-left: 4px solid var(--accent);
       padding-left: 12px; font-size: 1.25em; }
  h3 { color: var(--h3); font-size: 1.05em; }
  .meta { color: var(--meta); font-size: 0.9em; font-style: italic; }
  .caption-box { background: var(--code-bg); border-left: 4px solid var(--accent);
                 padding: 16px; margin: 16px 0; border-radius: 4px;
                 white-space: pre-wrap; word-break: break-word; }
  .audience { background: var(--card-bg); border: 1px solid var(--card-border);
              border-radius: 6px; padding: 12px 16px; margin: 8px 0;
              box-shadow: var(--shadow); }
  .audience-label { font-weight: 600; color: var(--accent); margin-right: 8px; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0;
          background: var(--card-bg); box-shadow: var(--shadow); }
  th, td { padding: 8px 12px; text-align: left;
           border-bottom: 1px solid var(--card-border); }
  th { background: var(--th-bg); color: var(--th-fg); font-weight: 600; }
  tbody tr:nth-child(even) { background: var(--row-alt); }
  .pass { color: var(--pass); font-weight: 600; }
  .fail { color: var(--fail); font-weight: 600; }
  .skip { color: var(--skip); }
  .score-pill { display: inline-block; padding: 3px 12px; border-radius: 12px;
                background: var(--accent); color: #fff; font-weight: 700;
                font-size: 0.9em; }
  .score-low { background: var(--fail); }
  .score-mid { background: #f39c12; }
  .score-high { background: var(--pass); }
  .figure-box { background: var(--card-bg); border: 1px solid var(--card-border);
                border-radius: 6px; padding: 16px; margin: 16px 0;
                text-align: center; box-shadow: var(--shadow); }
  /* 图表是「印刷品」：SVG 恒定浅底，保证深色轴线与文字在任意主题下都可读 */
  .figure-box svg { max-width: 100%; height: auto; background: #fff;
                    border-radius: 3px; padding: 4px; }
  .figure-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .footer { color: var(--footer); font-size: 0.85em; text-align: center;
            margin-top: 32px; padding-top: 16px;
            border-top: 1px solid var(--card-border); }

  /* ---------- 响应式 ---------- */
  @media (max-width: 720px) {
    body { padding: 14px; line-height: 1.6; }
    h1 { font-size: 1.35em; }
    h2 { font-size: 1.12em; margin-top: 24px; }
    .figure-row { grid-template-columns: 1fr; }
    table { font-size: 0.88em; }
    th, td { padding: 6px 8px; }
    .caption-box { padding: 12px; }
    .figure-box { padding: 10px; }
  }
  @media (max-width: 480px) {
    .score-pill { font-size: 0.8em; padding: 2px 8px; }
    .audience { padding: 10px 12px; }
  }

  /* ---------- 打印 ---------- */
  @media print {
    body { max-width: 100%; padding: 0; background: #fff; color: #000; }
    .figure-box, .audience, table { box-shadow: none; }
    h2 { page-break-after: avoid; }
    table, .figure-box { page-break-inside: avoid; }
  }
"""

_HTML_CSS = """<style>
  :root {
%(light)s  }
  /* auto 模式：跟随系统偏好 */
  @media (prefers-color-scheme: dark) {
    html[data-theme="auto"] {
%(dark)s    }
  }
  /* 强制 dark（置于 auto 之后，优先级最高） */
  html[data-theme="dark"] {
%(dark)s  }
%(base)s</style>
""" % {"light": _LIGHT_VARS, "dark": _DARK_VARS, "base": _BASE_RULES}


def _escape(text: str) -> str:
    """HTML 转义。"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def build_html_report(
    data: dict,
    chart_type: str,
    figure_number: str = "1",
    language: str = "zh",
    style: str = "generic",
    include_svg: bool = True,
    include_radar: bool = True,
    theme: str = "auto",
) -> str:
    """v1.5.0: 生成单文件 HTML 报告（v1.6.0: 支持主题与响应式）。

    内容：标题 + caption + 受众解读 + 评价清单（含表格）+ 雷达图（如 ML 触发）+ 图表 SVG。
    所有资源 inline（base64 / inline SVG），无外部依赖。

    参数:
        data: 原始图表数据
        chart_type: 'kaplan_meier' / 'roc_curve' / ...
        figure_number: 图编号字符串
        language: 'zh' / 'en'
        style: caption 风格
        include_svg: 是否内嵌图表 SVG（数据→SVG 重绘）
        include_radar: ML 触发时是否生成 14 维雷达图
        theme: 'auto' 跟随系统 / 'light' 强制浅色 / 'dark' 强制深色 (v1.6.0)
    """
    from parsers import PARSERS
    from appraisal import auto_evaluate
    from captions import generate_caption
    from audiences import render_all

    gi_type = _TYPE_ALIAS.get(chart_type, chart_type)
    summary = PARSERS[gi_type].parse(data)
    title = data.get("title", f"Figure {figure_number}")
    appraisal = auto_evaluate(summary)
    caption = generate_caption(summary, style=style, language=language,
                                figure_id=f"图{figure_number}" if language == "zh" else f"Figure {figure_number}")

    # 评分
    score = appraisal.overall_score or 0.0
    score_class = "score-low" if score < 0.4 else "score-mid" if score < 0.7 else "score-high"
    score_pill = f'<span class="score-pill {score_class}">{score*100:.0f}%</span>'

    # 受众
    aud_html = ""
    for aud_name, aud_text in render_all(summary, locale="zh_CN" if language == "zh" else "en").items():
        aud_html += (
            f'<div class="audience">'
            f'<span class="audience-label">{_escape(aud_name)}</span>'
            f'{_escape(aud_text)}</div>\n'
        )

    # 评价清单
    items_rows = ""
    for it in appraisal.items:
        if it.passed is True:
            mark, cls = "✓", "pass"
        elif it.passed is False:
            mark, cls = "✗", "fail"
        else:
            mark, cls = "·", "skip"
        items_rows += (
            f"<tr><td>{_escape(it.id)}</td><td>{mark}</td>"
            f"<td>{_escape(it.question)}</td>"
            f"<td class='{cls}'>{_escape(it.note or '')}</td></tr>\n"
        )

    # 图表 SVG
    figure_svg_html = ""
    has_calibration = False
    if include_svg:
        figure_svg = _svg_render_for_type(gi_type, data)

        # v1.6.0: ML 场景追加 calibration 子图（ROC / calibration 并排）
        # get 不到 calibration 字段时 render_calibration 返回空串，自动跳过
        calib_svg = ""
        if _SVG_AVAILABLE and _svg_render is not None and gi_type in (
            "roc_curve", "scatter_plot",
        ):
            try:
                calib_svg = _svg_render.render_calibration(
                    data, title=f"Calibration - {title}"
                ) or ""
            except Exception:
                calib_svg = ""

        if figure_svg and calib_svg:
            has_calibration = True
            figure_svg_html = (
                '<div class="figure-row">'
                '<div class="figure-box">'
                f'<h3>{_escape("Figure")} {_escape(figure_number)}</h3>'
                f'{figure_svg}'
                '</div>'
                '<div class="figure-box">'
                f'<h3>{_escape("Calibration plot")}</h3>'
                f'{calib_svg}'
                '</div>'
                '</div>'
            )
        elif figure_svg:
            figure_svg_html = (
                '<div class="figure-box">'
                f'<h3>{_escape("Figure")} {_escape(figure_number)}</h3>'
                f'{figure_svg}'
                '</div>'
            )

    # 雷达图（如 ML 触发）
    radar_html = ""
    if include_radar:
        try:
            from tripod_ai_radar import render_tripod_ai_radar
            radar_svg = render_tripod_ai_radar(appraisal)
            if radar_svg:
                radar_html = (
                    '<div class="figure-box">'
                    f'<h3>{_escape("TRIPOD-AI 14 维雷达图")}</h3>'
                    f'{radar_svg}'
                    '</div>'
                )
        except Exception:
            pass

    # 拼接
    theme = theme if theme in ("auto", "light", "dark") else "auto"

    html = f"""<!DOCTYPE html>
<html lang="{language}" data-theme="{theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(title)} | graph-interpretation v1.6.0</title>
{_HTML_CSS}
</head>
<body>
<h1>{_escape(title)}</h1>
<p class="meta">
  图表类型: <b>{_escape(gi_type)}</b> ·
  编号: <b>{_escape(figure_number)}</b> ·
  语言: <b>{_escape(language)}</b> ·
  风格: <b>{_escape(style)}</b> ·
  评价框架: <b>{_escape(appraisal.framework)}</b> ·
  整体得分: {score_pill} ({appraisal.n_passed}/{appraisal.n_items} 通过)
</p>

<h2>1. 图注 / Caption</h2>
<div class="caption-box">{_escape(caption)}</div>

<h2>2. 图表重绘 / {_escape("Figures (ROC + Calibration)" if has_calibration else "Figure SVG")}</h2>
{figure_svg_html if figure_svg_html else '<p class="meta">(未启用 --with-svg)</p>'}

<h2>3. 受众解读 / Audiences</h2>
{aud_html if aud_html else '<p class="meta">(无受众数据)</p>'}

<h2>4. 评价清单 / Appraisal ({appraisal.n_items} items)</h2>
<table>
  <thead><tr>
    <th>ID</th><th>{_escape("判定")}</th><th>{_escape("问题")}</th><th>{_escape("备注")}</th>
  </tr></thead>
  <tbody>{items_rows}</tbody>
</table>

<h2>5. 雷达图 / Radar Chart</h2>
{radar_html if radar_html else '<p class="meta">(非 ML 模型，未触发 TRIPOD-AI 雷达图)</p>'}

<div class="footer">
  Generated by graph-interpretation v1.5.0 ·
  <a href="https://github.com/AIPOCH/graph-interpretation">graph-interpretation</a>
</div>
</body>
</html>"""
    return html


def write_html_report(html: str, output_path: Path) -> None:
    """v1.5.0: 把 HTML 字符串保存为单文件报告。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"[html] 已写入 {output_path}（{len(html)} 字符）")


# ---------- v1.5.0: TRIPOD-AI sentinel docx（字段缺失警示） ----------

# 14 个标准 TRIPOD-AI 字段（与 build_sentinel_docx 配套使用）
_TRIPOD_AI_FIELDS = [
    ("model_type", "模型类型", str),
    ("data_source", "训练数据来源 / 时间窗", str),
    ("events_per_predictor", "EPP（事件数 / 预测因子数）", (int, float)),
    ("split_strategy", "训练 / 测试划分策略", str),
    ("internal_validation", "内部验证方法", str),
    ("external_validation_temporal", "时间外部验证", bool),
    ("external_validation_geographic", "地理外部验证", bool),
    ("calibration_slope", "calibration（slope/intercept/Brier）", (int, float)),
    ("explainability_method", "可解释性方法（SHAP/LIME/…）", str),
    ("fairness_assessed", "亚组公平性评估", bool),
    ("decision_curve", "决策曲线 / 临床净收益", bool),
    ("code_availability", "代码 / 数据可获得性", str),
    ("model_version_pinned", "模型版本 / 随机种子锁定", bool),
    ("bias_assessed", "潜在偏倚讨论", bool),
]

_SENTINEL_THRESHOLD = 7  # ai_items < 7 触发警示


def collect_missing_fields(raw: dict) -> tuple[list[str], list[str], int]:
    """返回 (缺失字段列表, 已报告字段列表, 已报告数)。

    缺失：raw 中无对应 key 或值为 None/空字符串。
    已报告：raw 中存在且类型符合期望。
    """
    raw = raw or {}
    missing, present = [], []
    for field, label, expected_type in _TRIPOD_AI_FIELDS:
        v = raw.get(field)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(field)
            continue
        # 类型校验
        ok = False
        if expected_type is bool:
            ok = isinstance(v, bool)
        elif isinstance(expected_type, tuple):
            ok = isinstance(v, expected_type)
        elif expected_type is str:
            ok = isinstance(v, str) and bool(v.strip())
        if ok:
            present.append(field)
        else:
            missing.append(f"{field} (type mismatch: {type(v).__name__})")
    return missing, present, len(present)


def is_sentinel_needed(raw: dict, n_ai_items: int) -> bool:
    """判断是否需要生成 sentinel docx。

    触发条件：
    1) raw 表明是 ML/DL 模型（model_type / methodology / 超参命中）
    2) TRIPOD-AI 标准字段已报告数 < 7（即 ai_items 数）
    """
    if not raw:
        return False
    try:
        from tripod_ai_checklist import _is_ml_model
    except ImportError:
        return False
    if not _is_ml_model(raw):
        return False
    _, _, n_present = collect_missing_fields(raw)
    return n_present < _SENTINEL_THRESHOLD


def build_sentinel_docx(
    raw: dict,
    output_path: Path,
    title: str = "TRIPOD-AI 字段缺失警示",
    summary=None,
) -> None:
    """v1.5.0: 生成 TRIPOD-AI 字段缺失警示 docx。

    内容包括：
    - 橙色大标题"⚠️ TRIPOD-AI 字段缺失警示"
    - 已识别的 ML 模型类型 / 触发方式
    - 缺失字段清单（红字）
    - 已报告字段清单（绿字）
    - 14 项 TRIPOD-AI 空白模板（待人工补全）
    - 自动生成的下一步建议
    """
    from docx import Document
    from docx.shared import RGBColor, Pt

    missing, present, n_present = collect_missing_fields(raw)
    raw = raw or {}

    # 触发方式
    triggers = []
    mt = (raw.get("model_type") or raw.get("model_name") or "").strip()
    if mt:
        triggers.append(f"model_type = {mt}")
    meth = (raw.get("methodology") or raw.get("algorithm") or "").strip()
    if meth:
        triggers.append(f"methodology = {meth}")
    hp = [f for f in [
        "learning_rate", "epochs", "batch_size", "loss_fn", "loss_function",
        "optimizer", "weight_decay", "l1", "l2", "dropout", "warmup_steps",
        "early_stopping", "gradient_accumulation",
    ] if f in raw]
    if hp:
        triggers.append(f"超参字段 = {hp[:3]}{'…' if len(hp) > 3 else ''}（共 {len(hp)} 项）")

    doc = Document()

    # 标题（橙色）
    h = doc.add_heading("⚠️ TRIPOD-AI 字段缺失警示", level=0)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0xE6, 0x7E, 0x22)  # 橙色

    sub = doc.add_paragraph()
    sub.add_run(f"目标图表：{title}").italic = True

    # 概述
    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run(
        f"已识别本图为 ML/DL 预测模型评估（ROC 或 calibration plot），"
        f"但 TRIPOD-AI 14 项标准字段中仅报告 {n_present}/14（阈值 ≥ {_SENTINEL_THRESHOLD}）。"
        f"建议在发表前向作者索要缺失字段，或在自家报告时补全。"
    )
    run.font.size = Pt(11)

    # 触发方式
    if triggers:
        doc.add_heading("1. ML 触发方式", level=2)
        for t in triggers:
            doc.add_paragraph(t, style="List Bullet")

    # 缺失字段（红色列表）
    doc.add_heading(f"2. 缺失字段清单（{len(missing)} 项）", level=2)
    if missing:
        for m in missing:
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(f"✗ {m}")
            run.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)  # 红色
    else:
        doc.add_paragraph("（无）").italic = True

    # 已报告字段（绿色列表）
    doc.add_heading(f"3. 已报告字段清单（{len(present)} 项）", level=2)
    if present:
        for f in present:
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(f"✓ {f}")
            run.font.color.rgb = RGBColor(0x27, 0xAE, 0x60)  # 绿色
    else:
        doc.add_paragraph("（无）").italic = True

    # 14 项空白模板（待补全）
    doc.add_heading("4. TRIPOD-AI 14 项空白模板（待人工补全）", level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light List Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "ID"
    hdr[1].text = "检查项"
    hdr[2].text = "报告内容（待补）"
    for cell in hdr:
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
    for field, label, _ in _TRIPOD_AI_FIELDS:
        row = table.add_row().cells
        row[0].text = field.replace("_", "-").upper()
        row[1].text = label
        row[2].text = ""

    # 后续建议
    doc.add_heading("5. 后续建议", level=2)
    suggestions = [
        "联系作者索要缺失字段（特别是 model_type、data_source、EPP、validation 策略）",
        "若为自家研究：在 Methods / Results 段按 TRIPOD-AI 14 项模板补全",
        "若使用公共模型：检查 GitHub README 或 Hugging Face / ModelScope 模型卡是否已声明",
        "可在 docx 中直接填写上方「待补」列，再以 .docx 形式存档或返给作者",
        "完成补全后重跑 graph-interp appraise 或 export-csv 确认 14 项均通过",
    ]
    for s in suggestions:
        doc.add_paragraph(s, style="List Number")

    # 页脚
    doc.add_paragraph()
    foot = doc.add_paragraph()
    fr = foot.add_run(
        f"由 graph-interpretation v1.5.0 自动生成 · 触发条件 ML+字段 < {_SENTINEL_THRESHOLD}"
    )
    fr.italic = True
    fr.font.size = Pt(9)
    fr.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)  # 灰色

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True,
                    choices=list(_TYPE_ALIAS.keys()))
    ap.add_argument("--data", help="JSON 数据文件路径")
    ap.add_argument("--inline", help="直接传 JSON 字符串")
    ap.add_argument("--figure-number", default="1")
    ap.add_argument("--language", default="zh", choices=["en", "zh"])
    ap.add_argument("--out", required=True, help="输出 .docx 路径")

    # 新增：SVG 嵌入支持（v1.2.0）
    ap.add_argument("--with-svg", action="store_true",
                    help="自动调用 svg_render 把数据绘成 SVG 并嵌入 docx")
    ap.add_argument("--svg-width", type=float, default=6.0,
                    help="嵌入 docx 的 SVG（PNG）宽度，单位英寸")

    ap.add_argument("--print-md", action="store_true", help="同时打印 markdown")
    args = ap.parse_args()

    if args.data:
        data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    else:
        data = json.loads(args.inline)

    md = render_chart_legend(
        data=data,
        chart_type=args.type,
        figure_number=args.figure_number,
        language=args.language,
    )

    title = data.get("title", f"Figure {args.figure_number}")

    # 可选：渲染并嵌入 SVG
    svg_text = None
    if args.with_svg:
        gi_type = _TYPE_ALIAS.get(args.type) or args.type
        svg_text = _svg_render_for_type(gi_type, data)
        if svg_text is None:
            print(f"[warn] SVG 不可用：{gi_type}。请确认 svg_render.py 与依赖可用。")

    write_docx(
        legend_text=md,
        output_path=Path(args.out),
        title=title,
        svg_text=svg_text,
        svg_width=args.svg_width,
    )

    if args.print_md:
        print("\n=== Markdown legend ===")
        print(md)


if __name__ == "__main__":
    main()
