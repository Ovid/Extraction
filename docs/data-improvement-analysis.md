# Data Improvement Analysis: What Can Be Fixed and How

*Analysis date: 2026-04-10*
*Companion to: critical-review-economist-perspective.md*

## Purpose

This document catalogs concrete data and scoring changes that would address the economist objections identified in the critical review. Changes are separated into two categories: those achievable with data we already have, and those requiring new data sources. Each change includes the specific data involved, the expected impact on scores, and implementation complexity.

---

## Part 1: Changes Using Existing Data

These changes require no new data fetches. The raw data is already on disk in `raw_data/`.

---

### 1.1 Transnational Facilitation: Use FSI Value Instead of FSI Score

> **Status: Evaluated and rejected.** After analysis, the implementation chose to use the raw **secrecy score** (`index_score`) instead of `index_value`. FSI Value is extremely right-skewed (USA=2018, median ~161), and min-max normalization gave the US a perfect 100 while compressing traditional tax havens to ~25. The secrecy score measures policy choice on a 0-100 scale and is used raw (no normalization). FSI Value is retained as a displayed context fact. See `docs/plans/2026-04-10-tf-scoring-fix-design.md` for the full rationale.

**Original proposal (below) is retained for context.**

**Problem:** The domain currently uses the TJN Financial Secrecy Index *score* (`index_score`), which measures only how secretive a jurisdiction's laws are. It ignores *volume* — how much offshore finance actually flows through the jurisdiction. This produces anomalies: Norway (secrecy score 54.6) appears to be a significant enabler of global extraction, when in reality it handles a negligible 0.35% of global offshore financial services.

**The fix:** Switch to TJN's own composite measure, `index_value`, which combines secrecy laws with the Global Scale Weight (the jurisdiction's share of global offshore financial services). This is the number TJN itself uses for its headline rankings.

**Data already available:** The `raw_data/tjn/fsi_jurisdictions.csv` file already contains `index_value`, `index_share`, and `gsw` columns alongside `index_score`. We fetch this data but only use one column.

**Impact on scores:**

| Country | Current Score (secrecy only) | New Score (secrecy × volume) | Direction |
|---------|----------------------------|-------|-----------|
| United States | 77 | ~100 | Up — world's #1 secrecy jurisdiction by volume |
| Switzerland | 89 | ~69 | Down — highly secretive but smaller scale |
| Singapore | 76 | ~61 | Down — moderate scale |
| Germany | 59 | ~38 | Down significantly — moderate secrecy, moderate volume |
| Luxembourg | 52 | ~40 | Down — high volume relative to size, but moderate secrecy |
| Japan | 66 | ~33 | Down significantly — low secrecy, moderate volume |
| Norway | 50 | ~12 | Down dramatically — negligible offshore finance |
| United Kingdom | 31 | ~24 | Down slightly — low domestic secrecy, moderate volume |
| China | 79 | ~31 | Down dramatically — secretive but small offshore share |
| Ireland | 55 | ~30 | Down — moderate on both dimensions |

**Why this is better:** The FSI Value is the measure TJN designed for exactly this purpose. A jurisdiction that has secretive laws but handles no offshore finance is not facilitating transnational extraction. The current approach over-penalizes countries that happen to have privacy laws but don't function as offshore centers, and under-penalizes the actual major conduits.

**Potential concern:** The FSI Value is heavily skewed — the US (2018) is ~14× the median (~140). Min-max normalization would compress most countries into the bottom quarter. Log transformation (as used for resource rents) may be appropriate, or the normalization approach may need adjustment. This should be tested during implementation.

**Also available in the TJN data:**
- `index_share` — the jurisdiction's percentage of the global FSI Value. An alternative normalization basis that is already 0-100 and naturally handles scale. The US accounts for 5.66% of global financial secrecy value.
- `gsw` — Global Scale Weight alone (share of global offshore financial services, without the secrecy multiplier). This could be used as a separate indicator alongside secrecy score, giving the domain two indicators like most other domains.

