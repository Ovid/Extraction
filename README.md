# The Extraction Index

An interactive world map visualizing **extraction** — the systematic capture of value by the powerful from the less powerful — across seven domains for every country.

By [Curtis "Ovid" Poe](https://curtispoe.org/)

**[Live Demo →](#)** *(link TBD after deployment)*

## What This Measures

Most governance indices measure corruption, freedom, or rule of law. The Extraction Index measures something different: the degree to which a country's institutions, economy, and power structures systematically transfer value from the many to the few — whether or not those transfers are legal.

Extraction is not the same as corruption. The United States has low corruption by most measures but high extraction through financialized healthcare, wage stagnation despite productivity gains, and regulatory complexity that serves concentrated interests. This distinction is the core contribution of the project.

## The Seven Domains

| # | Domain | What It Captures |
|---|--------|-----------------|
| 1 | **Political Capture** | Elite monopolization of political power, clientelism, electoral integrity |
| 2 | **Economic Concentration** | Wealth inequality, labor share of income, oligarchic control |
| 3 | **Financial Extraction** | Financialization depth, financial secrecy, predatory finance |
| 4 | **Institutional Gatekeeping** | Whether legal/regulatory structures serve broad populations or narrow interests |
| 5 | **Information & Media Capture** | Control over narrative, media freedom, information access |
| 6 | **Resource Capture** | Natural resource governance, vulnerability to elite capture |
| 7 | **Transnational Facilitation** | Enabling extraction *elsewhere* through tax havens, financial secrecy, profit shifting |

Axis 7 exists because some countries score well on domestic governance while facilitating massive extraction elsewhere. Without it, Luxembourg looks like Denmark.

## Scoring

- Each domain is scored **0-100** (0 = no extraction detected, 100 = extreme extraction)
- The **composite score** is a weighted average of all seven domains
- Default weights are equal (1/7 each); users can adjust weights interactively
- All scores include a **confidence level** (high, moderate, low, very low) that controls the visual opacity of the country on the map
- All scores include a **trend** (rising, falling, stable, unknown) over roughly the past decade

The most extractive regimes often produce the least reliable data — what the project calls the **legibility paradox**. Rather than hiding this problem, the map encodes it visually: saturated colors indicate high confidence, transparent colors indicate low confidence.

## Context

The Extraction Index argues that AI is arriving into a society whose institutions have already been systematically hollowed out by extraction. The index is an attempt to make that argument visible and interactive.

## Known Limitations

1. **Institutional gatekeeping is under-measured.** No existing index directly measures "who does the law serve."
2. **OECD data bias.** Sources have better coverage for wealthy nations.
3. **The legibility paradox.** The most extractive regimes produce the worst data.
4. **Weighting is normative.** Equal weights are a defensible default, not an empirical claim.

## Further Reading

- [Methodology](METHODOLOGY.md) — scoring methodology, data sources, confidence model, and replication instructions
- [Developer Guide](DEVELOPER.md) — project structure, data pipeline, and contribution guidelines
- [Data Sources](sources.md) — complete source registry with URLs and coverage details

## License

MIT. See [LICENSE](LICENSE).
