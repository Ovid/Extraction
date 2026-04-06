# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Extraction Index is a static single-page application that visualizes systematic value capture ("extraction") across seven domains for countries worldwide. It is a companion to the book "Bread, Circuses, and GPUs." There is no build system, no backend, and no framework — just vanilla HTML/CSS/JS with D3.js.

## Running Locally

```bash
python3 -m http.server 8000
# or: npx serve .
```

Open `http://localhost:8000`. No build step required.

## Architecture

Everything lives in `index.html` — markup, styles, and all JavaScript are in a single file. Data is loaded at init via `Promise.all` from three sources:

- `scores.json` — country-level extraction scores across seven domains, keyed by ISO 3166-1 alpha-3 codes
- `schema.json` — JSON Schema defining the data structure and validation rules
- World topology from CDN (world-atlas TopoJSON)

### Data Flow

`scores.json` → `computeComposite()` (weighted average of domain scores) → `countryFill()` (D3 color scale) + `countryOpacity()` (confidence-based) → SVG map render.

Users can adjust domain weights interactively; composite scores and map colors recalculate in real time.

### Seven Extraction Domains

Political Capture, Economic Concentration, Financial Extraction, Institutional Gatekeeping, Information & Media Capture, Resource & Labor Extraction, Transnational Facilitation. Each domain has a score (0–100), confidence level, trend indicator, sources array, and justification text.

### Visualization Components

- **Choropleth map** (D3 + TopoJSON): countries colored by composite score, opacity by confidence
- **Radar chart**: seven-axis domain comparison per country
- **Side panel**: domain breakdown cards with score bars, sources, and trends
- **Weight sliders**: interactive domain weight adjustment

### Key Mappings

The JS contains a hard-coded `isoNumericToAlpha3` mapping (ISO 3166-1 numeric → alpha-3) used to join TopoJSON geometry IDs to scores.json keys. Currently only 8 countries have actual scores; others render as greyed out.

## Data Schema

Scores follow `schema.json`. Key constraints:
- Country keys are 3-letter ISO 3166-1 alpha-3 codes
- Scores are integers 0–100
- Confidence levels: `high`, `moderate`, `low`, `very_low`
- Trends: `increasing`, `stable`, `decreasing`
- Default weights are equal (1/7 ≈ 0.143 per domain)

## Data Sources

`sources.md` documents 30+ data sources with coverage details, update cycles, and confidence guidelines. Consult this when adding or updating country scores.
