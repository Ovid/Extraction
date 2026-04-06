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

How much wealth is extracted through debt, financial fees, and financialization.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Domestic credit to private sector (% GDP) | World Bank | FS.AST.PRVT.GD.ZS | Direct |

Domain score = normalized indicator score.

### 4. Institutional Gatekeeping

Whether institutions serve the broad population or narrow interests.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Control of Corruption | World Bank (WGI) | CC.EST | Inverted |
| Regulatory Quality | World Bank (WGI) | RQ.EST | Inverted |
| Government Effectiveness | World Bank (WGI) | GE.EST | Inverted |
| Rule of Law | V-Dem | v2x_rule | Inverted |

When both World Bank and V-Dem data are available for this domain, the domain score is the average of the World Bank group score and the V-Dem score.

### 5. Information & Media Capture

Control over the flow of information and media freedom.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Press Freedom Index | RSF | (composite score) | Direct (higher RSF score = less free) |
| Freedom of Expression | V-Dem | v2x_freexp_altinf | Inverted |
| Alternative Info Sources | V-Dem | v2xme_altinf | Inverted |

When both RSF and V-Dem data are available, scores are merged by averaging.

### 6. Resource Capture

How vulnerable resource wealth is to elite capture. This is a **composite score**:

```
resource_capture = resource_rents × institutional_weakness / 100
```

Where:
- `resource_rents` = normalized World Bank natural resource rents (% GDP), indicator NY.GDP.TOTL.RT.ZS
- `institutional_weakness` = the institutional_gatekeeping domain score (0-100)

This means high resource dependence only produces a high score when institutions are too weak to prevent elite capture. For example, Norway has significant resource rents but strong institutions, resulting in a very low resource capture score (1/100). DR Congo has moderate resource rents and very weak institutions, resulting in a high score (56/100).

When institutional data is unavailable to weight against, the raw resource rents score is used with confidence capped at "low."

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

For the resource capture domain, context facts reflect the composite calculation (resource rents moderated by institutional strength) rather than raw resource rents alone.

## Data Sources

| Source | Type | Domains | Coverage |
|--------|------|---------|----------|
| [World Bank](https://data.worldbank.org/) | API (automatic) | Economic concentration, financial extraction, institutional gatekeeping, resource capture | 190+ countries |
| [V-Dem](https://www.v-dem.net/) | Manual download (CAPTCHA-protected) | Political capture, information capture, institutional gatekeeping | 202 countries |
| [RSF Press Freedom Index](https://rsf.org/) | Web scrape (automatic) | Information capture | 180 countries |
| [Tax Justice Network FSI](https://fsi.taxjustice.net/) | API with public token (automatic) | Transnational facilitation | 141 jurisdictions |

See `sources.md` for the complete source registry including URLs, coverage details, and update cycles.

## Known Limitations

1. **Three of seven domains have no trend data.** Political capture, information capture (V-Dem portion), and transnational facilitation lack time-series trend analysis because the trend function only processes World Bank data.

2. **Financial extraction relies on a single indicator** (domestic credit to private sector). This is a crude proxy — it captures the scale of financialization but not the distributional consequences.

3. **The legibility paradox.** The most extractive regimes produce the worst data. Countries like North Korea and Eritrea have very few indicators, and their scores may understate actual extraction.

4. **Legal extraction is hard to measure.** Most structurally important extraction is legal (tax policy, intellectual property, regulatory capture). The index captures some of this indirectly through institutional indicators but cannot directly measure legislative capture.

5. **Normalization is relative.** Min-max scaling means scores reflect a country's position relative to the global range, not an absolute standard. If all countries became more extractive simultaneously, individual scores might not change.

6. **Resource capture depends on institutional data.** Countries without institutional gatekeeping data get a raw resource rents score with reduced confidence, which may misrepresent their actual extraction dynamics.

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

**V-Dem requires manual download:** Visit https://www.v-dem.net/data/the-v-dem-dataset/, download "Country-Year: V-Dem Core" (CSV), and extract to `raw_data/vdem/vdem_core_full.csv`. The download is CAPTCHA-protected.

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
