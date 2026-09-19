"""graph-interpretation v1.5.0 —— bundled samples 资源访问层。

使用 importlib.resources 在 wheel 安装态也能读到内置示例。
不引入第三方依赖；sample_* 数据通过 pyproject.toml 的 package-data 打包。

典型用法：
    from _samples import load_bundled_sample, list_samples
    data = load_bundled_sample("km")          # 自动别名解析
    data = load_bundled_sample("kaplan_meier") # 全名
    print(list_samples())                     # ['km', 'forest', 'roc', ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    # Python 3.9+ 标准 API
    from importlib import resources
except ImportError:  # pragma: no cover
    resources = None  # type: ignore


# 资源文件名映射：alias → bundled JSON 文件名
_ALIAS_MAP = {
    "km": "sample_km.json",
    "kaplan": "sample_km.json",
    "kaplan_meier": "sample_km.json",
    "forest": "sample_forest.json",
    "forest_plot": "sample_forest.json",
    "roc": "sample_roc.json",
    "roc_curve": "sample_roc.json",
    "roc_ml": "sample_roc_ml.json",
    "roc_curve_ml": "sample_roc_ml.json",
    "roc_partial_ml": "sample_roc_partial_ml.json",
    "roc_curve_partial_ml": "sample_roc_partial_ml.json",
    "box": "sample_box.json",
    "box_plot": "sample_box.json",
    "scatter": "sample_scatter.json",
    "scatter_plot": "sample_scatter.json",
    "bar": "sample_bar.json",
    "bar_chart": "sample_bar.json",
    "heatmap": "sample_heatmap.json",
    "volcano": "sample_volcano.json",
    "volcano_plot": "sample_volcano.json",
    "csco_km": "sample_csco_gastric_km.json",
    "csco_gastric_km": "sample_csco_gastric_km.json",
    "km_svg": "sample_km_svg.json",
}


def list_samples() -> list[str]:
    """返回所有 bundled sample 的 alias 列表。"""
    return sorted(_ALIAS_MAP.keys())


def _read_via_importlib(filename: str) -> str | None:
    """优先路径 1：importlib.resources（wheel 安装态）。"""
    if resources is None:
        return None
    try:
        return (
            resources.files("scripts")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        return None


def _read_via_filesystem(filename: str) -> str | None:
    """优先路径 2：源码态（pip install -e / 直接 python scripts/main.py）。"""
    here = Path(__file__).resolve().parent
    target = here / filename
    if target.exists():
        return target.read_text(encoding="utf-8")
    return None


def _read_text(filename: str) -> str:
    """自动 fallback：importlib → 文件系统 → 报错。"""
    text = _read_via_importlib(filename) or _read_via_filesystem(filename)
    if text is None:
        raise FileNotFoundError(
            f"找不到 bundled sample '{filename}'。"
            f"请确认已通过 'pip install .' 或 'pip install -e .' 安装。"
        )
    return text


def load_bundled_sample(name: str) -> dict[str, Any]:
    """加载内置示例数据。

    参数:
        name: alias（如 'km' / 'roc_ml' / 'csco_km'）或文件名（如 'sample_km.json'）

    返回:
        解析后的 dict。
    """
    key = name.lower().strip()
    if key.endswith(".json"):
        filename = key
    elif key in _ALIAS_MAP:
        filename = _ALIAS_MAP[key]
    else:
        raise KeyError(
            f"未知 sample alias '{name}'。"
            f"可选：{list_samples()[:5]}..."
        )
    return json.loads(_read_text(filename))


def has_sample(name: str) -> bool:
    """快速判断某个 sample 是否存在（不抛异常）。"""
    key = name.lower().strip()
    if key.endswith(".json"):
        filename = key
    elif key in _ALIAS_MAP:
        filename = _ALIAS_MAP[key]
    else:
        return False
    try:
        _read_text(filename)
        return True
    except FileNotFoundError:
        return False


# CLI 自检（python -m scripts._samples）
if __name__ == "__main__":
    samples = list_samples()
    print(f"bundled samples: {len(samples)} 个")
    ok = 0
    for s in samples:
        try:
            data = load_bundled_sample(s)
            ok += 1
            print(f"  [OK] {s:18s} -> {len(json.dumps(data, ensure_ascii=False)):>5d} chars")
        except Exception as e:
            print(f"  [FAIL] {s}: {e}")
    print(f"\n成功 {ok}/{len(samples)}")
    sys.exit(0 if ok == len(samples) else 1)