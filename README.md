# Medical Report Skills · 医学科研报告 Skill 套件

> 一套面向医学/生命科学科研的 WorkBuddy Skills，覆盖**文献检索 → 解读 → 图表 → 综述/手稿 → 参考文献排版**全链路。
> A bundle of WorkBuddy Skills for medical / life-science research, covering the full chain of **literature search → interpretation → figures → review/manuscript → reference formatting**.

## 组件 / Components

| Skill (EN) | 名称 (中文) | 一句话简介 (One-liner) |
|---|---|---|
| [Medical Literature Report](medical-literature-report/README.md) | 医学文献解读报告 | 面向临床（内科/外科/检验/护理/药学/公卫）与生物医学科研的英文医学文献一站式解读流水线：检索… |
| [Graph Interpretation](graph-interpretation/README.md) | 医学科研图表解读器 | 解读医学/生命科学图表与数据可视化。覆盖 8 类核心图表（ROC、KM、森林图、热图、散点、箱线… |
| [Figure Legend Generator](figure-legend-gen/README.md) | 医学科研图注生成器 | 为科学图表生成标准化图注：支持条形图、折线图、散点图、箱线图、热图与显微镜图像。仅生成文字图注（… |
| [Literature Close-Read](literature-close-read/README.md) | 文献精读报告 | 从论文完整的 PDF→Markdown 文本（含 `## Page XX` 页码与图片引用）生成… |
| [Basic Research Design Extractor](basic-research-design-extractor/README.md) | 基础研究设计提取器 | 从一篇基础研究论文、摘要、全文或方法/结果内容，快速产出详细的 Markdown 实验方案：按检… |
| [Clinical Research Design Extractor](clinical-research-design-extractor/README.md) | 临床研究设计提取器 | 从一篇临床研究论文快速产出中文立项风格的临床研究方案：疾病负担、研究依据、目标、方法、终点、统计… |
| [Biomedical SCI Manuscript](biomedical-sci-manuscript/README.md) | 生物医学 SCI 手稿起草 | 面向生物信息、临床、基础生物医学三类研究的 SCI 手稿 Methods/Results 起草：… |
| [Medical Review Writer](medical-review-writer/README.md) | 医学综述写作器 | 快速完成医学综述的工作流引擎：大纲构建 → 主题总检索 → 连续写作 → 章节校验 → 合并定稿… |
| [Find Paper References](find-paper-references/README.md) | 参考文献检索插入 | 自动为论文 Markdown 查找参考文献：识别需引用的知识点（流行病学数据、机制描述、已有结论… |
| [Reference Retrieval](reference-retrieval-skill/README.md) | 文献检索式构建 | 按中/英文意图直接查找文献，或自动构建 PubMed 布尔检索式并检索筛选，适合快速补全引用与获… |
| [Format References (EndNote)](format-references-endnote/README.md) | EndNote 文献排版 | 将手稿中的 [PMID:xxxx] 转为 Word(.docx)，写入 EndNote CWYW… |
| [Format References (Zotero)](format-references-zotero/README.md) | Zotero 文献排版 | 将手稿中的 [PMID:xxxx] 转为 Word(.docx)，写入原生 Zotero 域代码… |

### 写作与本地化 / Writing & Localization（通用伴随技能）

| Skill (EN) | 名称 (中文) | 一句话简介 (One-liner) |
|---|---|---|
| [Natural Rewrite](write/README.md) | 自然改写 | 去除文本中的「AI 味」，把稿件改写得更自然、像人写的；支持中英文润色、发布说明、社交文案、产品本地化审校。 |
| [Humanizer](humanizer/README.md) | 去 AI 写作痕迹 | 识别并去除 24 类 AI 写作痕迹（夸张象征、营销腔、破折号滥用等），让文字更像人写，保留原意与语气。 |
| [Style & Journal Rewrite](style-journal-rewrite/README.md) | 文风与期刊格式适配 | 按目标文风或目标期刊格式改写初稿：套用期刊体例与作者文风，支持 .docx/.md/.txt 输入。 |

## 推荐工作流 / Recommended Workflow

1. **检索与立项**：`reference-retrieval-skill` / `find-paper-references` 找文献；`basic-` / `clinical-research-design-extractor` 提取研究设计。
2. **解读与精读**：`medical-literature-report` 出中文解读 + PPT；`graph-interpretation` / `figure-legend-gen` 做图表图注；`literature-close-read` 出精读报告。
3. **写作**：`medical-review-writer` 写综述；`biomedical-sci-manuscript` 起草 SCI 手稿。
4. **润色与适配**：`write` / `humanizer` 去 AI 味、做发布前终稿润色；`style-journal-rewrite` 按目标期刊/文风重排版式与语气。
5. **排版**：`format-references-endnote` 或 `format-references-zotero` 完成参考文献终排版。

## 安装 / Install

把 `medical-report-skills-export/` 下的各个 skill 目录整体复制到 WorkBuddy 的 skills 目录：

```bash
# Windows (PowerShell)
Copy-Item -Recurse medical-report-skills-export/* "$env:USERPROFILE/.workbuddy/skills/"

# macOS / Linux
cp -r medical-report-skills-export/* ~/.workbuddy/skills/
```

多数脚本仅依赖 Python 标准库（managed Python 3.13）；`graph-interpretation` 的部分 SVG 渲染需要 `cairosvg`（缺失时自动降级）。

## 许可 / License

各 skill 许可见其目录内说明；未声明者默认以 MIT 授权。本仓库整体以 MIT 授权。

---

*Generated for publishing to GitHub. 本套件由 WorkBuddy 自动整理并生成双语介绍。*
