---

name: clinical-research-design-extractor
description: "Extract a clinical research design from one clinical article and quickly produce a formatted Chinese project-application-style clinical study proposal. Use when the user provides one clinical research paper, abstract, full text, or Methods/Results content and asks for clinical research plan, project proposal, 立项依据, 研究方案, cohort design, trial design, retrospective/prospective study plan, or fast structured clinical proposal with disease burden, study rationale, objectives, methods, endpoints, statistics, ethics, and outputs."
---

# Clinical Research Design Extractor

## Purpose

Use this skill to turn one clinical research article into a detailed but fast Chinese clinical project proposal. The output must follow the application-style format in the template, not a free-form protocol workflow.

Read [clinical-template.md](references/clinical-template.md) when generating the final formatted plan.

## PDF Reading

When the user provides a PDF path, do not read the PDF page-by-page visually. First extract text with the bundled script:

```powershell
python .\\skill\\clinical-research-design-extractor\\scripts\\extract\_pdf\_text.py <paper.pdf> --out <paper.extracted.md>
```

Then use the extracted Markdown as the article source. Prefer sections titled Abstract, Introduction, Methods, Results, Discussion, Tables/Figures, and Supplementary methods when present. If extraction returns very little text, tell the user the PDF may be scanned and ask for OCR text or a text-based PDF.

## Input Handling

Accept any of these as source material:

* One text-based PDF article path.
* Full text of one clinical research article.
* Abstract plus Methods/Results.
* User notes summarizing one clinical paper.
* Extracted trial/cohort/case-control/diagnostic/prognostic study methods and outcomes.

If the input contains multiple papers, choose the primary one if obvious; otherwise ask which single article to use.

## Process

1. Identify the original article's clinical question, disease, population, exposure/intervention, comparator, outcome, follow-up, and study design.
2. Extract the PICO/PECO logic:

   * Population,
   * Intervention/exposure/test/predictor,
   * Comparator/control/reference standard,
   * Outcomes,
   * observation window or follow-up.
3. Determine study type: randomized trial, prospective cohort, retrospective cohort, case-control, cross-sectional, diagnostic study, prognostic model, risk-factor study, treatment comparison, real-world study, or registry/database study.
4. Convert the article into a formatted clinical project proposal:

   * keep the core clinical logic,
   * avoid copying article wording,
   * place details under the required headings: 立项依据, 研究方案, 统计方法, 伦理说明, 团队与资源保障, 预算与成果产出,
   * use `待定` for missing operational details.
5. Output in the fixed detailed format from the reference template.

## Output Rules

* Use Chinese by default. Preserve the required Chinese heading structure unless the user explicitly asks for another format.
* Do not use basic-experiment fields such as `目的/模型/样本/检测方法` as the main structure.
* Use clinical protocol fields: research question, cohort source, eligibility, grouping, exposure/intervention definition, endpoint definition, covariates, statistical model, subgroup/sensitivity analysis, and risk control.
* Keep sections concise, but make `研究方法`, `研究程序`, `观察指标或结局`, and `统计分析方法` granular enough to reproduce the article logic.
* Do not invent sample size, follow-up duration, drug dosage, cutoff, center count, missing-data method, or statistical effect size when absent. Use `待定`.
* Distinguish what the article did from what the proposed plan will do.
* Include primary endpoint, secondary endpoints, key confounders, subgroup analyses, sensitivity analyses, and data-quality controls.
* Always output `前期研究基础【固定输出“略”】` as `略`, `(三)团队与资源保障` as `略`, and the budget part under `(四)预算与成果产出` as `略`.

