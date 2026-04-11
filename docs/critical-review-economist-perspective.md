# Critical Review: The Extraction Index from an Economist's Perspective

*Review date: 2026-04-10*
*Index version: 0.1.0*
*Methodology reference: METHODOLOGY.md*

## Purpose of This Review

This document subjects the Extraction Index to the kind of scrutiny it would face from professional economists, development researchers, and policy analysts. The goal is not to undermine the index but to identify where its claims are strongest, where they are weakest, and where presentation can be improved to preempt credible objections.

The index draws its conceptual framework from Acemoglu and Robinson's "Why Nations Fail" (2012), which distinguishes extractive institutions (concentrating power and wealth in narrow elites) from inclusive institutions (distributing opportunity broadly). The seven-domain structure is an attempt to operationalize that distinction with available cross-country data.

---

## Part 1: Domain-by-Domain Critique

### 1.1 Political Capture (USA: 14)

**What it measures:** V-Dem indices for political corruption (0.06), clientelism (0.10), electoral democracy (0.73), and physical violence (0.79).

**What it gets right:** These are well-established, peer-reviewed indices from one of the most respected political science datasets in the world. The V-Dem methodology uses expert coding with Bayesian measurement models. For countries where political extraction takes the form of outright vote-buying, patronage networks, and violent repression, this domain works well.

**The structural blind spot — legalized influence:**

The US scores 14/100 on political capture. This would strike most political economists as implausible, and the reason is fundamental: V-Dem's corruption and clientelism indices are calibrated to detect the forms of political extraction prevalent in developing countries — cash-for-votes, patronage appointments, kleptocratic diversion. They are largely blind to the institutionalized influence industry in mature democracies.

Consider what is absent:

| Mechanism | Scale (US) | Captured by V-Dem? |
|-----------|-----------|-------------------|
| Federal lobbying expenditure | ~$4.3B/year (OpenSecrets, 2024) | No |
| Campaign contributions (federal) | ~$14B in 2020 cycle | No |
| Revolving door (Congress ↔ K Street) | ~50% of retiring members become lobbyists | No |
| Regulatory capture | Systematic but unquantified | No |
| Gerrymandering / voter suppression | Extensive documentation | Partially (polyarchy) |
| Citizens United and dark money | Unlimited corporate political spending since 2010 | No |

The result is that the US (14) scores lower on political capture than Brazil (29), India, or Mexico — countries where political corruption is more visible but arguably less *structurally embedded* than in the US. An Acemoglu/Robinson framework would classify the US lobbying system as a textbook extractive institution: it is legal, stable, self-reinforcing, and systematically transfers policy outcomes from broad public interests to narrow economic elites.

**Severity: High.** This is the single most damaging credibility gap for US-focused audiences, who will immediately notice that their country's well-documented influence industry is invisible to the index.

**Possible mitigations:**
- Acknowledge the gap explicitly in country-level presentation
- Add lobbying/campaign finance data if a cross-country source exists (V-Dem's "party institutionalization" and "legislative corruption" variables may partially help; IDEA's Political Finance Database is another option)
- Consider renaming the domain to clarify scope: "Political Capture (Electoral)" vs. the broader concept

---

### 1.2 Economic Concentration (USA: 38)

**What it measures:** Gini coefficient (41.8) and ILO labour share of GDP (55.8%).

**What it gets right:** Both indicators are well-sourced and conceptually relevant. The Gini index is the standard cross-country inequality measure. Labour share of GDP directly measures the capital-labour split — when labour share falls, a larger fraction of economic output is captured by capital owners, which is definitionally extraction in the Acemoglu/Robinson sense.

**Objection 1 — Income vs. wealth inequality:**

The Gini coefficient measures *income* inequality. For the US, this substantially understates concentration because:

- The US *wealth* Gini is approximately 0.85 (Federal Reserve SCF data), among the highest in the OECD.
- The top 1% holds ~31% of total household wealth; the bottom 50% holds ~2.6%.
- Much of the most consequential extraction in the US operates through asset appreciation (real estate, equities) that never appears in income statistics until realized.
- Capital gains, carried interest, and unrealized appreciation in closely-held businesses are largely invisible to income-based Gini.

