# Methodological Paradigms in AIGC-Driven E-Commerce User Behavior Research — Data and Code

**Companion data repository for the manuscript:**

> Wang, R., Lu, X., & Wang, X. (under review). *Methodological Paradigms in AIGC-Driven E-Commerce User Behavior Research: A Bibliometric and Time-Breakpoint Analysis*. Electronic Commerce Research (Springer).

## Contents

### data/

| File | Description | Rows | Corresponds to |
|---|---|---|---|
| `paradigm_codes.csv` | Paper-level analysis dataset: title, journal, year, CNKI citation count, paradigm label (calibrated dictionary coding), post-2018 indicator, age (months), log age, author count, funding flag, keyword count, journal composite impact factor (2024 edition) | 1,328 | Sections 3.5, 5.1, 5.2; Tables 2, 7 |
| `year_paradigm_distribution.csv` | Annual counts of articles by paradigm, 2015–2026 (2026 = Q1 only) | 12 | Table 3 |
| `validation_150_articles.csv` | Independent human coding of a stratified random sample of 150 articles vs. dictionary predictions, with per-article agreement | 150 | Section 3.3 |
| `journal_impact_factors.csv` | Journal-level CNKI composite impact factors (2024 edition) for the 419 journals in the corpus | 419 | Section 5.1 |
| `journal_disciplines.csv` | Discipline and CSSCI tier (source/extension) of the 419 journals | 419 | Section 5.1 |
| `coding_dictionary.csv` | Final keyword dictionary per paradigm used for the automated coding | 4 paradigms | Section 3.3 |

### code/

| Script | Purpose |
|---|---|
| `01_parse_cnki_exports.py` | Parse the CNKI export files and merge records |
| `02_clean_records.py` | Clean merged records (year filter, de-duplication, journal summary) |
| `03_final_dictionary_coding.py` | Final keyword dictionary and paradigm assignment rule (word-level dictionary v3: a non-logical paradigm is assigned only if its score strictly exceeds the logical-speculation score; title terms count double) |
| `04_calibrate_and_validate.py` | Recompute the 150-article validation metrics and the full-sample calibrated labels |
| `05_negative_binomial_analysis.py` | Negative binomial models of paper-level citation counts (Table 7) |
| `06_time_breakpoint_analysis.py` | Local-linear time-breakpoint estimates, subsamples, robustness and Mann-Kendall trends (Tables 4–6) |

## Validation metrics (Section 3.3 of the manuscript)

Reproduced by `04_calibrate_and_validate.py`:

- Overall agreement with human coding on the 150-article stratified sample: **77.3%** (Cohen's κ = 0.587 ≈ 0.59)
- Per-paradigm F1: logical speculation **0.84**, positivism **0.83**, technology-driven **0.40**, humanistic interpretation **0.51**
- Full-corpus paradigm distribution: logical speculation 1,133 (85.3%), positivism 112 (8.4%), technology-driven 23 (1.7%), humanistic interpretation 60 (4.5%)

## Data not shared (restricted by licensing)

The following inputs are **not** included in this repository because they derive from the commercial CNKI (China National Knowledge Infrastructure) database and are subject to its licensing terms:

- Raw CNKI search exports (`.xls` files per year) and the raw merged/cleaned record files that contain **full abstracts** of the retrieved articles (`_merged_raw.csv`, `_clean_records.csv`);
- Raw CNKI citation-count retrievals.

The repository contains the derived, article-level analysis data (titles, journals, years, paradigm labels, model variables) which are sufficient to reproduce all analyses and tables in the manuscript. Full abstracts and the raw export files are available from the corresponding author (Xinyuan Lu, luxy@ccnu.edu.cn) on reasonable request, subject to CNKI's terms.

## Reproducibility notes

- Search: CNKI journal database, topic field (title + keywords + abstract), technology-term family AND e-commerce-context family, publication window 2015-01-01 to 2026-03-04, journal articles only, de-duplicated by title, snowballing of key references. See `search_strategy.md`.
- Citation counts retrieved from CNKI on 2026-09-16; journal composite impact factors from the CNKI Journal Citation Report (2024 edition).
- The scripts contain absolute Windows paths and Chinese column names; adjust paths/column names as needed for your environment.

## License

The analysis data and code in this repository are shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Bibliographic metadata (titles, journal names) are used for scholarly analysis under the respective database terms; the original full texts and abstracts remain subject to CNKI's licensing.
