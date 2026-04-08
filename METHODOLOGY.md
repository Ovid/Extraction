# Methodology

This document explains how the Extraction Index scores are calculated, what data sources are used, and how researchers can replicate the results.

## What the Index Measures

The Extraction Index measures systematic value capture ("extraction") across seven domains for countries worldwide. Extraction is defined as the structural transfer of value from broader populations to narrow interests — whether through political monopolization, economic concentration, financial mechanisms, institutional capture, information control, resource exploitation, or transnational flows.

A key insight: extraction is **cross-domain convertible**. Block it in one domain and it migrates to another. This is why the index uses seven axes rather than a single measure.

All scores run from 0 (no extraction) to 100 (extreme extraction). Most structurally important extraction is legal. A country can score low on corruption and high on extraction (e.g., financial extraction through legal debt mechanisms).

## The Seven Domains

### 1. Political Capture

Elite monopolization of political power. Measured through:

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Political Corruption | V-Dem | v2x_corr | Direct (higher = more extraction) |
| Clientelism | V-Dem | v2xnp_client | Direct |
| Electoral Democracy | V-Dem | v2x_polyarchy | Inverted (higher = less extraction) |
| Political Violence | V-Dem | v2x_clphy | Inverted |

Domain score = mean of normalized indicator scores.

### 2. Economic Concentration

Wealth inequality and the gap between productivity and worker compensation.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Gini Index | World Bank | SI.POV.GINI | Direct |
| GDP per worker | World Bank | SL.GDP.PCAP.EM.KD | Direct |

Domain score = mean of normalized indicator scores.

### 3. Financial Extraction

The cost of financial intermediation — how much the financial sector extracts as its cut when mediating between savers and borrowers. A large financial sector is not inherently extractive; what matters is whether intermediation is priced competitively or used as a rent-seeking mechanism.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Domestic credit to private sector (% GDP) | World Bank | FS.AST.PRVT.GD.ZS | Direct |
| Bank net interest margin (%) | World Bank (GFDD) | GFDD.EI.01 | Direct |

Domain score = mean of normalized indicator scores.

**Why these indicators:**

- **Domestic credit (% GDP)** measures the scale of financial exposure. Higher credit volumes create more surface area for extraction, though high credit alone is not sufficient evidence of extraction — it must be interpreted alongside the net interest margin.
- **Bank net interest margin** directly measures the price of intermediation — the difference between what banks earn on loans and what they pay on deposits, as a share of assets. Countries with competitive, well-regulated financial markets (e.g., Scandinavia) have low margins even when credit volumes are high, while countries where banks extract more rent per dollar intermediated (e.g., the United States) have higher margins.

**Why equal weighting:** Each indicator contributes equally to the domain score, consistent with all other multi-indicator domains in the index. Domestic credit's influence is reduced from 100% to 50% — not through arbitrary downweighting, but as a structural consequence of measuring the concept more completely. The principle is that each theoretically justified indicator gets one vote.

**Limitations:**

- **Credit volume is ambiguous.** High domestic credit can reflect either productive financialization (e.g., Scandinavian mortgage markets where homeownership builds household wealth) or extractive financialization (e.g., US medical and student debt). The net interest margin partially disambiguates this, but cannot fully distinguish wealth-building credit from extractive credit.
- **Net interest margins reflect business model, not just extraction.** Banks with high fee income may show low margins while still extracting heavily through non-interest charges. Conversely, banks in developing economies may have high margins that partly reflect legitimate credit risk rather than rent-seeking.
- **Household-level data is unavailable.** The World Bank does not provide cross-country household debt-to-income ratios, household net wealth, or mortgage-specific default rates. These would better capture whether financial activity builds or destroys household wealth, but would require BIS, OECD, or IMF data sources not yet integrated into the pipeline.
- **NIM data lags.** The most recent World Bank GFDD data is typically 2-3 years behind the current year.

### 4. Institutional Gatekeeping