An economist would argue that wealth inequality is the *stock* variable that matters for structural extraction, while income inequality is merely the *flow*. A country with moderate income inequality but extreme wealth concentration (the US pattern) is one where extraction has already occurred and is locked in through dynastic wealth transmission.

**Objection 2 — Labour share trends matter more than levels:**

The US labour share of 55.8% is scored as "moderate" extraction. But the Acemoglu/Robinson framework cares about *institutional dynamics*, not just snapshots. The US labour share declined from approximately 65% in the early 1970s to the mid-50s today — a transfer of roughly 10 percentage points of GDP from workers to capital owners over five decades. This is one of the most-studied extraction dynamics in modern economics (Autor et al. 2020, Karabarbounis & Neiman 2014).

The index marks this trend as "stable," which is technically correct for the recent decade (the decline plateaued around 2012-2015), but obscures the larger story. A country that completed a massive extraction shift and then stabilized at the new level appears no different from one that was always at that level.

**Objection 3 — Market concentration is absent:**

The US has experienced significant increases in market concentration across most industries over the past 25 years (Grullon, Larkin & Michaely 2019; De Loecker, Eeckhout & Unger 2020). Corporate markups have risen from ~20% above marginal cost in 1980 to ~60% by 2020. This is a direct measure of economic extraction — firms charging above competitive prices — and it is entirely absent from the domain.

**Severity: Moderate.** The score of 38 is in the right ballpark, but for the wrong reasons. The domain captures income inequality reasonably well but misses the more distinctive features of US economic extraction: extreme wealth concentration and rising market power.

---

### 1.3 Financial Extraction (USA: 52)

**What it measures:** Domestic credit to private sector (200.9% of GDP) and bank net interest margin (2.77%).

**What it gets right:** The conceptual framing is sound — financial extraction is about the *cost* of intermediation, not just the *size* of the financial sector. Adding the net interest margin (NIM) was a significant improvement over credit volume alone.

**Objection 1 — Credit volume is doing almost all the work:**

The USA's financial extraction score of 52 breaks down as:
- Domestic credit normalized: **87.0** (200.9% of GDP, near global maximum of 231%)
- Net interest margin normalized: **17.9** (2.77%, which is below the global median of 3.1%)
- Average: **52.4**

The NIM tells us that US banks extract *less per dollar intermediated* than the global median. The score of 52 is almost entirely driven by credit *volume*. An economist would make two objections:

First, deep credit markets are a feature of financial development, not evidence of extraction. The US has the world's deepest corporate bond market, securitization markets, and venture capital ecosystem. High domestic credit/GDP reflects this market depth. Penalizing it is equivalent to saying financial development is extractive — a claim that contradicts the mainstream development economics literature (Levine 2005, Beck et al. 2000).

Second, the NIM of 2.77% is *low by global standards* and *moderate among high-income countries* (39% above the HIC average of 2.00%). Labeling it "Low" in the UI but having it contribute to a score of 52 is confusing. The user sees "Low extraction per dollar" but the composite says "moderately extractive financial system."

**Objection 2 — The wrong kind of financial extraction:**

What makes the US financial system extractive is not bank lending but rather:

| Mechanism | Approximate scale | In the index? |
|-----------|------------------|---------------|
| Medical debt | $220B outstanding | No |
| Student loan debt | $1.77T outstanding | No |
| Credit card interest spreads | Average rate ~22% vs. ~5% fed funds | No (NIM is a bank-level measure) |
| Private equity fee extraction | ~$7T AUM, 2-and-20 fee structure | No |
| Pharmaceutical pricing | US prices 2-3x other OECD countries | No |
| Housing cost burden | 30%+ of income for ~40% of renters | No |

These are the mechanisms that an American economist would identify as financial extraction. Bank NIM is a legitimate but narrow proxy. The index measures the plumbing (banks) but misses the buildings connected to it (debt burdens, fee structures, price gouging in credit-adjacent markets).

**Objection 3 — Hong Kong, Japan, and China all score similarly, for very different reasons:**

Hong Kong (credit 231% GDP) and Japan (credit 197% GDP) score high on the credit metric, but their financial systems extract in fundamentally different ways from the US. Japan's high credit reflects decades of low-interest corporate lending (NIM 0.54% — nearly the global minimum). Hong Kong's reflects its role as a financial entrepot. The index treats them as equivalently extractive because the indicators can't distinguish financial depth from financial predation.

