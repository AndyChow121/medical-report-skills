# 批判性评价 checklist（appraisal）

`scripts/appraisal.py` 按图表类型匹配评价框架，输出 `AppraisalResult`。

## 框架映射

| 图表 | 评价框架 | 条目数 |
|------|----------|--------|
| kaplan_meier | CONSORT + Cochrane RoB 2 | 6 |
| forest_plot | Cochrane + GRADE | 7 |
| roc_curve | STARD | 6 |
| box_plot | CONSORT + Cochrane | 5 |
| scatter_plot | STARD + Cochrane | 4 |
| bar_chart | CONSORT + Cochrane | 4 |
| heatmap | MIAME | 4 |
| volcano_plot | MIAME + Cochrane | 4 |

## 框架释义

### CONSORT

随机对照试验报告规范（Consolidated Standards of Reporting Trials）。
重点：随机化、盲法、样本量、随访、风险表。

### Cochrane RoB 2

Cochrane 偏倚风险评估工具第 2 版。
5 域：随机化过程、偏离既定干预、缺失数据、结局测量、报告结果选择。

### GRADE

证据质量分级系统（Grading of Recommendations Assessment, Development and Evaluation）。
从 RCT 开始，每降一级因素（偏倚、不一致性、间接性、不精确、发表偏倚）减一档。
观察性研究起点低，但大效应可上调。

### STARD

诊断准确性研究报告标准（Standards for Reporting Diagnostic Accuracy Studies）。
重点：参考标准、盲法、截断点说明、样本量与事件数。

### MIAME

微阵列实验最小信息标准（Minimum Information About a Microarray Experiment）。
适用于表达矩阵/组学热图：归一化、聚类、注释、原始数据可获取性。

### TRIPOD

多变量预测模型透明报告规范（TRansparent reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis），2015 年发布。
**适用范围**：开发 / 验证多变量诊断或预后预测模型的研究。
**核心 22 条**，精简为 7 项机器可判定的关键评估：

| 编号 | 评估要点 |
|------|----------|
| TRI-1 | 研究类型：development / validation / both 是否声明 |
| TRI-2 | discrimination：C 统计量 / AUC + 95% CI |
| TRI-3 | calibration：calibration plot / Hosmer-Lemeshow / slope+intercept |
| TRI-4 | 模型规格：公式 / 截距 / 系数 |
| TRI-5 | 内验证：bootstrap / cross-validation / split-sample |
| TRI-6 | 外部验证：独立队列（不要和训练集共享病例） |
| TRI-7 | 临床效用：decision curve / NRI / IDI |

**Calibration plot 散点专用条目**（挂在 `scatter_plot`）：

| 编号 | 评估要点 |
|------|----------|
| TRI-3c | calibration plot：x=预测概率，y=实际概率，按十分位分组 |
| TRI-8 | calibration slope 与 intercept：理想为 y=x（slope=1, intercept=0） |
| TRI-9 | Brier score / 平均绝对误差：综合判别+校准的整体度量 |

**判读规则**：
- 论文未提及上述任一项 → 默认不通过
- 仅做内部验证 → TRI-5 通过，TRI-6 不通过
- 仅报告 discrimination 未报告 calibration → TRI-3 不通过
- 模型性能"好"但未见 DCA/NRI/IDI → TRI-7 不通过，临床推广价值待考

## 自动判定 vs 人工判定

可机器判定的条目（来自 `StatisticalSummary.raw` 字段）：

- KM-2/3/4：风险表、log-rank p、Schoenfeld p
- FP-3/4：I²、模型选择
- ROC-1/4：AUC CI、敏感度/特异度
- BAR-2/3：y 轴截断、样本量
- VOL-1/2：阈值与 FDR 校正

其余条目由人工评估（标记 `passed=True/False`，并填 `note`）。

## 整体得分

`overall_score = n_passed / (n_passed + n_failed)`，未评估条目（`passed=None`）不计入分母。
- 0.8-1.0：质量良好，可信度较高
- 0.5-0.8：中等质量，需关注未通过条目
- < 0.5：质量不足，谨慎引用

## 在带教中使用

```bash
python main.py appraise --type kaplan_meier --data sample.json
```

输出格式（人读友好）：

```
图表类型: kaplan_meier
评价框架: CONSORT + Cochrane RoB 2
条目: 6（已评估 3，未评估 3）
得分: 100.0%

  [·] KM-1 是否报告中位生存期与 95% CI？
  [✓] KM-2 是否提供风险表（at-risk table）？
  [✓] KM-3 是否给出 log-rank p 值？
  ...
```

JSON 模式（`--json`）便于后续处理：

```json
{
  "chart_type": "kaplan_meier",
  "framework": "CONSORT + Cochrane RoB 2",
  "n_items": 6,
  "n_passed": 3,
  "overall_score": 1.0,
  "items": [...]
}
```
