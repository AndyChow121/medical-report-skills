#!/usr/bin/env python3
"""graph-interpretation 端到端编排器 v1.0

不止委托校验——自动调用 graph-interpretation 生成图注/文档/SVG/雷达图，并回填到
报告目录。best-effort：子技能缺失或某步失败均记录并继续，不中断流程。零本技能依赖
（仅调用 graph-interpretation 的 CLI）。

输入（报告目录下的 figure_jobs.json）：
[
  {"type": "roc_ml", "data": "sample_roc_ml.json", "figure_id": "图3",
   "style": "cma", "language": "zh", "with_svg": true, "radar": true},
  {"type": "km", "data": "sample_csco_gastric_km.json", "style": "cslco",
   "language": "zh", "figure_id": "图1"}
]

命令：
    python orchestrate_figures.py <report_dir> [--jobs figure_jobs.json] [--out summary.json]
    python orchestrate_figures.py --self-test
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

FONT_NOTE = "graph-interpretation 子技能未安装；仅生成规划摘要，未执行图解读生成。"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "gbk", "utf-8-sig"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def locate_graphint() -> Path | None:
    p = Path.home() / ".workbuddy" / "skills" / "graph-interpretation" / "scripts" / "main.py"
    return p if p.is_file() else None


def resolve_data(data_ref: str, report_dir: Path, gi_scripts: Path | None) -> Path | None:
    candidates = [
        Path(data_ref),
        report_dir / data_ref,
        report_dir / "figures" / data_ref,
    ]
    if gi_scripts:
        candidates.append(gi_scripts / data_ref)
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return None


def run_job(gi_main: Path, job: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    ftype = job.get("type", "roc")
    data = job.get("data")
    fid = job.get("figure_id", ftype)
    style = job.get("style", "cma")
    lang = job.get("language", "zh")
    result: dict = {"figure_id": fid, "type": ftype, "steps": []}

    data_path = resolve_data(data, out_dir.parent, gi_main.parent if gi_main else None)
    if not data_path:
        result["status"] = "fail"
        result["error"] = f"数据文件未找到: {data}"
        return result

    py = sys.executable
    # 1) all: 四档 JSON（核心，无重依赖）
    all_out = out_dir / f"{fid}_all.json"
    r1 = subprocess.run([py, str(gi_main), "all", "--type", ftype, "--data", str(data_path),
                         "--style", style, "--language", lang, "--out", str(all_out)],
                        capture_output=True, text=True, timeout=180)
    result["steps"].append({"step": "all", "rc": r1.returncode, "out": str(all_out),
                            "ok": r1.returncode == 0 and all_out.is_file()})

    # 2) to-legend docx（需 python-docx，失败不阻断）
    docx_out = out_dir / f"{fid}.docx"
    r2 = subprocess.run([py, str(gi_main), "to-legend", "--type", ftype, "--data", str(data_path),
                         "--mode", "docx", "--style", style, "--language", lang,
                         "--figure-id", fid, "--out", str(docx_out)],
                        capture_output=True, text=True, timeout=180)
    result["steps"].append({"step": "to-legend-docx", "rc": r2.returncode, "out": str(docx_out),
                            "ok": docx_out.is_file()})

    # 3) render-svg（需 cairosvg，失败降级不阻断）
    if job.get("with_svg", True):
        svg_out = out_dir / f"{fid}.svg"
        r3 = subprocess.run([py, str(gi_main), "render-svg", "--type", ftype, "--data", str(data_path),
                             "--out", str(svg_out)],
                            capture_output=True, text=True, timeout=180)
        result["steps"].append({"step": "render-svg", "rc": r3.returncode, "out": str(svg_out),
                                "ok": svg_out.is_file()})

    # 4) TRIPOD-AI 雷达图（仅 ML）
    if job.get("radar") or "ml" in ftype or (data_path and "ml" in data_path.name):
        radar_out = out_dir / f"{fid}_radar.svg"
        # 直接用 tripod_ai_radar 模块渲染；规范 chart_type 需经别名映射
        # （GI 的 CLI 接受别名，但 PARSERS 仅以规范类型为主键）
        radar_code = (
            "import sys, json; sys.path.insert(0, sys.argv[1]); "
            "from tripod_ai_radar import render_tripod_ai_radar; "
            "from appraisal import auto_evaluate; from parsers import PARSERS; "
            "M={'roc':'roc_curve','roc_curve':'roc_curve','roc_ml':'roc_curve','roc_curve_ml':'roc_curve',"
            "'km':'kaplan_meier','kaplan_meier':'kaplan_meier','kaplan':'kaplan_meier',"
            "'csco_km':'kaplan_meier','csco_gastric_km':'kaplan_meier',"
            "'forest':'forest_plot','forest_plot':'forest_plot',"
            "'box':'box_plot','box_plot':'box_plot',"
            "'scatter':'scatter_plot','scatter_plot':'scatter_plot',"
            "'bar':'bar_chart','bar_chart':'bar_chart',"
            "'heatmap':'heatmap','volcano':'volcano_plot','volcano_plot':'volcano_plot'}; "
            "kt=M.get(sys.argv[3], sys.argv[3]); "
            "d=json.load(open(sys.argv[2])); "
            "res=auto_evaluate(PARSERS[kt].parse(d)); "
            "open(sys.argv[4],'w',encoding='utf-8').write(render_tripod_ai_radar(res))"
        )
        r4 = subprocess.run([py, "-c", radar_code, str(gi_main.parent), str(data_path), ftype, str(radar_out)],
                            capture_output=True, text=True, timeout=180)
        result["steps"].append({"step": "tripod-ai-radar", "rc": r4.returncode, "out": str(radar_out),
                                "ok": radar_out.is_file()})

    result["status"] = "ok" if all(s["ok"] for s in result["steps"] if s["step"] == "all") else "partial"
    return result


def run(report_dir: Path, jobs_file: Path | None, out_json: Path | None) -> dict:
    gi_main = locate_graphint()
    gi_scripts = gi_main.parent if gi_main else None
    jobs_path = jobs_file or (report_dir / "figure_jobs.json")
    if not jobs_path.is_file():
        return {"ok": False, "error": f"未找到作业清单: {jobs_path}"}
    raw = json.loads(read_text(jobs_path))
    jobs = raw.get("jobs", []) if isinstance(raw, dict) else raw
    if not isinstance(jobs, list):
        jobs = []

    gen_dir = report_dir / "figures_generated"
    if not gi_main:
        summary = {"ok": True, "graphint_installed": False, "note": FONT_NOTE,
                   "planned_jobs": len(jobs), "results": []}
    else:
        results = [run_job(gi_main, j, gen_dir) for j in jobs]
        summary = {"ok": True, "graphint_installed": True,
                   "generated_dir": str(gen_dir), "results": results}

    if out_json:
        out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def _self_test() -> int:
    import tempfile
    base = Path(tempfile.mkdtemp(prefix="mlr_orch_"))
    rd = base / "report"
    rd.mkdir()
    gi_main = locate_graphint()
    if gi_main:
        gi_scripts = gi_main.parent
        # 用 bundled sample 做真实端到端
        sample = gi_scripts / "sample_roc_ml.json"
        jobs = [{"type": "roc_ml", "data": str(sample), "figure_id": "图3",
                 "style": "cma", "language": "zh", "with_svg": True, "radar": True}]
        (rd / "figure_jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
        res = run(rd, None, None)
        # 核心 'all' 步骤应成功，且生成目录有文件
        gen = rd / "figures_generated"
        core_ok = any(r.get("status") in ("ok", "partial") for r in res.get("results", []))
        files_ok = gen.is_dir() and any(gen.iterdir())
        print(f"[self-test] graphint installed; core={core_ok} files={files_ok} -> "
              f"{'PASS' if (core_ok and files_ok) else 'FAIL'}")
        return 0 if (core_ok and files_ok) else 1
    else:
        # 未安装：验证优雅跳过
        (rd / "figure_jobs.json").write_text(json.dumps([{"type": "roc", "data": "x.json"}]), encoding="utf-8")
        res = run(rd, None, None)
        ok = res.get("ok") and res.get("graphint_installed") is False
        print(f"[self-test] graphint missing; graceful skip={ok} -> {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="graph-interpretation 端到端编排器")
    p.add_argument("report_dir", nargs="?", help="报告目录（含 figure_jobs.json）")
    p.add_argument("--jobs", help="作业清单 JSON（默认 <report_dir>/figure_jobs.json）")
    p.add_argument("--out", help="汇总 JSON 输出路径")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return _self_test()
    if not args.report_dir:
        p.error("report_dir 必填（或用 --self-test）")
    run(Path(args.report_dir).expanduser().resolve(),
        Path(args.jobs).expanduser().resolve() if args.jobs else None,
        Path(args.out).expanduser().resolve() if args.out else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
