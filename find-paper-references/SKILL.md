---
name: find-paper-references
description: >
  自动为学术论文 Markdown 文件查找参考文献。读取论文全文，识别每个需要引用的知识点（流行病学数据、机制描述、已有研究结论等），为每个知识点通过 PubMed 检索 3-5 篇最相关文献，在原文句末插入 [PMID:XXXXXXXX] 标记，并生成独立的候选参考文献列表文件。

  本 skill 止步于 PMID 标记的 .md 文件。后续参考文献排版请使用 format-references-endnote（EndNote）或 format-references-zotero（Zotero）skill。

  当用户说「插参考文献」「补引用」「找文献」「搜 PubMed」「加引文」「给文章加上引用」「find references」「cite」「为这篇论文找文献」时必须使用此 skill。
---

# find-paper-references — 学术论文 PubMed 参考文献查找

## 工具

脚本位于本 skill 目录的 `scripts/` 子目录下：

- `batch_search.py` — **主入口**：一次性接收所有查询，并行搜索，批量拉取 esummary，典型耗时 10-20s
- `remap_refs.py` — 将文中 `[PMID:XXXXXXXX]` 标记转为 `[1][2]` 编号并生成正式参考文献（**本 skill 不再调用，由后续 endnote/zotero skill 接手**）
- `convert_to_docx.py` — 将 `.md` 文件转为 `.docx`（**本 skill 不再调用**）

### 本 skill 的边界

```
┌─────────────────────────────────────────────────────┐
│  find-paper-references                              │
│  ─────────────────────────────────────────────────  │
│  Step 0-3: 识别知识点 → 构建 PubMed 检索 JSON       │
│  Step 4:   batch_search.py 批量检索                 │
│  Step 5:   选择文献 → 插入 [PMID:xxxxxxxx] 标记      │
│  Step 6:   写回 .md 文件                             │
│  Step 7:   生成 _candidates.md 候选文献列表          │
│  Step 8:   提醒用户选择 EndNote / Zotero 继续        │
│  ──────────────── 工作流结束 ─────────────────────── │
│                                                     │
│  后续排版 → format-references-endnote (EndNote)     │
│          → format-references-zotero (Zotero)        │
└─────────────────────────────────────────────────────┘
```

---

## 工作流（按顺序执行）

### Step 0：询问 NCBI API Key

在开始任何搜索之前，先检查并询问：

```
你有 NCBI API key 吗？有的话可以把搜索速度从 3 次/秒提升到 10 次/秒。
没有也完全没关系，直接跳过就行。
```

- **用户提供了 key**：在本次所有脚本调用之前，先执行：
  ```bash
  # Windows
  $env:NCBI_API_KEY = "用户提供的key"
  # Mac/Linux
  export NCBI_API_KEY="用户提供的key"
  ```
  然后正常继续工作流。key 只在当次会话有效，不写入任何文件。

- **用户没有 / 跳过**：直接进入 Step 1，脚本会自动使用 3 req/s 的保守速率。

### Step 1：确定目标文件 + 文章类型

读取完整文件内容，然后判断文章类型——可以自动识别，也可以询问用户确认：

**自动识别规则：**
- 含有 `## 材料与方法` / `## Methods` / `## 方法` 章节 → **Research Article**
- 无上述章节，正文以多个综述性段落为主 → **Review**
- 不确定时直接问用户

---

## 文章类型引用规则

根据识别结果，本次工作流须遵守对应规则：

### Research Article 规则
```
引用区域：  仅引言（Introduction）和讨论（Discussion）
            材料与方法、结果 章节 → 完全跳过，不插任何引用
每知识点：  最多选 2 篇文献（取相关性最高的 2 篇，不凑数）
总数目标：  正文引用不少于 30 个唯一 PMID
```

### Review 规则
```
引用区域：  除结论（Conclusion/总结）外，全文所有段落均可引用
            结论段落 → 跳过
每知识点：  最多选 5 篇文献
总数目标：  按正文总字数计算，约每 100 字插 1 篇，上下浮动 20%
            即目标区间 = [总字数×0.8÷100, 总字数×1.2÷100]（取整）
            例如：正文 5000 字 → 目标 40~60 篇；正文 8000 字 → 目标 64~96 篇
```

---

### Step 2：识别需要引用的句子

通读论文，**严格按当前文章类型的引用区域规则**筛选段落，跳过不需要引用的章节。

在允许引用的区域内，找出所有**需要文献支撑的知识点**：

