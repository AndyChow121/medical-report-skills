"""Heatmap 解析器（表达矩阵 / 组学）。"""
from __future__ import annotations

from typing import Any

from .base import BaseParser, StatisticalSummary, EffectEstimate


class HeatmapParser(BaseParser):
    """Heatmap：抽取行/列注释、聚类方法、缩放方式。"""

    chart_type = "heatmap"

    def parse(self, data: dict[str, Any]) -> StatisticalSummary:
        primary = EffectEstimate(measure="matrix_dim")
        notes: list[str] = []

        rows = data.get("rows", [])
        cols = data.get("cols", [])
        primary.raw = None  # type: ignore
        primary.value = float(len(rows)) if rows else None
        primary.ci_lower = float(len(cols)) if cols else None

        notes.append(f"维度: {len(rows)} 行 × {len(cols)} 列")

        if data.get("clustering_rows") or data.get("clustering_cols"):
            notes.append(
                f"聚类方法: 行={data.get('clustering_rows', 'none')}, "
                f"列={data.get('clustering_cols', 'none')}"
            )

        scale = data.get("scale", "raw")
        notes.append(f"缩放方式: {scale}")

        # 行/列注释
        if data.get("row_annotations"):
            notes.append(f"行注释类别: {data['row_annotations']}")
        if data.get("col_annotations"):
            notes.append(f"列注释类别: {data['col_annotations']}")

        # 显著性阈值
        if data.get("significance_threshold") is not None:
            notes.append(f"FDR/significance 阈值: {data['significance_threshold']}")

        # 颜色映射
        cmap = data.get("colormap", "viridis")
        if cmap in {"RdBu", "bwr", "coolwarm"}:
            notes.append(f"色板: {cmap}（双向发散）")
        else:
            notes.append(f"色板: {cmap}")

        return StatisticalSummary(
            chart_type=self.chart_type,
            title=data.get("title", "Heatmap"),
            primary=primary,
            notes=notes,
            # v1.5.0: 透传 data，便于 legend_bridge 拿 row_labels/col_labels/matrix
            raw={**data, "n_rows": len(rows), "n_cols": len(cols)},
        )
