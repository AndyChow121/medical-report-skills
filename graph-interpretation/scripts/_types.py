"""向后兼容层（v1.3.0）。

所有 dataclass 已在 `models.py` 统一定义。此文件保留仅供外部脚本
（如旧版 `from _types import ChecklistItem`）平滑迁移。

新代码请使用：

    from models import StatisticalSummary, EffectEstimate, ChecklistItem, AppraisalResult
"""
from __future__ import annotations

from models import ChecklistItem  # noqa: F401