**需要引用（适用于允许引用的章节）：**
- 流行病学数据（"肺癌是全球发病率最高的恶性肿瘤之一"）
- 蛋白/基因的已知生物学功能（"GPX4 可将脂质过氧化物还原为无毒醇"）
- 信号通路描述（"xCT 介导细胞摄取胱氨酸"）
- 已有研究报道的结论（"TRIM3 在乳腺癌中表达下调"）
- 治疗方法/药物的已知机制（"Erastin 通过抑制 xCT 诱导铁死亡"）

**始终不需要引用：**
- 本研究自己做出的实验结果
- 材料与方法中的仪器/试剂描述（Research Article 整个章节跳过）
- 结果章节（Research Article 整个跳过）
- 结论章节（Review 跳过）
- 通用技术操作说明

**识别完成后，预估知识点总数：**
- Research Article：目标覆盖 ≥ 30 个唯一引用 → 通常需要识别 20-35 个知识点
- Review：**先计算正文总字数**，按每 100 字 1 篇估算目标引用数，通常需要识别与目标数相近的知识点数量（每个知识点 1~2 篇）

将识别到的知识点整理成列表，每项包含：
- 所在章节名（用于确认是否在允许引用的区域）
- 原文中的句子
- 该知识点的核心概念（用于生成搜索词）

### Step 3：一次性整理所有查询，写入临时 JSON

将所有知识点整理成以下格式，写入 `%TEMP%\ref_queries.json`（或 `/tmp/ref_queries.json`）：

```json
[
  {"id": 1, "description": "肺癌全球发病率", "query": "global cancer statistics 2020 GLOBOCAN lung cancer Sung", "method": "pubmed"},
  {"id": 2, "description": "铁死亡定义",     "query": "Ferroptosis iron-dependent nonapoptotic cell death Dixon 2012", "method": "pubmed"},
  {"id": 3, "description": "TRIM3结构功能",  "query": "TRIM3 ubiquitin ligase RING domain substrate degradation", "method": "litsense"},
  ...
]
```

**method 说明：**
- `"pubmed"` — 关键词精确检索（推荐，适合大多数知识点）
- `"litsense"` — 语义检索（适合描述性句子、某蛋白的具体功能等）
- `"auto"` — 先试 LitSense，若结果 <2 篇自动 fallback 到 PubMed

**query 写法：**
- 用英文，3-8 个关键词
- MeSH 术语优先（ferroptosis, non-small cell lung cancer, ubiquitin ligase）
- 已知经典论文可在 query 里加作者或年份（"Dixon 2012", "Stockwell 2017"）

### Step 4：运行一次 batch_search.py 获取所有结果

```bash
python "SKILL_DIR/scripts/batch_search.py" "%TEMP%\ref_queries.json" --max 5
```

脚本并行搜索所有查询，最后批量拉 esummary，**典型耗时 10-20 秒**（而非逐条搜索的数分钟）。

输出 JSON 格式：
```json
[
  {"id": 1, "description": "...", "results": [{pmid, title, authors, journal, year, doi}, ...]},
  ...
]
```

**若某条结果为空**，补充一个带调整后关键词的新 JSON 文件，再用 batch_search.py 重新搜索。

### Step 5：选择最相关文献并插入 PMID 标记

对于每个需要引用的句子：

1. 从候选文章中按相关性排序，根据**文章类型上限**选取：
   - **Research Article**：每个知识点最多选 **2 篇**，只选最相关的，不凑数
   - **Review**：每个知识点最多选 **5 篇**，可覆盖不同研究角度
2. 在**原句末尾**插入 `[PMID:XXXXXXXX]`，多篇时连续写：`[PMID:111][PMID:222]`
3. 同一 PMID 已引用过则直接复用，不重复插入

**插入完成后，统计当前唯一 PMID 总数：**
- Research Article：若不足 30，回到 Step 2 补充识别更多知识点
- Review：**先计算正文总字数，按每 100 字 1 篇计算目标区间 [总字数×0.8÷100, 总字数×1.2÷100]（取整）**，若不在区间内，回到 Step 2 补充或精简

**示例（修改前后对比）：**
```
修改前：铁死亡是一种由铁依赖性脂质过氧化驱动的调节性细胞死亡方式。
修改后：铁死亡是一种由铁依赖性脂质过氧化驱动的调节性细胞死亡方式[PMID:25789077]。
```

