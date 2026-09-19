#!/usr/bin/env python3
"""报告自我批判叙述生成器 v1.0

从结构化「研究设计属性」规则化生成 strengths / limitations / applicability 叙述段落，
并合成一段批判性评价小结。规则化、best-effort，产出为可编辑模板（最终判断仍需人工）。
零第三方依赖。

用法：
    python self_critique.py study.json [--out critique.md]
    python self_critique.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def build(d: dict) -> dict:
    strengths, limitations = [], []

    if d.get("randomization"):
        strengths.append("采用随机化分配，降低选择偏倚。")
    else:
        limitations.append("未说明随机化（或非随机），选择偏倚风险需关注。")

    blinding = d.get("blinding")
    if blinding and blinding not in ("无", "none", "开放"):
        strengths.append(f"实施{blinding}，降低测量偏倚与绩效偏倚。")
    elif blinding in ("无", "none", "开放"):
        limitations.append("未设盲，测量/绩效偏倚风险升高。")

    if d.get("allocation_concealment"):
        strengths.append("分配隐藏到位，进一步减少选择偏倚。")

    if d.get("intention_to_treat"):
        strengths.append("采用意向性分析（ITT），减少随访与退出带来的偏倚。")

    n = d.get("sample_size")
    if d.get("power_adequate") or (isinstance(n, int) and n and n >= 200):
        strengths.append(f"样本量充分（n={n}），统计检验效能较充足。" if n else "样本量充分，统计检验效能较充足。")
    elif isinstance(n, int) and n and n < 100:
        limitations.append(f"样本量偏小（n={n}），检验效能可能不足。")

    fu = d.get("loss_to_followup")
    try:
        fu_num = float(str(fu).rstrip("%"))
    except ValueError:
        fu_num = None
    if fu_num is not None and fu_num > 10:
        limitations.append(f"失访率偏高（{fu}），可能引入随访偏倚。")

    het = d.get("heterogeneity")
    if het:
        import re
        m = re.search(r"I[\s²2]*\s*[=:]?\s*(\d+)", str(het), re.IGNORECASE)
        if m and int(m.group(1)) > 50:
            limitations.append(f"异质性较高（{het}），合并效应解释需谨慎。")

    if d.get("multi_center"):
        strengths.append("多中心设计，人群代表性较好，外推性较强。")
    elif d.get("single_center"):
        limitations.append("单中心设计，外推至其他人群/机构需谨慎。")

    if d.get("confounders_controlled"):
        strengths.append("控制了主要混杂因素，因果推断更可靠。")

    if d.get("industry_funding"):
        limitations.append("研究受行业资助，需警惕利益冲突与发表偏倚。")

    # 用户显式给出的局限性
    for item in d.get("key_limitations", []) or []:
        limitations.append(str(item))

    # 适用性
    appl = []
    if d.get("multi_center"):
        appl.append("多中心样本提升结果向相似医疗环境外推的把握。")
    else:
        appl.append("外推性受研究人群与机构限制，临床落地应结合本地数据。")
    pop = d.get("population_note")
    if pop:
        appl.append(f"适用人群：{pop}。")
    if d.get("generalizability_note"):
        appl.append(str(d.get("generalizability_note")))

    return {"strengths": strengths, "limitations": limitations, "applicability": appl}


def render_markdown(d: dict, crit: dict) -> str:
    title = d.get("title", "研究报告自我批判")
    lines = [
        f"# 研究质量自我批判：{title}",
        "",
        f"**设计**：{d.get('design', '—')}　**样本量**：{d.get('sample_size', '—')}　"
        f"**随访**：{d.get('follow_up', '—')}",
        "",
        "## 优势 (Strengths)",
        "",
    ]
    lines += [f"- {s}" for s in crit["strengths"]] or ["- （未检测到明确优势字段，请人工补充）"]
    lines += ["", "## 局限 (Limitations)", ""]
    lines += [f"- {l}" for l in crit["limitations"]] or ["- （未检测到明确局限字段，请人工补充）"]
    lines += ["", "## 适用性 (Applicability / 外部真实性)", ""]
    lines += [f"- {a}" for a in crit["applicability"]]
    lines += [
        "",
        "## 批判性评价小结（可编辑模板）",
        "",
        f"本研究为{d.get('design','—')}设计，主要优势在于" +
        ("、".join(crit['strengths'][:2]) if crit['strengths'] else "（待补充）") +
        "；需关注的局限包括" +
        ("、".join(crit['limitations'][:2]) if crit['limitations'] else "（待补充）") +
        "。综合判断证据可用性" +
        ("较好" if len(crit['strengths']) > len(crit['limitations']) else "需结合更多证据") +
        "，临床应用前建议结合指南与个体情况。",
        "",
        "> 本模板由 `self_critique.py` 规则化生成，最终质量判断须由具备方法学训练的人员确认。",
    ]
    return "\n".join(lines)


def run(data: dict, out: Path | None) -> dict:
    crit = build(data)
    md = render_markdown(data, crit)
    if out:
        out.write_text(md + "\n", encoding="utf-8")
    else:
        print(md)
    return {"ok": True, "strengths": len(crit["strengths"]),
            "limitations": len(crit["limitations"]), "applicability": len(crit["applicability"])}


def _self_test() -> int:
    good = {
        "title": "他汀二级预防 RCT", "design": "RCT", "randomization": True,
        "blinding": "双盲", "allocation_concealment": True, "sample_size": 480,
        "power_adequate": True, "follow_up": "中位 24 月", "loss_to_followup": "6%",
        "multi_center": True, "intention_to_treat": True, "confounders_controlled": True,
        "industry_funding": False, "population_note": "中高危成人",
    }
    bad = {
        "title": "单中心观察", "design": "回顾性队列", "randomization": False,
        "blinding": "无", "single_center": True, "sample_size": 60,
        "industry_funding": True, "key_limitations": ["未校正关键混杂"],
    }
    r_good = run(good, None)
    r_bad = run(bad, None)
    good_ok = r_good["ok"] and r_good["strengths"] >= 4 and r_good["limitations"] <= 1
    bad_ok = r_bad["ok"] and r_bad["limitations"] >= 3  # 应含：非随机/未设盲/单中心/行业资助/显式局限
    print(f"[self-test] good strengths={r_good['strengths']} limits={r_good['limitations']} -> {'PASS' if good_ok else 'FAIL'}")
    print(f"[self-test] bad limits={r_bad['limitations']} -> {'PASS' if bad_ok else 'FAIL'}")
    return 0 if (good_ok and bad_ok) else 1


def main() -> int:
    p = argparse.ArgumentParser(description="报告自我批判叙述生成器")
    p.add_argument("json_path", nargs="?", help="研究设计属性 JSON")
    p.add_argument("--out", help="Markdown 输出路径")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return _self_test()
    if not args.json_path:
        p.error("json_path 必填（或用 --self-test）")
    data = json.loads(read_text(Path(args.json_path).expanduser().resolve()))
    run(data, Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
