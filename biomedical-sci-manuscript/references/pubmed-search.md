# PubMed API Search

Use this workflow when the user does not provide a literature set or asks to retrieve supporting references. Use `curl` from the terminal to call NCBI E-utilities API endpoints directly. Do not browse PubMed webpages, do not open E-utilities URLs as webpages, and do not inspect PMC/full-text pages.

## Hard Restrictions

- Do not use browser/webpage tools to open `eutils.ncbi.nlm.nih.gov`, `pubmed.ncbi.nlm.nih.gov`, or `pmc.ncbi.nlm.nih.gov`.
- Do not use web search for PubMed retrieval. Use terminal `curl` commands against E-utilities.
- Do not check PMC pages or full text to support claims.
- Do not retrieve one PMID at a time unless only one PMID remains after screening.
- Do not use claims that are only visible in full text, tables, figures, or supplements.
- Use only API-returned metadata and abstracts as evidence for manuscript claims.
- If an abstract does not support a claim, do not cite that paper for the claim.
- If abstract evidence is insufficient, write a more cautious claim or omit the citation.

## Search Goals

Search PubMed for literature that supports:

- disease burden, epidemiology, diagnosis, treatment, prognosis, or clinical limitations;
- disease biology, molecular mechanisms, pathways, immune microenvironment, biomarkers, or therapeutic targets;
- methods used in the manuscript, such as multi-omics, single-cell sequencing, radiomics, Mendelian randomization, machine learning, animal models, or in vitro validation;
- prior studies that agree or conflict with the manuscript's major findings.

## Retrieval Limits

Fast mode is the default. Keep search aggressively bounded:

- Full manuscript: retain at most 30 PubMed candidate records total before final citation selection.
- Introduction support: retain about 10-30 candidates.
- Discussion support: retain about 10-30 candidates.
- Methods/background-only support: retain about 10-30 candidates.
- Section-only task: retain at most 30 candidates.
- Final cited references should usually be 10-30 for a full manuscript and 3-15 for a single section.
- Run at most 2-3 small ESearch calls in fast mode, one per citation module, followed by one batched ESummary and one batched EFetch.
- If the first search returns too many results, narrow by adding disease subtype, molecule/pathway, study design, or `Title/Abstract` terms before opening many records.
- If the first search returns too few results, broaden once only if the user requested stronger referencing; otherwise write with verified records.
- Use the expanded mode only when the user explicitly asks for more citations or comprehensive literature support. Expanded mode may retain up to 40 candidates and cite 10-18 references.

## API Workflow

Use NCBI E-utilities against the PubMed database.

Base URL:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

Run API calls with `curl`, saving responses to local files when useful. In module-based fast mode, use this pattern:

```powershell
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<background_query>&retmode=json&retmax=4&sort=relevance" -o pubmed_esearch_background.json
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<object_or_method_query>&retmode=json&retmax=4&sort=relevance" -o pubmed_esearch_object.json
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<discussion_mechanism_query>&retmode=json&retmax=6&sort=relevance" -o pubmed_esearch_discussion.json
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<comma_separated_pmids>&retmode=json" -o pubmed_esummary.json
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<selected_pmids>&rettype=abstract&retmode=text" -o pubmed_abstracts.txt
```

Do not paste the URL into a browser and do not use webpage-opening tools.

Preferred sequence:

1. Decide which 2-3 manuscript modules require citations.
2. `esearch.fcgi`: run one small search per module and return PMIDs.
3. Merge and deduplicate PMIDs.
4. `esummary.fcgi`: fetch compact metadata for screening and NLM reference assembly in one batch.
5. `efetch.fcgi`: fetch abstracts in one batch only for the final selected candidates.

### Step 1: ESearch

Use `retmode=json`, `db=pubmed`, and a bounded `retmax`.

Single-module example:

```powershell
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%28lung%20cancer%5BTitle%2FAbstract%5D%29%20AND%20%28prognosis%20OR%20survival%29&retmode=json&retmax=4&sort=relevance" -o pubmed_esearch_background.json
```

Recommended `retmax`:

- Disease/background module: `retmax=40`.
- Study object/method module: `retmax=40`.
- Discussion mechanism/comparison module: `retmax=40`.
- Section-only task: `retmax=40`.
- Minimal background-only query: `retmax=40`.
- Never retain more than 80 unique PMIDs in fast mode unless the user explicitly asks for more citations.

Use `sort=relevance` for mechanism/topic support and `sort=pub+date` when current clinical burden, guidelines, or recent treatment evidence matters.

### Step 2: ESummary

Use ESummary for title, source, authors, publication date, article IDs, and journal metadata. Screen quickly and select final PMIDs for EFetch.

Example:

```powershell
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<pmid1,pmid2,pmid3>&retmode=json" -o pubmed_esummary.json
```

Screen ESummary records first. Select only the final 10-30 likely references for EFetch in a full manuscript.

### Step 3: EFetch

Use EFetch only once for final selected PMIDs in fast mode. Batch IDs.

Examples:

```powershell
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<pmid1,pmid2,pmid3>&retmode=xml" -o pubmed_efetch.xml
```

```powershell
curl.exe -L "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<pmid1,pmid2,pmid3>&rettype=abstract&retmode=text" -o pubmed_abstracts.txt
```

