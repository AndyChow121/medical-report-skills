# Source Acquisition And Verification

## Source Priority

Use lawful sources in this order when practical:

1. publisher full text or official PDF;
2. PubMed Central or another official open repository;
3. institutional repository;
4. accepted author manuscript;
5. trial, protocol, data, or supplement repository linked by the article;
6. author-provided lawful copy.

Do not bypass paywalls, authentication, robots restrictions, or access controls. If full text cannot be obtained lawfully, disclose that limitation and propose an accessible substitute.

## Required Materials

Seek the applicable materials:

- main article PDF or official structured full text;
- supplementary figures, tables, methods, appendices, and data dictionaries;
- protocol, statistical analysis plan, registration record, or guideline evidence tables;
- reporting checklist when relevant;
- official figure assets when they improve readability;
- source URL, DOI or registry identifier, retrieval date, and access note.

## Completeness Checks

Check more than file existence:

- file signature and nonzero size;
- plausible page count;
- title, DOI, authors, version, and journal match;
- expected sections, references, tables, and figures are present;
- supplements open and match citations in the main article;
- figures are nonblank and readable;
- accepted manuscript, version of record, correction, retraction, and duplicate versions are distinguished;
- preferred version and missing content are documented.

Use `scripts/article_inventory.py` for mechanical checks, then inspect source files visually.

## Naming

Use a stable numeric prefix and descriptive ASCII slug:

```text
01_short-topic_journal_year_main.pdf
01_short-topic_journal_year_supplement.pdf
```

Preserve the original source file when renaming or copying. Never overwrite an approved or earlier version without explicit instruction.

## Provenance Log

Record:

```text
Article number
Source type and URL
DOI/PMID/PMCID/registry identifier
Retrieved date
Version and access/license note
Main/supplement status
Known missing or corrected content
```
