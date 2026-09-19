"""图表解析器统一数据结构与基类。"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class EffectEstimate:
    """点估计 + 区间估计。"""
    measure: str            # 例如 "HR", "OR", "RR", "MD", "AUC"
    value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    ci_level: float = 0.95
    p_value: float | None = None
    n: int | None = None

    def ci_str(self) -> str:
        if self.ci_lower is None or self.ci_upper is None:
            return ""
        pct = round(self.ci_level * 100)
        return f"{pct:g}% CI {self.ci_lower:g}-{self.ci_upper:g}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ci_str"] = self.ci_str()
        return d


@dataclass
class StatisticalSummary:
    """统一的统计摘要输出。"""
    chart_type: str
    title: str = ""
    primary: EffectEstimate | None = None
    secondary: list[EffectEstimate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "primary": self.primary.to_dict() if self.primary else None,
            "secondary": [s.to_dict() for s in self.secondary],
            "notes": self.notes,
            "raw": self.raw,
        }


class BaseParser:
    """解析器基类。所有图表解析器应继承并实现 parse()。"""

    chart_type: str = "base"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        raise NotImplementedError
