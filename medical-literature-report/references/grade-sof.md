# GRADE 证据摘要表（Summary of Findings, SoF）

GRADE 是目前国际公认的循证医学证据分级框架。`grade_sof.py` 把它从"手工填表"变成
结构化 JSON → 标准 SoF 表（Markdown，可选 .docx）。

## 何时生成

- 系统评价 / Meta 分析、RCT 网络 Meta、关键临床问题（PICO）需要给出"证据到底有多可靠"；
- 写 PPT 的「证据分级」「推荐依据」页；
- 给指南或科室学习材料附 SoF 表。

## 输入 JSON 结构

```json
{
  "title": "他汀 vs 安慰剂 主要心血管事件",
  "population": "中危成人", "intervention": "他汀", "comparison": "安慰剂",
  "outcomes": [
    {
      "name": "全因死亡",
      "studies": 12, "participants": 45000,
      "effect_type": "HR", "effect_estimate": 0.95, "ci_low": 0.88, "ci_high": 1.03,
      "absolute_effect": "干预 9.1% vs 对照 9.6%（每1000人少5例）",
      "quality": "中等",
      "downgrade_reasons": ["不精确（CI跨1）"],
      "benefit_harm": "不确定"
    }
  ]
}
```

字段约束：

| 字段 | 取值 |
|------|------|
| `effect_type` | RR / OR / HR / MD / RD / SMD |
| `quality` | 高 / 中等 / 低 / 极低 |
| `benefit_harm` | 明确获益 / 可能获益 / 不确定 / 可能有害 / 明确有害 |
| `downgrade_reasons` | 偏倚风险 / 不一致性 / 间接性 / 不精确性 / 发表偏倚（可多条） |

## 命令

```bash
python scripts/grade_sof.py sof.json --out sof.md
python scripts/grade_sof.py sof.json --docx sof.docx     # 需 python-docx，否则降级为 md
python scripts/grade_sof.py --self-test
```

## 质量自动建议

引擎默认「从高起步，每命中一条降级理由降一级」：`高 → 中等 → 低 → 极低`。
若你给定的 `quality` 与按 `downgrade_reasons` 条数算出的建议不一致，会打印 `[note]`
一致性提示，便于复核——这是辅助提醒，不阻断生成。

## 输出样例（Markdown 表）

| 结局 | 研究数(受试者) | 效应估计 (95% CI) | 绝对效应 | 证据质量 | 获益/伤害 |
|---|---|---|---|---|---|
| 全因死亡 | 12 (45000) | HR 0.95 (0.88–1.03) | …每1000人少5例 | 中等 ↓不精确 | 不确定 |

## 边界

- 质量评级、降级判断本质需方法学人工判断；本工具只做结构化呈现与一致性提示，不替你做临床决策。
- 效应估计/置信区间请来自已核验的源数据（见 `source-acquisition` / `verify-report`）。