Whether institutions serve the broad population or narrow interests.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Control of Corruption | World Bank (WGI) | CC.EST | Inverted |
| Rule of Law | V-Dem | v2x_rule | Inverted |
| Egalitarian Component | V-Dem | v2x_egal | Inverted |
| Participatory Democracy | V-Dem | v2x_partipdem | Inverted |

The World Bank WGI Control of Corruption indicator measures the extent to which public power is exercised for private gain, including capture of the state by elites — directly relevant to institutional gatekeeping. The V-Dem indicators measure how equally power and resources are distributed and how much citizens can participate in governance.

**Why Government Effectiveness and Regulatory Quality are excluded:** These WGI indicators measure state capacity (bureaucratic competence, pro-business regulatory environment) rather than who institutions serve. An efficient autocracy scores well on both — high government effectiveness and strong regulatory quality — without its institutions serving broad interests. Including them would systematically understate extraction in competent autocracies.

When both World Bank and V-Dem data are available for this domain, the domain score is the average of the World Bank group score and the V-Dem group score.

### 5. Information & Media Capture

Control over the flow of information and media freedom.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Press Freedom Index | RSF | (composite score) | Inverted (higher RSF score = more free, post-2022 methodology) |
| Freedom of Expression | V-Dem | v2x_freexp_altinf | Inverted |
| Alternative Info Sources | V-Dem | v2xme_altinf | Inverted |

When both RSF and V-Dem data are available, scores are merged by averaging.

### 6. Resource Capture

How vulnerable resource wealth is to elite capture. This is a **composite score**:

```
resource_capture = log_normalized_resource_rents × (100 - democratic_accountability) / 100
```

Where:
- `log_normalized_resource_rents` = World Bank natural resource rents (% GDP), indicator NY.GDP.TOTL.RT.ZS, log-transformed then min-max normalized to 0-100
- `democratic_accountability` = raw V-Dem electoral democracy index (v2x_polyarchy) × 100

Resource rents are log-transformed before min-max normalization because the raw distribution is heavily right-skewed (a few countries exceed 50% of GDP while most are under 5%). Without log transformation, linear min-max normalization compresses most countries into the lower range, understating resource capture vulnerability. Log transformation of right-skewed economic data is standard practice in economics research.

This formula uses the **raw** V-Dem polyarchy value (0-1 scale), not a min-max normalized score. Min-max normalization is relative to the dataset and would distort absolute levels — a country with polyarchy 0.50 (a hybrid regime) would appear to have majority accountability under normalization, when in reality 0.50 indicates genuinely weak democratic checks.

The justification is a first-principles argument supported by the resource curse literature (Ross 2012, Karl 1997): resource wealth is captured by elites to the extent that democratic accountability is absent. In a full autocracy, elites face no check on resource capture. In a full democracy, citizens can hold resource management accountable, reducing elite capture.

**Important limitations of this approach:**
- V-Dem polyarchy measures *electoral* democracy specifically, not all forms of accountability. Some non-electoral accountability mechanisms (tribal councils, traditional authority structures, religious checks on power) are not captured.
- The raw 0-1 scale assumes equal intervals — moving from 0.4 to 0.5 is treated as equivalent to moving from 0.8 to 0.9 — which may not reflect political reality.
- A country's formal democratic institutions may not reflect actual power dynamics. Elections can coexist with elite resource capture.
- Raw scores are guidelines. They cannot always explain reality.

When V-Dem data is unavailable, the raw resource rents score is used unmoderated, with confidence capped at "low" and a note that democratic accountability data is unavailable.

### 7. Transnational Facilitation

Enabling extraction elsewhere through financial secrecy, tax havens, and profit shifting.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Financial Secrecy Index | Tax Justice Network | (composite score) | Direct |

Domain score = normalized indicator score.

## Normalization

All indicators are normalized to 0-100 using global min-max scaling:

```
normalized = (value - min) / (max - min) × 100
```

Where `min` and `max` are computed across all countries in the dataset for that indicator. For inverted indicators (where higher raw values mean less extraction), the result is flipped:

