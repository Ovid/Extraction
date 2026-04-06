# Human-Readable Domain Justifications

## Goal

Replace technical auto-scored justifications with plain-English explanations that a general audience can understand, while preserving raw data access for researchers.

## Current State

Justifications look like:
> Auto-scored from V-Dem. Political Corruption: 0.060 (normalized: 6); Clientelism: 0.105 (normalized: 8); Electoral Democracy: 0.735 (normalized: 20); Physical Violence: 0.789 (normalized: 21).

## Target State

Justifications become:
> How corrupt is the political system? Very low. How common is vote-buying and patronage? Very low. How democratic are elections? Low. How common is political violence? Low.

With a "Show raw data" toggle revealing the original technical string.

## Design

### Indicator display names

Each indicator gets a conversational question-style name:

| Indicator key | Display question |
|---|---|
| `vdem_political_corruption` | How corrupt is the political system? |
| `vdem_clientelism` | How common is vote-buying and patronage? |
| `vdem_electoral_democracy` | How democratic are elections? |
| `vdem_physical_violence` | How common is political violence? |
| `wb_gini` | How unequal is income distribution? |
| `wb_labor_share` | How much of the economy goes to workers? |
| `rsf_press_freedom` | How free is the press? |
| `tjn_fsi_secrecy` | How much financial secrecy exists? |

(Full list to be completed from all indicators in score_countries.py)

### Score-to-label mapping

| Normalized score (0-100) | Label |
|---|---|
| 0-15 | very low |
| 16-35 | low |
| 36-55 | moderate |
| 56-75 | high |
| 76-100 | very high |

### Data changes (scores.json)

Each domain gains a new optional field `justification_detail` containing the current technical string. The existing `justification` field changes to human-readable sentences. Sources list is preserved in the data but removed from the default UI display.

### UI changes (domain cards)

- Justification text becomes the human-readable sentences
- Sources line hidden from default view
- "Show raw data" toggle expands to reveal technical justification and source keys
- No changes to score bar, trend badge, or confidence badge

## Implementation

### Step 1: Update score_countries.py

- Add INDICATOR_QUESTIONS map (indicator key -> question string)
- Add score_to_label() function (0-100 -> very low/low/moderate/high/very high)
- Modify justification generation to produce human-readable `justification` and technical `justification_detail`

### Step 2: Re-run scorer

- `python score_countries.py` to regenerate data/scores.json

### Step 3: Update js/app.js

- Update domain card template to render new justification format
- Add "Show raw data" toggle that reveals justification_detail and sources

### Step 4: Add CSS for toggle

- Style the toggle link and collapsed/expanded states in css/style.css