**Recommended approach:** Use `index_value` with log transformation, or split the domain into two indicators: `index_score` (secrecy laws) and `gsw` (offshore finance volume). The two-indicator approach would be consistent with how other domains work and would allow the domain to distinguish "secretive but small" from "open but massive."

---

### 1.2 Political Capture: Add Legislative Corruption and Horizontal Accountability

**Problem:** The US scores 14/100 on political capture — lower than Brazil (29), comparable to Japan (8). This is because V-Dem's political corruption index (v2x_corr) and clientelism index (v2xnp_client) are calibrated to detect developing-world patronage: cash-for-votes, kleptocratic diversion, patron-client networks. They are largely blind to the institutionalized influence industry in mature democracies — lobbying, campaign finance, regulatory capture, and the revolving door.

No single indicator fully captures legalized political capture. But two V-Dem variables already in our dataset substantially improve coverage:

**Variable 1: `v2lgcrrpt` — Legislature corrupt activities**

This measures how routinely members of the legislature unduly profit from their positions, engage in corrupt exchanges, or use public resources for private ends. Crucially, it captures *legislative* corruption specifically, not just executive-branch corruption.

Scale: approximately -3 to +3.5 (higher = less corrupt).

| Country | v2lgcrrpt | Interpretation |
|---------|-----------|---------------|
| Luxembourg | 3.50 | Global maximum — essentially no legislative corruption |
| Norway | 3.22 | Near-minimal |
| Germany | 1.71 | Low |
| UK | 1.70 | Low |
| Ireland | 1.66 | Low |
| Switzerland | 1.66 | Low |
| Japan | 1.60 | Low |
| **USA** | **1.05** | **Moderate — 75th percentile globally, but notably worse than all HIC peers** |
| China | 0.42 | High |
| Brazil | -1.33 | Very high |
| Nigeria | -1.32 | Very high |

The US at 1.05 is at the 75th percentile globally (better than most countries), but among high-income democracies it is a clear outlier. The gap between the US (1.05) and its nearest HIC peer (Japan, 1.60) is larger than the gap between Japan and Norway (3.22). V-Dem's expert coders are capturing something real here — the US Congress has documented issues with insider trading, PAC relationships, and the lobbying-to-legislating pipeline that other rich-country legislatures largely don't.

**Variable 2: `v2x_horacc` — Horizontal accountability**

This is a V-Dem index measuring the extent to which state institutions (legislature, judiciary, oversight bodies) can effectively hold the executive accountable. It captures checks and balances, oversight capacity, and institutional independence.

Scale: approximately -2 to +2.3 (higher = more accountability).

| Country | v2x_horacc | Interpretation |
|---------|------------|---------------|
| Norway | 2.21 | Near-maximum — strong independent oversight |
| Germany | 2.06 | Very strong |
| Switzerland | 1.99 | Very strong |
| Ireland | 1.64 | Strong |
| UK | 1.72 | Strong |
| Japan | 1.46 | Strong |
| **USA** | **0.55** | **56th percentile globally — strikingly weak for a rich democracy** |
| Singapore | 0.65 | Moderate (expected for a hybrid regime) |
| Nigeria | 0.20 | Weak |
| China | -0.79 | Very weak |
| Brazil | 1.41 | Strong (expected — Brazil has robust institutional checks) |

The US at 0.55 is the most revealing number in this analysis. Among all countries globally (including autocracies), the US is only at the 56th percentile for horizontal accountability. Among high-income OECD countries, it is an extreme outlier. This captures the erosion of congressional oversight, politicization of oversight bodies, executive overreach, and weakening of institutional checks that political scientists have extensively documented.

**Why these two variables work together:** `v2lgcrrpt` captures corruption *within* the legislature (the influence industry). `v2x_horacc` captures the *weakness of checks* on executive power. Together they measure two distinct mechanisms of political capture in mature democracies:
1. The legislature itself is captured by moneyed interests (v2lgcrrpt)
2. The institutions that should check power concentration cannot effectively do so (v2x_horacc)

**Impact on US political capture score:**

