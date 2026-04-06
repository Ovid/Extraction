# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Extraction Index is a static single-page application that visualizes systematic value capture ("extraction") across seven domains for countries worldwide. It is a companion to the book "Bread, Circuses, and GPUs." There is no build system, no backend, and no framework — just vanilla HTML/CSS/JS with D3.js.

The key insight of the extraction framework: extraction is **cross-domain convertible** — block it in one domain and it migrates to another. This is why the index has seven axes, not one.

## Running Locally

```bash
python3 -m http.server 8000
# or: npx serve .
```

Open `http://localhost:8000`. No build step required.

## Architecture

```
index.html            → Shell, loads CSS/JS, methodology modal, country picker
css/style.css         → All styles, including light/dark theme via CSS custom properties
js/app.js             → D3 map, radar chart, weight controls, panel logic, theme toggle
data/scores.json      → THE DATA FILE — per-country extraction scores (222 countries)
data/schema.json      → JSON Schema defining the data structure
sources.md            → Registry of every data source with keys, URLs, coverage
scripts/
  fetch_all.py        → Orchestrator for data fetching (--source, --list)
  score_countries.py  → Auto-scorer: raw data → normalized scores → scores.json
  requirements.txt    → Python dependencies (requests, pandas, openpyxl)
  fetchers/           → Per-source fetch scripts (worldbank, vdem, rsf, fsi, cpi)
raw_data/             → Fetched data (gitignored, reproduced via scripts)
raw_data/manifest.json → Tracks what was fetched, when, from where
.venv/                → Python virtual environment (gitignored)
```

Data is loaded at init via `Promise.all` from `data/scores.json` and a CDN-hosted world-atlas TopoJSON.

### Theming

Light/dark mode is driven by CSS custom properties on `:root` (dark default) and `:root[data-theme="light"]`. All colors — including overlays, radar chart fills, no-data country fills, and shadows — use variables so both themes stay consistent. The JS toggle respects `prefers-color-scheme`, persists to `localStorage`, and calls `refreshMapColors()` to repaint the map.

### Data Flow

`data/scores.json` → `computeComposite()` (weighted average of domain scores) → `countryFill()` (D3 color scale) → SVG map render.

Users can adjust domain weights interactively; composite scores and map colors recalculate in real time.

### Visualization Components

- **Choropleth map** (D3 + TopoJSON): countries colored by composite score
- **Radar chart**: seven-axis domain comparison per country
- **Side panel**: domain breakdown cards with score bars, sources, confidence, and trends
- **Weight sliders**: interactive domain weight adjustment
- **Country picker**: dropdown in header with A-Z / Score sort toggle
- **Methodology modal**: "?" button explaining data sources, scoring, and confidence

### Key Mappings

The JS contains a hard-coded `numericToAlpha3` mapping (ISO 3166-1 numeric → alpha-3) used to join TopoJSON geometry IDs to `data/scores.json` keys. A separate `COUNTRY_NAMES` object provides human-readable names for all mapped countries. Both must be updated when adding new territories.

## The Seven Domains

1. **political_capture** — elite monopolization of political power
2. **economic_concentration** — wealth inequality, labor share decline
3. **financial_extraction** — financialization, financial secrecy
4. **institutional_gatekeeping** — whether institutions serve broad population or narrow interests
5. **information_capture** — media freedom, information control
6. **resource_labor_extraction** — natural resource governance, labor rights
7. **transnational_facilitation** — enabling extraction elsewhere (tax havens, profit shifting)

## Data Pipeline

### Step 1: Fetch raw data

```bash
source .venv/bin/activate
cd scripts
python fetch_all.py                      # All sources
python fetch_all.py --source worldbank   # Single source
python fetch_all.py --list               # Show available sources
```

| Source | Type | Domains covered |
|--------|------|-----------------|
| World Bank | API (automatic) | economic_concentration, financial_extraction, institutional_gatekeeping, resource_labor_extraction |
| V-Dem | Manual download (CAPTCHA) | political_capture, information_capture, institutional_gatekeeping |
| RSF | Page scrape (automatic) | information_capture |
| TJN FSI | API with public token (automatic) | transnational_facilitation |
| CPI | Manual download (protected Excel) | institutional_gatekeeping (supporting) |

V-Dem requires downloading "Country-Year: V-Dem Core" (CSV) from https://www.v-dem.net/data/the-v-dem-dataset/ and extracting the CSV to `raw_data/vdem/vdem_core_full.csv`.

### Step 2: Score countries

```bash
python score_countries.py                  # Score all, preserve hand-scored
python score_countries.py --overwrite      # Re-score everything
python score_countries.py --preview        # Dry run
python score_countries.py --country USA    # Single country
```

The scorer reads all available raw data, normalizes each indicator to 0–100 via min-max scaling, averages within domains, and writes `data/scores.json`. When multiple sources cover the same domain (e.g. World Bank WGI + V-Dem rule of law for institutional_gatekeeping), scores are merged by averaging.

### Normalization

- Higher raw values = more extraction for most indicators (Gini, corruption, secrecy)
- Inverted indicators (democracy, press freedom, rule of law): flipped so higher = more extraction
- All normalization is global min-max across the full dataset

### Confidence Model

Confidence reflects data reliability, assessed per domain via three factors:

1. **Completeness** — number of indicators with data (0–3 points)
2. **Source diversity** — number of independent datasets (0–3 points)
3. **Recency** — how recent the latest data point is (0–3 points)

Total 0–9 maps to: high (7+), moderate (5–6), low (3–4), very_low (0–2).

Overall country confidence is also capped by domain coverage: ≤3 domains caps at "low", ≤5 at "moderate". This ensures sparse-data countries (like North Korea with 3/7 domains) don't appear over-confident.

### Adding new data sources

1. Create a fetcher in `scripts/fetchers/` with a `fetch(raw_data_dir)` function
2. Register it in `FETCHER_REGISTRY` in `fetch_all.py`
3. Add indicator config to `score_countries.py` (domain mapping, inversion, source key)
4. Add name overrides in `COUNTRY_NAME_OVERRIDES` for any non-standard country codes
5. Exclude aggregate/regional codes in `EXCLUDE_CODES`

### Code-to-name mappings

Country names must be maintained in two places:
- `scripts/score_countries.py` → `COUNTRY_NAME_OVERRIDES` (used when generating scores.json)
- `js/app.js` → `COUNTRY_NAMES` (used for tooltip display of countries not in scores.json)
- `js/app.js` → `NUMERIC_MAP` (TopoJSON numeric ID → alpha-3 mapping)

Non-standard codes from data sources (RSF, V-Dem) should be remapped or excluded in `score_countries.py`.

## Scoring Rules

- All scores: 0–100 (0 = no extraction, 100 = extreme extraction)
- Every score MUST have: confidence level, trend, source keys, justification
- Confidence: high | moderate | low | very_low
- Trend: rising | falling | stable | unknown (roughly past decade)
- Source keys reference entries in `sources.md`
- Composite score = weighted average of available domains (default: equal weights)

### Critical rules:
- **Never invent scores.** If data is missing, set confidence to `very_low` and note it.
- **Extraction ≠ corruption.** A country can be low-corruption and high-extraction (e.g. USA).
- **Legal extraction counts.** Most structurally important extraction is legal.
- **Transnational axis matters.** Without it, Luxembourg looks like Denmark.
- **Acknowledge the legibility paradox.** The most extractive regimes produce the worst data.

## Style & Tone

The project treats extraction as a structural pattern, not a moral failing. The tone is analytical, not polemical. Justifications should read like concise research notes, not advocacy.
