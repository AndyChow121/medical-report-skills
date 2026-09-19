#!/usr/bin/env python3
"""PRISMA 2020 流程图生成器 v1.0

从结构化 JSON 生成标准 PRISMA 检索漏斗流程图（SVG，手工绘制，无 cairosvg 依赖）
+ Markdown 文本漏斗。零第三方依赖。

用法：
    python prisma_flow.py prisma.json [--out flow.svg] [--md flow.md]
    python prisma_flow.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FONT = "'Microsoft YaHei', 'PingFang SC', sans-serif"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _box(x, y, w, h, fill, stroke="#2b4a6f"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')


def _text(x, y, s, size=15, anchor="middle", color="#1a1a1a", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-family={FONT!r} font-size="{size}" '
            f'text-anchor="{anchor}" fill="{color}" font-weight="{weight}">{s}</text>')


def _arrow(x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#555" '
            f'stroke-width="1.5" marker-end="url(#ah)"/>')


def render_svg(data: dict) -> str:
    db = data.get("identified", {}).get("databases", 0)
    reg = data.get("identified", {}).get("registers", 0)
    dedup = data.get("deduplicated", 0)
    ta_excl = data.get("title_abstract_excluded", 0)
    sought = data.get("fulltext_sought", 0)
    not_ret = data.get("fulltext_not_retrieved", 0)
    assessed = data.get("fulltext_assessed", 0)
    ft_excl = data.get("fulltext_excluded", 0)
    reasons = data.get("fulltext_excluded_reasons", {})
    inc_q = data.get("included_qualitative", 0)
    inc_m = data.get("included_quantitative", 0)

    W, H = 900, 820
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family={FONT!r}>',
        '<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,3 L0,6 Z" fill="#555"/></marker></defs>',
        _text(450, 32, data.get("title", "PRISMA 2020 流程图"), 20, "middle", "#1a1a1a", "bold"),
    ]

    # 中央主流程列 x=250 w=400
    cx, cw = 250, 400
    # 1) 识别
    parts.append(_box(cx, 60, cw, 60, "#dbe9f4"))
    parts.append(_text(cx + cw / 2, 82, "识别记录", 16, "middle", "#1a1a1a", "bold"))
    parts.append(_text(cx + cw / 2, 105, f"数据库检索 {db} ＋ 其他来源 {reg} ＝ 共 {db + reg}", 14))
    # 2) 去重后
    parts.append(_arrow(cx + cw / 2, 120, cx + cw / 2, 150))
    parts.append(_box(cx, 150, cw, 55, "#dbe9f4"))
    parts.append(_text(cx + cw / 2, 172, "去重后记录", 16, "middle", "#1a1a1a", "bold"))
    parts.append(_text(cx + cw / 2, 193, f"{dedup}", 14))
    # 3) 标题摘要筛选
    parts.append(_arrow(cx + cw / 2, 205, cx + cw / 2, 235))
    parts.append(_box(cx, 235, cw, 55, "#e3f0d8"))
    parts.append(_text(cx + cw / 2, 257, "标题/摘要筛选", 16, "middle", "#1a1a1a", "bold"))
    parts.append(_text(cx + cw / 2, 278, f"排除 {ta_excl} → 剩余 {dedup - ta_excl}", 14))
    # 4) 全文评估
    parts.append(_arrow(cx + cw / 2, 290, cx + cw / 2, 320))
    parts.append(_box(cx, 320, cw, 55, "#fdf0d5"))
    parts.append(_text(cx + cw / 2, 342, "全文评估", 16, "middle", "#1a1a1a", "bold"))
    parts.append(_text(cx + cw / 2, 363, f"寻求检索 {sought}，未获取 {not_ret}，评估 {assessed}", 13))
    # 5) 纳入
    parts.append(_arrow(cx + cw / 2, 375, cx + cw / 2, 405))
    parts.append(_box(cx, 405, cw, 70, "#f6d9d5"))
    parts.append(_text(cx + cw / 2, 430, "纳入研究", 16, "middle", "#1a1a1a", "bold"))
    parts.append(_text(cx + cw / 2, 453, f"定性综合 {inc_q}", 14))
    parts.append(_text(cx + cw / 2, 472, f"定量综合(Meta) {inc_m}", 14))

    # 右侧排除原因块
    rx, rw = 690, 190
    parts.append(_box(rx, 235, rw, 55, "#f4f4f4"))
    parts.append(_text(rx + rw / 2, 257, "排除(标题/摘要)", 14, "middle", "#a33", "bold"))
    parts.append(_text(rx + rw / 2, 278, f"{ta_excl}", 14))
    parts.append(_box(rx, 320, rw, 75, "#f4f4f4"))
    parts.append(_text(rx + rw / 2, 342, "排除(全文)", 14, "middle", "#a33", "bold"))
    parts.append(_text(rx + rw / 2, 363, f"{ft_excl}", 14))
    ry = 385
    for k, v in reasons.items():
        parts.append(_text(rx + 8, ry + 16, f"· {k}: {v}", 12, "start", "#a33"))
        ry += 18
    parts.append(_arrow(cx + cw, 262, rx, 262))
    parts.append(_arrow(cx + cw, 347, rx, 347))

    parts.append('</svg>')
    return "\n".join(parts)


def render_markdown(data: dict) -> str:
    db = data.get("identified", {}).get("databases", 0)
    reg = data.get("identified", {}).get("registers", 0)
    dedup = data.get("deduplicated", 0)
    ta_excl = data.get("title_abstract_excluded", 0)
    assessed = data.get("fulltext_assessed", 0)
    ft_excl = data.get("fulltext_excluded", 0)
    reasons = data.get("fulltext_excluded_reasons", {})
    inc_q = data.get("included_qualitative", 0)
    inc_m = data.get("included_quantitative", 0)
    lines = [
        f"# {data.get('title', 'PRISMA 2020 流程图')}",
        "",
        f"- 识别记录：数据库 {db} ＋ 其他 {reg} ＝ **{db + reg}**",
        f"- 去重后记录：**{dedup}**",
        f"- 标题/摘要筛选：排除 {ta_excl}，剩余 {dedup - ta_excl}",
        f"- 全文评估：{assessed}（排除全文 {ft_excl}）",
    ]
    if reasons:
        lines.append("  - 全文排除原因：")
        for k, v in reasons.items():
            lines.append(f"    - {k}: {v}")
    lines += [
        f"- 纳入：定性综合 **{inc_q}**，定量综合(Meta) **{inc_m}**",
        "",
        "> 流程图 SVG 由 `prisma_flow.py` 生成，遵循 PRISMA 2020 四阶段检索漏斗。",
    ]
    return "\n".join(lines)


def run(data: dict, out_svg: Path | None, out_md: Path | None) -> dict:
    svg = render_svg(data)
    md = render_markdown(data)
    if out_svg:
        out_svg.write_text(svg + "\n", encoding="utf-8")
    if out_md:
        out_md.write_text(md + "\n", encoding="utf-8")
    if out_svg is None and out_md is None:
        print(md)
    return {"ok": True, "svg_bytes": len(svg), "md": md}


def _self_test() -> int:
    sample = {
        "title": "示例系统评价 PRISMA",
        "identified": {"databases": 1234, "registers": 56},
        "deduplicated": 1100,
        "title_abstract_excluded": 980,
        "fulltext_sought": 120, "fulltext_not_retrieved": 10, "fulltext_assessed": 110,
        "fulltext_excluded": 25, "fulltext_excluded_reasons": {"不可得全文": 5, "不符合纳入": 20},
        "included_qualitative": 85, "included_quantitative": 80,
    }
    # 跑两次：一次落盘 svg 验证可写、一次纯打印
    tmp = Path("__prisma_selftest.svg")
    res = run(sample, tmp, None)
    written_ok = tmp.is_file() and tmp.stat().st_size > 500 and "<svg" in tmp.read_text(encoding="utf-8")
    tmp.unlink(missing_ok=True)
    md_ok = "识别记录" in res["md"] and "纳入" in res["md"]
    print(f"[self-test] svg generated={written_ok} -> {'PASS' if written_ok else 'FAIL'}")
    print(f"[self-test] markdown ok={md_ok} -> {'PASS' if md_ok else 'FAIL'}")
    return 0 if (written_ok and md_ok) else 1


def main() -> int:
    p = argparse.ArgumentParser(description="PRISMA 2020 流程图生成器")
    p.add_argument("json_path", nargs="?", help="PRISMA 数据 JSON")
    p.add_argument("--out", help="SVG 输出路径")
    p.add_argument("--md", help="Markdown 漏斗输出路径")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return _self_test()
    if not args.json_path:
        p.error("json_path 必填（或用 --self-test）")
    data = json.loads(read_text(Path(args.json_path).expanduser().resolve()))
    run(data, Path(args.out) if args.out else None, Path(args.md) if args.md else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