Current indicators (all inverted):
- Political corruption (v2x_corr): 0.06 → normalized ~6
- Clientelism (v2xnp_client): 0.10 → normalized ~10
- Electoral democracy (v2x_polyarchy): 0.73 → normalized ~27
- Physical violence (v2x_clphy): 0.79 → normalized ~21
- Mean: **14**

With new indicators added (also inverted):
- v2lgcrrpt: 1.05 (range -2.74 to 3.50) → normalized ~(1 - (1.05+2.74)/(3.50+2.74)) × 100 ≈ 39
- v2x_horacc: 0.55 (range -2.01 to 2.29) → normalized ~(1 - (0.55+2.01)/(2.29+2.01)) × 100 ≈ 40

New mean with 6 indicators: (6 + 10 + 27 + 21 + 39 + 40) / 6 ≈ **24**

This moves US political capture from 14 to approximately 24 — still well below Brazil (would also increase somewhat) and Nigeria, but no longer implausibly low for a country with a $4B/year lobbying industry and documented institutional erosion.

**Effect on other countries:** Norway moves from 1 to ~3, Germany from 3 to ~5, UK from 8 to ~10. The new indicators create minimal distortion for countries that already score well on the existing indicators. The main impact is on countries like the US where legislative corruption and weak horizontal accountability diverge from low electoral corruption.

---

### 1.3 V-Dem Trend Data: Enable Trends for V-Dem-Sourced Domains

**Problem:** Three of seven domains display "unknown" trends: political capture, information & media capture, and transnational facilitation. For the USA, this means the overall trend is computed from only 4/7 domains, and the excluded domains are exactly where much of the US extraction discourse is focused (political influence, media consolidation).

**The fix:** The V-Dem core dataset (`vdem_core_full.csv`) contains full time-series data going back to 1789. The trend computation function currently only processes World Bank CSVs because each source has a different file format. Extending it to also read V-Dem time series would fill this gap.

**Data already available:** All V-Dem indicators used in scoring have annual values in `vdem_core_full.csv`. The file is already parsed during scoring — the trend function just needs to use the same data.

**Expected impact:**

For the USA, this would enable trends on:
- **Political capture:** V-Dem shows US political corruption (v2x_corr) rising from ~0.02 in 2015 to 0.06 in 2025, clientelism rising from ~0.05 to 0.10, and polyarchy falling from ~0.87 to 0.73. This domain's trend would likely register as **rising extraction**.
- **Information capture:** V-Dem shows US freedom of expression (v2x_freexp_altinf) declining from ~0.88 in 2015 to 0.73 in 2025. This would also register as **rising extraction**.
- **Transnational facilitation** would remain "unknown" since TJN data doesn't have a comparable time series in our dataset.

The overall US trend (currently "rising" based on 4 domains) would be strengthened by two additional domains also showing rising extraction.

**Implementation notes:**
- The TJN FSI dataset has two methodology versions (2022 and 2025) in `fsi_jurisdictions.csv`, but the scoring methodologies differ between versions, making direct comparison unreliable. TJN trends should remain "unknown" unless the TJN provides a consistent time series.
- RSF press freedom also has a methodology break (pre-2022 vs. post-2022), which means the RSF indicator within information capture may not be suitable for trend analysis. But V-Dem's freedom of expression and alternative info sources indicators have consistent methodology across years and can carry the trend.

---

### 1.4 Institutional Gatekeeping: Restructure Domain Weighting

**Problem:** The domain averages four indicators equally:
1. WB Control of Corruption (inverted) — measures institutional quality
2. V-Dem Rule of Law (inverted) — measures institutional quality
3. V-Dem Egalitarian Component (inverted) — measures who institutions serve
4. V-Dem Participatory Democracy (inverted) — measures citizen agency

Indicators 1-2 measure whether institutions *function well*. Indicators 3-4 measure whether institutions *serve broad interests*. For the US, institutions function well (rule of law 0.92, corruption control 1.12) but serve narrower interests than peer democracies (egalitarian component 0.57, 28% below HIC average). Equal weighting dilutes the signal from the indicators most relevant to the Acemoglu/Robinson concept of extractive institutions.

