---

name: biomedical-sci-manuscript
description: "Create SCI manuscript drafts for biomedical Methods/Results material across three study types: bioinformatics, clinical medicine, and basic biomedical research. Use when asked to translate or reorganize Methods/Results, generate a manuscript title, build Introduction/Discussion outlines, search PubMed literature, draft Abstract/Introduction/Discussion sections with NLM-style numbered inline citations, assemble NLM-style references, or format a full Chinese or English biomedical manuscript."
---

# Biomedical SCI Manuscript

## Manuscript Drafting

Use this skill to turn biomedical Methods/Results material into a structured SCI manuscript draft. Determine the study type first:

* `bioinformatics`: omics, radiomics, computational biology, immune infiltration, pathway enrichment, model validation, subtype identification, drug prediction, causal inference, or integrated bioinformatics analyses.
* `clinical`: patient cohorts, diagnosis, treatment, drug efficacy, adverse events, prognosis, biomarkers, pathology, clinical mechanisms, statistical analysis, or risk factors.
* `basic`: molecular mechanisms, signaling pathways, gene function, cell behavior, immunology, biochemistry, pharmacology, structural biology, developmental biology, pathophysiology, microbiology, metabolism, epigenetics, stem cells, cancer biology, biomaterials, genome editing, or synthetic biology.

Ask for the study type only if it cannot be inferred from the supplied material and choosing incorrectly would change the output. Otherwise infer it and proceed.

## References

Read these files as needed:

* [manuscript-guide.md](references/manuscript-guide.md): common drafting sequence, citation rules, section assembly, and formatting.
* [study-types.md](references/study-types.md): study-type-specific outline prompts, result categories, discussion emphasis, and title rules.
* [pubmed-search.md](references/pubmed-search.md): PubMed API search workflow using NCBI E-utilities, query construction, screening, and evidence extraction.

## Procedure

1. Validate that the input is biomedical or scientific manuscript material. If not, respond with `## 未识别到提供的资料`.
2. Identify target language (`中文` or `English`) and study type (`bioinformatics`, `clinical`, or `basic`).
3. Normalize the Methods/Results text in the target language:

   * Chinese: `## 材料与方法`, `## 结果`, optional `## 参考文献`.
   * English: `## Materials and Methods`, `## Result`, optional `## References`.
   * Remove citation superscripts from Methods/Results unless preservation is requested.
   * Preserve useful tables and place table notes below tables.
4. Generate a Chinese outline first for full manuscripts, even when the final manuscript is English.
5. Use the study-type rules to generate:

   * a title,
   * an Introduction outline,
   * a Discussion outline with at least five result-focused discussion points.
6. Retrieve or use literature for the Introduction and Discussion. If no literature set is supplied, use module-based fast PubMed search by default: plan 2-3 modules that need citations, run one small ESearch per module, then one batched ESummary and one batched EFetch for selected PMIDs. Typical modules are disease/background, study object or method, and discussion mechanism/comparison. Keep at most 60 retained PubMed candidates and usually 10-40 final references. Do not use web search, do not open E-utilities URLs as webpages, do not inspect PubMed/PMC pages, and do not fetch full text. Use only API-returned metadata and abstracts as citation evidence. Prefer PubMed records with PMID. Do not fabricate citations.
7. Draft sections in this order: Abstract, Introduction, Discussion opening, core Discussion, limitations/conclusion.
8. Assemble the final manuscript with NLM-compatible citation-sequence inline citations such as `\[1]`, `\[2,3]`, and generate an NLM-style reference list only from cited literature.

## Quality Bar

* Use academic, publication-ready biomedical language in the requested language.
* Keep claims traceable to the supplied Methods/Results or verified literature.
* Do not invent disease burden, mechanisms, genes, pathways, datasets, sample sizes, p values, PMIDs, DOI values, references, or findings.
* Cite only when referring to published external findings. Do not cite claims that describe the present study's own design, novelty, results, or implications.
* If literature access is unavailable, mark citations as requiring verification instead of inventing references.