```
normalized = 100 - normalized
```

This ensures all scores follow the convention: **0 = no extraction, 100 = extreme extraction**.

### Log-Transformed Normalization

For indicators with extreme right skew (currently: natural resource rents), a log transform is applied before min-max scaling:

```
log_normalized = (log(1 + value) - log(1 + min)) / (log(1 + max) - log(1 + min)) × 100
```

This spreads the compressed middle of the distribution while preserving the 0-100 range and relative ordering. The choice of which indicators receive log transformation is based on distributional analysis — resource rents has a skewness that compresses most countries below the 50th percentile under linear scaling.

## Composite Score

Each country's composite score is a weighted average of its available domain scores. By default, all domains are weighted equally:

```
composite = sum(domain_scores) / number_of_available_domains
```

The web interface allows users to adjust domain weights interactively. Composite scores and map colors recalculate in real time.

Countries are only scored on domains for which data exists. Missing domains are omitted, not filled with placeholders.

## Merging Multiple Sources

When multiple data sources cover the same domain (e.g., World Bank WGI and V-Dem Rule of Law both contributing to institutional_gatekeeping), scores are merged by averaging the group scores from each source.

## Trend Estimation

Trends indicate whether extraction is rising, falling, or stable over approximately the past decade. They are estimated by comparing recent values (2018 and later) against older values (2015 and earlier) for each World Bank indicator:

```
change = (recent_mean - older_mean) / |older_mean|
```

For inverted indicators, the direction is flipped (a falling raw value on an inverted indicator means extraction is rising).

A change of **10% or more** is required to register as "rising" or "falling." Changes below 10% are reported as "stable." This threshold filters out noise — small fluctuations from already-extreme baselines should not be reported as meaningful trends.

Each domain's trend is determined by majority vote across its indicators. The overall country trend is a majority vote across domains, excluding domains with "unknown" trends.

Domains sourced exclusively from V-Dem, RSF, or TJN currently report "unknown" trends because the trend function only analyzes World Bank time-series data.

## Confidence Model

Confidence reflects data reliability, assessed per domain via three factors:

### Factor Scoring (0-3 points each)

**Completeness** (number of indicators with data):
| Indicators | Points |
|------------|--------|
| 4+ | 3 |
| 3 | 2 |
| 2 | 1 |
| 1 | 0 |

**Source Diversity** (number of independent datasets):
| Sources | Points |
|---------|--------|
| 3+ | 3 |
| 2 | 2 |
| 1 | 1 |
| 0 | 0 |

**Recency** (most recent data point):
| Year | Points |
|------|--------|
| 2022+ | 3 |
| 2019-2021 | 2 |
| 2015-2018 | 1 |
| Before 2015 | 0 |

### Total Score to Confidence Level

| Total (0-9) | Confidence |
|-------------|------------|
| 7+ | High |
| 5-6 | Moderate |
| 3-4 | Low |
| 0-2 | Very low |

### Domain Coverage Cap

Overall country confidence is further capped by how many of the seven domains have data:

| Domains covered | Maximum confidence |
|----------------|-------------------|
| 6-7 | High |
| 4-5 | Moderate |
| 1-3 | Low |

This ensures countries with sparse data (e.g., North Korea with 3/7 domains) do not appear overconfident.

## Context Facts

Each indicator displays 1-2 concrete facts beneath its score to make abstract numbers meaningful.

**Fact 1 — Raw value:** Always shown. The actual indicator value with units (e.g., "Gini coefficient: 41.8").

**Fact 2 — Peer comparison:** Shown when the country differs meaningfully (>10%) from its peer group average. The scorer compares against both:
- **Regional peers** (UN geoscheme regions: Eastern Africa, Northern Europe, South America, etc.)
- **Income peers** (World Bank income groups: High income, Upper middle income, Lower middle income, Low income)

Whichever comparison produces the larger divergence is shown. If fewer than 3 peers have data, that comparison is skipped.

