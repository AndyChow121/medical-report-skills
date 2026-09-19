# Medical Report Skills · WorkBuddy Skill Bundle

A bundle of WorkBuddy Skills for medical / life-science research, covering the full chain of **literature search → interpretation → figures → review/manuscript → reference formatting → writing & localization**.

> 中文版见 [README.md](README.md).

## Components

### Literature & Interpretation

| Skill | One-liner |
|---|---|
| [Medical Literature Report](medical-literature-report/README.md) | One-stop pipeline for interpreting English medical literature: search → translate → interpret → report → PPT, with a 9-gate self-check engine and GRADE/PRISMA/patient-evidence generators. |
| [Graph Interpretation](graph-interpretation/README.md) | Interpret medical/life-science charts (ROC, KM, forest, heatmap, scatter, box…) with critique and TRIPOD-AI radar. |
| [Figure Legend Generator](figure-legend-gen/README.md) | Standardized figure legends for bar/line/scatter/box/heatmap/microscopy images. |
| [Literature Close-Read](literature-close-read/README.md) | Structured close-reading report from a paper's full PDF→Markdown text. |
| [Basic Research Design Extractor](basic-research-design-extractor/README.md) | Extract a detailed Markdown experimental plan from a basic-research paper. |
| [Clinical Research Design Extractor](clinical-research-design-extractor/README.md) | Produce a Chinese grant-style clinical study protocol from a clinical paper. |

### Writing & Manuscript

| Skill | One-liner |
|---|---|
| [Biomedical SCI Manuscript](biomedical-sci-manuscript/README.md) | Draft SCI manuscript Methods/Results for bioinformatics, clinical, and basic biomedical studies. |
| [Medical Review Writer](medical-review-writer/README.md) | Workflow engine for fast medical review writing. |
| [Find Paper References](find-paper-references/README.md) | Auto-find references for knowledge points in a manuscript Markdown. |
| [Reference Retrieval](reference-retrieval-skill/README.md) | Build PubMed boolean queries and screen results from a CN/EN intent. |
| [Format References (EndNote)](format-references-endnote/README.md) | Convert `[PMID:xxxx]` markers into Word (.docx) with EndNote CWYW placeholders. |
| [Format References (Zotero)](format-references-zotero/README.md) | Convert `[PMID:xxxx]` markers into Word (.docx) with native Zotero field codes. |

### Writing & Localization (general companions)

| Skill | One-liner |
|---|---|
| [Natural Rewrite](write/README.md) | Strip AI taste from prose; Chinese/English polishing, release notes, social copy, localization review. |
| [Humanizer](humanizer/README.md) | Remove 24 categories of AI-writing smells while preserving meaning and voice. |
| [Style & Journal Rewrite](style-journal-rewrite/README.md) | Restyle a draft to a target voice or journal format (.docx/.md/.txt). |

## Recommended Workflow

1. **Search & design** — `reference-retrieval-skill` / `find-paper-references`; `basic-` / `clinical-research-design-extractor`.
2. **Interpret & read** — `medical-literature-report`; `graph-interpretation` / `figure-legend-gen`; `literature-close-read`.
3. **Write** — `medical-review-writer`; `biomedical-sci-manuscript`.
4. **Polish & adapt** — `write` / `humanizer`; `style-journal-rewrite`.
5. **Format references** — `format-references-endnote` or `format-references-zotero`.

## Install

Copy the skill directories under `medical-report-skills-export/` into your WorkBuddy skills folder:

```bash
# Windows (PowerShell)
Copy-Item -Recurse medical-report-skills-export/* "$env:USERPROFILE/.workbuddy/skills/"

# macOS / Linux
cp -r medical-report-skills-export/* ~/.workbuddy/skills/
```

Most scripts depend only on the Python standard library (managed Python 3.13); some `graph-interpretation` SVG rendering needs `cairosvg` (auto-degrades when missing).

## License

Each skill's license is noted in its own folder; unstated ones default to MIT. The repository as a whole is MIT.