**The fix:** The current scoring code already groups World Bank and V-Dem indicators separately and averages group scores when both sources are present. The restructuring could work within this existing framework:

**Option A — Source-group averaging with rebalanced groups:**

Currently:
- WB group: corruption control only → WB group score
- V-Dem group: rule of law, egalitarian, participatory → V-Dem group score
- Domain score = average(WB group, V-Dem group)

This already gives the WB indicator 50% weight and the three V-Dem indicators ~16.7% each. No change to the averaging logic needed.

**Option B — Conceptual sub-groups:**

- "Institutional quality" sub-group: WB corruption control + V-Dem rule of law → sub-score A
- "Institutional purpose" sub-group: V-Dem egalitarian + V-Dem participatory democracy → sub-score B
- Domain score = average(sub-score A, sub-score B)

This gives the "who do institutions serve?" question 50% of the domain weight, up from ~33% currently. The US score would move from 28 to approximately 33 (quality sub-score ~15, purpose sub-score ~51, average ~33).

**Recommendation:** Option B is more analytically sound because it maps to the conceptual distinction that matters. The domain is called "institutional *gatekeeping*" — the question is whether institutions gate-keep for elites or for the public. Institutional quality (rule of law, corruption control) is a necessary but not sufficient condition; institutions can be high-quality and still serve narrow interests. Option B makes this distinction explicit.

**Impact on other countries:**

| Country | Current | Option B (est.) | Change |
|---------|---------|-----------------|--------|
| USA | 28 | ~33 | +5 |
| Singapore | 22 | ~30 | +8 (low egalitarian/participatory despite high quality) |
| China | 69 | ~69 | ~0 (low on both dimensions) |
| Norway | 6 | ~5 | -1 |
| Germany | 13 | ~11 | -2 |
| Nigeria | 69 | ~67 | -2 |

The main effect is on countries where institutional quality diverges from institutional purpose — exactly the cases the Acemoglu/Robinson framework highlights.

---

### 1.5 Resource Capture: Fix Indicator Question Text

**Problem:** The `INDICATOR_QUESTIONS` dictionary in `score_countries.py` has:

```python
"wb_natural_rents": "How dependent is the economy on natural resources?"
```

But the domain measures *vulnerability of resource wealth to elite capture*, not just resource dependence. The panel display already uses the correct framing ("How vulnerable is resource wealth to elite capture?") because this comes from the resource_capture_composite indicator, but the raw indicator config retains the old phrasing.

**The fix:** Update the question text for `wb_natural_rents` to match the domain concept. This is a one-line change with no impact on scoring.

---

### 1.6 Trend Threshold: Consider Whether 10% Is Appropriate

**Side note identified during analysis:** The trend computation requires a 10% change to register as "rising" or "falling." For indicators that are already at extreme baselines, 10% may be too high. A country with a Gini of 60 would need to rise to 66 to register as "rising extraction" — a 6-point shift that represents a major structural change but might not clear the threshold due to the already-high baseline.

This is not a data change but a scoring parameter worth reviewing during implementation. No action recommended here — just flagging it for the implementation plan.

---

## Part 2: Changes Requiring New Data Sources

These changes require either fetching new indicators from existing source APIs or integrating entirely new data providers.

---

### 2.1 Economic Concentration: Add Income Share of Top 10% (World Bank)

**Problem:** The Gini coefficient is the standard inequality measure but is most sensitive to changes in the middle of the income distribution. For measuring *extraction* — systematic capture by elites — the income share of the top 10% (or top 1%) is more directly relevant. The US Gini of 41.8 understates how concentrated income is at the very top.

**The data:** The World Bank API provides:
- **SI.DST.10TH.10** — Income share held by highest 10%
- **SI.DST.FRST.10** — Income share held by lowest 10%
- **SI.DST.05TH.20** — Income share held by highest 20%
- **SI.DST.FRST.20** — Income share held by lowest 20%

