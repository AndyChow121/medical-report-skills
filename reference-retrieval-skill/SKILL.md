---
name: reference-retrieval-skill
description: 根据用户输入的中文或英文意图，直接根据需求查找相关文献，或自动构建PubMed布尔检索式，检索并筛选适合引用的参考文献。适用于快速寻找特定主题的高质量文献证据及补全引用。
---

# Reference Retrieval Skill

## 核心功能

该 Skill 旨在帮助用户根据自然语言描述（中文或英文），快速从 PubMed 检索并筛选出高质量、最相关的参考文献。



## 工作流程

### 第一步：构建检索式 (Construct Boolean Query)

1.  **分析意图**：理解用户语义，提取核心医学关键词（MeSH Terms 优先）。
2.  **构建布尔检索式**：
    - **逻辑运算符**：使用 `AND`（交集）、`OR`（并集）、`NOT`（排除）。
    - **截词符**：使用 `*` 匹配变体（如 `diaes*` 匹配 diagnosis, diagnostic）。
    - **示例**：用户查“二甲双胍治疗2型糖尿病”，构建：`Metformin AND "Diabetes Mellitus, Type 2" AND (Therapy OR Treatment)`。

> [!TIP]
> **关于转义 (Escaping)**：
> 如果检索式中包含双引号 `"`（如短语检索），**必须**使用**单引号** `'...'` 包裹整个检索式，或者对内部双引号进行转义 `\"`，以避免命令行解析错误。
> - 正确：`python scripts/pubmed_search.py 'Metformin AND "Type 2 Diabetes"'`
> - 正确：`python scripts/pubmed_search.py "Metformin AND \"Type 2 Diabetes\""`

### 第二步：执行检索 (Execute Search)

**优先使用 LitSense 进行语义检索**，仅在需要精确控制或复现复杂布尔逻辑时使用 PubMed 布尔检索。

**场景 A：语义/自然语言检索 (LitSense Semantic Search) [优先]**
适用于直接使用自然语言提问或查找长难句相关文献。
```bash
python scripts/litsense_search.py "natural language query"
```

**场景 B：基础布尔检索 (Boolean Search)**
适用于构建了精确布尔查询的情况。
```bash
python scripts/pubmed_search.py "YOUR_BOOLEAN_QUERY"
```

- `--max`: 默认返回 **20** 篇文献，如需更多可指定 `--max 50`。

### 第三步：结果评估与迭代 (Evaluation & Iteration)

如果初步检索结果不符合需求（如数量过少、相关性低或无结果），**必须**自动执行迭代检索，最多尝试 **5轮**。

1.  **分析原因**：
    - 结果为 0：关键词可能拼写错误或过于具体。
    - 结果不相关：关键词多义或布尔逻辑错误。
2.  **调整策略 (Refine Query)**：
    - **扩大范围**：移除非必要的 `AND` 条件，增加 `OR` 同义词。
    - **缩小范围**：增加限定词（如 `diagnosis`, `therapy`），或使用字段标签 `[ti]`。
    - **切换 API**：如果 LitSense (Semantic) 检索失败或准确度不足，尝试构建精确的布尔检索式并在 PubMed (Boolean) 中执行。
3.  **循环执行**：
    - 重复执行“修改检索式 -> 运行脚本 -> 评估结果”的循环。
    - **上限**：默认最多重试 5 次。若 5 次后仍无理想结果，向用户报告尝试过的策略并请求更多信息。

### 第四步：筛选与呈现 (Filter & Present)

脚本返回 JSON 结果后，请基于以下标准筛选出 **3-5 篇** 最佳文献：

1.  **筛选标准**：
    - **相关性**：标题/摘要必须直接回应用户问题。
    - **文献类型**：优先选择 **Review**, **Systematic Review**, **Meta-Analysis**。其次是高质量 **RCT** 或 **Original Article**。**严禁**引用 Letter, Editorial, Comment 等短文。
    - **时效性**：优先推荐近 **5-10年** 文献（经典理论除外）。
    - **Open Access (OA) / 免费全文**：如果明确需要查找 OA/免费期刊文献，请检查返回结果中是否包含 `is_oa: true` 或 `pmcid` 字段，这代表该文献具有 PMC 提供的免费全文。

2.  **输出格式**：
    请严格按照以下结构展示结果：

    **一、引用标注 (Citation Marking)**
    直接在回答用户意图的内容（或用户提供的原文）上，在关键观点处加上引用标记。
    - 格式示例：`...有效改善了预后[1]。` 或 `...treatment efficacy [1].`
    - 语言与用户提问语言保持一致。

    **二、参考文献 (References)**
    按引用顺序详细列出文献，**格式如下**：

    ```markdown
    [1] PMID: 34479503 | Title. Journal. https://pubmed.ncbi.nlm.nih.gov/34479503/
    
    引用理由：简要说明该文献为何支持上述观点（如：“文献[1]指出抗PD-L1...，支持了...的论断”）。

    [2] ...
    ```

    **PubMed 链接生成规则**：
    - 建议同时给出文献直链：`https://pubmed.ncbi.nlm.nih.gov/{pmid}`
    - 例如 PMID 为 `34479503`，链接可写为：`https://pubmed.ncbi.nlm.nih.gov/34479503`

    > [!NOTE]
    > Example:
    > [1] The augment of regulatory T cells undermines the efficacy of anti-PD-L1 treatment in cervical cancer. BMC Immunol. https://pubmed.ncbi.nlm.nih.gov/34479503/

## 注意事项

- **准确性**：检索式过宽会导致无关结果，过窄可能无结果。若结果少，尝试减少检索词。
- **语言一致性**：**严禁自动翻译**。Summary 语言必须与用户提问语言保持一致（用户问中文则回中文，问英文则回英文）。
- **检索语言**：始终将中文关键词翻译为准确的英文医学术语进行检索（检索必须用英文），但最终呈现结果时遵循“语言一致性”原则。
