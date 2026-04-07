# Agentic Code Review: ovid/saudi-arabia-issues

**Date:** 2026-04-07 12:45:00
**Branch:** ovid/saudi-arabia-issues -> main
**Commit:** 0f58c5f81aaa1b33d08bcb527e1828bd2a6ffb5d
**Files changed:** 7 | **Lines changed:** +5178 / -2028
**Diff size category:** Large (mostly scores.json regeneration; ~120 lines of meaningful code changes)

## Executive Summary

The branch fixes RSF label inversion, replaces the resource capture formula to use democratic accountability instead of institutional strength, and adds V-Dem egalitarian/participatory democracy indicators to institutional gatekeeping. One critical bug: the `v2x_egal` indicator's source key is derived incorrectly in the scoring loop, causing broken questions, labels, context facts, and peer comparisons for the Egalitarian Component indicator. Two important bugs around operator precedence in fact generation and confidence level inflation. Several documentation inconsistencies remain from the old formula.

## Critical Issues

### [C1] Source key mismatch for v2x_egal: `vdem_egalitarian_component` vs `vdem_egalitarian`
- **File:** `scripts/score_countries.py:937`
- **Bug:** The V-Dem scoring loop derives source keys dynamically via `'vdem_' + i['name'].lower().replace(' ', '_')`. For `v2x_egal`, the name is `'Egalitarian Component'` (line 756), producing `vdem_egalitarian_component`. However, all other registration points use `vdem_egalitarian`: INDICATOR_QUESTIONS (line 68), POSITIVE_QUESTION_INDICATORS (line 101), INDICATOR_DISPLAY (line 148), and vdem_source_key_map (line 793).
- **Impact:** For the Egalitarian Component indicator in every country: (1) `build_indicator_entry()` gets no display config, so no context facts are generated; (2) the question falls back to the raw key string instead of "How equally are political power and resources distributed?"; (3) the POSITIVE_QUESTION_INDICATORS check fails, so labels have wrong direction; (4) peer comparisons fail; (5) the source key in scores.json is wrong.
- **Suggested fix:** Rename `'Egalitarian Component'` to `'Egalitarian'` in `vdem_vars_config` at line 756. Or better: refactor the scoring loop (lines 931, 937) to use `vdem_source_key_map` instead of deriving keys from display names, eliminating the dual-derivation hazard entirely.
- **Confidence:** High
- **Found by:** Contract & Integration

## Important Issues

### [I1] Operator precedence bug in facts ternary expression
- **File:** `scripts/score_countries.py:1013`
- **Bug:** `resource_rents_facts + [moderation_fact] if resource_rents_facts else [fallback]` is parsed by Python as `resource_rents_facts + ([moderation_fact] if resource_rents_facts else [fallback])`, not `(resource_rents_facts + [moderation_fact]) if resource_rents_facts else [fallback]`. When `resource_rents_facts` is an empty list `[]` (falsy), the moderation fact is silently dropped and replaced with a less informative fallback string.
- **Impact:** Countries where `generate_context_facts` returns no facts for resource rents will lose the "Moderated by democratic accountability" context, even though moderation was applied.
- **Suggested fix:** Add explicit parentheses: `(resource_rents_facts + [moderation_fact]) if resource_rents_facts else [fallback]`
- **Confidence:** High
- **Found by:** Logic & Correctness, Error Handling

### [I2] Confidence overwrite can upgrade `very_low` to `low`
- **File:** `scripts/score_countries.py:1023`
- **Bug:** The fallback path unconditionally sets `domains['resource_capture']['confidence'] = 'low'`. If `assess_domain_confidence` had already assigned `very_low` (e.g., for a country with old/sparse World Bank data), this upgrades confidence without justification.
- **Impact:** Countries with minimal resource data and no V-Dem data may appear more confident than warranted.
- **Suggested fix:** Only downgrade, never upgrade:
  ```python
  conf_rank = {'very_low': 0, 'low': 1, 'moderate': 2, 'high': 3}
  current = domains['resource_capture']['confidence']
  if conf_rank.get(current, 0) > conf_rank.get('low', 1):
      domains['resource_capture']['confidence'] = 'low'
  ```
- **Confidence:** High
- **Found by:** Error Handling

### [I3] New V-Dem source keys missing from `SOURCE_URLS` in frontend
- **File:** `js/app.js` (SOURCE_URLS object, ~lines 13-30)
- **Bug:** `vdem_egalitarian` and `vdem_participatory_democracy` are not in `SOURCE_URLS`, so they render as plain text instead of clickable links in the domain detail panel.
- **Impact:** Inconsistent source attribution display; users cannot click through to V-Dem for these indicators.
- **Suggested fix:** Add entries:
  ```javascript
  vdem_egalitarian: 'https://www.v-dem.net/',
  vdem_participatory_democracy: 'https://www.v-dem.net/',
  ```
- **Confidence:** High
- **Found by:** Contract & Integration

## Suggestions

- `scripts/score_countries.py:1021-1035` — Fallback path doesn't update `justification_detail` to explain unmoderated score (Logic & Correctness)
- `METHODOLOGY.md:225` — Still says "moderated by institutional strength"; should say "democratic accountability" (Plan Alignment)
- `METHODOLOGY.md:250` — Known Limitation #6 still references "institutional data" instead of V-Dem democratic accountability data (Plan Alignment)
- `scripts/fetchers/vdem.py:14-24` — Docstring missing `v2x_rule` from key variables list (pre-existing) (Error Handling, Plan Alignment)
- `scripts/score_countries.py:1004-1008` and `1026-1030` — Duplicated facts extraction loop could be extracted before the if/else (Contract & Integration)
- `scripts/score_countries.py:747` — Comment only mentions `v2x_rule` for institutional_gatekeeping; missing `v2x_egal` and `v2x_partipdem` (Contract & Integration)

## Plan Alignment

- **Implemented:** All four fixes (RSF labels, V-Dem indicator additions, resource capture formula, METHODOLOGY.md main sections) match the design and implementation plans exactly.
- **Not yet implemented:** None; all plan tasks appear complete.
- **Deviations:** Two stale references in METHODOLOGY.md (lines 225 and 250) were not caught by the plan's update scope. The v2x_egal source key mismatch is an implementation bug, not a plan deviation.

## Review Metadata

- **Agents dispatched:** Logic & Correctness, Error Handling & Edge Cases, Contract & Integration, Concurrency & State, Security, Plan Alignment
- **Scope:** 7 changed files + js/app.js (frontend), METHODOLOGY.md, sources.md (adjacent)
- **Raw findings:** 13 (before verification)
- **Verified findings:** 11 (after verification)
- **Filtered out:** 2 (F2: v2x_partipdem key — no mismatch; F10: innerHTML XSS — not exploitable in static site context)
- **Steering files consulted:** CLAUDE.md
- **Plan/design docs consulted:** docs/plans/2026-04-07-scoring-accuracy-design.md, docs/plans/2026-04-07-scoring-accuracy-implementation.md