**remap_refs.py 支持的宽松写法（均可正确处理）：**
- 大小写任意：`[PMID:123]` `[pmid:123]` `[Pmid:123]`
- 冒号前后带空格：`[PMID: 123]` `[ PMID : 123 ]`
- 同一括号多条：`[PMID:123, PMID:456]` → `[1][2]`（逗号前后空格、中文逗号均可）

### Step 6：将带 PMID 标记的全文写入新文件

**不要覆盖原文件。** 将插入 `[PMID:XXXXXXXX]` 标记后的全文写入一个**新文件**：

- 原文件 `论文.md` → 新文件 `论文_refs.md`（在原文件同目录生成）

命名规则：原文件名去掉 `.md` 后缀，加上 `_refs.md`。例如：
- `TRIM3_ferroptosis.md` → `TRIM3_ferroptosis_refs.md`
- 无扩展名的情况：`手稿` → `手稿_refs.md`

原文件保持不动，不做任何修改。

### Step 7：将候选参考文献区写入独立文件

**不要**将参考文献候选区追加到原 `.md` 文件中，否则后续排版时会干扰正文。

改为在同目录下生成独立的候选文件 `原文件名_candidates.md`：

```markdown

## 参考文献候选

> 以下为各知识点的 PubMed 检索结果。已选入正文的用 ✓ 标注。
> 下一步：使用 format-references-endnote 或 format-references-zotero skill 排版。

### 知识点 1：[知识点简述]
- ✓ **[PMID:25789077]** Dixon SJ et al. "Ferroptosis: an iron-dependent form of nonapoptotic cell death." *Cell* 2012;149(5):1060-72.
- [PMID:26593993] Stockwell BR et al. "Ferroptosis: a regulated cell death nexus linking metabolism, redox biology, and disease." *Cell* 2017;171(2):273-285.
- [PMID:31634899] ...

### 知识点 2：[知识点简述]
...
```

**Step 7 完成即本次工作流结束。** 不再运行 remap_refs.py 或 convert_to_docx.py。

### Step 8：主动提醒用户选择后续排版工具

Step 7 完成后，**必须主动向用户提问**，让用户选择下一步：

```
引用标记已全部插入（共 N 篇唯一文献）。下一步要排版输出 Word 了吗？

你的文献管理工具是 EndNote 还是 Zotero？
```

- 用户选 **EndNote** → 立即加载 `format-references-endnote` skill 继续
- 用户选 **Zotero** → 立即加载 `format-references-zotero` skill 继续
- 用户说「暂不」/「先看看」→ 告知 "随时说「整理参考文献」或「排版」即可继续"

**不要**什么都不说就结束，必须给出这个提醒。

---

## 下一步：文献排版（另走独立 skill）

`[PMID:xxxxxxxx]` 标记的 .md 文件生成后，根据用户使用的文献管理工具选择：

### EndNote 用户

使用 **format-references-endnote** skill。该 skill 将：
1. 把 `[PMID:xxxx]` 标记转为 EndNote CWYW 识别的 `{Author, Year, Title}` 占位符
2. 生成 `.ris` 文件自动导入本地 EndNote 库
3. 输出 `.docx` 文件，用户在 Word 中点一次「Update Citations」即可完成排版

典型触发词：「整理参考文献」「排版」「参考文献格式化」

### Zotero 用户

使用 **format-references-zotero** skill。该 skill 将：
1. 把 `[PMID:xxxx]` 标记转为 Zotero 原生域代码
2. 搜索/下载任意 CSL 引用样式
3. 输出 `.docx` 文件，在 Word 中点一次「Refresh」即可完成

---

## NCBI API Key（可选，免费）

NCBI 提供免费 API key，有 key 时速率上限从 3 req/s 提升到 10 req/s，并发 worker 数也会自动从 4 提升到 8，检索速度更快且更不容易触发限流。

**如何获取：**
1. 注册 NCBI 账号：https://www.ncbi.nlm.nih.gov/account/
2. 进入 Account Settings → API Key Management → Generate

**如何使用：**
```bash
# 临时（当次有效）
set NCBI_API_KEY=你的key    # Windows
export NCBI_API_KEY=你的key  # Mac/Linux

# 永久（推荐写入系统环境变量或 .env 文件）
```

**没有 key 也完全可以用**，脚本会自动使用保守的 3 req/s 速率，并在遇到 429 时自动退让重试，不会报错。

## 注意事项

- 搜索词必须用英文（PubMed 收录以英文文献为主）
- 对于非常新的研究（2024 年以后），PubMed 收录可能有延迟
- 遇到 429 限流时脚本会自动退让重试（最多 4 次），无需手动干预
