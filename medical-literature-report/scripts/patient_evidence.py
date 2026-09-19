#!/usr/bin/env python3
"""患者导向证据换算器 v1.0 (NNT / NNH / ARR / RRR)

把相对效应(HR/RR/OR)与事件率翻译成患者能懂的绝对获益/伤害：
ARR 绝对风险降低、RRR 相对风险降低、NNT 需治疗人数、NNH 需伤害人数、
每 1000 人绝对差异、患者友好表述。零第三方依赖。

用法：
    python patient_evidence.py --cer 0.096 --eer 0.091 --event 死亡 --intervention 他汀
    python patient_evidence.py --cer 0.10 --rr 0.80 --event 死亡
    python patient_evidence.py data.json
    python patient_evidence.py --self-test
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


def derive_eer(cer: float, rr: float | None, orr: float | None, hr: float | None) -> tuple[float | None, str]:
    """由 rr/or/hr 推导 eer，返回 (eer, 说明)。"""
    note = ""
    if rr is not None:
        return cer * rr, "由 RR 推导 EER = CER×RR"
    if orr is not None:
        r = orr / (1 - cer + orr * cer)  # OR→RR (需 CER)
        return cer * r, "由 OR 经 CER 近似为 RR 再推导 EER"
    if hr is not None:
        note = "HR 按 RR 近似处理（时间-事件终点，仅近似）"
        return cer * hr, note
    return None, note


def compute(cer: float, eer: float | None, event: str, intervention: str, derived_note: str = "") -> dict:
    if eer is None:
        return {"ok": False, "error": "缺少 EER，且未提供 rr/or/hr 用于推导"}
    arr = cer - eer
    is_benefit = arr > 0
    rrr = (arr / cer) if cer > 0 else 0.0
    if is_benefit:
        nnt = (1 / arr) if arr > 0 else float("inf")
        metric = "NNT(需治疗人数)"
        n_value = nnt
        per1000 = arr * 1000
        friendly = (
            f"与对照组相比，接受{intervention}约每 {nnt:.0f} 人可多避免 1 例{event}；"
            f"每 1000 人治疗可多避免约 {per1000:.0f} 例。绝对获益"
            f"{'较大' if per1000 >= 20 else ('中等' if per1000 >= 5 else '较小')}，请结合个人情况与医生讨论。"
        )
    else:
        ari = -arr
        nnh = (1 / ari) if ari > 0 else float("inf")
        metric = "NNH(需伤害人数)"
        n_value = nnh
        per1000 = ari * 1000
        friendly = (
            f"与对照组相比，接受{intervention}约每 {nnh:.0f} 人会多发生 1 例{event}；"
            f"每 1000 人治疗会多发生约 {per1000:.0f} 例。属潜在伤害，需权衡利弊。"
        )
    return {
        "ok": True,
        "cer": cer, "eer": eer, "arr": arr, "rrr": rrr,
        "is_benefit": is_benefit, "metric": metric, "n_value": n_value,
        "per_1000": per1000, "friendly": friendly,
        "derived_note": derived_note,
    }


def render_markdown(d: dict) -> str:
    if not d.get("ok"):
        return f"# 患者导向证据换算\n\n❌ {d.get('error')}"
    lines = [
        "# 患者导向证据换算（NNT / NNH）",
        "",
        f"- 结局：**{d.get('event','事件')}**",
        f"- 对照组事件率 (CER)：{d['cer']*100:.1f}%",
        f"- 干预组事件率 (EER)：{d['eer']*100:.1f}%",
        f"- 绝对风险降低 (ARR)：{d['arr']*100:.1f} 个百分点",
        f"- 相对风险降低 (RRR)：{d['rrr']*100:.1f}%",
        f"- **{d['metric']}：{d['n_value']:.0f}**",
        f"- 每 1000 人绝对差异：{d['per_1000']:.0f} 例",
    ]
    if d.get("derived_note"):
        lines.append(f"- 推导说明：{d['derived_note']}")
    lines += [
        "",
        f"> 患者友好表述：{d['friendly']}",
        "",
        "> NNT/NNH 为决策辅助工具，具体治疗请结合临床情境、患者偏好与指南。",
    ]
    return "\n".join(lines)


def run(cer: float, eer: float | None, rr, orr, hr, event: str, intervention: str, out: Path | None) -> dict:
    derived = ""
    if eer is None:
        eer, derived = derive_eer(cer, rr, orr, hr)
    d = compute(cer, eer, event, intervention, derived)
    md = render_markdown(d)
    if out:
        out.write_text(md + "\n", encoding="utf-8")
    else:
        print(md)
    return d


def _self_test() -> int:
    # 获益示例：CER=0.10, RR=0.80 -> EER=0.08, ARR=0.02, RRR=0.20, NNT=50
    r1 = run(0.10, None, 0.80, None, None, "死亡", "他汀", None)
    nnt_ok = r1.get("ok") and abs(r1["n_value"] - 50) < 1 and r1["is_benefit"]
    # 伤害示例：CER=0.05, EER=0.06 -> ARI=0.01, NNH=100
    r2 = run(0.05, 0.06, None, None, None, "肌病", "他汀", None)
    nnh_ok = r2.get("ok") and (not r2["is_benefit"]) and abs(r2["n_value"] - 100) < 1
    # OR 推导示例：CER=0.20, OR=0.5
    r3 = run(0.20, None, None, 0.5, None, "事件", "药", None)
    or_ok = r3.get("ok") and r3["is_benefit"]
    print(f"[self-test] NNT derive ok={nnt_ok} (n={r1.get('n_value')}) -> {'PASS' if nnt_ok else 'FAIL'}")
    print(f"[self-test] NNH ok={nnh_ok} (n={r2.get('n_value')}) -> {'PASS' if nnh_ok else 'FAIL'}")
    print(f"[self-test] OR derive ok={or_ok} -> {'PASS' if or_ok else 'FAIL'}")
    return 0 if (nnt_ok and nnh_ok and or_ok) else 1


def main() -> int:
    p = argparse.ArgumentParser(description="患者导向证据换算器 (NNT/NNH)")
    p.add_argument("json_path", nargs="?", help="可选 JSON（含 cer/eer/rr/or/hr/event/intervention）")
    p.add_argument("--cer", type=float, help="对照组事件率 (0-1)")
    p.add_argument("--eer", type=float, help="干预组事件率 (0-1)")
    p.add_argument("--rr", type=float, help="相对危险度 RR")
    p.add_argument("--or", dest="orr", type=float, help="比值比 OR")
    p.add_argument("--hr", type=float, help="风险比 HR（按 RR 近似）")
    p.add_argument("--event", default="事件", help="结局名称（患者友好表述用）")
    p.add_argument("--intervention", default="该干预", help="干预名称")
    p.add_argument("--out", help="Markdown 输出路径")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return _self_test()
    cer = args.cer
    if args.json_path:
        data = json.loads(read_text(Path(args.json_path).expanduser().resolve()))
        cer = data.get("cer", cer)
        args.eer = data.get("eer", args.eer)
        args.rr = data.get("rr", args.rr)
        args.orr = data.get("or", args.orr)
        args.hr = data.get("hr", args.hr)
        args.event = data.get("event", args.event)
        args.intervention = data.get("intervention", args.intervention)
    if cer is None:
        p.error("需提供 --cer 或 JSON 中的 cer")
    run(cer, args.eer, args.rr, args.orr, args.hr, args.event, args.intervention,
        Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
