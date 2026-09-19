---
name: medical-literature-report
description: 面向临床医学、检验医学、护理、药学、公共卫生及生物医学科研，完成英文医学文献的检索筛选、合法全文与补充材料核验、专业中文翻译、研究设计和统计方法解读、批判性评价、证据边界标注、专业实践启示、图文汇报PPT制作及文件归档。适用于按专业方向、关键词、主题、期刊、作者、机构、DOI、PMID等条件查找与比较文献，以及科室学习、研究生组会、文献精读、教学查房和科研汇报。
---

# Medical Literature Report

Build evidence-traceable Chinese literature reports for any medical specialty. Adapt the workflow to the article type, audience, and reporting purpose instead of forcing every paper into one template.

## Route The Request

- Read `references/literature-screening.md` for discovery, comparison, and article selection.
- Read `references/source-acquisition.md` for lawful full-text and supplement acquisition.
- Read `references/medical-translation.md` for Chinese translation or structured close reading.
- Read `references/study-design-appraisal.md` for design-specific methods and critical appraisal.
- Read `references/figures-interpretation.md` to plug `graph-interpretation` into the chart-reading step (PDF/OCR/structured parse/critical appraisal/SVG redraw/TRIPOD-AI radar for ML models).
- Read `references/report-standard.md` before creating or revising a PPT.
- Read `references/evidence-and-practice-interpretation.md` for evidence boundaries and professional implications.
- Read `references/grade-sof.md` to generate a GRADE Summary of Findings table for synthesized evidence.
- Read `references/prisma-flow.md` to render a PRISMA 2020 search-flow diagram for systematic reviews / meta-analyses.
- Read `references/patient-evidence.md` to convert relative effects into patient-friendly NNT/NNH.
- Read `references/orchestrate-figures.md` to drive `graph-interpretation` end-to-end and backfill figure artifacts.
- Read `references/self-critique.md` to draft strengths / limitations / applicability narrative.
- Read `references/verify-report.md` before the final self-check, and run `scripts/verify_report.py` to gate the deliverables against the automatable Completion Gate items.
- Run `scripts/article_inventory.py` to inventory PDFs, Office files, and deliverables.
- Run `scripts/package_deliverables.py` to create a verified delivery folder from a manifest.

## Intake

Accept any combination of:

- specialty, disease, population, intervention, exposure, test, biomarker, or outcome;
- keywords or Boolean expressions;
- clinical question or reporting theme;
- journal name, tier, publisher, author, research group, or institution;
- DOI, PMID, PMCID, exact title, or title fragment;
- publication window, language, article type, access requirement, article count, and audience;
- output request such as candidate table, translation, appraisal, PPT, speaker notes, or archive.

Classify each criterion as:

- `hard`: every selected paper must satisfy it;
- `preferred`: use it to rank otherwise eligible papers.

Infer conservatively when the user does not label criteria. State material assumptions in the candidate table. Ask only when a mistaken assumption would change the result substantially.

## Integrated Workflow

1. Normalize the request into hard filters, preferred filters, audience, and deliverables.
2. Identify the article type and study design before selecting an appraisal path.
3. Search current primary sources. Browse whenever publication status, journal metrics, guidelines, access status, affiliations, or other current facts matter.
4. Build a candidate matrix before recommending papers. Never judge suitability from titles alone.
5. Verify bibliographic identity, article type, study design, population, sample size, methods, outcomes, full-text status, figure completeness, and relevance to the target audience.
6. Obtain the main article and necessary supplements from lawful sources. Never bypass paywalls or access controls.
7. Build a source fact sheet before translating or designing slides. Capture numbers, units, effect estimates, confidence intervals, P values, time points, interventions, assays, eligibility criteria, outcome definitions, and stated limitations.
8. Translate or summarize with consistent medical terminology. Preserve uncertainty, null findings, and study-design language.
9. Apply the design-specific appraisal. Distinguish risk of bias, reporting quality, external validity, and practical relevance.
10. **Read every core result figure through `graph-interpretation`** — extract effect estimates, generate journal-style captions (10 styles: 6 English + 4 Chinese including CMA/CSCO/CEBM/zhcore), render multi-audience explanations, and run figure-level appraisal (KM/Forest/ROC/STARD/CONSORT/MIAME checklists). **For ML/DL prediction models, TRIPOD-AI 14 items are appended automatically;** a 14-dimension radar SVG is also available. File the output in `figures-interpretation.md` and cite it from the figure caption, evidence section, and PPT slides.
11. Build the presentation claim spine before layout: background -> gap -> objective -> design -> methods -> results -> interpretation -> limitations -> implications.
12. Use original article figures and tables as evidence objects. Crop or enlarge without changing data meaning, labels, scales, or context.
13. Separate original findings, Chinese paraphrase, author interpretation, external evidence, and presenter inference.
14. Render and inspect every slide. Verify citations, page count, media integrity, text overflow, figure readability, and PowerPoint opening.
15. Preserve prior versions and package only requested deliverables after hash verification.
16. **Run `scripts/verify_report.py <report_dir>` as the closing self-check.** It automates the Completion Gate: confirms required deliverables, article identity, figure/table provenance, evidence-label and inference separation, overclaim heuristics, PPTX integrity/zero-byte media, delivery-hash consistency, and ML TRIPOD-AI coverage. Fix every ❌ (hard fail) before delivery; treat ⚠️ (manual-review) items as human-visual-check prompts. Add `--delegate-graphint` to also run `graph-interpretation`'s own `verify`.

