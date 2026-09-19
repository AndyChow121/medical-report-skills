# PRISMA 2020 检索流程图

系统评价 / Meta 分析必须附检索漏斗图（PRISMA 2020 四阶段：识别 → 筛选 → 合格性 → 纳入）。
`prisma_flow.py` 把各阶段数字变成标准 SVG 流程图 + Markdown 文本漏斗，零依赖、无 cairosvg 需求。

## 何时生成

- 系统评价 / Meta 分析的「检索策略与筛选」页；
- 给方法学报告（如 PRISMA 核查表）附图；
- 向编辑/审稿人展示纳入排除全过程。

## 输入 JSON 结构

```json
{
  "title": "示例系统评价 PRISMA",
  "identified": {"databases": 1234, "registers": 56},
  "deduplicated": 1100,
  "title_abstract_excluded": 980,
  "fulltext_sought": 120, "fulltext_not_retrieved": 10, "fulltext_assessed": 110,
  "fulltext_excluded": 25,
  "fulltext_excluded_reasons": {"不可得全文": 5, "不符合纳入": 20},
  "included_qualitative": 85, "included_quantitative": 80
}
```

缺字段默认 0；数字不强制自洽（由你保证漏斗逻辑正确），引擎只负责呈现。

## 命令

```bash
python scripts/prisma_flow.py prisma.json --out flow.svg --md flow.md
python scripts/prisma_flow.py prisma.json            # 仅打印 Markdown 漏斗
python scripts/prisma_flow.py --self-test
```

## 输出

- `flow.svg`：手工绘制的 PRISMA 四阶段图，中央主流程 + 右侧排除原因块，可直接嵌入 PPT/报告；
- Markdown 漏斗：纯文本版，便于快速核对数字。

## 边界

- 漏斗数字的自洽性（如 去重后 ≥ 标题摘要排除后剩余）由人工保证；引擎不做算术校验，只呈现。
- 英文环境若缺中文字体，SVG 中文可能回退为系统默认；建议在 Windows/macOS 中文环境渲染。