Use API-returned XML or abstract text only. Do not follow PubMed, PMC, publisher, DOI, or full-text links.

### API Etiquette

- Batch PMIDs in ESummary/EFetch instead of requesting one record at a time.
- In fast mode, prefer 2-3 `curl` ESearch calls, exactly one `curl` ESummary call, and exactly one `curl` EFetch call.
- Avoid repeated equivalent queries.
- If an API key is available in the environment, include `api_key=<key>`; otherwise use the default public rate limit conservatively.
- Include `tool` and `email` parameters only if configured by the runtime or user; do not invent an email address.
- If the API fails or network access is unavailable, ask for a supplied literature set or mark citations as needing verification. Do not fall back to PubMed/PMC webpage browsing.

## Query Construction

Build citation modules before querying. Do not search every outline point. Search only the modules that truly need citations.

Use module-based fast strategy:

1. `疾病/背景模块`: disease burden, epidemiology, diagnosis, treatment, prognosis, or review.
2. `研究对象/方法模块`: phenotype, exposure, biomarker, pathway, cell type, omics method, model, or clinical intervention.
3. `讨论机制/对比模块`: major result mechanism, prior consistency/conflict, prognosis, immune, therapy, validation, cohort, or experimental mechanism.
4. Retain up to 40 unique candidates across modules.
5. Select final references from ESummary metadata.
6. Fetch abstracts once for those selected PMIDs.

## Module Planning

Choose modules by manuscript section:

- Introduction usually needs:
  - disease/background module;
  - study object or method module.
- Discussion usually needs:
  - mechanism/comparison module;
  - optionally prognosis/treatment/validation module if it is central to the results.
- If a module is already supported by a selected review or original article, do not run another query for the same module.

Typical allocation:

| Module | Query input | retmax | Final citations |
|---|---|---:|---:|
| Disease/background | disease + burden/diagnosis/treatment/prognosis/review | 40 | 10-30 |
| Study object/method | disease + phenotype/exposure/biomarker/pathway/method | 40 | 10-30 |
| Discussion mechanism/comparison | disease + main result molecule/pathway/model + mechanism/prognosis/validation | 40 | 10-30 |

### Introduction Queries

Use combinations of:

```text
("<disease>"[Title/Abstract] OR "<synonym>"[Title/Abstract])
AND ("epidemiology" OR "burden" OR "diagnosis" OR "treatment" OR "prognosis" OR "review")
```

```text
("<disease>"[Title/Abstract])
AND ("<phenotype/exposure/biomarker/pathway>"[Title/Abstract])
```

### Discussion Queries

Use result-specific queries:

```text
("<disease>"[Title/Abstract])
AND ("<gene/pathway/cell type/biomarker/model>"[Title/Abstract])
AND ("mechanism" OR "prognosis" OR "immune" OR "therapy" OR "validation")
```

For clinical manuscripts:

```text
("<disease>"[Title/Abstract])
AND ("<intervention/exposure/biomarker>"[Title/Abstract])
AND ("outcome" OR "survival" OR "risk" OR "prognosis" OR "cohort")
```

For basic manuscripts:

```text
("<disease/model>"[Title/Abstract])
AND ("<molecule/pathway/cell phenotype>"[Title/Abstract])
AND ("mechanism" OR "signaling" OR "knockdown" OR "overexpression")
```

For bioinformatics manuscripts:

```text
("<disease>"[Title/Abstract])
AND ("bioinformatics" OR "transcriptome" OR "single-cell" OR "immune infiltration" OR "machine learning" OR "radiomics")
```

## Screening Rules

- Prefer PubMed-indexed original articles, systematic reviews, meta-analyses, guidelines, and high-quality reviews.
- Prefer recent literature for clinical practice and disease burden, but keep landmark mechanism papers when relevant.
- Do not open webpages for search hits. Screen ESearch/ESummary results first, then keep only the best candidates up to the retrieval limits.
- Use ESummary metadata screening before EFetch abstract retrieval.
- Keep the PMID, title, authors, journal abbreviation, year, DOI, abstract, and the specific claim supported.
- Do not use papers whose abstract does not support the claim being written.
- Do not cite a paper only because it contains a keyword.
- Keep module labels for each candidate so the same paper can support the correct manuscript section.
- Deduplicate overlapping records across pools. If one paper supports multiple claims, reuse it instead of adding another similar paper.
- In fast mode, one strong review can support broad background, and one original article can support one or more specific discussion claims when its abstract supports them.

## Evidence Extraction Table

Before drafting, create a working evidence list internally:

```text
Ref candidate:
- PMID:
- Authors/year:
- Title:
- Journal:
- DOI:
- Supported claim:
- Best manuscript location: Introduction / Discussion opening / Core Discussion / Limitations
- Notes:
```

## Citation Integration

- Convert selected PubMed records to numbered NLM-style citations only after drafting claims.
- Number citations by first appearance in the manuscript.
- Use inline citations like `[1]`, `[2,3]`, or `[4-6]`.
- Do not use `[PMID: ...]` inline.
- Generate NLM-style reference list entries from the same selected records.
- The supported claim for each reference must be derivable from the API-returned abstract or metadata.