## Auxiliary Generators

These standalone, zero-dependency scripts (all under `scripts/`, each with a `--self-test`) harden and accelerate the report. Invoke them at the matching workflow stage; each outputs Markdown (and JSON/SVG/docx where relevant) that you fold back into the deck.

- **`grade_sof.py`** — after appraisal of a synthesis: emit a GRADE Summary of Findings table (quality rating + downgrade reasons + benefit/harm). Use for systematic reviews, network meta, or any PICO needing "how sure are we".
- **`prisma_flow.py`** — for systematic reviews / meta-analyses: render the PRISMA 2020 four-stage funnel as SVG + a Markdown count list.
- **`patient_evidence.py`** — when a result is expressed as HR/RR/OR: convert to NNT/NNH and a patient-friendly sentence for the "clinical meaning" slide and shared-decision materials.
- **`orchestrate_figures.py`** — drive `graph-interpretation` end-to-end from a `figure_jobs.json` manifest: generate captions/docx/SVG and (for ML) TRIPOD-AI radar, backfilled into `figures_generated/`. Beyond the `verify_report --delegate-graphint` check, this actually produces the figure artifacts.
- **`self_critique.py`** — draft strengths / limitations / applicability narrative from study-design attributes for the critical-appraisal slide.

All five are best-effort and rule-based; they produce editable drafts, not final methodologic judgments.

## Default Deliverables

Produce the applicable subset:

- candidate literature comparison table;
- main article, supplements, and provenance log;
- structured Chinese translation or close-reading document;
- design-specific critical appraisal;
- source-faithful Chinese PPTX with speaker-ready narrative;
- separately labeled clinical, laboratory, nursing, pharmacy, or public-health implications;
- discrepancy log for conflicts among text, tables, figures, supplements, registries, or metadata;
- verified archive folder with inventory and hashes.

Do not impose a fixed slide count. A focused paper may need 20-25 slides; a complex trial, diagnostic study, omics paper, or meta-analysis may need 30 or more. Completeness and comprehensibility take priority unless the user gives a hard limit.

## Evidence Rules

- Do not fabricate data, significance, mechanisms, thresholds, citations, impact factors, or article availability.
- Do not convert association into causation or statistical significance into clinical importance.
- Do not present exploratory cutoffs as validated clinical decision limits.
- Do not generalize animal, cell, single-center, subgroup, or post hoc findings beyond their evidence.
- Do not redraw or edit a result figure in a way that changes its meaning.
- Label presenter-derived practice implications as inference based on the paper.
- Verify current journal metrics at task time and record metric name, year, and source.
- Flag discrepancies instead of silently choosing a convenient value.
- Do not expose patient-identifiable or confidential data in outputs.
- Treat outputs as research and education materials, not patient-specific medical advice.

## Script Commands

Self-check the report against the automatable Completion Gate items:

```bash
python scripts/verify_report.py <report_dir> --single-paper --out selfcheck.json
python scripts/verify_report.py <report_dir> --fail-on-error          # CI 门禁
python scripts/verify_report.py <report_dir> --delegate-graphint      # 同步委托图解读校验
python scripts/verify_report.py --self-test                           # 合成样本自测
```

GRADE Summary of Findings table:

```bash
python scripts/grade_sof.py sof.json --out sof.md
python scripts/grade_sof.py --self-test
```

PRISMA 2020 flow diagram:

```bash
python scripts/prisma_flow.py prisma.json --out flow.svg --md flow.md
python scripts/prisma_flow.py --self-test
```

Patient-oriented evidence (NNT / NNH):

```bash
python scripts/patient_evidence.py --cer 0.096 --eer 0.091 --event 死亡 --intervention 他汀
python scripts/patient_evidence.py --self-test
```

End-to-end graph-interpretation orchestration (figure artifacts):

```bash
python scripts/orchestrate_figures.py <report_dir> --out orch_summary.json
python scripts/orchestrate_figures.py --self-test
```

Self-critique narrative (strengths / limitations / applicability):

```bash
python scripts/self_critique.py study.json --out critique.md
python scripts/self_critique.py --self-test
```

Inventory deliverables:

```bash
python scripts/article_inventory.py paper.pdf report.pptx --output inventory.json
```

Package deliverables:

```bash
python scripts/package_deliverables.py manifest.json delivery-folder
```

Manifest example:

```json
{
  "articles": [{"source": "/path/paper.pdf", "name": "01_paper.pdf"}],
  "supplements": [],
  "translations": [],
  "presentations": [{"source": "/path/report.pptx"}],
  "source_notes": []
}
```

## Completion Gate

The automatable items below are enforced by `scripts/verify_report.py` (see `references/verify-report.md`); run it as the closing step and fix every ❌ before delivery. Do not call the work complete until:

- selected papers satisfy all hard criteria and recommendation reasons are explicit;
- article identity, design, date, and access status are verified;
- main text and required supplements are complete or missing content is disclosed;
- translated values and terminology match the source;
- appraisal follows the correct study design;
- every result figure or table in the PPT has provenance;
- inference is visibly separated from source conclusions;
- every slide is rendered and visually checked;
- final files open successfully and copied files match their source hashes.