**Severity: High.** The domain's core insight (measuring the *cost* of intermediation) is good, but the implementation still lets credit volume dominate the score, producing counterintuitive results for financially developed economies.

---

### 1.4 Institutional Gatekeeping (USA: 28)

**What it measures:** World Bank control of corruption (1.12), V-Dem rule of law (0.92), V-Dem egalitarian component (0.57), V-Dem participatory democracy (0.51).

**What it gets right:** This is the most conceptually sophisticated domain. It explicitly tries to measure whether institutions serve broad or narrow interests, going beyond simple "good governance" metrics.

**The core tension — strong institutions enforcing extractive arrangements:**

The US scores "Very high" on rule of law (0.92) and "High" on corruption control (1.12). These are accurate. US courts enforce contracts reliably, property rights are secure, and overt corruption is relatively rare.

But this is precisely the pattern Acemoglu and Robinson identify as the most durable form of extraction: *strong institutions that enforce rules designed to benefit narrow interests*. Consider:

- The US patent system (strong rule of law) enables pharmaceutical companies to maintain monopoly pricing that extracts $100B+/year above competitive levels
- Bankruptcy law (strong rule of law) was reformed in 2005 to make student debt non-dischargeable, protecting lender extraction
- Forced arbitration clauses (enforced by strong courts) strip consumers and workers of legal remedies
- Non-compete agreements (enforced by strong courts, until recently) suppressed worker bargaining power

Rule of law scores high because the institutions *work*. Extraction scores low because the institutions are *not corrupt*. But "efficient and non-corrupt institutions that serve narrow interests" is exactly what extractive institutions look like in a mature democracy.

The egalitarian component (0.57, 28% below HIC average) is the indicator that actually captures this — and it's telling us something important. But it gets equal weight with three indicators that measure institutional *quality* rather than institutional *purpose*, so its signal is diluted.

**Severity: Moderate-High.** The domain includes the right indicator (egalitarian component) but dilutes it with indicators that measure something different (institutional quality). An economist might argue the egalitarian component should be weighted more heavily in this domain, or that rule-of-law and corruption-control are better suited to a separate "institutional quality" domain.

---

### 1.5 Information & Media Capture (USA: 32)

**What it measures:** RSF Press Freedom score (65.5), V-Dem freedom of expression (0.73), V-Dem alternative information sources (0.65).

**What it gets right:** These are reputable sources measuring important dimensions of information freedom. The score of 32 — moderately extractive — is broadly defensible.

**Objection — media ownership concentration and algorithmic capture are absent:**

The US media landscape has undergone massive consolidation. Six companies control ~90% of US media (down from 50+ in the 1980s). Local news has collapsed — roughly 2,900 newspapers have closed since 2005 (Northwestern Medill, 2024). Sinclair Broadcasting controls ~190 local TV stations with centralized editorial mandates.

Meanwhile, algorithmic information curation (Facebook, YouTube, TikTok) creates extraction dynamics that no press freedom index captures: not *suppression* of information but *manipulation* of attention for advertising revenue.

These are real forms of information capture, but they don't register on indices designed to measure state censorship and journalist safety.

**Severity: Low-Moderate.** The score of 32 is plausible. The missing dimensions would push it higher but probably not dramatically so. This is less of a credibility issue than political capture or financial extraction.

---

### 1.6 Resource Capture (USA: 5)

**What it measures:** Natural resource rents (1.3% of GDP), moderated by democratic accountability (V-Dem polyarchy 0.73).

**What it gets right:** The formula (resource rents * democratic deficit) is well-grounded in the resource curse literature. For the US, resource rents are genuinely low as a share of GDP, and democratic accountability provides a real check on resource capture.

**Objection — fossil fuel subsidies and public land policy:**

The US provides approximately $20B/year in direct fossil fuel subsidies (OECD estimate) and $600B+/year when including health and environmental externalities (IMF estimate). Federal lands are leased for mining and drilling at below-market rates (the General Mining Law of 1872 is still in effect). These represent resource extraction in both the geological and Acemoglu/Robinson senses — public resources captured by private interests through institutional mechanisms.

