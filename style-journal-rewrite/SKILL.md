---
name: style-journal-rewrite
description: 按目标文风或目标期刊格式改写初稿。用户说"改成XX风格""仿照这个味道""按XX期刊格式整理""参考这篇格式改"时触发。输入可为 .docx / .md / .txt 或对话文本。
---

# 文风与期刊格式适配 Skill

## 触发条件

### 触发
- 改文风："改成XX风格""写得像XX""仿照这个味道"
- 套期刊格式："按XX期刊格式整理""参考这篇格式改""改成NC格式"
- 调参考文献体例或摘要结构

### 不触发
- 事实补充、内容扩写
- 校对错别字
- 完整结构重写（与文风/格式无关）
- 单纯插参考文献（走 `find-paper-references`）

## 环境要求

- `python-docx`：`pip install python-docx`（B4/C4 视觉格式、B1/B2 脚本均依赖）

## 流程

### 0. 锁定边界

确定三件事：
- **输入格式**：DOCX / MD / TXT / 对话文本？
- **任务类型**：只改文风 / 只改格式 / 两者都要？
- **输出格式**：与输入一致还是要求特定格式？

然后按以下分叉进入对应路径。

### 1. 提取目标画像

读取 `references/` 中的提取指南：
- 文风适配 → `references/style-profile-extraction.md`
- 期刊格式适配 → `references/journal-format-extraction.md`

**不准编造**用户材料中没有的规则。

---

## 路径 A：纯文风适配（不限输入格式）

直接读 `references/rewriting-criteria.md`，按画像改写。不改任何格式，只改表达方式。

输出与输入同格式。DOCX 只改文本不改样式；MD/TXT 输出同格式文件；对话文本直接输出。

**完成后跳到第 6 节 QC。**

---

## 路径 B：DOCX + 格式适配

输入为 `.docx`，需要改期刊格式（可能同时改文风）。

### B1. 结构层
- 标题编号：
  - 参考文章无编号 → 运行 `scripts/remove_heading_numbers.py <输入> <输出>`
  - 参考文章有编号但格式不同 → 手动改标题文本
- 摘要结构、章节顺序：AI 直接修改

### B2. 引用层
- 文末列表编号用 `convert_ref_format.py --ref-list-style` 切换 `[N]` / `N.`
- 文内引文用 `convert_ref_format.py --style` 切换上标（Unicode / 字体格式）
- `--range-joiner` 和 `--group-separator` **必须从参考文章实际书写方式提取**，不准假设
- 参考文章连续引用如何组合：在文中找多引用连写处观察，再设参数

### B3. 域代码检测
扫描 DOCX XML 中的 `w:instrText`：
- 含 `ADDIN ZOTERO_ITEM` → 加载 `format-references-zotero` skill，搜 CSL 样式 → 安装 → Refresh 刷新
- 含 `{Author, Year, Title}` → 加载 `format-references-endnote` skill，检查同目录 `.ris` → 交付
- 纯文本引用（无域代码）→ 跳过此步，B2 已处理

### B4. 视觉格式
`python-docx` 逐段落调字体、字号、行距、段间距、缩进、对齐。用 `para.runs` 设 `font.name` / `font.size`，用 `para.paragraph_format` 设间距。

**/!\** 不要用 `para._element.clear()` 暴力清空含域代码的段落——这会毁掉 Zotero/EndNote 域代码。B4 只改 `w:rPr` 和 `w:pPr`。

---

## 路径 C：MD + 格式适配

输入为 `.md`，需要改期刊格式（可能同时改文风）。

### C1. 检查 PMID 标记
MD 必须含 `[PMID:xxxxxxxx]` 标记才能走此路径。

- 有标记 → 继续
- 无标记 → **提示用户**：先运行 `find-paper-references` 为 MD 插入 PMID 标记，再回到此 skill

### C2. 文风与结构调整
AI 直接修改 MD 文本：
- 去标题编号、调摘要结构、调章节顺序
- 改文风（如需要）

**/!\ 关键约束**：移动或重写包含引用的句子时，`[PMID:xxxxxxxx]` 标记必须跟着原文走，不能丢失、不能改数字、不能增删空格。

### C3. 交给引用排版 skill
根据用户使用的工具加载对应 skill：
- Zotero → `Skill("format-references-zotero")`
- EndNote → `Skill("format-references-endnote")`

两个 skill 做的事：解析 `[PMID:xxxxx]` → 查 PubMed 拿元数据 → 下载目标期刊 CSL 样式 → 输出 DOCX（文内引文和文末参考文献列表已按期刊体例排好）。

**这一步等价于替代路径 B 中 `convert_ref_format.py` 的全部工作**，而且结果更专业——引用排版由 Zotero/EndNote 引擎驱动，不会出现手工拼接 Unicode 上标时的不一致。

### C4. 视觉格式
`python-docx` 在 C3 产出的 DOCX 上套期刊要求的字体、字号、行距、页边距、图表标题位置。

与 B4 相同，只改 `w:rPr` 和 `w:pPr`，不影响 Zotero/EndNote 域代码。

### C5. 产出
最终 DOCX = C2（结构+文风） → C3（引用排版） → C4（视觉格式）

---

## 4. 输出与交付

- DOCX → `doc.save()` → `deliver_attachments`
- MD → `Write()` → `deliver_attachments`
- TXT → `Write()` → `deliver_attachments`
- 对话文本 → 直接输出到对话
- 交付后一句话说清改了哪些

---

## 5. 质量检查

逐项核对：

- [ ] 原稿关键信息完整保留，没有混入示例文本的具体内容
- [ ] 若有文风目标：全篇语气一致，不是只改了开头几段
- [ ] 若有期刊格式目标：
  - [ ] 标题编号与参考文章一致
  - [ ] 摘要结构与参考文章一致
  - [ ] （DOCX 路径）域代码已检测，对应引用 skill 已执行
  - [ ] （MD 路径）PMID 标记完好无损，引用 skill 已执行
  - [ ] 视觉格式（字体/字号/行距）已体现
- [ ] 没有捏造用户材料未支持的"期刊规定"
- [ ] 文件可正常打开，格式无异常（MD 路径下最终 DOCX 打开后 Refresh/Update Citations 可正常刷新）
