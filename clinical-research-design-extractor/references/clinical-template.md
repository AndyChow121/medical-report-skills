# Clinical Template

Use this template to produce a formatted Chinese clinical project proposal from one article. The proposal should look like a compact application document: structured, detailed enough to execute, but not as long as a full ethics protocol.

## Extraction Checklist

Extract only what the article supports:

- Disease, clinical problem, and disease burden.
- Target population and care setting.
- Study design: RCT, prospective cohort, retrospective cohort, case-control, cross-sectional, diagnostic accuracy, prognostic model, survival analysis, treatment comparison, risk factor analysis.
- Data source: single-center, multicenter, database, registry, inpatient/outpatient, trial, claims data, EHR, imaging system, pathology archive, or laboratory system.
- Exposure, intervention, biomarker, diagnostic test, treatment strategy, predictor, or risk factor.
- Comparator, control group, or reference standard.
- Inclusion and exclusion criteria.
- Follow-up or observation window.
- Primary and secondary outcomes.
- Key covariates, confounders, and stratification variables.
- Statistical methods, subgroup analysis, sensitivity analysis, and bias control.

## Required Output Format

```markdown
## 项目名称
<一句话题目，突出疾病/人群/暴露或干预/主要结局/研究设计>

## 摘要
<300-500字。包括疾病背景、临床问题、研究目的、研究设计、研究对象、核心观察指标、统计方法和预期意义。>

## 申请人及团队信息
略

## 关键词
- ...
- ...
- ...
- ...

## (一)立项依据

### 1. 疾病负担
<说明疾病流行情况、患者结局、医疗负担、诊疗痛点。若文献未提供具体数值，用概括性表达，不编造数据。>

### 2. 国内外研究进展
<围绕文献主题总结已有研究：当前诊断/治疗/预测/风险评估现状，已有证据，仍存在的问题。>

### 3. 前期研究基础
略

### 4. 科学假说
<用1段或2-3条提出可检验假说，明确研究对象、暴露/干预/预测因素、结局和可能机制或临床解释。>

### 5. 研究创新性与科学意义
- 创新性：...
- 科学意义：...
- 临床意义：...

## (二)研究方案

### 1. 研究目的
- 主要目的：...
- 次要目的：
  1. ...
  2. ...
  3. ...

### 2. 研究方法

#### 2.1 研究设计
- 研究类型：...
- 数据来源：...
- 研究场景：...
- 研究时间范围：...
- 随访或观察窗口：...
- 分组/比较逻辑：...
- 主要效应指标：...

#### 2.2 研究对象
- 目标人群：...
- 起始人群：...
- 索引事件/索引日期：...
- 暴露/干预/检测对象：...
- 对照或参照人群：...
- 预期样本量：待定（依据主要结局和预期效应量估算）

#### 2.3 纳入标准
1. ...
2. ...
3. ...
4. ...

#### 2.4 排除标准
1. ...
2. ...
3. ...
4. ...

#### 2.5 研究程序
1. 数据来源确认：明确病例来源、数据库、登记系统、病历模块或随访系统。
2. 研究队列构建：按时间范围、索引事件、纳排标准筛选目标人群。
3. 分组或暴露定义：定义暴露/干预/检测/预测因素，明确分类方式、测量时间窗和数据字段。
4. 协变量收集：提取人口学资料、疾病严重程度、合并症、既往治疗、实验室、影像、病理及用药信息。
5. 结局判定：按预设标准判定主要结局、次要结局和安全性结局。
6. 数据质控：处理缺失值、异常值、重复记录、随访不完整和结局判定不一致。
7. 统计分析：完成描述性分析、组间比较、主效应模型、亚组分析和敏感性分析。

#### 2.6 观察指标或结局
- 主要结局：...
- 次要结局：
  1. ...
  2. ...
  3. ...
- 安全性结局（如适用）：...
- 暴露/干预指标：...
- 关键协变量：
  1. 人口学变量：...
  2. 疾病相关变量：...
  3. 治疗相关变量：...
  4. 实验室/影像/病理变量：...
- 质量控制指标：...

### 3. 研究统计方法

#### 3.1 样本量估算
<说明样本量估算依据。若原文未提供参数，写：样本量暂定为待定，后续将依据主要结局发生率、预期效应量、α=0.05和检验效能80%或90%进行估算。>

#### 3.2 统计分析方法
1. 描述性分析：...
2. 组间比较：...
3. 主效应分析：...
4. 混杂因素控制：...
5. 亚组分析：...
6. 敏感性分析：...
7. 缺失值处理：...
8. 统计软件与显著性标准：...

### 4. 临床伦理学说明
<说明研究类型、知情同意、隐私保护、数据脱敏、伦理审批和风险控制。回顾性研究可说明拟申请知情同意豁免；前瞻性或干预研究需说明知情同意和安全监测。>

## (三)团队与资源保障
略

## (四)预算与成果产出

### 预算
略

### 成果产出
- 论文产出：...
- 数据或模型产出：...
- 临床转化产出：...
```

## Granularity Rules

- Preserve the required headings exactly.
- The output must not revert to a `阶段/任务` protocol unless the user asks.
- Keep high granularity inside `2.5 研究程序`, `2.6 观察指标或结局`, and `3.2 统计分析方法`.
- Do not collapse exposure definition, endpoint definition, covariate definition, and statistical analysis into one paragraph.
- If details are missing, write `待定` rather than omitting the field.
- `前期研究基础`, `(三)团队与资源保障`, and `预算` must output `略`.

## Study Type Adaptation

- For randomized trials, emphasize randomization, allocation concealment, blinding, intervention protocol, adherence, safety endpoints, per-protocol and intention-to-treat analyses.
- For retrospective cohorts, emphasize data source, index date, exposure window, follow-up window, confounder control, missing data, and sensitivity analysis.
- For prognostic models, emphasize outcome definition, candidate predictors, training/validation split, discrimination, calibration, decision curve analysis, and external validation.
- For diagnostic studies, emphasize index test, reference standard, threshold selection, sensitivity, specificity, AUC, PPV/NPV, likelihood ratios, and decision curve analysis.
- For risk factor studies, emphasize exposure definition, outcome definition, covariates, multivariable regression, subgroup analysis, interaction tests, and causal language limits.
- For treatment comparisons, emphasize indication bias, baseline balance, propensity score methods, treatment switching, adherence, and safety outcomes.

## Writing Style

- Use direct clinical project-application language.
- Use short but information-dense bullets.
- Avoid long literature-review paragraphs.
- Avoid overclaiming causality for observational studies.
- Do not include citations unless the user asks.