These use the same World Bank API endpoint we already fetch from. Adding them requires only new entries in the `INDICATORS` list in `scripts/fetchers/worldbank.py` and corresponding entries in `score_countries.py`.

**Recommended indicator:** `SI.DST.10TH.10` (top 10% income share). This directly measures how much of national income is captured by the top decile. Higher values = more extraction.

**Expected coverage:** Similar to Gini (~165 countries), since both come from household survey data. Some countries will have Gini but not decile shares, and vice versa.

**Impact on US score:** The US top-10% income share is approximately 30-31% (World Bank estimate), compared to a high-income country average of ~25% and a Scandinavian average of ~22-23%. This would add a moderately high normalized score to the economic concentration domain, likely pushing it from 38 to ~42-45.

**Why this is better than Gini alone:** The Gini measures the full distribution. The top-10% share measures concentration at the top. In the Acemoglu/Robinson framework, what matters is whether narrow elites capture a disproportionate share — which is exactly what the top decile share measures. Using both Gini and top-10% share captures two different aspects of economic concentration (overall inequality vs. elite capture).

**Implementation:** Low effort — same API, same fetcher pattern, one new indicator config entry.

---

### 2.2 Data Quality Flags for Known Problem Countries

**Problem:** Several countries have scores that are arithmetically correct but substantively misleading due to known data quality issues:

**Nigeria (and other large informal economies):**
- ILO labour share of 75.1% (global maximum) is almost certainly an artifact of self-employment income imputation in an economy where ~65% of employment is informal
- The ILO's own methodology documentation acknowledges substantial uncertainty for countries with large self-employment shares
- Presenting Nigeria as having less economic concentration than Norway would instantly discredit the index

**Ireland (and other multinational profit-shifting hubs):**
- GDP is inflated by ~25-40% due to multinational IP relocation (the "leprechaun economics" phenomenon, first identified in 2016)
- Any indicator denominated as % of GDP (domestic credit, resource rents) is mechanically deflated
- Ireland's own Central Statistics Office created GNI* specifically because GDP is misleading
- Domestic credit at 23.8% of GDP (score: 9) would be ~40% of GNI* — roughly doubling the normalized score

**Small states with limited statistical capacity:**
- Several Pacific Island states, Caribbean nations, and microstates have data from infrequent surveys
- Scores may reflect conditions years or decades ago

**The fix:** Add a `data_quality_notes` field to country entries in `scores.json` that the UI can display as visible warnings. These are not score adjustments — they are contextual notes that prevent misinterpretation.

**Proposed notes:**

```json
{
  "NGA": "Labour share estimates may be unreliable due to Nigeria's large informal sector (~65% of employment). ILO data uses imputations for self-employment income that are known to have high uncertainty in this context.",
  "IRL": "Ireland's GDP is significantly inflated by multinational profit shifting. Indicators denominated as % of GDP (domestic credit, resource rents) may understate extraction. Ireland's Central Statistics Office recommends GNI* as a more accurate measure of domestic economic activity.",
  "ETH": "Labour share estimates may be unreliable due to Ethiopia's large informal and subsistence agriculture sector.",
  "LUX": "Luxembourg's GDP per capita is inflated by cross-border workers (~200,000 non-residents work in Luxembourg). GDP-denominated indicators may not reflect domestic economic conditions."
}
```

**Implementation:** Low effort — add a dictionary of notes to the scorer, include them in the JSON output, display them in the UI. The list of affected countries should be curated based on known data quality issues documented by the source organizations themselves (ILO, World Bank, CSO Ireland).

