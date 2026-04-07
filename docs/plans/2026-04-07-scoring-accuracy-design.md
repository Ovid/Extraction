# Scoring Accuracy Fixes: RSF Labels, Resource Capture, Institutional Gatekeeping

**Date:** 2026-04-07
**Status:** Approved (post-pushback review)

## Problem Statement

Three interrelated scoring issues produce misleading results, particularly for autocracies with competent bureaucracies (Saudi Arabia, UAE, Qatar, etc.):

1. **RSF label inversion** — The question "How free is the press?" generates the label "Very high" for Saudi Arabia (27.9/100 press freedom) because `rsf_press` is not in `POSITIVE_QUESTION_INDICATORS`. The label reflects the normalized extraction score magnitude, not what the question asks.

2. **Resource capture formula** — The formula `resource_rents x institutional_weakness / 100` treats institutional strength as always protective. In autocracies, strong institutions facilitate extraction rather than checking it. Saudi Arabia gets a resource_capture score of 21 despite 25.6% GDP in resource rents controlled by the royal family.

3. **Institutional gatekeeping measurement** — Three of four indicators (WGI corruption control, regulatory quality, government effectiveness) measure bureaucratic competence, not the domain's stated purpose: "whether institutions serve broad population or narrow interests." This inflates scores for efficient autocracies.

## Design

### Fix 1: RSF Label and Comparison Labels

Add `rsf_press` to `POSITIVE_QUESTION_INDICATORS` in `score_countries.py`. The question "How free is the press?" is a positive question — a low raw value means low freedom, so the label should reflect that.

Also swap the RSF `comparison_label` in `INDICATOR_DISPLAY` from `['Least free press among', 'Freest press among']` to `['Freest press among', 'Least free press among']`. The current order is backwards — the highest raw RSF value means the freest press, not the least free.

### Fix 2: Resource Capture Formula

**Current formula:**
```
resource_capture = resource_rents x institutional_weakness / 100
```

**New formula:**
```
resource_capture = resource_rents x (100 - democratic_accountability) / 100
```

Where `democratic_accountability` is the **raw** V-Dem electoral democracy index (v2x_polyarchy) multiplied by 100. Not the min-max normalized score — the raw 0-1 value used directly as a 0-100 scale.

**Why raw, not normalized:** Min-max normalization is relative to the global dataset. A country with v2x_polyarchy of 0.50 (a hybrid/competitive authoritarian regime like Turkey or Hungary) would normalize to ~54 under min-max, making it look like it has majority accountability. The raw scale has inherent meaning: 0.5 is genuinely half-democratic, and the formula should reflect that.

**Justification (first principles, no magic numbers):**

Resource wealth is captured by elites to the extent that democratic accountability is absent. In a full autocracy, elites face no check on resource capture. In a full democracy, citizens can hold resource management accountable, reducing elite capture toward zero. This aligns with the resource curse literature (Ross, Karl): point-source resources + absent democratic accountability = elite capture.

**Expected results:**
- Saudi Arabia (rents=42, democracy raw 0.02): `42 x 98/100 = 41` (was 21)
- Norway (rents~20, democracy raw ~0.90): `20 x 10/100 = 2` (was ~1)
- USA (rents~3, democracy raw ~0.75): `3 x 25/100 = 1` (stays low)
- Russia (rents~high, democracy raw ~0.15): significantly higher than current

**Fallback:** When V-Dem data is unavailable for a country, resource_capture = raw resource rents score (unmoderated). Mark confidence "low" with an explicit note that democratic accountability data is unavailable. Do NOT fall back to institutional_gatekeeping as moderator — that perpetuates the bias for exactly the countries most affected (data-sparse autocracies).

**Not double-counting:** Political capture uses v2x_polyarchy as one of four indicators to measure elite monopolization of power. Resource capture uses it as a moderator to assess whether citizens can check resource management. Different questions, same underlying data. The current formula already cross-references domains (institutional_gatekeeping), so cross-domain interaction is established precedent.

### Fix 3: Institutional Gatekeeping Rebalancing

**Current indicators (all equally weighted):**
- wb_wgi_corruption (control of corruption) — competence metric
- wb_reg_quality (regulatory quality) — competence metric
- wb_wgi_gov_eff (government effectiveness) — competence metric
- vdem_rule_of_law — partially relevant

**New indicators (all equally weighted):**
- vdem_rule_of_law — keep (measures legal consistency)
- v2x_egal (V-Dem egalitarian component) — add (measures equal distribution of political power and resources)
- v2x_partipdem (V-Dem participatory democracy) — add (measures citizen participation in governance)
- wb_wgi_corruption — keep (balanced by accountability metrics)
- wb_reg_quality — keep (balanced by accountability metrics)
- wb_wgi_gov_eff — keep (balanced by accountability metrics)

Equal weighting across all 6 indicators. The 3 accountability indicators naturally dilute the 3 competence indicators from 75% to 50% of the domain. The WGI metrics aren't wrong — they're incomplete. Keeping them provides useful signal about state capacity; the accountability indicators provide the missing dimension of who that capacity serves.

The V-Dem variables `v2x_egal` and `v2x_partipdem` are confirmed present in `raw_data/vdem/vdem_core_full.csv`. The fetcher (`scripts/fetchers/vdem.py`) needs to add them to its extraction list.

**Side effect:** Indicator count increases from 4 to 6, which will slightly raise confidence for institutional_gatekeeping. This is appropriate — more indicators should increase confidence.

**Effect:** Autocracies with competent bureaucracies (Saudi Arabia, UAE, Singapore) will score higher on institutional_gatekeeping, reflecting that their institutions serve narrow interests despite being well-run. Democracies with strong accountability will score lower, reflecting that their institutions genuinely serve broad populations.

### Fix 4: METHODOLOGY.md Updates

All three changes must be reflected in METHODOLOGY.md:
- RSF direction: already fixed to "Inverted" in a previous commit
- Resource capture: document the new formula, its justification, and a candid discussion of the fragility of using raw V-Dem polyarchy — raw numbers are guidelines but can't always explain reality. Specific limitations to document:
  - V-Dem polyarchy measures electoral democracy specifically, not all forms of accountability
  - Some non-electoral accountability mechanisms (tribal councils, religious authority checks) aren't captured
  - The raw scale assumes equal intervals (0.4 to 0.5 is the same as 0.8 to 0.9), which may not hold
  - A country's formal democratic institutions may not reflect actual power dynamics
- Institutional gatekeeping: document the new indicator mix and rationale for rebalancing
- Add V-Dem egalitarian and participatory indices to the indicator tables

### Validation Step

After re-scoring, spot-check before/after for benchmark countries across all domains and composite:
- Saudi Arabia (efficient autocracy, high resource rents)
- Norway (strong democracy, high resource rents)
- Singapore (efficient autocracy, low resource rents)
- USA (democracy, low resource rents)
- North Korea (closed autocracy, sparse data)

Verify that composite scores and domain scores are sensible before committing.

## Files Changed

- `scripts/score_countries.py` — all three fixes
- `scripts/fetchers/vdem.py` — add v2x_egal, v2x_partipdem to extracted variables and metadata
- `data/scores.json` — re-scored output
- `METHODOLOGY.md` — document changes
