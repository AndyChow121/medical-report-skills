---
name: Medical Review Writer
description:  >
  专门用于快速完成医学综述的工作流引擎。只要用户需求涉及“写医学综述”“写文献综述”“基于 PubMed 写 review”或类似任务，请直接使用本技能。此版本只保留快速模式：大纲构建 → 主题总检索 → 连续写作 → 章节校验 → 合并定稿 → 引用格式化。
  Do NOT trigger for casual queries: "深度研究"
---

# Medical Review Writer

## 核心定位

默认目标：

- 中文综述总字数 **3000字~5000字~**
- 总参考文献数 **大于30篇**
- 保持完整文件流转：`outline.md` → `references.json` → `introduction.md` / `section_*.md` → `conclusion.md` / `abstract.md` → `Review_Final.md` → `Review_Final_Formatted.md`

## 唯一工作流

严格按以下六阶段执行。

### 第一阶段：大纲构建

1. 围绕主题创建 `outline.md`
2. 默认结构固定为：
   - `前言`
   - `3个主章节`
   - `结论`
3. 每个主章节必须有 `2` 个三级标题 `###`
4. 大纲一次确认后立即进入检索，不做反复重写

### 第二阶段：主题总检索

1. 不再按章节分别联网检索
2. 统一执行：
   `python scripts/build_topic_library.py "TOPIC QUERY" --max 60`
3. 检索结果统一写入 `references.json`
4. 默认文献标签为 `global_pool`
5. 运行：
   `python scripts/count_references.py`
6. 若总 Unique PMIDs 少于 `30`，只允许再补 `1` 次主题总检索，优先优化检索词，不要拆成多章节慢检索

### 第三阶段：连续写作

1. 统一读取总库：
   `python scripts/read_references.py global_pool`
2. 后续所有章节默认复用同一个总库写作
3. 创建：
   - `introduction.md`
   - `section_1.md`
   - `section_2.md`
   - `section_3.md`
4. 推荐字数：
   - `introduction.md`：`500-700` 字
   - 每个 `section_*.md`：`800` 字
5. 所有客观观点均使用 `[PMID: xxx]` 标注
6. 不要把整章写成单个长段落
7. 不做逐章等待确认，章节达标后直接进入下一章

### 第四阶段：章节校验

1. 每章写完后运行：
   `python scripts/check_section.py "section_1.md"`
2. 只有在明显证据不足时，才允许做一次局部补检索
3. 局部补检索仍优先补入总库，而不是恢复旧版按章节多轮联网

### 第五阶段：摘要与定稿

1. 创建 `conclusion.md`
   - 不要包含引用
2. 创建 `abstract.md`
   - 第1行写入综述标题（一级标题 `# `），格式如 `# 综述主题研究进展（XXXX-XXXX）`
   - 第2行空行
   - 第3行写入 `## 摘要`
   - 摘要正文
   - **不要包含引用**
   - 关键词使用中文分号 `；`
3. 合并：
   `python scripts/merge_review.py abstract.md introduction.md section_1.md section_2.md section_3.md conclusion.md -o Review_Final.md`
4. 合并后总稿必须达到：
   - 总参考文献数 `>= 30`

### 第六阶段：格式化引用

1. **前置检查**：确认 `Review_Final.md` 中无残留的复合PMID格式：
   ```bash
   grep -c 'PMID:.*,.*PMID:' Review_Final.md
   # 必须返回 0，否则先修初稿
   ```
2. 运行：
   `python scripts/format_citations.py Review_Final.md -o Review_Final_Formatted.md`
3. **终验**：确认终稿中无残留 `[PMID:` 标记：
   ```bash
   grep -c '\[PMID:' Review_Final_Formatted.md
   # 必须返回 0，否则说明脚本未完成所有替换
   ```
4. 一旦发现终稿有问题（如残留 `[PMID:` 或引用格式不完整），**禁止直接修改终稿**。必须回到初稿定位问题根源、修改初稿，然后**重新跑脚本生成终稿**。终稿必须始终由脚本产出。

## 强制规则

- **只保留快速版**：不要默认采用旧版按章节检索流程
- **总库优先**：所有章节默认共享 `global_pool`
- **控制上下文**：默认只读取精简文献视图，不反复展开全部摘要
- **引用规范**：正文与前言使用 `[PMID: xxx]`；摘要与结论不使用引用
- **PMID 格式规则**：每个PMID必须放在独立的 `[PMID: xxx]` 中，**禁止使用复合格式**如 `[PMID: xxx, PMID: yyy]`。多个引用相邻时写为 `[PMID: xxx] [PMID: yyy]`（中间加空格）。这条规则在**每章写作时就要遵守**，不要等合并后再统一修。`format_citations.py` 的 regex 只匹配 `[PMID:\s*(\d+)]`，复合格式会被跳过
- **终稿不可直接编辑**：终稿 `Review_Final_Formatted.md` 必须由 `format_citations.py` 生成。如果格式有误，必须修改初稿 `Review_Final.md` 后重新运行脚本，**严禁直接编辑终稿文件**
- **结构稳定**：默认 `前言 + 3个主章节 + 结论 + 摘要`
- **优先成稿**：先完整交付，再考虑局部精修

## 资源文件

- `scripts/build_topic_library.py`：一次性建立主题总库
- `scripts/read_references.py`：读取 `global_pool` 精简文献视图
- `scripts/check_section.py`：检查单章节字数与引用数
- `scripts/merge_review.py`：合并并检查总稿字数与总引用数
- `scripts/format_citations.py`：格式化 PMID 引用
- `references/workflow-details.md`：快速版工作流详细说明
- `references/citation-guide.md`：引用格式说明
