---

name: basic-research-design-extractor
description: "Extract a basic biomedical research design from one article and quickly produce a detailed Markdown-document experimental plan. Use when the user provides one basic research paper, abstract, full text, or Methods/Results content and asks for topic design, study design extraction, experimental protocol, simplified proposal, replication plan, mechanism-validation plan, markdown plan or a fast structured research plan with experiments split by assay and reproduction step."
---

# Basic Research Design Extractor

## Purpose

Use this skill to turn one basic biomedical research article into a structured Markdown experimental proposal. Prioritize speed and readability, but make the plan look substantial: split each major experiment into replication-level subexperiments, and separate different detection methods instead of compressing them into one line.

Read [design-template.md](references/design-template.md) when generating the final formatted plan.

## PDF Reading

When the user provides a PDF path, do not read the PDF page-by-page visually. First extract text with the bundled script:

```powershell
python .\\skill\\basic-research-design-extractor3\\scripts\\extract\_pdf\_text.py <paper.pdf> --out <paper.extracted.md>
```

Then use the extracted Markdown as the article source. Prefer sections titled Abstract, Introduction, Methods, Results, Discussion, Figures/Tables, and Supplementary methods when present. If extraction returns very little text, tell the user the PDF may be scanned and ask for OCR text or a text-based PDF.

## Input Handling

Accept any of these as source material:

* One text-based PDF article path.
* Full text of one basic research article.
* Abstract plus Methods/Results.
* Screenshots or extracted text from a paper, if enough experimental detail is visible.
* User notes summarizing one article.

If the input contains multiple papers, choose the primary one if obvious; otherwise ask the user which single article to use.

## Process

1. Identify the article's core research question, disease/model context, key molecule/pathway/cell type, and main conclusion.
2. Extract the original study design:

   * hypothesis,
   * experimental model,
   * intervention or perturbation,
   * grouping,
   * detection methods,
   * outcome indicators,
   * mechanism-validation logic.
3. Convert the article into a new concise experimental plan:

   * keep the same research logic,
   * avoid copying the exact article wording,
   * anonymize specific genes, proteins, transcription factors, enzymes, pathways, compounds, and non-coding RNAs with generic labels,
   * make the plan executable and easy to scan,
   * include only experiments supported or naturally implied by the article,
   * break broad ideas into concrete experiment modules and reproduction steps.
4. Output in the fixed simplified format from the reference template.

## Output Rules

* Use Chinese by default unless the user requests English.
* Output as a Markdown document, not as plain prose and not inside a fenced code block. Start with `# <课题名称>`, then use `##`, `###`, and `####` headings.
* Do not output specific gene/protein/molecule names from the paper unless the user explicitly asks to preserve them. Replace them with generic labels such as `基因A`, `转录因子B`, `酶C`, `通路D`, `lncRNA-E`, `miRNA-F`, `蛋白G`, `药物H`, `代谢物I`.
* Keep the output concise at the paragraph level but detailed at the experiment level; each subexperiment must include purpose, model, grouping, sample/material, detection method, detection indicators, expected result, and notes.
* Do not invent unmentioned cell lines, animal strains, doses, time points, antibodies, primers, or sample sizes. Use `待定` when not available.
* Distinguish original article evidence from proposed follow-up design.
* Prefer 4-7 major experiments, each with 2-5 subexperiments arranged in reproduction order.
* Split different assays into separate subexperiments. Do not merge qPCR, western blot, IF/IHC, flow cytometry, EdU, CCK-8, Transwell, wound healing, animal phenotype, or sequencing analysis into one generic method line.
* Include controls, readouts, quantitative indicators, and step labels such as `实验1.1`, `实验1.2`, `实验2.1` for each subexperiment.
* Write expected results as design targets or screening criteria, not as fixed claims copied from the article. Prefer wording such as `筛选...进入下一步`, `预期获得...候选对象`, `验证...是否改变`, `若结果符合预期则进入机制验证`.
* End with a short feasibility/risk note.

