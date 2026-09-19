# 报告自检（verify_report）工作流

`medical-literature-report` 的「Completion Gate」此前是纯人工清单。本工作流把它里
**可机器化**的条目变成可运行、可 CI、可自测的质量关卡，让报告能力具备「自我复核」机制。

> 与子能力 `graph-interpretation` 的 `verify`/`validate` 同源演进：零第三方依赖
> （仅 Python 标准库），输出 JSON（供 CI）+ Markdown（供人读）。

## 何时运行

- 交付前最后一步：生成翻译 / 评价 / 事实表 / PPTX 后，跑一次自检；
- 接入 CI：用 `--fail-on-error` 把失败关卡转为非 0 退出码；
- 委托图解读：加 `--delegate-graphint`，让 `graph-interpretation` 同步做图层级校验。

## 命令

```bash
# 默认 Markdown 报告到终端
python scripts/verify_report.py <报告目录> --single-paper

# 同时落盘 JSON + 同名 .md
python scripts/verify_report.py <报告目录> --out selfcheck.json

# CI 模式：任何失败关卡即返回非 0
python scripts/verify_report.py <报告目录> --fail-on-error

# 委托 graph-interpretation 做图解读级校验
python scripts/verify_report.py <报告目录> --delegate-graphint

# 自带合成样本自测（证明关卡可区分合格/踩雷）
python scripts/verify_report.py --self-test
```

## 报告目录约定（自动递归定位，文件名可中文）

| 角色 | 候选文件名 |
|------|-----------|
| 中文翻译/转述 | `*翻译*.md` / `translation.md` / `*中文转述*.md` |
| 研究设计批判性评价 | `*评价*.md` / `appraisal.md` / `*批判*.md` |
| 原文事实表 | `*fact*sheet*.md` / `source_fact_sheet.md` / `*原文*.md` |
| 图解读/溯源 | `figures_interpretation.md` / `*图解读*.md` / `*provenance*.md` |
| 候选文献比较表 | `*candidate*.md` / `candidate_table.md`（多文献建议） |
| 汇报 PPTX | `*.pptx` |
| 交付哈希清单 | `package_inventory.json`（由 `package_deliverables.py` 生成） |

## 关卡明细（v1.0.0，9 项）

| ID | 关卡 | 失败后果 |
|----|------|---------|
| G1 | 必备交付物齐全（翻译/评价/事实表/PPTX） | fail（缺核心件） |
| G2 | 文献身份/研究设计已核验（DOI/PMID + 设计词） | fail（无身份） |
| G3 | 图表溯源完整（引用图/表均能在图解读文档找到） | fail（无溯源） |
| G4 | 证据标签/推理分离（5 类标签 + 显式「延伸解读」） | fail（未分离推理） |
| G5 | 证据规则（关联→因果、基础→临床、单中心→普适等越界） | warn（需人工复核） |
| G6 | PPTX 完整性与媒体（幻灯片数>0、无零字节媒体） | fail（损坏）；排版需人工视觉复核 |
| G7 | 交付物哈希一致（读 `package_inventory.json`） | fail（哈希不一致） |
| G8 | ML 论文 TRIPOD-AI（命中 ML 关键词必须含 TRIPOD-AI） | fail（缺 TRIPOD-AI） |
| G9 | graph-interpretation 委托（可选） | warn（不影响主关卡） |

## 评分与判定

- 综合评分 = Σ(关卡权重) / 总关卡 × 100；权重 pass=1.0 / warn=0.5 / fail=0.0。
- 判定：`fail==0` 即「通过」，否则「未通过」。
- ⚠️ 关卡为「建议/人工复核」不阻断交付；❌ 关卡为硬性失败，必须修复后重跑。

## 已知边界

- 本引擎**无视觉能力**：PPTX 排版、溢出、对比度、文字重叠等只能靠人工视觉复核（G6 已显式标注）。
- 越界表述（G5）为启发式正则，命中即提示人工复核，不自动判定造假。
- 依赖 `package_deliverables.py` 产出的 `package_inventory.json` 做哈希校验；未打包时 G7 降级为 warn 并提示先打包。
