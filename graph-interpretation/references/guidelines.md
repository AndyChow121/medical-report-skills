# 图表解读 - 参考资料

更细的文档请查阅：
- `chart-types.md` — 8 类图表的数据契约（最小可用 JSON）
- `journal-styles.md` — 6 种期刊风格图注的段落模板与字数上限
- `appraisal-checklists.md` — Cochrane / GRADE / STARD / CONSORT / MIAME 条目释义

## 学术写作

- 图形描述遵循 CONSORT / STARD 等报告规范的具体条目
- 统计报告标准参见 `references/appraisal-checklists.md`

## 数据流

```
原始图表（图/表/数据）
    │
    ├─→ OCR/文本抽取（ocr_extract.py） → 关键统计量 dict
    │                                      ↓
    ├─→ 解析器（parsers/*.py） ───────→ StatisticalSummary
    │                                      ↓
    ├─→ audiences.py ──→ 多受众文本（researchers/clinicians/patients/policy_makers）
    ├─→ captions.py   ──→ 期刊风格图注（nature/lancet/jama/cell/nejm/generic）
    ├─→ appraisal.py  ──→ 批判性评价 checklist（Cochrane/GRADE/STARD/CONSORT/MIAME）
    └─→ svg_render.py ──→ KM/Forest/ROC SVG（数据 → 可视化重绘）
```
