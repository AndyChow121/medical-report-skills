# 期刊风格图注（caption）

`scripts/captions.py` 提供 6 种期刊风格的图注生成。每种风格都有：

- 字数上限（按 word 等价字符）
- 段落结构（按顺序拼接）
- 语气预设（注释中可见）

## 风格清单

### 1. nature（默认）

- max_words: 200
- 结构：title → panel_description → key_finding → statistics → meaning
- 语气：concise, results-first
- 适用：跨学科数据型论文（机制/计算/材料）

### 2. lancet

- max_words: 250
- 结构：title → population → finding → statistics → clinical_implication
- 语气：clinical, PICO-aware
- 适用：临床试验、队列研究、RCT

### 3. jama

- max_words: 250
- 结构：title → setting → design → main_outcome → statistics
- 语气：structured, formal
- 适用：临床研究、流行病学、卫生政策

### 4. cell

- max_words: 220
- 结构：title → panel_description → mechanism → statistics → biological_meaning
- 语气：mechanistic
- 适用：分子机制、组学、模型生物

### 5. nejm

- max_words: 180
- 结构：title → finding → numbers → clinical_decision
- 语气：clinical-decision
- 适用：临床决策类研究，强调 actionable 数字

### 6. generic

- max_words: 250
- 结构：title → what_is_shown → key_finding → statistics → interpretation
- 语气：balanced
- 适用：兜底风格，未指定期刊时使用

## 输出语言

- `--language en` → 英文图注
- `--language zh` → 中文图注

所有结构块（title/setting/mechanism/...）都做了双语映射。

## 段块填充规则

每个结构块从 `StatisticalSummary` 取值：

| 段块 | 数据来源 |
|------|----------|
| `title` | `summary.title` 或 `chart_type` |
| `key_finding` / `finding` | `summary.notes` 前 3 条 |
| `statistics` | `summary.primary`（HR/OR/AUC/... + 95% CI + p + n） |
| `panel_description` | `chart_type` |
| 其余（setting/population/mechanism/...） | 默认 placeholder（"见正文方法学部分"） |

> ⚠️ placeholder 不替代原文信息。如需生成高质量图注，请先用 `interpret` 抽取并人工补充 setting/population 等字段。

## 字数截断

超过 `max_words` 的图注会被截断到 `max_words * 6` 个字符（粗略估算），末尾加 `…`。
中文字符算 1 字符，英文单词也按 1 字符估算；如需精确字数控制，可在此处扩展。
