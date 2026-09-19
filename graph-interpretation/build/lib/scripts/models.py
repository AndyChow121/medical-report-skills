"""graph-interpretation 公开数据模型 (v1.4.0)。

外部 Skill (如 figure-legend-gen) 可直接 `from models import ...` 引用此处的 dataclass
而不必关心内部模块拆分（_types / appraisal / parsers.base）。

使用示例：

    from models import StatisticalSummary, EffectEstimate, ChecklistItem, AppraisalResult

字段语义详见 dataclass 注释。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__version__ = "1.6.0"
__all__ = [
    "StatisticalSummary",
    "EffectEstimate",
    "ChecklistItem",
    "AppraisalResult",
    "is_ml_model",        # TRIPOD-AI 判定 API
    "extract_doi_pmid",   # 待 v1.5.0 引入
]

# StatisticalSummary 与 EffectEstimate 仍由 parsers.base 定义，此处 re-export，
# 保持模型定义与解析器就近维护，同时给外部脚本一个稳定入口。
from parsers.base import StatisticalSummary, EffectEstimate  # noqa: F401


@dataclass
class ChecklistItem:
    """单条评价项。"""

    id: str
    question: str
    passed: bool | None = None  # None=未评估，True=通过，False=未通过
    note: str = ""
    framework: str = ""        # "Cochrane RoB 2" / "GRADE" / "STARD" / "CONSORT" / "TRIPOD" / "TRIPOD-AI"


@dataclass
class AppraisalResult:
    """评价结果汇总。"""

    chart_type: str
    framework: str
    items: list[ChecklistItem] = field(default_factory=list)

    @property
    def n_items(self) -> int:
        return len(self.items)

    @property
    def n_passed(self) -> int:
        return sum(1 for it in self.items if it.passed is True)

    @property
    def n_failed(self) -> int:
        return sum(1 for it in self.items if it.passed is False)

    @property
    def n_unchecked(self) -> int:
        return sum(1 for it in self.items if it.passed is None)

    @property
    def overall_score(self) -> float | None:
        """已评估条目通过率（None 表示无已评估条目）。"""
        n_eval = self.n_passed + self.n_failed
        if n_eval == 0:
            return None
        return self.n_passed / n_eval

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "framework": self.framework,
            "n_items": self.n_items,
            "n_passed": self.n_passed,
            "n_failed": self.n_failed,
            "n_unchecked": self.n_unchecked,
            "overall_score": self.overall_score,
            "items": [
                {
                    "id": it.id,
                    "question": it.question,
                    "passed": it.passed,
                    "note": it.note,
                    "framework": it.framework,
                }
                for it in self.items
            ],
        }

    def by_framework(self) -> dict[str, list[ChecklistItem]]:
        out: dict[str, list[ChecklistItem]] = {}
        for it in self.items:
            out.setdefault(it.framework or "other", []).append(it)
        return out


__all__ = [
    "StatisticalSummary",
    "EffectEstimate",
    "ChecklistItem",
    "AppraisalResult",
]
