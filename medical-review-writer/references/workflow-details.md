# 工作流详细说明

本文档仅说明 **快速版 MedicalReviewSkill** 的唯一工作流。旧版按章节慢速检索流程已废弃。

## 总体目标

- 中文综述总字数 **3000字~5000字~**
- 总参考文献数 **大于30篇**
- 以最少轮次完成完整综述

## 快速版原则

- 先做大纲，再做**一次主题总检索**
- 所有章节默认共享同一个 `global_pool`
- 默认连续写作，不做逐章等待确认
- 只有在证据明显不足时才补检索
- 优先完成整稿，再处理局部优化

## 第一阶段：大纲构建

### 目标

快速搭出稳定结构，避免后续来回返工。

### 要求

- 创建 `outline.md`
- 默认结构：前言 + 3个主章节 + 结论
- 每个主章节设计 `2` 个三级标题
- 标题层级必须清晰

## 第二阶段：主题总检索

### 目标

一次性建立整篇综述共用的文献总库。

### 推荐命令

```bash
python scripts/build_topic_library.py "YOUR TOPIC QUERY" --max 120
```

### 要点

- 输出文件：`references.json`
- 默认标签：`global_pool`
- 不再默认为 `introduction`、`section_1`、`section_2` 分别检索
- 检索完成后运行：

```bash
python scripts/count_references.py
```

- 总 Unique PMIDs 少于 `30` 时，只再补 `1` 次主题总检索

## 第三阶段：连续写作

### 读取文献

```bash
python scripts/read_references.py global_pool
```

该脚本默认展示：

- PMID
- 标题
- 年份
- 检索式
- 摘要摘录

### 写作文件

- `introduction.md`
- `section_1.md`
- `section_2.md`
- `section_3.md`

### 推荐字数

- `introduction.md`：`500-700` 字
- `section_1.md`：`800-1000` 字
- `section_2.md`：`800-1000` 字
- `section_3.md`：`800-1000` 字

### 写作规则

- 每个关键观点都要有 `[PMID: xxx]`
- 每句话最多不超过 `2` 篇引用
- 每个主章节必须拆成 `2` 个子标题
- 不要把整章写成一个超长段落

## 第四阶段：章节校验

每章写完立即运行：

```bash
python scripts/check_section.py "section_1.md"
```

### 处理原则

- 若引用不足，先从现有总库补充引用
- 若确实没有合适证据，再做一次局部补检索

## 第五阶段：摘要与定稿

### 结论

- 创建 `conclusion.md`
- 不要包含引用

### 摘要

- 创建 `abstract.md`
- 第一行必须是完整标题
- 不要包含引用
- 关键词用中文分号 `；`

### 合并

```bash
python scripts/merge_review.py abstract.md introduction.md section_1.md section_2.md section_3.md conclusion.md -o Review_Final.md
```

### 合并后标准

- 总字数 `>= 3000`
- 总参考文献数 `>= 30`

## 第六阶段：格式化引用

```bash
python scripts/format_citations.py Review_Final.md -o Review_Final_Formatted.md
```

完成后检查：

- 引用链接是否正常
- 编号是否连续
- 参考文献列表是否完整
