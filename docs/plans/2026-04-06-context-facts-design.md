# Context Facts: Concrete Examples for Domain Indicators

**Date:** 2026-04-06
**Status:** Approved

## Problem

Domain scores are abstract numbers. A score of 52 for Economic Concentration doesn't tell users much without context. Real-world facts — raw values and peer comparisons — make scores meaningful.

## Design

### Data format

Add a `context_facts` array to each domain entry in `scores.json`:

```json
{
  "score": 52,
  "confidence": "moderate",
  "trend": "stable",
  "sources": ["wb_gini", "wb_labor_share"],
  "justification": "...",
  "justification_detail": "...",
  "context_facts": [
    {
      "indicator": "wb_gini",
      "facts": [
        "Gini coefficient: 41.8",
        "Highest among high-income countries (avg: 32.1)"
      ]
    },
    {
      "indicator": "wb_labor_share",
      "facts": [
        "Labor share of GDP: 52.3%",
        "Below regional average for North America (55.1%)"
      ]
    }
  ]
}
```

Each indicator gets 1-2 short factual strings. The scorer decides what's worth including; the frontend just renders them.

### Scorer changes (`score_countries.py`)

A new `generate_context_facts()` function runs after scoring each indicator:

**Fact #1 — Raw value (always present):**
Format the actual indicator value with units. E.g., "Gini coefficient: 41.8", "Press freedom score: 72.3 out of 100".

**Fact #2 — Peer comparison (when meaningful):**
- Look up the country's income group (from World Bank data already fetched) and region (from a new mapping dict)
- Calculate the peer group average for that indicator
- Pick whichever comparison (income or regional) produces the bigger delta from the peer average
- Skip when the country is within 10% of the peer mean
- Format as "Highest/Lowest among [group]" at extremes, or "[X]% above/below [group] average" otherwise

**Edge cases:**
- Fewer than 3 peers in a group: skip that comparison, try the other
- Binary/near-zero indicators (e.g., resource rents at 0%): raw value only, no comparison
- Inverted indicators: phrased so "higher extraction" is always the concerning direction

**New data required:**
- Region mapping: ~200-line dict mapping ISO alpha-3 to UN geoscheme regions
- Income groups: already available from World Bank API data

### Frontend changes (`js/app.js`)

After each indicator question line, render matching context facts as subdued lines:

```
How unequal is income distribution? Moderate
  Gini coefficient: 41.8
  Highest among high-income countries (avg: 32.1)
How little do workers get paid relative to what they produce? High
  Labor share of GDP: 52.3%
  Below regional average for North America (55.1%)
```

Style: smaller font, muted color via existing CSS custom properties. One new CSS class (`.context-fact`). Works in both light and dark themes.

### What's not included

- No new data fetching — uses only raw data already available
- No frontend interactivity — facts are static text, not clickable/filterable
- No user-selectable comparison groups — scorer picks the best one
- No facts for hand-scored countries — they lack raw indicator data
- No incremental updates — facts regenerate on every scorer run