None of this appears in "natural resource rents as % of GDP" because subsidies flow *from* the public *to* extractors, while the World Bank indicator measures rents flowing *from* resources *to* GDP.

**Severity: Low for the US** (resource rents genuinely are a small part of the economy), **but high for resource-rich democracies** like Norway, Canada, and Australia where the formula may understate extraction by giving too much credit to democratic institutions.

---

### 1.7 Transnational Facilitation (USA: 77)

**What it measures:** Tax Justice Network Financial Secrecy Index score (69/100).

**What it gets right:** The US *is* a major financial secrecy jurisdiction. Delaware, Nevada, Wyoming, and South Dakota allow shell companies and trusts with minimal beneficial ownership disclosure. The US has not joined the OECD's Common Reporting Standard (CRS) for automatic tax information exchange. The TJN's assessment is well-researched and the score of 69 is substantively justified.

**Objection 1 — Single-indicator domain:**

This is the only domain with a single data source, and its confidence is rated "low." An economist would want to see:

- Volume of offshore financial flows (not just secrecy laws)
- Effective corporate tax rates vs. statutory rates
- Profit shifting intensity (Torslov, Wier & Zucman 2022 estimate $1T/year shifted globally)
- Treaty shopping and tax haven network centrality

**Objection 2 — The UK anomaly:**

The UK scores 31 (FSI=45), which is arguably the single most misleading score in the entire index. The UK's domestic secrecy score is relatively low, but the UK *designed and controls* the world's largest network of offshore financial centers:

- Crown Dependencies: Jersey (FSI=67), Guernsey (FSI=68), Isle of Man (FSI=62)
- Overseas Territories: Cayman Islands (FSI=72), British Virgin Islands (FSI=72), Bermuda (FSI=68), Turks and Caicos, Gibraltar, Anguilla, Montserrat

The UK appoints the governors, retains constitutional authority, and can (and occasionally does) impose legislation on these territories. Academic literature on "the spider's web" of British offshore finance (Shaxson 2011, Bullough 2022) makes a strong case that the UK's *effective* transnational facilitation score should incorporate its dependencies.

Scoring the UK at 31 while Switzerland scores 89 would be considered misleading by most economists studying international tax avoidance.

**Severity: High for the UK; moderate for the US.** The US score is defensible in direction if not precision. The UK score is indefensible without a prominent disclaimer.

---

## Part 2: Cross-Country Anomalies

These are cases where the index produces results that would undermine its credibility with informed audiences.

### 2.1 Nigeria — Economic Concentration: 13

Nigeria's labour share of GDP is reported at 75.1% — the global maximum in the dataset, higher than Belgium, Switzerland, or any Scandinavian country. This drives the economic concentration score to 13, lower than Norway (26), Germany (20), or Japan (27).

**Why this is almost certainly wrong:**

Nigeria's informal economy accounts for approximately 65% of employment and an estimated 50-65% of GDP (IMF, AfDB estimates). The ILO's labour share estimates for countries with large informal sectors rely on imputations for self-employment income that are known to be unreliable. The ILO's own documentation flags this: "For countries with large shares of self-employment, estimates of labour income may be subject to substantial uncertainty."

In Nigeria specifically:
- Much of the imputed "labour income" is subsistence agriculture and petty trading
- The distinction between labour income and capital income is largely meaningless for informal sector workers
- The Gini of 33.9 also appears low given Nigeria's well-documented inequality (Africa's largest population of people in extreme poverty coexisting with Africa's richest individuals)
- The World Bank's own Nigeria poverty assessment notes "significant measurement challenges"

**An economist's verdict:** This is a data quality failure, not an analytical one. The methodology is sound — if the data were reliable, the calculation would be correct. But presenting Nigeria as having less economic concentration than Norway would instantly discredit the index with any Africa specialist.

### 2.2 Ireland — Financial Extraction: 9

Ireland's domestic credit to private sector is reported at 23.8% of GDP. This is almost certainly an artifact of Ireland's well-known GDP distortion.

Ireland's GDP was inflated by approximately 25% in a single year (2015, the "leprechaun economics" event) when several multinationals relocated intellectual property assets to Ireland for tax purposes. The Central Statistics Office of Ireland itself created an alternative measure — **Modified Gross National Income (GNI*)** — because GDP is so misleading.

