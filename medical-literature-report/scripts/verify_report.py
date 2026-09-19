#!/usr/bin/env python3
"""medical-literature-report 报告自检引擎 v1.0

把 SKILL.md 的「Completion Gate」中可机器化的条目变成可运行、可 CI、可自测的
质量关卡。零第三方依赖（仅 stdlib）：re / os / sys / json / zipfile / hashlib /
argparse / datetime / subprocess。

设计目标（与 graph-interpretation 的 verify 同源演进）：
- 可机器化的关卡全部自动跑；
- 需要人工视觉复核的项明确标注「需人工」，不假装有视觉能力；
- 输出 JSON（供 CI）+ Markdown（供人读）；
- --self-test 自带合成样本，证明关卡能区分「合格」与「踩雷」。

用法：
    python verify_report.py <report_dir> [--out report.json] [--format md|json]
                            [--fail-on-error] [--delegate-graphint]
    python verify_report.py --self-test
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

# --------------------------------------------------------------------------- #
# 文件定位：在 report_dir 内按候选名递归查找
# --------------------------------------------------------------------------- #

_LOCATORS = {
    "translation": ["*翻译*.md", "*translation*.md", "*中文转述*.md", "translation.md"],
    "appraisal": ["*评价*.md", "*appraisal*.md", "*批判*.md", "appraisal.md"],
    "fact_sheet": ["*fact*sheet*.md", "*事实表*.md", "*source*.md", "*原文*.md", "source_fact_sheet.md"],
    "figures": ["figures_interpretation.md", "*图解读*.md", "*provenance*.md", "*溯源*.md"],
    "candidate": ["*candidate*.md", "*候选*.md", "*比较表*.md", "candidate_table.md"],
    "pptx": ["*.pptx"],
    "package_inventory": ["package_inventory.json"],
}


def _glob_any(root: Path, patterns) -> list[Path]:
    found: list[Path] = []
    for pat in patterns:
        found.extend(root.rglob(pat))
    # 去重并排除自身产物
    seen, out = set(), []
    for p in found:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p)
    return out


def locate(root: Path) -> dict[str, Path | None]:
    result: dict[str, Path | None] = {}
    for key, patterns in _LOCATORS.items():
        hits = _glob_any(root, patterns)
        result[key] = hits[0] if hits else None
    return result


# --------------------------------------------------------------------------- #
# 文本读取（兼容 utf-8 / gbk）
# --------------------------------------------------------------------------- #

def read_text(path: Path) -> str:
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# 通用工具
# --------------------------------------------------------------------------- #

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


_FIG_REF = re.compile(r"(?:图|表|Figure|Table)\s*[-_]?\s*(\d+)", re.IGNORECASE)
_FIG_ID = re.compile(r"(?:图|表|Figure|Table)\s*[-_]?\s*(\d+)\b", re.IGNORECASE)


def cited_figure_ids(text: str) -> set[str]:
    return {m.group(1) for m in _FIG_REF.finditer(text)}


def pptx_text_and_media(pptx: Path) -> tuple[str, int, int]:
    """返回 (全部文本, 幻灯片数, 零字节媒体数)。"""
    text_parts: list[str] = []
    slides = 0
    zero_media = 0
    try:
        with zipfile.ZipFile(pptx) as archive:
            for name in archive.namelist():
                if re.match(r"^ppt/slides/slide\d+\.xml$", name):
                    slides += 1
                    data = archive.read(name).decode("utf-8", errors="replace")
                    text_parts.extend(re.findall(r"<a:t>(.*?)</a:t>", data, re.DOTALL))
                elif name.startswith("ppt/media/") and not name.endswith("/"):
                    info = archive.getinfo(name)
                    if info.file_size == 0:
                        zero_media += 1
    except Exception as exc:  # 损坏的 pptx
        return f"[PPTX_PARSE_ERROR: {exc}]", 0, 0
    return "\n".join(text_parts), slides, zero_media


def check_label(text: str, label: str) -> bool:
    return label in text


# --------------------------------------------------------------------------- #
# 关卡定义
# --------------------------------------------------------------------------- #

EVIDENCE_LABELS = ["原文结果", "中文转述", "作者解释", "外部证据", "延伸解读"]

# 证据规则启发式：在「解读/转述」文本里检测疑似越界表述
_OVERCLAIM_PATTERNS = [
    ("关联→因果", re.compile(r"(关联|相关|correlat|associat).{0,12}(导致|引起|造成|caus)")),
    ("显著→临床意义(无效应量)", re.compile(r"(具有临床意义|临床意义重大|临床获益显著).{0,30}(?!HR|OR|RR|MD|差|%|percent|倍)")),
    ("基础→临床推广", re.compile(r"(动物|细胞|体外|小鼠|大鼠|离体).{0,20}(可推广|适用于临床|临床转化|用于患者)")),
    ("单中心→普适", re.compile(r"(单中心|单机构|单一中心).{0,20}(普遍|广泛适用|外推|代表性好)")),
]

ML_KEYWORDS = re.compile(r"(XGBoost|LightGBM|CatBoost|Random ?Forest|神经网络|neural ?network|ResNet|Transformer|BERT|LogisticRegression|机器学习|深度学习|预测模型|prediction model|model_type)", re.IGNORECASE)


def gate_required_files(loc: dict, single_paper: bool) -> dict:
    missing = []
    if not loc["translation"]:
        missing.append("中文翻译/转述文档")
    if not loc["appraisal"]:
        missing.append("研究设计批判性评价文档")
    if not loc["fact_sheet"]:
        missing.append("原文事实表(source fact sheet)")
    if not loc["pptx"]:
        missing.append("汇报 PPTX")
    status = "pass" if not missing else ("warn" if single_paper and "候选文献比较表" in " ".join(missing) else "fail")
    # 候选表缺失仅 warn（单篇论文可无）
    if not loc["candidate"] and not single_paper:
        missing.append("候选文献比较表(多文献时建议提供)")
        status = "warn" if status == "pass" else status
    return {
        "id": "G1_required_files",
        "name": "必备交付物齐全",
        "status": status,
        "detail": "缺失: " + (", ".join(missing) if missing else "无") +
                  ("；单篇论文可不提供候选比较表。" if single_paper else ""),
    }


def gate_article_identity(fact_text: str) -> dict:
    has_doi = bool(re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", fact_text, re.IGNORECASE))
    has_pmid = bool(re.search(r"(PMID|PMCID)\s*[:：]?\s*\d{5,}", fact_text, re.IGNORECASE))
    has_design = bool(re.search(r"(RCT|随机|队列|病例对照|横断面|Meta|系统评价|诊断|交叉|自身前后|巢式)", fact_text, re.IGNORECASE))
    ok = has_doi or has_pmid
    detail = f"DOI/PMID: {'有' if has_doi or has_pmid else '无'}；研究设计标识: {'有' if has_design else '无'}"
    status = "pass" if ok and has_design else ("warn" if ok else "fail")
    return {"id": "G2_article_identity", "name": "文献身份/设计已核验", "status": status, "detail": detail}


def gate_provenance(translation_text: str, pptx_text: str, figures_path: Path | None) -> dict:
    cited = cited_figure_ids(translation_text) | cited_figure_ids(pptx_text)
    if not cited:
        return {"id": "G3_provenance", "name": "图表溯源完整", "status": "pass",
                "detail": "未在翻译/PPT 文本中检出图/表引用，无需溯源核对。"}
    if not figures_path:
        return {"id": "G3_provenance", "name": "图表溯源完整", "status": "fail",
                "detail": f"检出图/表引用 {sorted(cited)} 个，但缺少 figures_interpretation.md / provenance 文档，无法核对溯源。"}
    fig_text = read_text(figures_path)
    covered = {c for c in cited if c in fig_text}
    missing = cited - covered
    if not missing:
        return {"id": "G3_provenance", "name": "图表溯源完整", "status": "pass",
                "detail": f"引用的图/表编号 {sorted(cited)} 均能在图解读文档中找到对应条目。"}
    return {"id": "G3_provenance", "name": "图表溯源完整", "status": "fail",
            "detail": f"引用但未溯源: {sorted(missing)}；请在 figures_interpretation.md 补充这些图/表的来源(panel/table/附录)。"}


def gate_evidence_labels(translation_text: str) -> dict:
    present = [l for l in EVIDENCE_LABELS if check_label(translation_text, l)]
    missing = [l for l in EVIDENCE_LABELS if l not in present]
    has_inference = "延伸解读" in present
    if len(present) >= 4 and has_inference:
        status = "pass"
    elif has_inference:
        status = "warn"
    else:
        status = "fail"
    detail = f"已用标签: {present}；" + (f"缺: {missing}；" if missing else "") + \
             ("已显式分离「延伸解读」(推理)。" if has_inference else "❌未分离推理与原文结论。")
    return {"id": "G4_evidence_labels", "name": "证据标签/推理分离", "status": status, "detail": detail}


def gate_overclaim(text: str) -> dict:
    hits = []
    for name, pat in _OVERCLAIM_PATTERNS:
        m = pat.search(text)
        if m:
            snippet = text[max(0, m.start() - 15): m.end() + 15].replace("\n", " ")
            hits.append(f"{name}: …{snippet}…")
    status = "pass" if not hits else "warn"
    return {
        "id": "G5_evidence_rules",
        "name": "证据规则(越界表述)",
        "status": status,
        "detail": ("未检出越界表述。" if not hits else "疑似越界，需人工复核:\n- " + "\n- ".join(hits)),
    }


def gate_pptx(pptx: Path | None) -> dict:
    if not pptx:
        return {"id": "G6_pptx_integrity", "name": "PPTX 完整性与媒体", "status": "warn",
                "detail": "无 PPTX，跳过。"}
    text, slides, zero = pptx_text_and_media(pptx)
    if slides == 0:
        return {"id": "G6_pptx_integrity", "name": "PPTX 完整性与媒体", "status": "fail",
                "detail": "PPTX 无法解析或不含任何幻灯片。"}
    status = "pass" if zero == 0 else "fail"
    note = "；⚠️需人工视觉复核每页排版/溢出/对比度(本引擎无视觉能力)。"
    return {"id": "G6_pptx_integrity", "name": "PPTX 完整性与媒体", "status": status,
            "detail": f"幻灯片数={slides}，零字节媒体={zero}{note if status == 'pass' else '；存在损坏媒体，必须修复。'}"}


def gate_hashes(root: Path, loc: dict) -> dict:
    inv = loc["package_inventory"]
    if not inv:
        return {"id": "G7_hash_integrity", "name": "交付物哈希一致", "status": "warn",
                "detail": "未找到 package_inventory.json；建议先跑 package_deliverables.py 生成带哈希的交付清单再自检。"}
    try:
        data = json.loads(read_text(inv))
    except Exception as exc:
        return {"id": "G7_hash_integrity", "name": "交付物哈希一致", "status": "fail",
                "detail": f"package_inventory.json 解析失败: {exc}"}
    all_match = data.get("all_hashes_match", False)
    bad = [f["target"] for f in data.get("files", []) if not f.get("hash_match")]
    status = "pass" if all_match else "fail"
    detail = ("全部文件源-目标哈希一致。" if all_match else
              f"存在哈希不一致文件: {bad}；请重新打包。")
    return {"id": "G7_hash_integrity", "name": "交付物哈希一致", "status": status, "detail": detail}


def gate_ml_tripod(figures_path: Path | None, translation_text: str, appraisal_text: str) -> dict:
    combined = (read_text(figures_path) if figures_path else "") + translation_text + appraisal_text
    if not ML_KEYWORDS.search(combined):
        return {"id": "G8_ml_tripod_ai", "name": "ML 论文 TRIPOD-AI", "status": "pass",
                "detail": "未检出机器学习/预测模型论文特征，无需 TRIPOD-AI。"}
    has_tripod = bool(re.search(r"TRIPOD[- ]?AI", combined, re.IGNORECASE))
    if has_tripod:
        return {"id": "G8_ml_tripod_ai", "name": "ML 论文 TRIPOD-AI", "status": "pass",
                "detail": "检出 ML/预测模型且已包含 TRIPOD-AI 评价。"}
    return {"id": "G8_ml_tripod_ai", "name": "ML 论文 TRIPOD-AI", "status": "fail",
            "detail": "检出机器学习/预测模型关键词，但未见 TRIPOD-AI 14 项评价；ML 论文必须追加 TRIPOD-AI。"}


def gate_delegate_graphint(root: Path, figures_path: Path | None) -> dict:
    if not figures_path:
        return {"id": "G9_graphint", "name": "graph-interpretation 委托", "status": "pass",
                "detail": "无图解读产物，跳过委托。"}
    gi_main = Path.home() / ".workbuddy" / "skills" / "graph-interpretation" / "scripts" / "main.py"
    if not gi_main.is_file():
        return {"id": "G9_graphint", "name": "graph-interpretation 委托", "status": "warn",
                "detail": "未安装 graph-interpretation，跳过图解读级委托校验(不影响主关卡)。"}
    try:
        proc = subprocess.run(
            [sys.executable, str(gi_main), "verify", "--cleanup"],
            cwd=str(gi_main.parent), capture_output=True, text=True, timeout=120,
        )
        ok = proc.returncode == 0
        return {"id": "G9_graphint", "name": "graph-interpretation 委托", "status": "pass" if ok else "warn",
                "detail": ("graph-interpretation verify 通过。" if ok else
                           f"委托校验返回非 0: {proc.stderr[-300:] or proc.stdout[-300:]}")}
    except Exception as exc:
        return {"id": "G9_graphint", "name": "graph-interpretation 委托", "status": "warn",
                "detail": f"委托调用异常(不影响主关卡): {exc}"}


# --------------------------------------------------------------------------- #
# 编排
# --------------------------------------------------------------------------- #

def run_gates(root: Path, single_paper: bool, delegate: bool) -> list[dict]:
    loc = locate(root)
    translation_text = read_text(loc["translation"]) if loc["translation"] else ""
    appraisal_text = read_text(loc["appraisal"]) if loc["appraisal"] else ""
    fact_text = read_text(loc["fact_sheet"]) if loc["fact_sheet"] else ""
    pptx_text, _, _ = pptx_text_and_media(loc["pptx"]) if loc["pptx"] else ("", 0, 0)

    gates = [
        gate_required_files(loc, single_paper),
        gate_article_identity(fact_text),
        gate_provenance(translation_text, pptx_text, loc["figures"]),
        gate_evidence_labels(translation_text),
        gate_overclaim(translation_text + appraisal_text),
        gate_pptx(loc["pptx"]),
        gate_hashes(root, loc),
        gate_ml_tripod(loc["figures"], translation_text, appraisal_text),
    ]
    if delegate:
        gates.append(gate_delegate_graphint(root, loc["figures"]))
    return gates


_STATUS_WEIGHT = {"pass": 1.0, "warn": 0.5, "fail": 0.0}

_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}


def summarize(gates: list[dict]) -> dict:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for g in gates:
        counts[g["status"]] += 1
    total = len(gates)
    score = round(sum(_STATUS_WEIGHT[g["status"]] for g in gates) / total * 100) if total else 0
    return {"score": score, "total": total, "pass": counts["pass"],
            "warn": counts["warn"], "fail": counts["fail"],
            "overall": "pass" if counts["fail"] == 0 else "fail"}


def render_markdown(root: Path, gates: list[dict], summary: dict) -> str:
    lines = [
        f"# 医学文献解读报告 · 自检报告",
        f"",
        f"- 报告目录: `{root}`",
        f"- 生成时间: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 综合评分: **{summary['score']}/100** （通过 {summary['pass']} / 警告 {summary['warn']} / 失败 {summary['fail']}）",
        f"- 结论: {'✅ 通过（无失败项）' if summary['overall'] == 'pass' else '❌ 未通过（存在失败项，需修复）'}",
        f"",
        f"## 关卡明细",
        f"",
    ]
    for g in gates:
        lines.append(f"### {_ICON[g['status']]} {g['id']} — {g['name']}  [{g['status'].upper()}]")
        lines.append("")
        lines.append(g["detail"])
        lines.append("")
    lines.append("---")
    lines.append("说明：带 ⚠️ 的关卡为「需人工复核」或「建议项」，不阻断交付；带 ❌ 的关卡为硬性失败，必须修复后重新自检。")
    return "\n".join(lines)


def run_report(root: Path, single_paper: bool, delegate: bool, fmt: str, out: Path | None) -> dict:
    gates = run_gates(root, single_paper, delegate)
    summary = summarize(gates)
    payload = {
        "tool": "verify_report",
        "version": "1.0.0",
        "report_dir": str(root.resolve()),
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "checks": gates,
    }
    if out:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if fmt == "md":
        md = render_markdown(root, gates, summary)
        if out:
            out.with_suffix(".md").write_text(md + "\n", encoding="utf-8")
        print(md)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


# --------------------------------------------------------------------------- #
# 自测：合成「合格」与「踩雷」样本，证明关卡可区分
# --------------------------------------------------------------------------- #

def _self_test() -> int:
    import tempfile
    base = Path(tempfile.mkdtemp(prefix="mlr_selftest_"))

    # ---- 合格样本 ----
    good = base / "good"
    good.mkdir()
    (good / "source_fact_sheet.md").write_text(
        "DOI: 10.1001/jama.2024.1234\nPMID: 12345678\n研究设计: 多中心随机双盲 RCT\n"
        "HR=0.72 (95% CI 0.58-0.89), p=0.003, N=480", encoding="utf-8")
    (good / "translation.md").write_text(
        "【原文结果】实验组 OS 优于对照组。\n【中文转述】HR=0.72。\n"
        "【作者解释】机制可能为…\n【外部证据】既往研究一致。\n"
        "【延伸解读】本研究提示临床可谨慎采纳(推理)。\n参见 图1、表2。", encoding="utf-8")
    (good / "appraisal.md").write_text("采用 CONSORT 对 RCT 进行评价。", encoding="utf-8")
    (good / "figures_interpretation.md").write_text(
        "Figure 1: KM 曲线，HR=0.72。\nTable 2: 亚组分析。\nTRIPOD-AI 未触发(非 ML)。", encoding="utf-8")
    # 最小合法 pptx（zip + 一个 slide xml 含 <a:t>）
    _make_min_pptx(good / "report.pptx", ["图1 结果", "表2 亚组"])

    # ---- 踩雷样本 ----
    bad = base / "bad"
    bad.mkdir()
    (bad / "translation.md").write_text(
        "本研究关联指标 A 与结局 B，表明 A 导致 B 发生(因果)。\n"
        "动物实验显示该通路，可推广至临床患者。", encoding="utf-8")
    # 缺 fact_sheet / appraisal / pptx / figures
    # pptx 引用图3 但无溯源
    _make_min_pptx(bad / "report.pptx", ["见图3 结果"])

    good_res = run_report(good, single_paper=True, delegate=False, fmt="json", out=None)
    bad_res = run_report(bad, single_paper=True, delegate=False, fmt="json", out=None)

    good_ok = good_res["summary"]["fail"] == 0
    # bad 至少应 fail: 缺必备文件 + 溯源缺失 + 越界表述 + 无 identity
    bad_ok = bad_res["summary"]["fail"] >= 3

    print(f"[self-test] good fails={good_res['summary']['fail']} -> {'PASS' if good_ok else 'FAIL'}")
    print(f"[self-test] bad  fails={bad_res['summary']['fail']} -> {'PASS' if bad_ok else 'FAIL'}")
    return 0 if (good_ok and bad_ok) else 1


def _make_min_pptx(path: Path, texts: list[str]) -> None:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        for i, t in enumerate(texts, 1):
            slide = f'<?xml version="1.0"?><sld><txBody><a:p><a:r><a:t>{t}</a:t></a:r></a:p></txBody></sld>'
            z.writestr(f"ppt/slides/slide{i}.xml", slide)
        # 一个非空媒体
        z.writestr("ppt/media/image1.png", b"\x89PNG\r\n\x1a\nFAKE")
    path.write_bytes(buf.getvalue())


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description="medical-literature-report 报告自检引擎")
    parser.add_argument("report_dir", nargs="?", help="报告工作目录(含翻译/评价/事实表/PPTX 等)")
    parser.add_argument("--out", help="JSON 输出路径(同时生成同名 .md 报告)")
    parser.add_argument("--format", choices=["json", "md"], default="md", help="终端输出格式")
    parser.add_argument("--single-paper", action="store_true", help="单篇论文(不强制候选比较表)")
    parser.add_argument("--delegate-graphint", action="store_true", help="委托 graph-interpretation 做图解读级校验")
    parser.add_argument("--fail-on-error", action="store_true", help="存在失败关卡时返回非 0")
    parser.add_argument("--self-test", action="store_true", help="运行合成样本自测")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    if not args.report_dir:
        parser.error("report_dir 必填（或用 --self-test）")

    root = Path(args.report_dir).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"report_dir 不是目录: {root}")

    payload = run_report(root, args.single_paper, args.delegate_graphint, args.format,
                        Path(args.out) if args.out else None)
    if args.fail_on_error and payload["summary"]["fail"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
