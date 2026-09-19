---
name: figure-legend-gen
description: 为科学图表和图形生成标准化图注。当用户上传或请求研究图表、学术论文或数据图表的图注时触发。
  支持条形图、折线图、散点图、箱线图、热图和显微镜图像。本工具仅生成文字图注，不生成可视化图像。
version: "1.0.4"
category: Research
tags: []
author: AIPOCH
license: MIT
status: Draft
risk_level: High
skill_type: Hybrid (Tool/Script + Network/API)
owner: AIPOCH
reviewer: ''
last_updated: '2026-02-06'
displayName: "医学科研图注生成器"
slug: figure-legend-gen
---

# 医学科研图注生成器

为科学研究图表和图像生成符合发表标准的图注。

## 支持的图表类型

| 图表类型 | 描述 |
|----------|------|
| 条形图 | 比较各类别之间的数值 |
| 折线图 | 显示随时间变化的趋势或连续数据 |
| 散点图 | 显示变量之间的关系 |
| 箱线图 | 显示分布和异常值 |
| 热图 | 显示矩阵数据强度 |
| 显微镜图像 | 荧光/共聚焦图像 |
| 流式细胞术 | FACS图和直方图 |
| Western Blot | 蛋白质表达条带 |

## 使用方法

```bash
python scripts/main.py --input <image_path> --type <chart_type> [--output <output_path>]
```

### 参数

| 参数 | 必填 | 描述 |
|------|------|------|
| `--input` | 是 | 图表图像的路径 |
| `--type` | 是 | 图表类型（bar/line/scatter/box/heatmap/microscopy/flow/western） |
| `--output` | 否 | 图注文本的输出路径（默认：标准输出） |
| `--format` | 否 | 输出格式（text/markdown/latex），默认：markdown |
| `--language` | 否 | 语言（en/zh），默认：en |

### 示例

```bash
# Generate legend for bar chart
python scripts/main.py --input figure1.png --type bar

# Save to file
python scripts/main.py --input plot.jpg --type line --output legend.md

# Chinese output
python scripts/main.py --image.png --type scatter --language zh
```

## 图注结构

生成的图注遵循学术规范：

1. **图编号** - 顺序编号
2. **简短标题** - 简洁描述
3. **主要描述** - 图表展示的内容
4. **数据细节** - 关键统计数据/测量值
5. **方法论** - 简要实验背景
6. **统计信息** - P值、显著性标记
7. **比例尺** - 用于显微镜图像

## 技术说明

- **难度**：低
- **依赖项**：PIL, pytesseract（可选OCR）
- **处理方式**：视觉分析用于图表类型检测
- **输出**：默认为结构化markdown

## 参考资料

- `references/legend_templates.md` - 各图表类型的模板
- `references/academic_style_guide.md` - 格式规范

## 风险评估

| 风险指标 | 评估 | 级别 |
|----------|------|------|
| 代码执行 | 使用工具的Python脚本 | 高 |
| 网络访问 | 外部API调用 | 高 |
| 文件系统访问 | 读取/写入数据 | 中 |
| 指令篡改 | 标准提示指南 | 低 |
| 数据泄露 | 数据安全处理 | 中 |

## 安全检查清单

- [ ] 无硬编码凭据或API密钥
- [ ] 无未授权的文件系统访问（../）
- [ ] 输出不暴露敏感信息
- [ ] 已实施提示注入防护
- [ ] API请求仅使用HTTPS
- [ ] 输入已针对允许的模式进行验证
- [ ] 已实施API超时和重试机制
- [ ] 输出目录限制在工作区内
- [ ] 脚本在沙箱环境中执行
- [ ] 错误消息已净化（不暴露内部路径）
- [ ] 依赖项已审核
- [ ] 不暴露内部服务架构
## 前提条件

```bash
# Python dependencies
pip install -r requirements.txt
```

## 评估标准

### 成功指标
- [ ] 成功执行主要功能
- [ ] 输出符合质量标准
- [ ] 优雅处理边缘情况
- [ ] 性能可接受

### 测试用例
1. **基本功能**：标准输入 → 预期输出
2. **边缘情况**：无效输入 → 优雅的错误处理
3. **性能**：大型数据集 → 可接受的处理时间

## 生命周期状态

- **当前阶段**：草稿
- **下次审查日期**：2026-03-06
- **已知问题**：无
- **计划改进**：
  - 性能优化
  - 额外功能支持