If we use GNI* (roughly 60% of GDP), Ireland's domestic credit ratio would be approximately 40% — still low, but in a very different position on the global distribution. The financial extraction score would roughly double.

More fundamentally, Ireland's role in global financial extraction is as a *corporate tax conduit*. Apple, Google, Facebook, and other multinationals route hundreds of billions in profits through Irish subsidiaries. This is extraction in the most literal sense — value created in one jurisdiction, captured in another — but it shows up in the *transnational facilitation* domain (score 55), not financial extraction.

### 2.3 China — Economic Concentration: 34 (Below USA at 38)

China scoring lower than the US on economic concentration would surprise most economists. China's Gini has declined from ~47 to ~38 in recent years, and the ILO estimates a moderate labour share. The data-driven score is arithmetically correct.

**But:** China's economic extraction increasingly operates through mechanisms invisible to these indicators:

- State-directed capital allocation creates massive misallocation rents (estimated at 2-5% of GDP by Hsieh & Klenow 2009)
- SOE monopolies in banking, telecoms, energy, and tobacco capture rents without generating inequality in the income distribution (the rents accrue to the state/party, not to individuals)
- Land requisition from rural areas for urban development has been one of the largest wealth transfers in human history — rural residents are compensated at agricultural land values while local governments sell at urban development values, capturing the difference
- The hukou system creates a labour market segmentation that functions like extraction but doesn't show up in national Gini statistics

The deeper issue is that Gini and labour share measure *household-level* income distribution. In a state-capitalist system, the most consequential extraction occurs *between the state and households*, not between households.

### 2.4 Singapore — Composite: 37 (Higher Than USA: 35?)

Singapore's composite of 37 is dominated by information capture (59) and transnational facilitation (76). The economic concentration score of 49 reflects a genuine Gini (~52-54 range). But Singapore's institutional model produces outcomes that complicate the extraction framing:

- 90%+ homeownership through government HDB program
- Near-universal healthcare at a fraction of US cost
- CPF mandatory savings means retirement security is high despite income inequality
- One of the world's lowest poverty rates

An economist would ask: if Singapore has higher income inequality than the US but substantially better outcomes on housing, healthcare, and poverty, is income inequality actually measuring extraction? Or is it measuring something else (wage dispersion in a highly productive economy with strong redistribution through non-cash channels)?

This doesn't invalidate the score, but it highlights that extraction-as-measured-by-the-index and extraction-as-experienced-by-citizens can diverge significantly.

### 2.5 UK — Transnational Facilitation: 31

Discussed in detail in Section 1.7. This is the index's most indefensible single number for an informed audience. The UK scores lower than Norway (50), Luxembourg (52), and Ireland (55) on enabling global extraction — a result that would be met with disbelief by any economist working on international tax policy.

---

## Part 3: Systemic Methodological Concerns

### 3.1 Min-Max Normalization Creates Hidden Instability

All scores are relative to the global min and max for each indicator. This means:

- If the most extreme country is removed, all scores shift
- If a new data release changes one country's value, every country's normalized score changes
- Two versions of the index produced from different data vintages may produce different scores for a country even if that country's underlying reality hasn't changed

This is a well-known limitation of min-max normalization (OECD Handbook on Constructing Composite Indicators, 2008). Alternative approaches:

| Method | Advantage | Disadvantage |
|--------|-----------|--------------|
| Min-max (current) | Intuitive 0-100 range | Sensitive to outliers, relative |
| Z-score | Robust to outliers | No bounded range, less intuitive |
| Fixed benchmarks | Absolute, stable | Requires domain expertise to set thresholds |
| Percentile rank | Robust to outliers | Loses magnitude information |

**Recommendation:** At minimum, disclose the min and max anchor countries for each indicator. Consider whether fixed benchmarks (e.g., "Gini above 50 = extreme extraction") might be more defensible for indicators with well-established interpretive thresholds.

### 3.2 Equal Domain Weighting Is a Strong Implicit Claim

Equal weighting says that political capture and resource capture matter equally to every country's composite score. But:

- For Norway, resource capture is the central governance challenge; for Singapore, it's irrelevant
- For the US, financial extraction and institutional gatekeeping dominate; for Nigeria, political capture and resource capture dominate
- For Switzerland, transnational facilitation is arguably the most important domain; equal weighting buries it in the composite

