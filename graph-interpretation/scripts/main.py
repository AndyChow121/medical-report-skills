#!/usr/bin/env python3
"""graph-interpretation CLI 入口（v1.1.0）。

子命令：
- interpret:  解析图表数据 → 结构化统计摘要
- caption:    生成期刊风格图注
- audiences:  生成多受众解读（researchers/clinicians/patients/policy_makers）
- appraise:   批判性评价 checklist
- render-svg: KM/Forest/ROC 数据 → SVG
- ocr:        图像 → 关键统计量
- check:      跑通全部子命令的 smoke test

用法示例：
    python main.py interpret --type kaplan_meier --data data.json
    python main.py caption --type roc_curve --data data.json --style nature --language en
    python main.py audiences --type forest_plot --data data.json
    python main.py appraise --type kaplan_meier --data data.json --json
    python main.py render-svg --type km --data data.json --out km.svg
    python main.py ocr --image figure.png --text "HR=0.72 (95% CI 0.58-0.89), p=0.003"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 让 import 兼容以脚本方式或模块方式调用
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from parsers import PARSERS  # noqa: E402
from audiences import render_all  # noqa: E402
from captions import generate_caption, list_styles  # noqa: E402
from appraisal import auto_evaluate  # noqa: E402
from svg_render import (
    render_km, render_forest, render_roc,
    render_box, render_scatter, render_bar,
    render_heatmap, render_volcano,
)  # noqa: E402
from legend_bridge import to_legend_fields, to_legend_type, render_legend_context  # noqa: E402
from ocr_extract import extract_from_image, extract_from_text, extract_from_pdf, extract_auto  # noqa: E402
from _samples import load_bundled_sample, list_samples  # noqa: E402


# ---------- 共享工具 ----------

def _load_data(args: argparse.Namespace) -> dict[str, Any]:
    if args.data:
        return json.loads(Path(args.data).read_text(encoding="utf-8"))
    if args.inline:
        return json.loads(args.inline)
    raise SystemExit("必须提供 --data <json 文件> 或 --inline '<json 字符串>'")


def _type_alias(t: str) -> str:
    """CLI 友好别名 → parser chart_type。"""
    aliases = {
        "km": "kaplan_meier",
        "kaplan": "kaplan_meier",
        "forest": "forest_plot",
        "roc": "roc_curve",
        "box": "box_plot",
        "scatter": "scatter_plot",
        "bar": "bar_chart",
        "heatmap": "heatmap",
        "volcano": "volcano_plot",
        # v1.5.0: ML / 中文 / SVG 扩展 alias（解析器仍走标准 8 类）
        "roc_ml": "roc_curve",
        "roc_curve_ml": "roc_curve",
        "csco_km": "kaplan_meier",
        "csco_gastric_km": "kaplan_meier",
        "km_svg": "kaplan_meier",
        "scatter_ml": "scatter_plot",  # 预留：calibration plot ML
    }
    return aliases.get(t.lower(), t.lower())


# ---------- 子命令 ----------

def cmd_interpret(args: argparse.Namespace) -> int:
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}（支持：{list(PARSERS)}）")
    data = _load_data(args)
    summary = PARSERS[chart_type].parse(data)
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_caption(args: argparse.Namespace) -> int:
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    data = _load_data(args)
    summary = PARSERS[chart_type].parse(data)
    caption = generate_caption(
        summary,
        style=args.style,
        language=args.language,
        figure_id=args.figure_id,
    )
    if args.out:
        Path(args.out).write_text(caption, encoding="utf-8")
        print(f"[caption] 已写入 {args.out}")
    else:
        print(caption)
    return 0


def cmd_audiences(args: argparse.Namespace) -> int:
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    data = _load_data(args)
    summary = PARSERS[chart_type].parse(data)
    # v1.2.0: 支持 locale（"en" 或 "zh_CN"），中国语境下加 CSCO/医保话术
    result = render_all(summary, locale=args.locale)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for aud, text in result.items():
            print(f"\n=== {aud} ===\n{text}")
    return 0


def cmd_export_csv(args: argparse.Namespace) -> int:
    """导出 TRIPOD-AI 14 条评价为 CSV。"""
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    data = _load_data(args) if (args.data or args.inline) else {}
    summary = PARSERS[chart_type].parse(data) if data else None
    if summary is None:
        from parsers.base import StatisticalSummary
        summary = StatisticalSummary(chart_type=chart_type)
    result = auto_evaluate(summary)
    try:
        from tripod_ai_radar import export_tripod_ai_csv
        content = export_tripod_ai_csv(
            result,
            csv_path=args.out,
            summary=summary,
            include_bom=not args.no_bom,
        )
        n_tr = sum(1 for it in result.items if it.id.startswith("TRIPOD-AI"))
        print(f"[export-csv] 已写入 {args.out}（{n_tr} 条 TRIPOD-AI 评价）")
        if not args.out:
            sys.stdout.write(content)
        return 0
    except ImportError as e:
        raise SystemExit(f"TRIPOD-AI 不可用: {e}")


def cmd_appraise(args: argparse.Namespace) -> int:
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    data = _load_data(args) if (args.data or args.inline) else {}
    summary = PARSERS[chart_type].parse(data) if data else None
    if summary is None:
        # 空数据也能拿空 checklist
        from parsers.base import StatisticalSummary
        summary = StatisticalSummary(chart_type=chart_type)
    result = auto_evaluate(summary)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"图表类型: {result.chart_type}")
        print(f"评价框架: {result.framework}")
        print(f"条目: {result.n_items}（已评估 {result.n_passed + result.n_failed}，未评估 {result.n_unchecked}）")
        if result.overall_score is not None:
            print(f"得分: {result.overall_score*100:.1f}%")
        print()
        for item in result.items:
            mark = {"True": "✓", "False": "✗", "None": "·"}[str(item.passed)]
            print(f"  [{mark}] {item.id} {item.question}")
            if item.note:
                print(f"        {item.note}")
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """v1.3.0: 一次性输出 interpret + caption + audiences + appraisal 四档 JSON。"""
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    data = _load_data(args)
    summary = PARSERS[chart_type].parse(data)

    locale = getattr(args, "locale", "en")
    style = getattr(args, "style", "generic")
    language = getattr(args, "language", "en")
    figure_id = getattr(args, "figure_id", "Figure 1")

    caption = generate_caption(
        summary, style=style, language=language, figure_id=figure_id,
    )
    audiences = render_all(summary, locale=locale)
    appraisal_result = auto_evaluate(summary)

    out = {
        "chart_type": chart_type,
        "figure_id": figure_id,
        "style": style,
        "language": language,
        "locale": locale,
        "interpret": summary.to_dict(),
        "caption": caption,
        "audiences": audiences,
        "appraisal": appraisal_result.to_dict(),
    }
    if args.out:
        Path(args.out).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        print(f"[all] 已写入 {args.out}", file=sys.stderr)

    # 人类可读概览
    print(f"图表: {chart_type}  风格: {style}  语言: {language}")
    print(f"  interpret.primary: {summary.primary}")
    print(f"  caption 字数: {len(caption)}  字符")
    print(f"  audiences 受众: {list(audiences)}")
    print(f"  appraisal 条目: {appraisal_result.n_items}（通过 {appraisal_result.n_passed} / 失败 {appraisal_result.n_failed}）")
    if appraisal_result.overall_score is not None:
        print(f"  appraisal 整体得分: {appraisal_result.overall_score*100:.1f}%")
    print()
    print(f"完整 JSON 已写入：{args.out or '(stdout)'}")
    return 0


def cmd_render_svg(args: argparse.Namespace) -> int:
    chart_type = _type_alias(args.type)
    data = _load_data(args)
    title = args.title or data.get("title", "")
    dispatch = {
        "kaplan_meier": render_km,
        "forest_plot": render_forest,
        "roc_curve": render_roc,
        "box_plot": render_box,
        "scatter_plot": render_scatter,
        "bar_chart": render_bar,
        "heatmap": render_heatmap,
        "volcano_plot": render_volcano,
    }
    if chart_type not in dispatch:
        raise SystemExit(f"render-svg 不支持的图表类型: {args.type}")
    svg = dispatch[chart_type](data, title=title)
    if args.out:
        Path(args.out).write_text(svg, encoding="utf-8")
        print(f"[svg] 已写入 {args.out}（{len(svg)} 字符）")
    else:
        print(svg)
    return 0


def cmd_ocr(args: argparse.Namespace) -> int:
    if args.pdf:
        try:
            result = extract_from_pdf(args.pdf)
        except RuntimeError as e:
            raise SystemExit(str(e))
    elif args.image:
        try:
            result = extract_from_image(args.image)
        except RuntimeError as e:
            if args.text is None:
                raise SystemExit(str(e))
            result = extract_from_text(args.text)
            result["_note"] = "fallback to text mode"
    elif args.text:
        result = extract_from_text(args.text)
    else:
        raise SystemExit("必须提供 --image / --pdf / --text 之一")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_to_legend(args: argparse.Namespace) -> int:
    """导出 figure-legend-gen 桥接字段 / .docx 端到端。"""
    chart_type = _type_alias(args.type)
    if chart_type not in PARSERS:
        raise SystemExit(f"未知图表类型: {args.type}")
    # v1.5.0: 无 --data 时自动尝试 bundled sample（如 roc_ml / csco_km）
    if not getattr(args, "data", None) and not getattr(args, "inline", None):
        from _samples import load_bundled_sample
        try:
            data = load_bundled_sample(args.type)
            print(f"[v1.5.0] 自动加载 bundled sample: {args.type}", file=sys.stderr)
        except KeyError:
            raise SystemExit(
                f"未知图表类型: {args.type}；也无对应 bundled sample。可选 --data X.json 或 --type 标准 8 类"
            )
        except FileNotFoundError as e:
            raise SystemExit(str(e))
    else:
        data = _load_data(args)
    summary = PARSERS[chart_type].parse(data)

    if args.mode == "docx":
        # 端到端：graph-interpretation → figure-legend-gen → .docx
        try:
            from to_legend_docx import render_chart_legend, write_docx  # type: ignore
        except ImportError as e:
            raise SystemExit(
                "导出 .docx 需要安装 python-docx：`pip install python-docx` "
                f"({e})"
            )
        md = render_chart_legend(
            data=data,
            chart_type=chart_type,
            figure_number=args.figure_number,
            language=args.language,
            style=args.style,
        )
        out_path = Path(args.out) if args.out else Path(f"figure_{args.figure_number}_legend.docx")
        title = data.get("title", f"Figure {args.figure_number}")
        # v1.2.0: 可选嵌入 SVG
        svg_text = None
        if getattr(args, "with_svg", False):
            from to_legend_docx import _svg_render_for_type  # type: ignore
            svg_text = _svg_render_for_type(chart_type, data)
        write_docx(
            md, out_path, title=title,
            svg_text=svg_text,
            svg_width=getattr(args, "svg_width", 6.0),
        )

        # v1.5.0: TRIPOD-AI sentinel docx 自动检测
        ai_sentinel = getattr(args, "ai_sentinel", "auto")
        if ai_sentinel != "off":
            try:
                from to_legend_docx import (
                    build_sentinel_docx, is_sentinel_needed,
                )  # type: ignore
                from appraisal import auto_evaluate
                result = auto_evaluate(summary)
                ai_items = [it for it in result.items if it.id.startswith("TRIPOD-AI")]
                n_ai = len(ai_items)
                force = (ai_sentinel == "force")
                raw = (summary.raw or {})
                need = is_sentinel_needed(raw, n_ai) or force
                if need:
                    sentinel_path = out_path.with_name(out_path.stem + "_sentinel.docx")
                    build_sentinel_docx(
                        raw=raw,
                        output_path=sentinel_path,
                        title=title,
                        summary=summary,
                    )
                    print(
                        f"[v1.5.0 sentinel] ML 触发 + 字段 < 7，已生成警示 docx: {sentinel_path}",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(f"[v1.5.0 sentinel] 生成失败（非致命）：{e}", file=sys.stderr)

        if getattr(args, "print_md", False):
            print("\n=== Markdown legend ===")
            print(md)
        return 0

    if args.mode == "fields":
        output = json.dumps(to_legend_fields(summary), ensure_ascii=False, indent=2)
    elif args.mode == "html":
        # v1.5.0: 单文件 HTML 报告
        try:
            from to_legend_docx import build_html_report, write_html_report  # type: ignore
        except ImportError as e:
            raise SystemExit(f"导出 HTML 需要 to_legend_docx 模块: {e}")
        html = build_html_report(
            data=data,
            chart_type=chart_type,
            figure_number=args.figure_number,
            language=args.language,
            style=args.style,
            include_svg=getattr(args, "with_svg", False),
            include_radar=True,
            theme=getattr(args, "theme", "auto"),
        )
        if args.out:
            write_html_report(html, Path(args.out))
        else:
            print(html)
        return 0
    else:
        output = render_legend_context(
            summary,
            figure_id=args.figure_id,
            style=args.style,
            language=args.language,
        )
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"[bridge] 已写入 {args.out}（{len(output)} 字符）")
    else:
        print(output)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """v1.5.0: 跑通 bundled samples 的 demo 链路。

    用法：
        graph-interp demo                    # 跑遍所有 bundled samples
        graph-interp demo --type km          # 单类深度 demo（额外 render-svg + to-legend docx）
        graph-interp demo --type roc_ml      # ML 场景 demo
        graph-interp demo --type csco_km     # 中文期刊场景 demo
    """
    samples = list_samples()
    if args.type:
        # 单类深度 demo
        targets = [args.type]
        deep = True
    else:
        # 跑遍 8 类基础 sample（km/forest/roc/box/scatter/bar/heatmap/volcano）
        targets = [s for s in samples if s in {
            "km", "forest", "roc", "box", "scatter", "bar", "heatmap", "volcano",
        }]
        deep = False

    # alias → chart_type 映射
    SAMPLE_TO_TYPE = {
        "km": "kaplan_meier", "kaplan_meier": "kaplan_meier", "kaplan": "kaplan_meier",
        "forest": "forest_plot", "forest_plot": "forest_plot",
        "roc": "roc_curve", "roc_curve": "roc_curve",
        "roc_ml": "roc_curve", "roc_curve_ml": "roc_curve",
        "box": "box_plot", "box_plot": "box_plot",
        "scatter": "scatter_plot", "scatter_plot": "scatter_plot",
        "bar": "bar_chart", "bar_chart": "bar_chart",
        "heatmap": "heatmap",
        "volcano": "volcano_plot", "volcano_plot": "volcano_plot",
        "csco_km": "kaplan_meier", "csco_gastric_km": "kaplan_meier",
        "km_svg": "kaplan_meier",
    }

    print(f"=== graph-interpretation v1.5.0 demo ===")
    print(f"bundled samples: {len(list_samples())} 个；本次运行: {len(targets)} 个（deep={deep}）")
    print()

    n_ok = 0
    for sample_alias in targets:
        chart_type = SAMPLE_TO_TYPE.get(sample_alias)
        if chart_type is None or chart_type not in PARSERS:
            print(f"[skip] {sample_alias}: 未识别 chart_type")
            continue
        try:
            data = load_bundled_sample(sample_alias)
            summary = PARSERS[chart_type].parse(data)
            appraisal = auto_evaluate(summary)
            caption = generate_caption(summary, style="generic", language="en", figure_id="Figure 1")
            score = (
                f"{appraisal.overall_score*100:.0f}%"
                if appraisal.overall_score is not None else "n/a"
            )
            prim = summary.primary
            prim_str = (
                f"{prim.measure}={prim.value:.3f}" if getattr(prim, "value", None) is not None
                else f"{prim.measure}=n/a"
            )
            print(f"[{sample_alias:18s}] {chart_type:14s} | 条目={appraisal.n_items:>2d} 通过={appraisal.n_passed:>2d} | {score} | {prim_str}")

            if deep:
                # 额外渲染 SVG 与 docx
                svg_dispatch = {
                    "kaplan_meier": render_km, "forest_plot": render_forest,
                    "roc_curve": render_roc, "box_plot": render_box,
                    "scatter_plot": render_scatter, "bar_chart": render_bar,
                    "heatmap": render_heatmap, "volcano_plot": render_volcano,
                }
                fn = svg_dispatch.get(chart_type)
                if fn:
                    svg = fn(data, title=data.get("title", ""))
                    print(f"  └─ SVG 长度: {len(svg)} 字符")
                audiences = render_all(summary, locale="zh_CN")
                print(f"  └─ 中国语境受众: {list(audiences)}")

                # 端到端 docx
                try:
                    from to_legend_docx import render_chart_legend, write_docx
                    md = render_chart_legend(
                        data=data, chart_type=chart_type,
                        figure_number="demo", language="zh", style="cma",
                    )
                    out_path = Path(args.out_dir) / f"demo_{sample_alias}.docx" if args.out_dir else Path(f"demo_{sample_alias}.docx")
                    write_docx(md, out_path, title=data.get("title", sample_alias))
                    print(f"  └─ docx 已写入: {out_path}")
                except Exception as e:
                    print(f"  └─ [warn] docx 写入失败: {e}")
            n_ok += 1
        except Exception as e:
            print(f"[FAIL] {sample_alias}: {e}")

    print()
    print(f"成功 {n_ok}/{len(targets)}")
    return 0 if n_ok == len(targets) else 1


def cmd_diff(args: argparse.Namespace) -> int:
    """v1.6.0: 对比两个图表数据 / sample 的评价结果差异。

    两侧输入均可为：JSON 文件路径 或 bundled sample 别名。
    用途：审稿前后对比、补录数据前后对比、两个候选模型对比。
    """
    from _diff import diff_appraisals, render_diff
    from _samples import has_sample, load_bundled_sample, list_samples

    def _load_side(spec: str) -> tuple[dict[str, Any], str, str]:
        """加载一侧数据 → (data, chart_type, label)。"""
        p = Path(spec)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            label = p.stem
        else:
            # 依次尝试原名 / 剥 sample_ 前缀 / 剥 .json 后缀，三种写法都接受
            cands = [spec]
            stripped = spec
            if stripped.startswith("sample_"):
                stripped = stripped[len("sample_"):]
            cands.append(stripped)
            if stripped.endswith(".json"):
                cands.append(stripped[: -len(".json")])

            hit = next((c for c in cands if has_sample(c)), None)
            if hit is None:
                raise SystemExit(
                    f"无法定位 '{spec}'：既不是文件路径，也不是 bundled sample。\n"
                    f"可用 sample: {list_samples()}"
                )
            data = load_bundled_sample(hit)
            label = hit
        # 类型推断三路兜底：
        #   1) --type 显式指定
        #   2) JSON 内的 chart_type 字段
        #   3) 名称推断（bundled sample 的 JSON 常不带 chart_type，
        #      但别名本身如 roc_ml / csco_km 已在 _type_alias 表内）
        ctype = ""
        for cand in (
            args.type or "",
            str(data.get("chart_type") or ""),
            label,
            label[len("sample_"):] if label.startswith("sample_") else "",
        ):
            ctype = _type_alias(cand)
            if ctype in PARSERS:
                break
        if ctype not in PARSERS:
            raise SystemExit(
                f"无法确定 '{spec}' 的图表类型：请加 --type，"
                f"或在 JSON 中写 chart_type 字段。\n"
                f"当前解析为 '{ctype or '(空)'}'，支持: {sorted(PARSERS)}"
            )
        return data, ctype, label

    data_a, ctype_a, label_a = _load_side(args.a)
    data_b, ctype_b, label_b = _load_side(args.b)

    if ctype_a != ctype_b:
        print(
            f"[diff] 警告：两侧图表类型不同（{ctype_a} vs {ctype_b}），"
            f"条目对齐可能无意义",
            file=sys.stderr,
        )

    res_a = auto_evaluate(PARSERS[ctype_a].parse(data_a))
    res_b = auto_evaluate(PARSERS[ctype_b].parse(data_b))

    diff = diff_appraisals(res_a, res_b, label_a, label_b)
    print(render_diff(diff, fmt=args.format, verbose=args.verbose))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """v1.5.0: JSON Schema 校验。"""
    from _schema import validate_payload, SCHEMAS, schema_to_text

    if getattr(args, "show_schema", None):
        print(schema_to_text(args.show_schema))
        return 0

    if getattr(args, "list_schemas", False):
        print(f"支持的 schema: {sorted(SCHEMAS.keys())}")
        return 0

    data = _load_data(args)
    schema_name = _type_alias(args.type) if args.type else data.get("chart_type")
    if not schema_name:
        raise SystemExit(
            "需要 --type 指定 schema，或 --data JSON 中包含 chart_type 字段"
        )
    ok, errors = validate_payload(data, schema_name)
    if ok:
        print(f"[validate] OK 通过 schema '{schema_name}'（字段数: {len(data)}）")
        return 0
    print(f"[validate] FAIL 失败 schema '{schema_name}'（{len(errors)} 个错误）")
    for e in errors:
        print(f"  - {e}")
    return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """v1.5.0: 端到端全样本自检（CI 友好）。v1.6.0: 增加质量阈值判定。

    遍历 8 类 bundled samples（+ ML + 中文期刊），每类执行：
        interpret → caption → audiences → appraise → render-svg → to-legend(docx)

    失败判定（任一命中即计入退出码）：
        1) 链路抛异常（v1.5.0 起）
        2) --fail-on-low-score：overall_score 低于给定阈值（v1.6.0）
        3) --fail-on-missing：未评估条目数超过上限（v1.6.0）

    两个阈值默认关闭，保持与 v1.5.0 完全兼容的「跑通即通过」语义。
    """
    targets = [
        ("km", "kaplan_meier"),
        ("forest", "forest_plot"),
        ("roc", "roc_curve"),
        ("box", "box_plot"),
        ("scatter", "scatter_plot"),
        ("bar", "bar_chart"),
        ("heatmap", "heatmap"),
        ("volcano", "volcano_plot"),
    ]
    if not getattr(args, "no_ml", False):
        targets.append(("roc_ml", "roc_curve"))
    if not getattr(args, "no_zh", False):
        targets.append(("csco_km", "kaplan_meier"))

    print(f"=== graph-interpretation v1.5.0 verify ===")
    print(f"样本数: {len(targets)}（ML={'off' if getattr(args, 'no_ml', False) else 'on'}, "
          f"中文={'off' if getattr(args, 'no_zh', False) else 'on'}）")
    print()

    failed: list[tuple[str, str]] = []
    passed: list[tuple[str, str]] = []
    results: list[dict[str, Any]] = []

    # v1.6.0: 质量阈值（None = 不启用）
    low_th = getattr(args, "fail_on_low_score", None)
    miss_th = getattr(args, "fail_on_missing", None)
    if low_th is not None:
        print(f"质量阈值: 得分 >= {low_th*100:.0f}%"
              + (f"，未评估 <= {miss_th} 条" if miss_th is not None else ""))
        print()

    work_dir = Path(args.work_dir) if getattr(args, "work_dir", None) else Path(".verify_tmp")
    work_dir.mkdir(parents=True, exist_ok=True)

    for sample_alias, chart_type in targets:
        try:
            data = load_bundled_sample(sample_alias)
            summary = PARSERS[chart_type].parse(data)

            # 1. interpret
            _ = summary.to_dict()
            # 2. caption
            cap = generate_caption(summary, style="cma", language="zh", figure_id="图1")
            # 3. audiences
            aud = render_all(summary, locale="zh_CN")
            # 4. appraise
            ap = auto_evaluate(summary)
            # 5. render-svg
            svg_dispatch = {
                "kaplan_meier": render_km, "forest_plot": render_forest,
                "roc_curve": render_roc, "box_plot": render_box,
                "scatter_plot": render_scatter, "bar_chart": render_bar,
                "heatmap": render_heatmap, "volcano_plot": render_volcano,
            }
            fn = svg_dispatch.get(chart_type)
            svg = fn(data, title=data.get("title", "")) if fn else ""
            # 6. to-legend docx
            try:
                from to_legend_docx import render_chart_legend, write_docx
                md = render_chart_legend(
                    data=data, chart_type=chart_type,
                    figure_number="verify", language="zh", style="cma",
                )
                docx_path = work_dir / f"verify_{sample_alias}.docx"
                write_docx(md, docx_path, title=data.get("title", sample_alias))
            except Exception as e:
                raise RuntimeError(f"to-legend(docx) 失败: {e}")

            score = (
                f"{ap.overall_score*100:.0f}%"
                if ap.overall_score is not None else "n/a"
            )

            # v1.6.0: 质量阈值判定（链路跑通 ≠ 质量达标）
            reasons: list[str] = []
            if low_th is not None and ap.overall_score is not None:
                if ap.overall_score < low_th:
                    reasons.append(
                        f"得分 {ap.overall_score*100:.0f}% < 阈值 {low_th*100:.0f}%"
                    )
            if miss_th is not None and ap.n_unchecked > miss_th:
                reasons.append(f"未评估 {ap.n_unchecked} 条 > 上限 {miss_th}")
            ok = not reasons

            results.append({
                "alias": sample_alias,
                "chart_type": chart_type,
                "score": ap.overall_score,
                "n_items": ap.n_items,
                "n_passed": ap.n_passed,
                "n_unchecked": ap.n_unchecked,
                "ok": ok,
            })

            if ok:
                print(
                    f"  [OK] {sample_alias:14s} cap={len(cap):3d}c aud={len(aud)}r "
                    f"items={ap.n_items:>2d} {score:>4s} svg={len(svg)}c"
                )
                passed.append((sample_alias, chart_type))
            else:
                print(
                    f"  [LOW] {sample_alias:14s} items={ap.n_items:>2d} "
                    f"{score:>4s} -> {'; '.join(reasons)}"
                )
                failed.append((sample_alias, "; ".join(reasons)))
        except Exception as e:
            print(f"  [FAIL] {sample_alias:14s} -> {type(e).__name__}: {e}")
            failed.append((sample_alias, str(e)))
            results.append({
                "alias": sample_alias,
                "chart_type": chart_type,
                "score": None,
                "n_items": 0,
                "n_passed": 0,
                "n_unchecked": 0,
                "ok": False,
            })

    print()

    # v1.6.0: 按得分升序的汇总表（低分排最前，便于一眼定位弱样本）
    if results:
        ordered = sorted(
            results,
            key=lambda r: (
                r["score"] is None,                        # n/a 排最后
                r["score"] if r["score"] is not None else 0.0,
                r["alias"],
            ),
        )
        print("=== 汇总（按得分升序）===")
        print(
            f"  {'样本':<15}{'类型':<15}{'得分':>6}{'条目':>6}"
            f"{'通过':>6}{'未评':>6}   状态"
        )
        print("  " + "-" * 62)
        for r in ordered:
            s = f"{r['score']*100:.0f}%" if r["score"] is not None else "n/a"
            st = "OK" if r["ok"] else "LOW"
            print(
                f"  {r['alias']:<15}{r['chart_type']:<15}{s:>6}"
                f"{r['n_items']:>6}{r['n_passed']:>6}{r['n_unchecked']:>6}   {st}"
            )
        print()

    print(f"通过: {len(passed)}/{len(targets)}")
    if failed:
        print(f"失败: {len(failed)}")
        for sample_alias, err in failed:
            print(f"  - {sample_alias}: {err}")
    print(f"产物目录: {work_dir}")
    if getattr(args, "cleanup", False):
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)
        print("[cleanup] 已删除临时目录")
    return min(len(failed), 255)


def cmd_check(args: argparse.Namespace) -> int:
    """内部 smoke test：用一份最小数据走完整链路。"""
    sample = {
        "kaplan_meier": {
            "title": "OS by treatment",
            "hazard_ratio": 0.72,
            "hr_ci": [0.58, 0.89],
            "p_value": 0.003,
            "n_total": 480,
            "arms": [
                {"name": "Experimental", "median_survival": 19.6},
                {"name": "Control", "median_survival": 14.2},
            ],
            "at_risk": {"Experimental": [240, 220, 180, 120], "Control": [240, 200, 150, 90]},
            "schoenfeld_p": 0.42,
        },
        "forest_plot": {
            "title": "All-cause mortality",
            "measure": "OR",
            "model": "random",
            "i_squared": 32.5,
            "heterogeneity_p": 0.18,
            "overall_effect": 0.85,
            "overall_ci": [0.74, 0.98],
            "overall_p": 0.025,
            "studies": [
                {"name": "Study A", "effect": 0.78, "ci": [0.62, 0.98], "weight": 0.28, "n": 412},
                {"name": "Study B", "effect": 0.92, "ci": [0.71, 1.19], "weight": 0.30, "n": 380},
                {"name": "Study C", "effect": 0.83, "ci": [0.55, 1.25], "weight": 0.18, "n": 210},
                {"name": "Study D", "effect": 0.95, "ci": [0.74, 1.22], "weight": 0.24, "n": 305},
            ],
        },
        "roc_curve": {
            "title": "Diagnostic model",
            "auc": 0.86,
            "auc_ci": [0.81, 0.91],
            "optimal_cutoff": 0.45,
            "sensitivity": 0.82,
            "specificity": 0.78,
            "delong_p": 0.012,
        },
    }

    print("=== interpret: KM ===")
    print(json.dumps(PARSERS["kaplan_meier"].parse(sample["kaplan_meier"]).to_dict(), ensure_ascii=False, indent=2))
    print("\n=== interpret: Forest ===")
    print(json.dumps(PARSERS["forest_plot"].parse(sample["forest_plot"]).to_dict(), ensure_ascii=False, indent=2))
    print("\n=== caption (Nature, EN) ===")
    print(generate_caption(PARSERS["roc_curve"].parse(sample["roc_curve"]), style="nature", language="en"))
    print("\n=== audiences (Forest, ZH) ===")
    print(render_all(PARSERS["forest_plot"].parse(sample["forest_plot"]))["clinicians"])
    print("\n=== appraise: KM ===")
    res = auto_evaluate(PARSERS["kaplan_meier"].parse(sample["kaplan_meier"]))
    print(f"框架={res.framework}，已评估={res.n_passed + res.n_failed}，得分={res.overall_score}")
    print("\n=== svg: KM ===")
    km_svg = render_km(sample["kaplan_meier"], title="OS by treatment")
    print(f"KM SVG 长度: {len(km_svg)} 字符")
    print("\n=== svg: Forest ===")
    fp_svg = render_forest(sample["forest_plot"], title="All-cause mortality")
    print(f"Forest SVG 长度: {len(fp_svg)} 字符")
    print("\n=== svg: ROC ===")
    roc_svg = render_roc(sample["roc_curve"], title="Diagnostic model")
    print(f"ROC SVG 长度: {len(roc_svg)} 字符")
    print("\n=== ocr (text mode) ===")
    sample_text = "HR=0.72 (95% CI 0.58-0.89), p=0.003, N=480. I²=32%."
    print(json.dumps(extract_from_text(sample_text), ensure_ascii=False, indent=2))
    print("\n=== ocr (pdf mode) ===")
    pdf_sample = Path(__file__).with_name("figure_sample.pdf")
    if pdf_sample.exists():
        try:
            pdf_res = extract_from_pdf(str(pdf_sample))
            print(f"  pages={pdf_res.get('_pdf_pages')}, hr={pdf_res.get('hazard_ratio')}, p={pdf_res.get('p_value')}, inferred={pdf_res.get('_inferred_chart_type')}")
        except RuntimeError as e:
            print(f"  [skip] pdfplumber 不可用: {e}")
    else:
        print(f"  [skip] {pdf_sample} 不存在；先跑 make_sample_pdf.py 生成")
    print("\n[check] 全部通过 ✓")
    return 0


# ---------- 入口 ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="graph-interpretation",
        description="医学科研图表解读 v1.6.0（pip install . 后调用 graph-interp）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # interpret
    sp = sub.add_parser("interpret", help="解析图表数据为结构化统计摘要")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.set_defaults(func=cmd_interpret)

    # caption
    sp = sub.add_parser("caption", help="生成期刊风格图注")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--style", default="generic", choices=list_styles())
    sp.add_argument("--language", default="en", choices=["en", "zh"])
    sp.add_argument("--figure-id", default="Figure 1")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_caption)

    # audiences
    sp = sub.add_parser("audiences", help="生成多受众解读")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--locale", default="en", help='受众语境，默认 "en"；传 "zh_CN" 加入中国语境')
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_audiences)

    # appraise
    sp = sub.add_parser("appraise", help="批判性评价 checklist")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_appraise)

    # all (v1.3.0): 一次输出 interpret + caption + audiences + appraisal 四档 JSON
    sp = sub.add_parser("all", help="一次性输出四档产物（interpret + caption + audiences + appraisal）")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--style", default="generic", choices=list_styles())
    sp.add_argument("--language", default="en", choices=["en", "zh"])
    sp.add_argument("--locale", default="en", help='受众语境："en" / "zh_CN"')
    sp.add_argument("--figure-id", default="Figure 1")
    sp.add_argument("--out", help="JSON 输出文件路径")
    sp.set_defaults(func=cmd_all)

    # export-csv (v1.4.0): 把 TRIPOD-AI 14 条评价导出为 CSV（Excel 中文友好）
    sp = sub.add_parser("export-csv", help="导出 TRIPOD-AI 14 条评价为 CSV")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--out", default="tripod_ai.csv", help="CSV 输出路径（默认 tripod_ai.csv）")
    sp.add_argument("--no-bom", action="store_true", help="不加 UTF-8 BOM（默认有 BOM 便于 Excel 中文）")
    sp.set_defaults(func=cmd_export_csv)

    # render-svg
    RENDERABLE = {
        "km", "kaplan_meier",
        "forest", "forest_plot",
        "roc", "roc_curve",
        "box", "box_plot",
        "scatter", "scatter_plot",
        "bar", "bar_chart",
        "heatmap",
        "volcano", "volcano_plot",
    }
    sp = sub.add_parser("render-svg", help="8 类图表数据 → SVG")
    sp.add_argument("--type", required=True, choices=sorted(RENDERABLE))
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--title", default="")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_render_svg)

    # ocr
    sp = sub.add_parser("ocr", help="图像 / PDF / 文本 → 关键统计量")
    sp.add_argument("--image", help="PNG/JPG 图像路径（用 pytesseract）")
    sp.add_argument("--pdf", help="PDF 文件路径（用 pdfplumber 矢量抽取）")
    sp.add_argument("--text", help="直接给文本（兜底）")
    sp.set_defaults(func=cmd_ocr)

    # to-legend：导出 figure-legend-gen 可消费的桥接字段（含 .docx 端到端）
    sp = sub.add_parser("to-legend", help="导出 figure-legend-gen 桥接字段（支持 .docx）")
    sp.add_argument("--type", required=True)
    sp.add_argument("--data")
    sp.add_argument("--inline")
    sp.add_argument("--style", default="generic")
    sp.add_argument("--language", default="en")
    sp.add_argument("--figure-id", default="Figure 1")
    sp.add_argument("--mode", default="context", choices=["context", "fields", "docx", "html"])
    sp.add_argument("--figure-number", default="1")
    sp.add_argument("--with-svg", action="store_true",
                    help="(v1.2.0) 自动把数据渲染为 SVG 并嵌入 .docx")
    sp.add_argument("--svg-width", type=float, default=6.0,
                    help="(v1.2.0) 嵌入 docx 的 SVG/PNG 宽度（英寸）")
    sp.add_argument("--print-md", action="store_true",
                    help="同时把 markdown 图注打到 stdout")
    sp.add_argument("--out")
    sp.add_argument("--ai-sentinel", default="auto",
                    choices=["auto", "force", "off"],
                    help="(v1.5.0) TRIPOD-AI sentinel docx：auto=自动检测 force=强制 off=关闭")
    sp.add_argument("--theme", default="auto", choices=["auto", "light", "dark"],
                    help="(v1.6.0) HTML 报告主题：auto=跟随系统 light/dark=强制")
    sp.set_defaults(func=cmd_to_legend)

    # check
    sp = sub.add_parser("check", help="跑通全部子命令的 smoke test")
    sp.set_defaults(func=cmd_check)

    # demo (v1.5.0): 跑通 bundled samples 的 demo 链路
    sp = sub.add_parser("demo", help="(v1.5.0) 跑通 bundled samples 的端到端 demo")
    sp.add_argument("--type", help="指定单个 sample alias（km/forest/roc_ml/csco_km 等）")
    sp.add_argument("--out-dir", default="", help="(deep 模式) docx 输出目录")
    sp.set_defaults(func=cmd_demo)

    # verify (v1.5.0): 端到端全样本自检（CI 友好）
    sp = sub.add_parser("verify", help="(v1.5.0) 端到端跑通所有 bundled samples（CI 自检）")
    sp.add_argument("--no-ml", action="store_true", help="不跑 ML 场景（默认包含 roc_ml）")
    sp.add_argument("--no-zh", action="store_true", help="不跑中文期刊场景（默认包含 csco_km）")
    sp.add_argument("--work-dir", default=".verify_tmp", help="docx 产物目录")
    sp.add_argument("--cleanup", action="store_true", help="完成后删除产物目录")
    sp.add_argument("--fail-on-low-score", type=float, default=None, metavar="F",
                    help="(v1.6.0) 得分低于 F（0-1，如 0.6）判为失败")
    sp.add_argument("--fail-on-missing", type=int, default=None, metavar="N",
                    help="(v1.6.0) 未评估条目数超过 N 判为失败")
    sp.set_defaults(func=cmd_verify)

    # validate (v1.5.0): JSON Schema 校验
    # diff (v1.6.0): 两版评价结果差异对比
    sp = sub.add_parser(
        "diff", help="(v1.6.0) 对比两份数据的评价结果差异（文件 / sample 名均可）"
    )
    sp.add_argument("a", help="基线（旧版）：JSON 文件路径或 bundled sample 名")
    sp.add_argument("b", help="对比（新版）：JSON 文件路径或 bundled sample 名")
    sp.add_argument("--type", help="强制指定图表类型（两侧 chart_type 缺失时用）")
    sp.add_argument(
        "--format", default="table", choices=["table", "markdown", "json"],
        help="输出格式（默认 table）",
    )
    sp.add_argument("--verbose", action="store_true", help="一并列出未变化条目")
    sp.set_defaults(func=cmd_diff)

    sp = sub.add_parser("validate", help="(v1.5.0) JSON Schema 校验或查看 schema 定义")
    sp.add_argument("--data", help="待校验 JSON 文件路径")
    sp.add_argument("--inline", help="直接传 JSON 字符串")
    sp.add_argument("--type", help="指定 schema 名（默认从 data['chart_type'] 推断）")
    sp.add_argument("--show-schema", help="仅打印指定 schema 的 JSON Schema 定义，不做校验")
    sp.add_argument("--list-schemas", action="store_true", help="列出所有支持的 schema")
    sp.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
