# Developer Guide

Technical documentation for contributing to the Extraction Index. For the scoring methodology, data sources, and replication instructions, see [METHODOLOGY.md](METHODOLOGY.md).

## Project Structure

```
.
├── CLAUDE.md                  # Instructions for Claude Code
├── css/style.css              # Styles
├── data/
│   ├── schema.json            # JSON Schema for country data
│   └── scores.json            # Per-country extraction scores
├── index.html                 # Single-page application shell
├── js/app.js                  # D3 map, radar chart, all interactivity
├── LICENSE                    # MIT
├── README.md                  # User-facing overview
├── METHODOLOGY.md             # Scoring methodology and replication
├── DEVELOPER.md               # This file
├── sources.md                 # Data source registry
├── scripts/
│   ├── fetch_all.py           # Orchestrator for data fetching
│   ├── score_countries.py     # Auto-scorer: raw data → scores.json
│   ├── requirements.txt       # Python dependencies
│   └── fetchers/              # Per-source fetch scripts
│       ├── worldbank.py       # World Bank API (Gini, labor share, etc.)
│       ├── vdem.py            # V-Dem democracy indicators
│       ├── fsi.py             # Tax Justice Network FSI/CTHI
│       ├── rsf.py             # RSF Press Freedom Index
│       └── cpi.py             # Transparency International CPI
└── raw_data/                  # Fetched data (gitignored)
    └── manifest.json          # Tracks what was fetched and when
```

## Running Locally

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

No build step required. The map loads TopoJSON from a CDN.

## Data Pipeline

### 1. Fetch raw data

```bash
source .venv/bin/activate
cd scripts
python fetch_all.py                      # All sources
python fetch_all.py --source worldbank   # Single source
python fetch_all.py --list               # Show available sources
```

Raw data lands in `raw_data/` (gitignored — large files). The manifest tracks provenance.

Some sources require manual download (noted in fetcher output). V-Dem requires downloading "Country-Year: V-Dem Core" (CSV) from https://www.v-dem.net/data/the-v-dem-dataset/ and extracting to `raw_data/vdem/vdem_core_full.csv`.

### 2. Generate scores

```bash
python score_countries.py                  # Score all countries
python score_countries.py --preview        # Dry run — show changes without writing
python score_countries.py --country USA    # Score a single country
python score_countries.py --overwrite      # Re-score everything, including hand-scored
```

See `CLAUDE.md` for detailed scoring rules and constraints.

### 3. Serve the site

```bash
python3 -m http.server 8000
```

## Contributing Data

See `CLAUDE.md` for the scoring methodology and ground rules. The short version:

- **No overclaiming.** Low-confidence scores honestly labeled beat precise-looking numbers backed by nothing.
- **Show your work.** Every score needs a justification and source citations.
- **Extraction ≠ corruption.** Legal extraction is the structurally important kind.
- **Use ISO 3166-1 alpha-3** country codes.