**Which countries to flag:** A principled approach would be to flag all countries where the ILO labour share estimate has an informal employment share above 50% (data available from ILO's ILOSTAT). This would catch Nigeria, Ethiopia, India, Bangladesh, and others where the labour share number is structurally unreliable. For Ireland and Luxembourg, the GDP distortion is well-documented and specific to those countries.

---

### 2.3 UK Crown Dependencies: Annotation Approach

**Problem:** The UK scores 31 on transnational facilitation (FSI score 44.8), which is lower than Norway (50), Luxembourg (52), and Ireland (55). This is arguably the single most misleading score in the index. The UK designed and retains constitutional authority over the world's largest network of offshore financial centers:

| Territory | FSI Secrecy Score | Global FSI Share |
|-----------|------------------|-----------------|
| UK (domestic) | 44.8 | 1.36% |
| Cayman Islands | 73.3 | 1.40% |
| British Virgin Islands | 71.5 | 1.58% |
| Guernsey | 75.4 | 1.87% |
| Jersey | 63.8 | 1.19% |
| Bermuda | 71.3 | 0.67% |
| Isle of Man | 68.1 | 0.47% |
| Turks and Caicos | 77.0 | 0.21% |
| Gibraltar | 69.2 | 0.27% |
| Anguilla | 78.4 | 0.23% |
| Montserrat | 70.7 | 0.01% |
| **UK network total** | — | **9.27%** |

The UK network accounts for 9.27% of global financial secrecy value — larger than the United States (5.66%) and substantially larger than Switzerland (3.92%).

**Why this is hard to fix with a score change:** Attributing dependent territory scores to parent states opens a precedent problem. Should the Netherlands include Curacao, Aruba, and Sint Maarten? Should the US include the US Virgin Islands and Puerto Rico? Should France include its overseas territories? The constitutional relationships differ in each case.

**The fix — two-layer approach:**

**Layer 1 (data):** Add a `related_jurisdictions` field to the UK's transnational facilitation domain in `scores.json`:

```json
"transnational_facilitation": {
  "score": 31,
  "related_jurisdictions": {
    "note": "The UK retains constitutional authority over Crown Dependencies and Overseas Territories that collectively account for 9.27% of global financial secrecy value (vs. UK domestic: 1.36%).",
    "territories": [
      {"id": "KY", "name": "Cayman Islands", "fsi_score": 73.3, "fsi_share_pct": 1.40},
      {"id": "VG", "name": "British Virgin Islands", "fsi_score": 71.5, "fsi_share_pct": 1.58},
      {"id": "GG", "name": "Guernsey", "fsi_score": 75.4, "fsi_share_pct": 1.87}
    ],
    "network_total_share_pct": 9.27
  }
}
```

**Layer 2 (UI):** Display this as a visible callout on the UK's transnational facilitation card: "See also: Crown Dependencies and Overseas Territories scored separately — UK network accounts for 9.27% of global financial secrecy."

**Implementation:** Medium effort. The TJN data for all these territories is already in `fsi_jurisdictions.csv`. The scorer needs to identify UK-related jurisdictions and attach the annotation. The UI needs a new component to display the note.

**A possible extension for later:** Offer a toggle or alternative view that shows "network-attributed" transnational facilitation scores. This would be clearly labeled as an alternative interpretation, not a replacement for the jurisdiction-level score.

---

### 2.4 Economic Concentration: World Bank Top-10% Income Share

(Detailed in section 2.1 above. Separated here because it requires a new World Bank API fetch, even though the fetcher infrastructure already exists.)

---

## Part 3: Changes Considered and Deferred

These were identified in the critical review but are not recommended for the current implementation cycle.

### Deferred: BIS Household Debt Data

The Bank for International Settlements publishes household debt-to-GDP ratios for ~40 countries. This would improve the financial extraction domain by distinguishing household debt burden from corporate credit. However:
- Coverage is ~40 countries (vs. 184 for World Bank credit data)
- Requires a new fetcher for a new API
- The 40-country coverage is heavily biased toward OECD countries
- Would create a two-tier system where rich countries have more indicators than poor ones

**Recommendation:** Defer until the index has a framework for handling indicators with limited coverage (e.g., weighting by coverage, or presenting as supplementary data).

### Deferred: GNI-Based Denominators

Using GNI instead of GDP as the denominator for %-of-GDP indicators would fix Ireland's distortion and partially address Luxembourg's. However:
- Requires re-engineering all indicators that use GDP denominators
- The World Bank indicators are *defined* as %-of-GDP; there is no corresponding %-of-GNI variant
- We would need to fetch raw numerator data and GNI separately, then compute the ratio ourselves
- This introduces a divergence from the published source data that would need careful documentation

**Recommendation:** Defer. The data quality flag approach (section 2.2) addresses the most acute cases without the engineering complexity.

### Deferred: Market Concentration / Markup Data

No good cross-country source exists. The OECD has partial data for ~38 countries. Academic estimates (De Loecker et al.) are research datasets, not regularly published indicators. This is a genuine data gap that the economics profession hasn't yet filled with a standard cross-country indicator.

### Deferred: Tax Policy Data

The OECD Tax Database and ICTD/UNU-WIDER Government Revenue Dataset have relevant indicators (effective tax rates, tax-to-GDP ratios), but integrating them would add a new domain or significantly restructure economic concentration. This is a larger methodological decision.

### Deferred: Healthcare / Housing Extraction

These are important forms of extraction, particularly in the US, but no single cross-country indicator captures them in a way comparable to the current domain structure. WHO health expenditure data and OECD housing affordability data could be explored in a future cycle.

---

## Part 4: Interaction Effects and Risks

### Score Changes Are Interconnected

Several of these changes affect the same countries simultaneously:

**United States:**
- Transnational facilitation: 77 → ~100 (FSI Value)
- Political capture: 14 → ~24 (new V-Dem indicators)
- Institutional gatekeeping: 28 → ~33 (restructured weighting)
- Composite: 35 → approximately **41-43**

The US composite would rise by 6-8 points — from "moderate" to "moderate-high." This is directionally correct but significant enough to warrant careful communication.

**Norway:**
- Transnational facilitation: 50 → ~12 (FSI Value)
- Composite: 18 → approximately **12-13**

Norway would look significantly better, which is defensible — it is not a major financial secrecy jurisdiction.

**China:**
- Transnational facilitation: 79 → ~31 (FSI Value)
- Composite: 58 → approximately **51-52**

China's transnational score drops dramatically because its offshore financial services are small relative to the US/Switzerland/Singapore. This is defensible for transnational facilitation specifically, though it makes China look less extractive overall. The domain is measuring "enabling extraction elsewhere," and China's extraction is mostly domestic.

### Min-Max Normalization Cascade

Changing the TJN indicator from `index_score` to `index_value` changes the min and max values, which affects every country's normalized score. The US becomes the new maximum (value 2018.1), anchoring the top of the scale. This means the US is definitionally 100 on this domain, which may feel like an artifact. Log transformation would spread the distribution more evenly.

### Communication Risk

These changes will shift composite scores for many countries. Users who have already seen the current scores may interpret changes as errors or bias. Clear changelog documentation and a methodology version bump are essential.

---

## Summary Table

| # | Change | Source | New Data? | Effort | Impact | Risk |
|---|--------|--------|-----------|--------|--------|------|
| 1 | TJN: FSI Value instead of FSI Score | TJN | No — already fetched | Low | High | Normalization cascade |
| 2 | V-Dem: add v2lgcrrpt + v2x_horacc | V-Dem | No — in vdem_core_full.csv | Medium | High | Changes political capture scores globally |
| 3 | V-Dem: enable trend computation | V-Dem | No — time series in existing file | Medium | Moderate | May reveal uncomfortable trends |
| 4 | Institutional gatekeeping: restructure weighting | None | No | Low | Moderate | Changes domain meaning slightly |
| 5 | WB: add top-10% income share | World Bank | Yes — new API call (easy) | Low | Moderate | Coverage gaps vs. Gini |
| 6 | Resource capture: fix question text | None | No | Trivial | Low | None |
| 7 | Data quality flags | None | No (presentation) | Low | Moderate | Need principled criteria for which countries to flag |
| 8 | UK Crown Dependencies annotation | TJN | No — already fetched | Medium | High (for credibility) | Precedent for other parent-dependency relationships |
