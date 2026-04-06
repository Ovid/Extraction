# The Extraction Index

An interactive world map visualizing **extraction** — the systematic capture of value by the powerful from the less powerful — across seven domains for every country.

**[Live Demo →](#)** *(link TBD after deployment)*

## What This Measures

Most governance indices measure corruption, freedom, or rule of law. The Extraction Index measures something different: the degree to which a country's institutions, economy, and power structures systematically transfer value from the many to the few — whether or not those transfers are legal.

Extraction is not the same as corruption. The United States has low corruption by most measures but high extraction through financialized healthcare, wage stagnation despite productivity gains, and regulatory complexity that serves concentrated interests. This distinction is the core contribution of the project.

## The Seven Domains

| # | Domain | What It Captures | Primary Sources |
|---|--------|-----------------|-----------------|
| 1 | **Political Capture** | Elite monopolization of political power, clientelism, electoral integrity | V-Dem, Freedom House |
| 2 | **Economic Concentration** | Wealth inequality, labor share of income, oligarchic control | World Inequality Database, World Bank |
| 3 | **Financial Extraction** | Financialization depth, financial secrecy, predatory finance | BIS, Tax Justice Network |
| 4 | **Institutional Gatekeeping** | Whether legal/regulatory structures serve broad populations or narrow interests | World Justice Project, World Bank |
| 5 | **Information & Media Capture** | Control over narrative, media freedom, information access | RSF, V-Dem |
| 6 | **Resource & Labor Extraction** | Natural resource governance, labor rights, wage theft | NRGI, ITUC, ILO |
| 7 | **Transnational Facilitation** | Enabling extraction *elsewhere* through tax havens, financial secrecy, profit shifting | Tax Justice Network, OECD, Global Financial Integrity |

Axis 7 exists because some countries score well on domestic governance while facilitating massive extraction elsewhere. Without it, Luxembourg looks like Denmark.

## Scoring

- Each domain is scored **0–100** (0 = no extraction detected, 100 = extreme extraction)
- The **composite score** is a weighted average of all seven domains
- Default weights are equal (1/7 each); users can adjust weights interactively
- All scores include a **confidence level** (high, moderate, low, very low) that controls the visual opacity of the country on the map
- All scores include a **trend** (rising, falling, stable, unknown) over roughly the past decade

### Confidence Visualization

The most extractive regimes often produce the least reliable data — what the project calls the **legibility paradox**. Rather than hiding this problem, the map encodes it visually:

- **Saturated colors** = high data confidence
- **Desaturated/transparent colors** = low data confidence

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
├── README.md                  # This file
├── sources.md                 # Data source registry
├── scripts/
│   ├── fetch_all.py           # Orchestrator for data fetching
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

## Data Pipeline

### 1. Fetch raw data

```bash
cd scripts
pip install -r requirements.txt
python fetch_all.py                      # All sources
python fetch_all.py --source worldbank   # Single source
python fetch_all.py --list               # Show available sources
```

Raw data lands in `raw_data/` (gitignored — large files). The manifest tracks provenance.

Some sources require manual download (noted in fetcher output). The fetchers will generate `DOWNLOAD_INSTRUCTIONS.md` files when automated access fails.

### 2. Generate scores (Claude Code)

With raw data in place, use Claude Code to:
1. Read raw indicator values for each country
2. Normalize to 0–100 using min-max scaling across the global dataset
3. Set confidence based on source availability
4. Estimate trends from ~10 years of data
5. Write justifications citing specific numbers
6. Update `data/scores.json`

See `CLAUDE.md` for detailed instructions.

### 3. Serve the site

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

No build step required. The map loads TopoJSON from a CDN.

## Contributing Data

See `CLAUDE.md` for the scoring methodology and ground rules. The short version:

- **No overclaiming.** Low-confidence scores honestly labeled beat precise-looking numbers backed by nothing.
- **Show your work.** Every score needs a justification and source citations.
- **Extraction ≠ corruption.** Legal extraction is the structurally important kind.
- **Use ISO 3166-1 alpha-3** country codes.

## Known Limitations

1. **Sample data only.** The current dataset covers 8 countries for illustration.
2. **Institutional gatekeeping is under-measured.** No existing index directly measures "who does the law serve."
3. **OECD data bias.** Sources have better coverage for wealthy nations.
4. **Static snapshot.** Trend indicators are directional estimates, not full time series.
5. **Weighting is normative.** Equal weights are a defensible default, not an empirical claim.

## Context

The Extraction Index argues that AI is arriving into a society whose institutions have already been systematically hollowed out by extraction. The index is an attempt to make that argument visible and interactive.

## License

MIT. See [LICENSE](LICENSE).