The adjustable weights in the UI are a good design choice, but the *default* composite — which is what gets cited, shared, and compared — makes the equal-weighting assumption.

**Recommendation:** The current equal-weighting default is defensible (it's the least arbitrary choice when no weighting theory is available), but the presentation should make this explicit: "Composite scores assume equal domain weights. Adjust weights to reflect different theoretical priorities."

### 3.3 The Cross-Domain Convertibility Thesis Needs Evidence

The index's key analytical claim is that extraction is "cross-domain convertible — block it in one domain and it migrates to another." This is a strong and interesting hypothesis, but as currently presented it is unfalsifiable:

- If a country reduces extraction in one domain and another rises → confirms the thesis
- If a country reduces extraction in one domain and others don't rise → successful reduction (thesis not tested)
- If all domains rise → extraction is increasing (thesis not tested)

To make this testable, the index would need:
- Time-series data showing correlated movements across domains
- Case studies of policy interventions that reduced extraction in one domain, with evidence of migration
- Statistical tests of cross-domain correlation

This is more of a research agenda than a presentation fix, but the current framing overstates the evidentiary basis for the claim.

### 3.4 Trends Are Inconsistent Across Domains

Three of seven domains (political capture, information capture, transnational facilitation) show "unknown" trends because the trend function only processes World Bank time-series data. For the USA:

- Political capture: unknown trend (despite V-Dem time series existing)
- Economic concentration: stable
- Financial extraction: rising
- Institutional gatekeeping: rising
- Information capture: unknown trend
- Resource capture: falling
- Transnational facilitation: unknown trend

The overall trend is marked "rising" but is based on only 4/7 domains. An economist would note that the excluded domains (political and information capture) are where much of the US extraction discourse is focused (Citizens United, media consolidation, tech monopolies on information). Excluding them from trend analysis makes the trend estimate unreliable precisely where it matters most.

### 3.5 Missing Domains

Several forms of extraction that economists would consider central to the Acemoglu/Robinson framework are entirely absent:

| Missing domain | Why it matters | Data availability |
|----------------|---------------|-------------------|
| **Tax policy** | Effective corporate tax rates, capital gains treatment, estate tax erosion | OECD Tax Database, ICTD/UNU-WIDER GRD |
| **Intellectual property rents** | Patent monopolies, copyright extension, pharma pricing | No single cross-country source |
| **Housing/land extraction** | Largest asset class; land value capture by owners vs. renters | OECD Housing Affordability, BIS property prices |
| **Labour market monopsony** | Non-competes, occupational licensing, union suppression | OECD Employment Protection, ILO (partial) |
| **Healthcare extraction** | Cost of care as share of outcomes | WHO, OECD Health Statistics |
| **Debt burden** | Household debt/income, student debt, medical debt | BIS, national sources only |

Not all of these are feasible to add, but their absence means the index systematically understates extraction in countries where it operates through these channels — which is precisely the set of mature democracies where the index should be most illuminating.

---

## Part 4: What the Index Gets Right

It would be unfair to conclude without noting what the index does well, because these strengths are real and worth preserving:

1. **The seven-domain structure is genuinely insightful.** Most indices measure corruption OR inequality OR press freedom. Measuring all of them and presenting them together reveals patterns that single-axis indices miss. The US profile (low political capture + high financial extraction + high transnational facilitation) tells a story that no single indicator can.

2. **The transnational facilitation axis is critical and rare.** Almost no other governance index captures how countries *enable* extraction elsewhere. Without it, Luxembourg looks like Denmark and Switzerland looks like Norway. This axis alone makes the index worth building.

3. **The resource capture formula is well-designed.** Modulating resource rents by democratic accountability is grounded in peer-reviewed literature and produces sensible results (Norway gets more credit for democratic oversight of oil wealth than Saudi Arabia does).

4. **The confidence model is honest.** Most indices present point estimates without uncertainty. The extraction index's per-domain confidence ratings and known-limitations disclosure are better practice than most of the field.

5. **The interactive weight adjustment is excellent.** Letting users change domain weights converts a normative debate (which domains matter most?) into an empirical exploration. This is the right approach when no consensus weighting exists.

6. **The methodology document is unusually transparent.** The full formula, every indicator, every data source, and known limitations are disclosed. Most published indices are far less transparent.

---

## Part 5: Recommendations for Presentation

The following changes address economist objections through presentation improvements rather than methodology changes. They can be implemented without modifying the scoring algorithm.

### 5.1 Per-Domain Scope Statements

Each domain should include a brief "What this measures (and what it doesn't)" statement visible to users. Examples:

> **Political Capture** measures electoral corruption, patronage, and democratic freedom. It does not capture legalized influence channels (lobbying, campaign finance, revolving doors) which may be the dominant form of political capture in mature democracies.

> **Financial Extraction** measures the scale of bank credit and the cost of bank intermediation. It does not capture non-bank financial extraction (student debt terms, medical billing, private equity fees) or distinguish credit that builds household wealth from credit that destroys it.

> **Transnational Facilitation** measures domestic financial secrecy laws. For the UK, Crown Dependencies and Overseas Territories (Cayman Islands, BVI, Jersey, etc.) are scored as separate jurisdictions. The UK's effective facilitation network is substantially larger than this domestic score indicates.

### 5.2 Data Quality Flags

Countries with known data reliability issues should display visible warnings:

- **Nigeria, Ethiopia, and other large informal economies:** "Labour share estimates may be unreliable due to large informal sector. ILO data relies on imputations for self-employment income."
- **Ireland:** "GDP is significantly inflated by multinational profit shifting. Indicators denominated in % of GDP may understate extraction. Ireland's Central Statistics Office recommends using GNI* instead."
- **Small island states:** "Small population and limited statistical capacity increase measurement uncertainty."

### 5.3 "Known Blind Spots" Per Country

For countries where the index is known to miss important extraction mechanisms, a brief section:

> **United States — What this profile doesn't capture:**
> - Lobbying expenditure (~$4B/year federal)
> - Wealth inequality (wealth Gini ~0.85 vs. income Gini 0.42)
> - Healthcare cost extraction (18% of GDP, ~2x OECD average)
> - Student and medical debt burden ($2T+)
> - Market concentration and rising corporate markups

### 5.4 Distributional Context for Normalized Scores

When a score is shown, indicate where it falls in the global distribution. "Financial Extraction: 52" is ambiguous — it could mean median or moderately high. Adding "higher than 75% of countries" or showing a small distribution sparkline would help users interpret the number correctly.

### 5.5 Cross-Reference Notes for Split Jurisdictions

Where a country's score is known to be affected by jurisdictional splitting:

> **United Kingdom** — See also: Cayman Islands, British Virgin Islands, Jersey, Guernsey, Isle of Man, Bermuda, Gibraltar (UK Crown Dependencies and Overseas Territories scored separately).

### 5.6 Composite Score Methodology Callout

The composite score should always display a brief note:

> "Composite = unweighted average of 7 domains. Adjust domain weights to reflect different analytical priorities."

This preempts the "why equal weights?" objection by making it a feature rather than a hidden assumption.

---

## Part 6: Summary of Issues by Severity

### Critical (would undermine credibility with informed audiences)

1. **US political capture at 14** — the lobbying/campaign finance blind spot
2. **UK transnational facilitation at 31** — Crown Dependencies excluded
3. **Nigeria economic concentration at 13** — ILO labour share data unreliable for informal economies

### Significant (would draw objections from specialists)

4. **Financial extraction dominated by credit volume** — penalizes financial development
5. **Income vs. wealth inequality** — understates concentration in asset-rich economies
6. **Ireland's GDP distortion** — affects any %-of-GDP indicator
7. **China economic concentration below USA** — misses state-level extraction
8. **Three of seven domains have no trend data**

### Moderate (worth acknowledging but not fatal)

9. Min-max normalization instability
10. Equal weighting assumption
11. Cross-domain convertibility thesis lacks evidence
12. Information capture misses media consolidation and algorithmic curation
13. Singapore's outcome paradox (high inequality, good outcomes)

### Low Priority (theoretical concerns, hard to address)

14. Missing domains (tax policy, IP rents, housing, healthcare)
15. Resource capture formula may over-credit democratic institutions
16. NIM reflects business model, not just extraction
