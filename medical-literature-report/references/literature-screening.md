# Literature Screening

## Search Inputs

Support interchangeable entry modes:

1. Specialty or broad direction: oncology, endocrinology, infectious disease, laboratory medicine, nursing, pharmacy, public health, or basic medicine.
2. Keywords: disease, population, intervention, exposure, test, biomarker, mechanism, or outcome.
3. Topic or question: a PICO, PECO, diagnostic, prognostic, etiologic, or mechanistic question.
4. Journal: exact journal, whitelist, tier, publisher, or metric preference.
5. Author: exact author, corresponding author, research group, or recent output.
6. Institution: hospital, university, laboratory, center, country, or collaboration network.
7. Identifier: DOI, PMID, PMCID, registry number, exact title, or title fragment.

Also accept study design, date range, language, open-access status, desired count, audience, and presentation purpose.

## Search Contract

Write a compact contract before searching:

```text
Hard filters:
- date: 2024-06-01 to present
- type: original research
- population: adults with sepsis

Preferred filters:
- topic: host-response biomarkers
- journals: high-quality critical care or laboratory journals
- complete full text, figures, and supplements
- direct relevance to the reporting audience
```

For a multi-paper report, optimize the set as well as each paper. Prefer a coherent series linked by population, intervention, test, outcome, mechanism, or a clinical-to-translational progression.

## Search Construction

Translate the question into structured concepts and synonyms. Use database-specific fields and controlled vocabulary where available.

Example:

```text
(sepsis OR septic shock)
AND (biomarker OR transcriptomic OR proteomic)
AND (diagnosis OR prognosis OR mortality)
NOT review[pt]
```

Add journal, affiliation, author, date, article-type, and language filters only when they are part of the search contract. Avoid filters so narrow that they hide eligible evidence.

Search more than one relevant source. Cross-check publisher records, PubMed/PMC, Crossref or DataCite, trial registries, guideline repositories, and official data repositories as applicable.

## Candidate Verification

Verify each candidate against the full record or full text:

- exact title, journal, date, DOI, PMID/PMCID, authors, and affiliations;
- article type and study design;
- population, setting, sample size, intervention/exposure/index test, comparator, and outcome;
- specimen, assay, imaging, computational, or statistical methods when central;
- preregistration, protocol, reporting guideline, and data availability when relevant;
- original figures, tables, appendices, and supplements;
- lawful full-text route;
- direct, indirect, or weak relevance to the audience;
- overlap or complementarity with papers already selected.

## Ranking

Reject candidates that fail hard filters. Rank remaining papers transparently using 0-2 scores:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Topic fit | peripheral | partial | direct |
| Audience relevance | minimal | interpretive | practice/method central |
| Study quality | major concerns | usable | strong for design |
| Recency | outside preference | acceptable | target range |
| Journal level | lower | moderate | high |
| Full-text completeness | unavailable | main text only | text + figures/supplements |
| Set coherence | isolated | related | strongly aligned |

Do not hide major weaknesses behind a total score. State decisive selection and exclusion reasons in prose.

## Candidate Table

Use these columns:

```text
Rank | Title | Journal | Date | Article type/design | Population/sample |
Intervention/exposure/test | Outcome | DOI/PMID | Journal metric (year/source) |
Full text/figures | Audience relevance | Criteria match | Concerns | Recommendation
```

For author- or institution-led searches, add author role, corresponding author, affiliation match, and team continuity.

## Recommendation Language

- Use `recommended for reporting` only after reading enough methods and results to judge suitability.
- Explain when a paper is scientifically strong but poorly matched to the audience.
- Distinguish journal influence from study quality.
- Flag date-window or article-type exceptions instead of silently including them.