At extremes, comparisons use natural language appropriate to the indicator — e.g., "Strongest rule of law among high-income countries" rather than generic "Highest among."

For the resource capture domain, context facts reflect the composite calculation (resource rents moderated by democratic accountability) rather than raw resource rents alone.

## Data Sources

| Source | Type | Domains | Coverage |
|--------|------|---------|----------|
| [World Bank](https://data.worldbank.org/) | API (automatic) | Economic concentration, financial extraction, institutional gatekeeping, resource capture | 190+ countries |
| [V-Dem](https://www.v-dem.net/) | Manual download (form required) | Political capture, information capture, institutional gatekeeping | 202 countries |
| [RSF Press Freedom Index](https://rsf.org/) | Web scrape (automatic) | Information capture | 180 countries |
| [Tax Justice Network FSI](https://fsi.taxjustice.net/) | API with public token (automatic) | Transnational facilitation | 141 jurisdictions |

See `sources.md` for the complete source registry including URLs, coverage details, and update cycles.

## Known Limitations

1. **Three of seven domains have no trend data.** Political capture, information capture (V-Dem portion), and transnational facilitation lack time-series trend analysis because the trend function only processes World Bank data.

2. **Financial extraction remains under-measured.** The domain uses two indicators (domestic credit and bank net interest margin), which better capture the cost of financial intermediation than credit volume alone. However, both are macro-level proxies that cannot distinguish household-level outcomes — whether a given level of credit builds wealth (as in Scandinavian mortgage markets) or destroys it (as in US medical debt). Fully resolving this would require household-level data not available from the World Bank.

3. **The legibility paradox.** The most extractive regimes produce the worst data. Countries like North Korea and Eritrea have very few indicators, and their scores may understate actual extraction.

4. **Legal extraction is hard to measure.** Most structurally important extraction is legal (tax policy, intellectual property, regulatory capture). The index captures some of this indirectly through institutional indicators but cannot directly measure legislative capture.

5. **Normalization is relative.** Min-max scaling means scores reflect a country's position relative to the global range, not an absolute standard. If all countries became more extractive simultaneously, individual scores might not change.

6. **Resource capture depends on democratic accountability data.** Countries without V-Dem democratic accountability data get a raw resource rents score with reduced confidence, which may misrepresent their actual extraction dynamics.

## Replication

### Prerequisites

- Python 3.8+
- Dependencies: `pip install -r scripts/requirements.txt` (requests, pandas, openpyxl)

### Step 1: Fetch raw data

```bash
source .venv/bin/activate
cd scripts

# Fetch all automatic sources (World Bank, RSF, TJN)
python fetch_all.py

# Or fetch individual sources
python fetch_all.py --source worldbank
python fetch_all.py --source rsf
python fetch_all.py --source tjn

# List available sources
python fetch_all.py --list
```

**V-Dem requires manual download:** Visit https://www.v-dem.net/data/the-v-dem-dataset/, download "Country-Year: V-Dem Core" (CSV), and extract to `raw_data/vdem/vdem_core_full.csv`. The download requires filling out a form.

Raw data is stored in `raw_data/` (gitignored). A manifest at `raw_data/manifest.json` tracks what was fetched, when, and from where.

### Step 2: Generate scores

```bash
python score_countries.py                  # Score all countries
python score_countries.py --preview        # Dry run — show changes without writing
python score_countries.py --country USA    # Score a single country
python score_countries.py --overwrite      # Re-score everything, including hand-scored
```

Output is written to `data/scores.json`.

### Step 3: Verify

Open `index.html` in a browser (serve with `python3 -m http.server 8000`) and spot-check country scores against the source data.

### Reproducibility Notes

- All normalization is deterministic given the same input data.
- Source data may change between fetches as organizations update their datasets. The manifest records fetch timestamps for auditability.
- Hand-scored countries (those already in `scores.json` before running the scorer) are preserved by default. Use `--overwrite` to replace them.
- The scorer only produces scores for domains where raw data exists. It never invents scores for missing data.
