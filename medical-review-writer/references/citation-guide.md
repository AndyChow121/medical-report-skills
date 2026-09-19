# 引用格式指南

本文档详细说明MedicalReviewSkill中使用的引用格式规范和最佳实践。

## 引用格式概述

MedicalReviewSkill使用两阶段引用系统：

1. **撰写阶段**：使用简化的 `[PMID: xxx]` 格式
2. **定稿阶段**：自动转换为标准的带编号格式和完整参考文献列表

## 撰写阶段引用格式

### 基本格式

```markdown
句子内容 [PMID: 123456]。
```

### 多个引用

**方法1：连续引用**
```markdown
句子内容 [PMID: 123456, PMID: 234567]。
```

**方法2：分别引用**
```markdown
句子内容 [PMID: 123456][PMID: 234567]。
```

### 引用位置

**推荐做法**：
- 引用放在句末，句号之前
- 一个观点对应一个或多个引用
- 保持引用与内容的紧密关联

```markdown
✅ 正确示例：
糖尿病是一种常见的代谢性疾病 [PMID: 123456]。

❌ 错误示例：
[PMID: 123456] 糖尿病是一种常见的代谢性疾病。
```

## 定稿阶段引用格式

经过 `format_citations.py` 处理后，引用会被转换为：

### 行内引用格式

```markdown
句子内容 [[1]](https://pubmed.ncbi.nlm.nih.gov/123456/)。
```

- `[[1]]`：引用编号
- 超链接指向PubMed原文

### 参考文献列表

文档末尾自动生成APA格式的参考文献列表：

```markdown
## References

1. Author A, Author B, Author C. Title of the article. *Journal Name*. 2023;10(2):123-145. doi:10.1234/journal.2023.123456
2. Author D, Author E. Another article title. *Another Journal*. 2022;15(3):234-256. PMID: 234567
```

## 引用管理最佳实践

### 1. 何时引用

**必须引用的情况**：
- 提出具体数据或统计结果
- 引用他人的研究发现
- 描述特定的研究方法
- 提及争议性观点
- 引用权威定义或分类

**无需引用的情况**：
- 普遍接受的常识
- 自己的总结和分析
- 逻辑推理和讨论

### 2. 引用数量

**建议**：
- Introduction：每2-3句一个引用
- Methods/Mechanisms：每个关键观点都需要引用
- Results/Clinical Evidence：大量引用，几乎每句都需要
- Discussion/Conclusion：适度引用，主要引用关键发现

### 3. 引用质量

**优先级**（从高到低）：
1. 系统性综述和Meta分析
2. 随机对照试验（RCT）
3. 队列研究
4. 病例对照研究
5. 病例报告
6. 专家意见

**时效性**：
- 优先引用近5年文献
- 经典文献不受时限限制
- 最新进展引用1-2年内文献

### 4. 引用平衡与频率

**引用频率限制**（重要）：
- **原则**：尽量引用不同的文献，展示研究的广度。
- **限制**：单篇文献的引用次数建议 **不超过 2 次**。
- **上限**：绝对不超过 3 次。如果某篇文献非常重要需要多次引用，请尝试寻找其他支持相同观点的文献替换部分引用。

**避免**：
- 过度引用某一团队的研究
- 忽略相反的证据
- 只引用支持性文献

建议：
- 平衡不同观点的文献
- 包含正面和负面结果
- 引用来自不同研究团队的工作

## format_citations.py 脚本使用

### 基本用法

```bash
python scripts/format_citations.py Review_Final.md -o Review_Final_Formatted.md
```

### 参数说明

- 第一个参数：输入文件（必需）
- `-o` 或 `--output`：输出文件（可选，默认为 `输入文件名_Formatted.md`）

### 脚本工作流程

1. **扫描文档**：识别所有 `[PMID: xxx]` 格式的引用
2. **去重编号**：为每个唯一的PMID分配编号
3. **API查询**：调用PubMed API获取完整引文信息
4. **替换引用**：将简化格式替换为编号+链接格式
5. **生成列表**：在文档末尾添加完整的参考文献列表

### 处理时间

- 取决于引用数量和网络速度
- 脚本按批次请求元数据，30篇左右参考文献通常可在较短时间内完成
- 若文献量显著增加，格式化时间也会随之上升

### 错误处理

**常见错误**：

1. **PMID格式错误**
   ```
   Warning: Invalid PMID format: [PMID: abc123]
   ```
   解决：检查PMID是否全为数字

2. **网络连接问题**
   ```
   Error: Failed to fetch PMID 123456
   ```
   解决：检查网络连接，稍后重试

3. **PMID不存在**
   ```
   Warning: PMID 999999 not found in PubMed
   ```
   解决：核实PMID是否正确

## 引用格式示例

### 示例1：单个引用

**撰写阶段**：
```markdown
糖尿病的全球患病率持续上升，已成为重要的公共卫生问题 [PMID: 12345678]。
```

**定稿阶段**：
```markdown
糖尿病的全球患病率持续上升，已成为重要的公共卫生问题 [[1]](https://pubmed.ncbi.nlm.nih.gov/12345678/)。
```

### 示例2：多个引用

**撰写阶段**：
```markdown
多项研究表明，生活方式干预可以有效预防糖尿病 [PMID: 12345678, PMID: 23456789, PMID: 34567890]。
```

**定稿阶段**：
```markdown
多项研究表明，生活方式干预可以有效预防糖尿病 [[1]](https://pubmed.ncbi.nlm.nih.gov/12345678/),[[2]](https://pubmed.ncbi.nlm.nih.gov/23456789/),[[3]](https://pubmed.ncbi.nlm.nih.gov/34567890/)。
```

### 示例3：同一文献多次引用

**撰写阶段**：
```markdown
Smith等人的研究 [PMID: 12345678] 显示...后续分析进一步证实了这一发现 [PMID: 12345678]。
```

**定稿阶段**：
```markdown
Smith等人的研究 [[1]](https://pubmed.ncbi.nlm.nih.gov/12345678/) 显示...后续分析进一步证实了这一发现 [[1]](https://pubmed.ncbi.nlm.nih.gov/12345678/)。
```

## APA格式规范

### 期刊文章

```
Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Title of Periodical*, volume(issue), pages. https://doi.org/xx.xxxx/xxxxx
```

### 在线文章（无DOI）

```
Author, A. A. (Year). Title of article. *Title of Periodical*, volume(issue), pages. PMID: xxxxxxxx
```

### 书籍章节

```
Author, A. A. (Year). Title of chapter. In B. B. Editor (Ed.), *Title of book* (pp. xxx-xxx). Publisher.
```

## 质量检查清单

撰写完成后，检查以下项目：

- [ ] 所有关键观点都有引用支持
- [ ] PMID格式正确（全部为数字）
- [ ] 没有重复或冗余的引用
- [ ] 引用位置恰当（通常在句末）
- [ ] 引用来源多样化
- [ ] 包含近期文献（近5年）
- [ ] 包含高质量证据（Meta分析、RCT等）

## 常见问题

### Q: 如何引用同一篇文章的不同部分？
A: 使用同一个PMID即可，格式化后会自动合并为同一编号。

### Q: 可以手动添加参考文献吗？
A: 不建议。所有引用应通过PMID标注，由脚本自动生成参考文献列表。

### Q: 引用过多会不会影响阅读？
A: 适度引用即可。一般每段2-4个引用足够。

### Q: 如何处理无法获取的PMID？
A: 检查PMID是否正确，或者替换为其他相关文献的PMID。

### Q: 格式化后可以再修改吗？
A: 可以，但需要注意不要破坏引用编号的连续性。建议在格式化前完成所有修改。
