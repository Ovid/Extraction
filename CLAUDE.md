# CLAUDE.md

## Project Overview

Static single-page app visualizing systematic value capture ("extraction") across seven domains for countries worldwide. No build system, no backend, no framework — vanilla HTML/CSS/JS with D3.js.

Key insight: extraction is **cross-domain convertible** — block it in one domain and it migrates to another. This is why the index has seven axes.

## Running Locally

```bash
python3 -m http.server 8000   # or: npx serve .
```

## Architecture

```
index.html              → Shell, CSS/JS loading, methodology modal, country picker
css/style.css            → All styles, light/dark theme via CSS custom properties
js/app.js                → D3 map, radar chart, weight controls, panel logic, theme toggle
data/scores.json         → Per-country extraction scores (222 countries)
data/schema.json         → JSON Schema for the data structure
sources.md               → Data source registry with keys, URLs, coverage
scripts/fetch_all.py     → Data fetch orchestrator (--source, --list)
scripts/score_countries.py → Raw data → normalized scores → scores.json
scripts/requirements.txt → Python deps (requests, pandas, openpyxl)
scripts/fetchers/        → Per-source fetch scripts (worldbank, vdem, rsf, fsi, cpi)
raw_data/                → Fetched data (gitignored), manifest.json tracks provenance
.venv/                   → Python venv (gitignored)
```

**Data flow:** `scores.json` → `computeComposite()` (weighted average) → `countryFill()` (D3 color scale) → SVG map. Users adjust domain weights interactively; composite scores and map colors recalculate in real time.

**Theming:** CSS custom properties on `:root` (dark default) and `:root[data-theme="light"]`. JS toggle respects `prefers-color-scheme`, persists to `localStorage`, calls `refreshMapColors()`.

**Visualizations:** Choropleth map (D3+TopoJSON), radar chart (7-axis per country), side panel (domain cards with scores/sources/confidence/trends), weight sliders, country picker (A-Z/Score sort), methodology modal.

**Key mappings in JS:** `numericToAlpha3` (ISO numeric → alpha-3, joins TopoJSON to scores.json) and `COUNTRY_NAMES` (human-readable names). Both must be updated when adding territories.

## The Seven Domains

1. **political_capture** — elite monopolization of political power
2. **economic_concentration** — wealth inequality, labor share decline
3. **financial_extraction** — financialization, financial secrecy
4. **institutional_gatekeeping** — institutions serving narrow vs. broad interests
5. **information_capture** — media freedom, information control
6. **resource_capture** — vulnerability of resource wealth to elite capture
7. **transnational_facilitation** — enabling extraction elsewhere (tax havens, profit shifting)

## Data Pipeline

### Step 1: Fetch raw data

```bash
source .venv/bin/activate && cd scripts
python fetch_all.py                      # All sources
python fetch_all.py --source worldbank   # Single source
python fetch_all.py --list               # Show available
```

| Source | Type | Domains |
|--------|------|---------|
| World Bank | API (auto) | economic_concentration, financial_extraction, institutional_gatekeeping, resource_capture |
| ILO | API (auto) | economic_concentration |
| V-Dem | Manual CSV download | political_capture, information_capture, institutional_gatekeeping |
| RSF | Page scrape (auto) | information_capture |
| TJN FSI | API w/ public token | transnational_facilitation |
| CPI | Manual Excel download | institutional_gatekeeping (supporting) |

V-Dem: download "Country-Year: V-Dem Core" CSV from v-dem.net → `raw_data/vdem/vdem_core_full.csv`.

### Step 2: Score countries

```bash
python score_countries.py                  # Score all, preserve hand-scored
python score_countries.py --overwrite      # Re-score everything
python score_countries.py --preview        # Dry run
python score_countries.py --country USA    # Single country
```

**Normalization:** Min-max scaling to 0–100. Higher = more extraction. Inverted indicators (democracy, press freedom, rule of law) are flipped.

**Confidence model:** Per-domain score from completeness (0–3) + source diversity (0–3) + recency (0–3) = 0–9. Maps to: high (7+), moderate (5–6), low (3–4), very_low (0–2). Country-level confidence capped by domain coverage: ≤3 domains → "low", ≤5 → "moderate".

### Adding new data sources

1. Create fetcher in `scripts/fetchers/` with `fetch(raw_data_dir)` function
2. Register in `FETCHER_REGISTRY` in `fetch_all.py`
3. Add indicator config to `score_countries.py` (domain mapping, inversion, source key)
4. Add name overrides in `COUNTRY_NAME_OVERRIDES`; exclude aggregates in `EXCLUDE_CODES`

### Code-to-name mappings (maintain in two places)

- `scripts/score_countries.py` → `COUNTRY_NAME_OVERRIDES` (scores.json generation)
- `js/app.js` → `COUNTRY_NAMES` (tooltip display) + `NUMERIC_MAP` (TopoJSON ID → alpha-3)

## Scoring Rules

**Changes to scoring methodology must be reflected in `METHODOLOGY.md`.**

- Scores: 0–100 (0 = no extraction, 100 = extreme)
- Every score requires: confidence level, trend, source keys, justification
- Confidence: high | moderate | low | very_low
- Trend: rising | falling | stable | unknown (roughly past decade)
- Source keys reference `sources.md`
- Composite = weighted average of available domains (default: equal weights)

### Critical rules

- **Never invent scores.** Missing data → confidence `very_low`, note it.
- **Extraction ≠ corruption.** Low-corruption + high-extraction is possible (e.g. USA).
- **Legal extraction counts.** Most structurally important extraction is legal.
- **Transnational axis matters.** Without it, Luxembourg looks like Denmark.
- **Legibility paradox.** The most extractive regimes produce the worst data.

## Definition of Done

**No task is finished until `make all` passes with zero errors.** This is non-negotiable. Before declaring any work complete — whether a bug fix, feature, refactor, or data change — run `make all` and confirm it exits cleanly. If it fails, fix the failures before moving on. Do not commit, create PRs, or claim completion with a failing `make all`.

## Style & Tone

Extraction is a structural pattern, not a moral failing. Tone is analytical, not polemical. Justifications should read like concise research notes, not advocacy.

## Commit messages

Commit messages must ALWAYS be bare strings. NO EXCEPTIONS.

Bad:

   git commit -m "$(cat <<'EOF'
      refactor: register ILO fetcher, remove GDP per worker from World Bank
    EOF
    )"

Good:

    git commit -m "refactor: register ILO fetcher, remove GDP per worker from World Bank"
