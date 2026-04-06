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

## Confidence Visualization

The most extractive regimes often produce the least reliable data — what the project calls the **legibility paradox**. Rather than hiding this problem, the map encodes it visually:

- **Saturated colors** = high data confidence
- **Desaturated/transparent colors** = low data confidence

A country can score 95 (extreme extraction) but appear faded because the data behind that score is sparse or indirect. This is by design.

## Data Sources

See [`data/sources.md`](data/sources.md) for a complete registry of every data source, including coverage, update frequency, and known limitations.

## Project Structure

```
extraction/
├── index.html           # Single-page application (D3 + TopoJSON)
├── data/
│   ├── schema.json      # JSON Schema for country data
│   ├── scores.json      # Per-country scores (the actual data)
│   └── sources.md       # Source documentation
├── LICENSE              # MIT
└── README.md            # This file
```

## Running Locally

No build step required. Serve the directory with any static file server:

```bash
# Python
python3 -m http.server 8000

# Node
npx serve .

# Then open http://localhost:8000
```

The map loads TopoJSON data from a CDN. The country scores are loaded from `data/scores.json`.

## Contributing Data

The project currently has sample data for 8 countries. To add a country:

1. Follow the schema in `data/schema.json`
2. Use ISO 3166-1 alpha-3 country codes
3. Document every score with:
   - Source keys referencing `data/sources.md`
   - A brief justification
   - An honest confidence level
   - A trend direction with reasoning
4. Submit a pull request with your additions to `data/scores.json`

### Ground Rules

- **No overclaiming.** If data is sparse, say so. A low-confidence score honestly labeled is more valuable than a precise-looking number backed by nothing.
- **Show your work.** Every score needs a justification and source citations.
- **Extraction ≠ corruption.** A country can have low corruption and high extraction. The score should reflect *systematic value capture*, not just bribery.
- **Legal extraction counts.** In fact, the most structurally important extraction is usually perfectly legal. That's what makes it hard to fight.

## Known Limitations

1. **Sample data only.** The current dataset covers 8 countries for illustration. Real global coverage will take time and collaboration.
2. **Institutional gatekeeping is under-measured.** No existing index directly measures "who does the law serve." This domain carries higher uncertainty.
3. **OECD data bias.** Sources have better coverage for wealthy nations, creating systematic confidence gaps for developing countries.
4. **Static snapshot.** The trend indicators are directional estimates, not time-series data. Proper longitudinal tracking is a future goal.
5. **Weighting is normative.** Equal weights are a defensible default, not an empirical claim.

## Context

This project is a companion to the book *Bread, Circuses, and GPUs*, which argues that AI is arriving into a society whose institutions have already been systematically hollowed out by extraction. The index is an attempt to make that argument visible and interactive.

## License

MIT. See [LICENSE](LICENSE).
