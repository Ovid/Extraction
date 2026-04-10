# Agentic Code Review: ovid/wages-gdp

**Date:** 2026-04-10 21:30:00
**Branch:** ovid/wages-gdp -> main
**Commit:** 2d9dadbe091769f3f95f7bc2a092cac0138f745c
**Files changed:** 16 | **Lines changed:** +3009 / -2002
**Diff size category:** Medium (code ~500 lines; remainder is scores.json regeneration)

## Executive Summary

This branch replaces the GDP-per-worker indicator with ILO labour income share of GDP in the economic_concentration domain. The implementation is solid and well-structured. One important bug was found: the confidence calculation for multi-source domains hardcodes `n_sources=1` instead of using the actual source count, undermining the confidence benefit of adding ILO as a second source. One additional important finding is a dead parameter in `estimate_trend` that misleads readers about the function's interface.

## Critical Issues

None found.

## Important Issues

### [I1] Hardcoded `n_sources=1` underreports source diversity for confidence

- **File:** `scripts/score_countries.py:1508`
- **Bug:** `assess_domain_confidence(n_indicators, 1, most_recent)` passes a literal `1` for the `n_sources` parameter. The actual source count `n_sources = group["source_name"].nunique()` is computed at line 1539 but is only stored in the return dict — it is never fed into the confidence calculation.
- **Impact:** For `economic_concentration`, countries with both WB Gini and ILO labour share have 2 distinct sources, but confidence is assessed as if there were only 1. Source diversity contributes up to 3 points to the 0-9 confidence scale. This systematically undercounts confidence for the domain that this branch was designed to improve.
- **Suggested fix:** Move `n_sources` computation before `assess_domain_confidence` and pass it:
  ```python
  n_sources = group["source_name"].nunique()
  confidence = assess_domain_confidence(n_indicators, n_sources, most_recent)
  ```
- **Confidence:** High
- **Found by:** Logic & Correctness, Error Handling & Edge Cases, Contract & Integration

### [I2] Dead `df_full` parameter in `estimate_trend`

- **File:** `scripts/score_countries.py:1386`
- **Bug:** `estimate_trend(df_full, country_code, indicator_file, ...)` accepts `df_full` as its first parameter but never uses it. The function reads from disk instead. All callers pass `None`.
- **Impact:** Misleading API contract. A future developer may pass a pre-loaded DataFrame expecting it to be used, only for it to be silently ignored.
- **Suggested fix:** Remove the `df_full` parameter and update all call sites.
- **Confidence:** High
- **Found by:** Logic & Correctness, Error Handling & Edge Cases, Contract & Integration

## Suggestions

- `scripts/fetchers/ilo.py:36-44` — Inconsistent dict access: `row.get("OBS_VALUE")` (safe) vs `row["REF_AREA"]` / `row["TIME_PERIOD"]` (unsafe). If API ever returns non-CSV content, crash is unhelpful. Consider validating `reader.fieldnames` or using `.get()` consistently. (Found by: Error Handling)
- `scripts/score_countries.py:1325` — Docstring says "Load a World Bank indicator CSV" but function now also handles ILO data. Update to "Load an indicator CSV". (Found by: Logic, Error Handling)
- `js/app.js:3-22` — `wb_net_interest_margin` missing from `SOURCE_URLS` (pre-existing, not introduced by this branch). Source link won't render in UI. (Found by: Logic, Contract)
- `tests/python/unit/test_indicator_config.py` — Plan called for this test file but it was not created. The `data_dir` resolution and source key validity are tested only implicitly. (Found by: Plan Alignment)

## Plan Alignment

- **Implemented:** All 6 plan tasks completed — ILO fetcher with tests (Task 1), fetcher registration (Task 2), scorer swap with data_dir support (Task 3), documentation updates (Task 4), data fetch and score regeneration (Task 5), write-up in BOOK.md (Task 6)
- **Not yet implemented:** `tests/python/unit/test_indicator_config.py` (two tests from plan Task 3 Step 1)
- **Deviations:** (1) `build_wb_domain` renamed to `build_indicator_domain` — sensible improvement not in plan. (2) ILO API URL uses dynamic `date.today().year` instead of hardcoded 2025 — improvement. (3) Empty-response guard added to `fetch()` — defensive improvement. (4) `source_name` field added to all `INDICATOR_CONFIG` entries for multi-source justification labels — necessary addition not in plan.

## Review Metadata

- **Agents dispatched:** Logic & Correctness, Error Handling & Edge Cases, Contract & Integration, Concurrency & State, Security, Plan Alignment
- **Scope:** 16 changed files + callers/callees of modified functions
- **Raw findings:** 10 (before verification)
- **Verified findings:** 6 (after verification)
- **Filtered out:** 4 (ILO aggregate regex: codes not present in actual data; TIME_PERIOD format: annual filter prevents non-integer periods; ILO-only country names: all ILO countries also have WB data; float crash: SDMX values always numeric)
- **Steering files consulted:** CLAUDE.md
- **Plan/design docs consulted:** docs/plans/2026-04-10-ilo-labor-share.md
