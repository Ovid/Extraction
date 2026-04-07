# Map Data and Disputed Territories

The choropleth map uses [world-atlas@2 (countries-110m.json)](https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json), a TopoJSON build of Natural Earth's 1:110 million scale dataset. The project's code maps numeric geometry IDs to country scores — it does not draw borders. All boundary decisions are upstream in Natural Earth/world-atlas.

## How Country Matching Works

Each TopoJSON geometry has a numeric ID (ISO 3166-1 numeric). The JS code maps these to alpha-3 codes (e.g., 643 → RUS) to join with `data/scores.json`. Three geometries lack numeric IDs (Kosovo, Somaliland, N. Cyprus) and are matched by name instead via `NAME_TO_ALPHA3` in `js/app.js`.

## Disputed Territories

| Territory | Status in TopoJSON | Map behavior |
|-----------|-------------------|--------------|
| **Crimea** | Part of Russia's geometry (643) | Colored with Russia's score, not Ukraine's |
| **Kosovo** | Separate polygon, no numeric ID | Matched by name → XKX; has scores (composite: 35) |
| **N. Cyprus** | Separate polygon, no numeric ID | Matched by name → NCY; no scores, renders as no-data |
| **Somaliland** | Separate polygon, no numeric ID | Matched by name → SML; no scores, renders as no-data |
| **Taiwan (158)** | Own geometry with numeric ID | Scored independently |
| **Palestine (275)** | Own geometry with numeric ID | Scored independently |
| **Western Sahara (732)** | Own geometry with numeric ID | Scored independently |

Crimea is the only disputed area attributed to another country's score. The others either have their own ID or are matched by name.

## Known Limitations

- The 110m resolution is coarse. Small territories and complex coastlines are simplified.
- Boundary decisions reflect Natural Earth's editorial choices, not the project's political position.
