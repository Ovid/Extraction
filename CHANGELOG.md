# Changelog

Curated log of significant changes to the Extraction Index — methodology
updates, new data sources, and user-visible improvements.

## Data Quality & Security Hardening (2026-04-11)

- Added type-to-filter search in the country picker dropdown
- Added Subresource Integrity hashes to all CDN script tags
- Added keyboard-accessible focus styles to the country picker search
- V-Dem data year is now derived from actual data instead of being hardcoded
- FSI data year is now derived from scoring timestamps instead of being hardcoded
- Territories with no scoring data no longer trigger broken zoom/highlight behavior
- Added epistemic caveat to the "About the Data" section

## Transnational Facilitation Redesign (2026-04-10)

- Transnational facilitation domain now scores on financial secrecy
  rather than raw FSI value, better capturing the structural mechanisms
  that enable cross-border extraction
- Updated methodology documentation to reflect secrecy score approach
  and political capture limitations

## Financial & Economic Data (2026-04-08 -- 2026-04-10)

- Added ILO labour income share as the primary labour extraction
  indicator, replacing GDP per worker which conflated productivity
  with extraction
- Added bank net interest margin to the financial extraction domain
- Scoring methodology improvements based on external economist review
- Fixed confidence calculation to use actual source counts
- Map legend now always shows the full 0--100 scale

## Scoring Accuracy Overhaul (2026-04-07)

- Integrated V-Dem egalitarian and participatory democracy indicators
  into institutional gatekeeping
- Replaced resource capture formula: democratic accountability now used
  instead of institutional strength, better capturing elite resource control
- Log-transformed resource rents normalization to reduce distortion from
  extreme values (e.g., oil states)
- Fixed RSF press freedom score inversion that had reversed country rankings
- Fixed Saudi Arabia scoring that under-represented extraction
- Added comprehensive test suite (pytest for Python pipeline, Vitest for
  JS logic)
- Added linting and formatting enforcement (ruff, ESLint, Prettier)
- Added Makefile with standard targets for tests, coverage, and data pipeline

## Visualization & UX Polish (2026-04-06)

- Replaced red-green color scale with colorblind-safe Crameri lajolla palette
- Added quantile-based color scaling so colors spread across actual data
  distribution
- Added methodology modal with source reliability notes, author links,
  and data source links
- Added custom dropdown country picker with rank display and A-Z/score
  sorting
- Country scores now include contextual comparisons against regional
  and income-group peers
- Added structured indicators with context facts in domain cards,
  replacing plain justification text
- Added drag-resizable panel divider between map and sidebar
- Added map zoom/pan with center-on-selected-country
- Selected countries now highlighted with bold outline and glow effect
- Added trend badges showing whether domain scores are rising, falling,
  or stable over the past decade
- Made the layout responsive for smaller screens

## Initial Build (2026-04-06)

- Launched interactive choropleth map of extraction scores for 222
  countries across seven domains
- Built automated data pipeline fetching from World Bank, V-Dem, RSF,
  and TJN Financial Secrecy Index
- Added radar chart showing seven-axis extraction profile per country
- Added side panel with domain cards showing scores, confidence levels,
  trends, and source citations
- Added interactive weight sliders allowing users to adjust domain
  importance and see composite scores recalculate in real time
- Added light/dark theme toggle respecting system preference
- Published METHODOLOGY.md documenting scoring approach, data sources,
  and replication steps
