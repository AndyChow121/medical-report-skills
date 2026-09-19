# 研究质量自我批判叙述生成器

`self_critique.py` 从「研究设计属性」JSON 规则化生成 **优势 / 局限 / 适用性** 三段叙述
与一段可编辑的批判性评价小结，供 PPT「批判性评价」页快速起稿。规则化、best-effort，
**最终方法学判断仍须人工确认**。

## 输入 JSON 字段（按需填，缺失即不触发对应规则）

| 字段 | 含义 | 触发 |
|------|------|------|
| `design` | 研究设计 | 展示 |
| `randomization` | 是否随机 | 否→局限 |
| `blinding` | 盲法（如「双盲」） | 有→优势；无→局限 |
| `allocation_concealment` | 分配隐藏 | 有→优势 |
| `intention_to_treat` | 意向性分析 | 有→优势 |
| `sample_size` / `power_adequate` | 样本量/效能 | 充分→优势；<100→局限 |
| `loss_to_followup` | 失访率 | >10%→局限 |
| `heterogeneity` | 异质性（含 I²） | I²>50%→局限 |
| `single_center` / `multi_center` | 单/多中心 | 多→优势；单→局限 |
| `confounders_controlled` | 混杂控制 | 有→优势 |
| `industry_funding` | 行业资助 | 有→局限 |
| `key_limitations` | 显式局限列表 | 直接纳入 |
| `population_note` / `generalizability_note` | 适用人群/外推说明 | 纳入适用性 |

## 命令

```bash
python scripts/self_critique.py study.json --out critique.md
python scripts/self_critique.py --self-test
```

## 输出结构

- **优势 (Strengths)**：从随机/盲法/分配隐藏/ITT/样本量/多中心/混杂控制逐项生成；
- **局限 (Limitations)**：从非随机/未设盲/单中心/小样本/高失访/高异质性/行业资助/显式列表生成；
- **适用性**：单/多中心 + 人群说明；
- **批判性评价小结**：自动缝合前两项的模板句，留空处供人工补全。

## 边界

- 这是「起稿辅助」，不是方法学评级；正式交付前请结合 CONSORT/STARD/ROBINS 等工具人工复核。
- 未命中任何字段时对应段落给出「请人工补充」占位，不会编造内容。
