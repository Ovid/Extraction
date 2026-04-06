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
index.html            → Shell, loads CSS/JS
css/style.css         → All styles, including light/dark theme via CSS custom properties
js/app.js             → D3 map, radar chart, weight controls, panel logic, theme toggle
data/scores.json      → THE DATA FILE — per-country extraction scores
data/schema.json      → JSON Schema defining the data structure
sources.md            → Registry of every data source with keys, URLs, coverage
scripts/              → Python scripts that fetch raw data from public APIs
raw_data/             → Fetched data (gitignored, reproduced via scripts)
raw_data/manifest.json → Tracks what was fetched, when, from where
```

Data is loaded at init via `Promise.all` from `data/scores.json` and a CDN-hosted world-atlas TopoJSON.

### Theming

Light/dark mode is driven by CSS custom properties on `:root` (dark default) and `:root[data-theme="light"]`. All colors — including overlays, radar chart fills, no-data country fills, and shadows — use variables so both themes stay consistent. The JS toggle respects `prefers-color-scheme`, persists to `localStorage`, and calls `refreshMapColors()` to repaint the map.

### Data Flow

`data/scores.json` → `computeComposite()` (weighted average of domain scores) → `countryFill()` (D3 color scale) + `countryOpacity()` (confidence-based) → SVG map render.

Users can adjust domain weights interactively; composite scores and map colors recalculate in real time.

### Visualization Components

- **Choropleth map** (D3 + TopoJSON): countries colored by composite score, opacity by confidence
- **Radar chart**: seven-axis domain comparison per country
- **Side panel**: domain breakdown cards with score bars, sources, and trends
- **Weight sliders**: interactive domain weight adjustment

### Key Mappings

The JS contains a hard-coded `numericToAlpha3` mapping (ISO 3166-1 numeric → alpha-3) used to join TopoJSON geometry IDs to `data/scores.json` keys. A separate `COUNTRY_NAMES` object provides human-readable names for all mapped countries. Currently only 8 countries have actual scores; others render as greyed out.

## The Seven Domains

1. **political_capture** — elite monopolization of political power
2. **economic_concentration** — wealth inequality, labor share decline
3. **financial_extraction** — financialization, financial secrecy
4. **institutional_gatekeeping** — whether institutions serve broad population or narrow interests
5. **information_capture** — media freedom, information control
6. **resource_labor_extraction** — natural resource governance, labor rights
7. **transnational_facilitation** — enabling extraction elsewhere (tax havens, profit shifting)

## Scoring Rules

- All scores: 0–100 (0 = no extraction, 100 = extreme extraction)
- Every score MUST have: confidence level, trend, source keys, justification
- Confidence: high | moderate | low | very_low
- Trend: rising | falling | stable | unknown (roughly past decade)
- Source keys reference entries in `sources.md`
- Composite score = weighted average of 7 domains (default: equal weights)

## Working with data/scores.json

Country entries are keyed by ISO 3166-1 alpha-3 codes. Scores follow `data/schema.json`.

When adding or updating a country:
1. Pull indicator values from `raw_data/` files
2. Normalize to 0–100 using min-max scaling across the global dataset
3. Set confidence based on source availability (see sources.md)
4. Estimate trend from the most recent ~10 years of data where available
5. Write a brief justification grounding the score in specific indicators
6. List source keys used

### Critical rules:
- **Never invent scores.** If data is missing, set confidence to `very_low` and note it.
- **Extraction ≠ corruption.** A country can be low-corruption and high-extraction (e.g. USA).
- **Legal extraction counts.** Most structurally important extraction is legal.
- **Transnational axis matters.** Without it, Luxembourg looks like Denmark.
- **Acknowledge the legibility paradox.** The most extractive regimes produce the worst data.

## Data Pipeline

### Fetching raw data

```bash
cd scripts
pip install -r requirements.txt
python fetch_all.py              # Fetches all API-accessible sources
python fetch_all.py --source worldbank   # Fetch a single source
python fetch_all.py --list       # Show available sources
```

Raw data lands in `raw_data/` as CSV/JSON files, one per source per indicator. The manifest tracks provenance.

### From raw data to scores

1. Read the relevant raw_data files for a country
2. Extract the specific indicator values
3. Normalize: for each indicator, apply min-max scaling across all countries in the dataset
4. Average indicators within each domain (equal weight within domain)
5. Set confidence based on how many sources had data for this country/domain
6. Estimate trend by comparing most recent value to value ~10 years ago
7. Write justification citing the specific numbers
8. Update data/scores.json

### Normalization approach

For most indicators, higher raw values = more extraction:
- Gini coefficient: higher = more extraction
- Top 1% wealth share: higher = more extraction
- Financial secrecy score: higher = more extraction

For inverted indicators (where higher = less extraction):
- V-Dem democracy scores: INVERT (subtract from max)
- Press freedom: INVERT
- Rule of law: INVERT
- Labor rights score: depends on scale (ITUC: higher = worse rights = more extraction)

The `sources.md` file specifies the direction for each indicator.

## Style & Tone

The project treats extraction as a structural pattern, not a moral failing. The tone is analytical, not polemical. Justifications should read like concise research notes, not advocacy.
