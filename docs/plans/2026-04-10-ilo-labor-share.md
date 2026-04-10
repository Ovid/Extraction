# Replace GDP per Worker with ILO Labour Share

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the incorrect GDP-per-worker indicator with ILO labour income share (% of GDP) in the economic_concentration domain.

**Architecture:** New ILO SDMX fetcher → CSV in raw_data/ilo/ → scorer picks it up via INDICATOR_CONFIG with `data_dir` support. Remove GDP-per-worker from World Bank fetcher and all references. Update all documentation.

**Tech Stack:** Python requests, SDMX CSV API (ILO), existing pandas scorer pipeline.

**Pushback resolutions:**
- File path resolution: Add `data_dir` key to INDICATOR_CONFIG; update both `build_country_scores()` (line 1539) and `estimate_trend()` (line 1376) to use `RAW_DATA_DIR / config["data_dir"]` instead of hardcoded `WB_DIR`.
- Country codes: Verify ILO alpha-3 codes against existing scores.json during Task 6 spot-check. Fix mismatches in `COUNTRY_CODE_OVERRIDES`.
- SDMX format: Verified against live API. Actual columns are: `DATAFLOW,REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE,OBS_STATUS,UNIT_MEASURE_TYPE,UNIT_MEASURE,UNIT_MULT,SOURCE,NOTE_SOURCE,NOTE_INDICATOR,NOTE_CLASSIF,DECIMALS,UPPER_BOUND,LOWER_BOUND` (17 columns, not 7). Test fixtures updated to match.
- Tasks 4+5 merged: Scorer config swap and data_dir support are one task since they can't be tested independently.

---

### Task 1: Write ILO fetcher with test

**Files:**
- Create: `scripts/fetchers/ilo.py`
- Create: `tests/python/unit/test_ilo_fetcher.py`

**Step 1: Write the failing test**

Test fixtures use the actual ILO SDMX CSV format (17 columns):

```python
"""Tests for ILO SDMX fetcher."""

import csv
from pathlib import Path
from unittest.mock import patch

from fetchers.ilo import fetch, parse_sdmx_csv, ILO_API_URL

# Realistic fixture matching actual ILO SDMX CSV response format
SAMPLE_CSV = (
    "DATAFLOW,REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE,OBS_STATUS,"
    "UNIT_MEASURE_TYPE,UNIT_MEASURE,UNIT_MULT,SOURCE,NOTE_SOURCE,"
    "NOTE_INDICATOR,NOTE_CLASSIF,DECIMALS,UPPER_BOUND,LOWER_BOUND\n"
    "ILO:DF_LAP_2GDP_NOC_RT(1.0),USA,A,LAP_2GDP_RT,2023,55.385,I,RT,PT,0,"
    "ILO - Modelled Estimates,,,,1,,\n"
    "ILO:DF_LAP_2GDP_NOC_RT(1.0),CAN,A,LAP_2GDP_RT,2023,58.495,I,RT,PT,0,"
    "ILO - Modelled Estimates,,,,1,,\n"
    "ILO:DF_LAP_2GDP_NOC_RT(1.0),USA,A,LAP_2GDP_RT,2022,56.163,I,RT,PT,0,"
    "ILO - Modelled Estimates,,,,1,,\n"
)

SAMPLE_CSV_WITH_EMPTY = (
    "DATAFLOW,REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE,OBS_STATUS,"
    "UNIT_MEASURE_TYPE,UNIT_MEASURE,UNIT_MULT,SOURCE,NOTE_SOURCE,"
    "NOTE_INDICATOR,NOTE_CLASSIF,DECIMALS,UPPER_BOUND,LOWER_BOUND\n"
    "ILO:DF_LAP_2GDP_NOC_RT(1.0),USA,A,LAP_2GDP_RT,2023,55.385,I,RT,PT,0,"
    "ILO - Modelled Estimates,,,,1,,\n"
    "ILO:DF_LAP_2GDP_NOC_RT(1.0),CAN,A,LAP_2GDP_RT,2023,,I,RT,PT,0,"
    "ILO - Modelled Estimates,,,,1,,\n"
)


class TestParseSDMXCSV:
    def test_parses_valid_csv(self):
        records = parse_sdmx_csv(SAMPLE_CSV)
        assert len(records) == 3
        assert records[0]["country_code"] == "USA"
        assert records[0]["year"] == 2023
        assert records[0]["value"] == 55.385

    def test_skips_rows_with_missing_values(self):
        records = parse_sdmx_csv(SAMPLE_CSV_WITH_EMPTY)
        assert len(records) == 1
        assert records[0]["country_code"] == "USA"


class TestFetch:
    def test_writes_csv_to_output_dir(self, tmp_path):
        with patch("fetchers.ilo.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SAMPLE_CSV
            mock_get.return_value.raise_for_status = lambda: None
            files = fetch(tmp_path)

        output_file = tmp_path / "ilo" / "ilo_labor_share.csv"
        assert output_file.exists()
        assert "ilo/ilo_labor_share.csv" in files
        # Verify CSV structure matches World Bank convention
        with open(output_file) as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert set(row.keys()) == {"country_code", "country_name", "year", "value", "indicator"}
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_ilo_fetcher.py -v`
Expected: FAIL with ImportError (module doesn't exist yet)

**Step 3: Write minimal implementation**

Create `scripts/fetchers/ilo.py`:

```python
"""
ILO (International Labour Organization) data fetcher.

Uses the ILO SDMX REST API to fetch labour income share of GDP.
Docs: https://ilostat.ilo.org/data/sdmx-api/

Covers domains:
  - economic_concentration: labour income share of GDP
"""

import csv
import io
import json
from pathlib import Path

import pandas as pd
import requests

ILO_API_URL = (
    "https://sdmx.ilo.org/rest/data/ILO,DF_LAP_2GDP_NOC_RT/..A."
    "?startPeriod=2010&endPeriod=2025"
)

# ILO uses ISO alpha-3 codes; add overrides for any mismatches
COUNTRY_CODE_OVERRIDES = {}


def parse_sdmx_csv(csv_text):
    """Parse ILO SDMX CSV response into records.

    The ILO SDMX CSV has 17 columns. We extract REF_AREA, TIME_PERIOD,
    and OBS_VALUE, skipping rows with missing values.
    """
    records = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        obs_value = row.get("OBS_VALUE", "").strip()
        if not obs_value:
            continue
        code = row["REF_AREA"]
        code = COUNTRY_CODE_OVERRIDES.get(code, code)
        records.append(
            {
                "country_code": code,
                "year": int(row["TIME_PERIOD"]),
                "value": float(obs_value),
            }
        )
    return records


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch ILO labour income share data. Returns list of output filenames."""
    output_dir = raw_data_dir / "ilo"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("    Fetching LAP_2GDP_NOC_RT (Labour income share of GDP)...")
    resp = requests.get(
        ILO_API_URL,
        headers={"Accept": "application/vnd.sdmx.data+csv"},
        timeout=60,
    )
    resp.raise_for_status()

    records = parse_sdmx_csv(resp.text)
    print(f"      → {len(records)} records")

    df = pd.DataFrame(records)
    if not df.empty:
        # Add columns to match World Bank CSV convention
        df["country_name"] = ""  # Scorer resolves names separately
        df["indicator"] = "LAP_2GDP_NOC_RT"
        df = df.sort_values(["country_code", "year"]).reset_index(drop=True)
        df = df[["country_code", "country_name", "year", "value", "indicator"]]

    output_path = output_dir / "ilo_labor_share.csv"
    df.to_csv(output_path, index=False)

    # Write metadata
    meta = {
        "source": "International Labour Organization (ILO) — ILOSTAT",
        "api": ILO_API_URL,
        "indicator": "LAP_2GDP_NOC_RT",
        "description": "Labour income share as a percent of GDP (ILO modelled estimates, SDG 10.4.1)",
        "note": "Inverted for scoring: higher labour share = less extraction",
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    files = [
        str(output_path.relative_to(raw_data_dir)),
        str(meta_path.relative_to(raw_data_dir)),
    ]
    return files
```

**Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_ilo_fetcher.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add scripts/fetchers/ilo.py tests/python/unit/test_ilo_fetcher.py
git commit -m "feat: add ILO SDMX fetcher for labour income share"
```

---

### Task 2: Register ILO fetcher and remove GDP per worker from World Bank

**Files:**
- Modify: `scripts/fetch_all.py:28-54` (FETCHER_REGISTRY)
- Modify: `scripts/fetchers/worldbank.py:25-45` (INDICATORS list)
- Modify: `scripts/fetchers/worldbank.py:1-12` (docstring)

**Step 1: Add ILO to FETCHER_REGISTRY in fetch_all.py**

Add after the "cpi" entry:

```python
    "ilo": {
        "module": "ilo",
        "description": "ILO labour income share of GDP (SDG 10.4.1)",
        "type": "api",
    },
```

**Step 2: Update worldbank description in fetch_all.py**

Change:
```
"description": "World Bank Development Indicators (Gini, labor share, domestic credit, natural resource rents, corruption control)",
```
to:
```
"description": "World Bank Development Indicators (Gini, domestic credit, net interest margin, natural resource rents, corruption control)",
```

**Step 3: Remove the GDP per worker tuple from worldbank.py INDICATORS**

Remove this entry:
```python
    (
        "SL.GDP.PCAP.EM.KD",
        "wb_gdp_per_worker.csv",
        "GDP per person employed (constant 2017 $)",
        "economic_concentration",
        False,
    ),
```

**Step 4: Update the worldbank.py module docstring**

Change `economic_concentration: Gini, labor share` to `economic_concentration: Gini`.

**Step 5: Commit**

```bash
git add scripts/fetch_all.py scripts/fetchers/worldbank.py
git commit -m "refactor: register ILO fetcher, remove GDP per worker from World Bank"
```

---

### Task 3: Swap indicator in scorer and add data_dir support

This task merges indicator config swap and data_dir support since they can't be tested independently — the scorer will crash looking for `ilo_labor_share.csv` in `raw_data/worldbank/` without the path fix.

**Files:**
- Modify: `scripts/score_countries.py:40-84` (INDICATOR_CONFIG)
- Modify: `scripts/score_countries.py:86-109` (INDICATOR_QUESTIONS)
- Modify: `scripts/score_countries.py:126-137` (POSITIVE_QUESTION_INDICATORS)
- Modify: `scripts/score_countries.py:149-170` (INDICATOR_DISPLAY)
- Modify: `scripts/score_countries.py:1539` (build_country_scores — file path resolution)
- Modify: `scripts/score_countries.py:1376` (estimate_trend — file path resolution)
- Modify: `scripts/score_countries.py:1497` (build_wb_domain — trend call passes data_dir)
- Modify: `js/app.js:5` (SOURCE_URLS)

**Step 1: Write a failing test for data_dir resolution**

Create or add to an existing test file:

```python
"""Test that indicator file path resolution supports data_dir."""

from score_countries import INDICATOR_CONFIG, RAW_DATA_DIR, WB_DIR


def test_indicator_config_with_data_dir_resolves_correctly():
    """Indicators with data_dir should resolve to RAW_DATA_DIR/data_dir/file."""
    for cfg in INDICATOR_CONFIG:
        if "data_dir" in cfg:
            expected_dir = RAW_DATA_DIR / cfg["data_dir"]
            assert expected_dir != WB_DIR, (
                f"data_dir '{cfg['data_dir']}' should not resolve to WB_DIR"
            )


def test_all_indicators_have_valid_source_keys():
    """Every INDICATOR_CONFIG entry must have a source_key."""
    for cfg in INDICATOR_CONFIG:
        assert "source_key" in cfg, f"Missing source_key in {cfg['file']}"
        assert cfg["source_key"], f"Empty source_key in {cfg['file']}"
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_indicator_config.py -v`
Expected: FAIL (no data_dir entries exist yet)

**Step 3: Replace GDP per worker config with ILO labour share in INDICATOR_CONFIG**

Replace:
```python
    {
        "file": "wb_gdp_per_worker.csv",
        "domain": "economic_concentration",
        "inverted": False,
        "source_key": "wb_labor_share",
        "name": "GDP per worker",
    },
```
with:
```python
    {
        "file": "ilo_labor_share.csv",
        "domain": "economic_concentration",
        "inverted": True,
        "source_key": "ilo_labor_share",
        "name": "Labour income share of GDP",
        "data_dir": "ilo",
    },
```

**Step 4: Update file path resolution in build_country_scores() (line ~1539)**

Change:
```python
    for cfg in INDICATOR_CONFIG:
        filepath = WB_DIR / cfg["file"]
```
to:
```python
    for cfg in INDICATOR_CONFIG:
        data_dir = RAW_DATA_DIR / cfg["data_dir"] if "data_dir" in cfg else WB_DIR
        filepath = data_dir / cfg["file"]
```

**Step 5: Update file path resolution in estimate_trend() (line ~1376)**

Change the function signature to accept an optional `data_dir` parameter:
```python
def estimate_trend(df_full, country_code, indicator_file, inverted=False, data_dir=None):
    filepath = (data_dir or WB_DIR) / indicator_file
```

**Step 6: Update estimate_trend call site in build_wb_domain() (line ~1497)**

Pass the resolved data_dir through. In the loop that calls estimate_trend:
```python
    for _, row in group.iterrows():
        cfg = next((c for c in INDICATOR_CONFIG if c["file"] == row["indicator_file"]), None)
        inv = cfg["inverted"] if cfg else False
        trend_data_dir = RAW_DATA_DIR / cfg["data_dir"] if cfg and "data_dir" in cfg else None
        t = estimate_trend(None, code, row["indicator_file"], inverted=inv, data_dir=trend_data_dir)
```

**Step 7: Update INDICATOR_QUESTIONS**

Remove:
```python
    "wb_labor_share": "How little do workers get paid relative to what they produce?",
```
Add:
```python
    "ilo_labor_share": "What share of GDP goes to workers as income?",
```

**Step 8: Add to POSITIVE_QUESTION_INDICATORS**

Add `"ilo_labor_share"` to the set (higher share going to workers is good):
```python
    "ilo_labor_share",  # "What share of GDP goes to workers?" — higher = good
```

**Step 9: Update INDICATOR_DISPLAY**

Remove the `wb_labor_share` entry. Add:
```python
    "ilo_labor_share": {
        "label": "Labour income share of GDP",
        "format": "{:.1f}",
        "unit": "%",
        "comparison_label": ["Highest labour share among", "Lowest labour share among"],
    },
```

**Step 10: Update SOURCE_URLS in js/app.js**

Remove:
```javascript
  wb_labor_share: 'https://data.worldbank.org/indicator/SL.GDP.PCAP.EM.KD',
```
Add:
```javascript
  ilo_labor_share: 'https://ilostat.ilo.org/data/',
```

**Step 11: Run tests**

Run: `make all`
Expected: All tests pass (note: scores won't regenerate correctly until ILO data is fetched in Task 5, but the scorer handles missing files gracefully)

**Step 12: Commit**

```bash
git add scripts/score_countries.py js/app.js tests/python/unit/test_indicator_config.py
git commit -m "feat: replace GDP per worker with ILO labour income share in scorer, add data_dir support"
```

---

### Task 4: Update documentation

**Files:**
- Modify: `METHODOLOGY.md:28-37` (Economic Concentration section)
- Modify: `METHODOLOGY.md:~265` (data sources table)
- Modify: `sources.md` (Economic Concentration table)
- Modify: `index.html:52,61-63` (methodology modal)
- Modify: `CLAUDE.md:61-67` (data pipeline table)

**Step 1: Update METHODOLOGY.md Economic Concentration section**

Replace:
```markdown
### 2. Economic Concentration

Wealth inequality and the gap between productivity and worker compensation.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Gini Index | World Bank | SI.POV.GINI | Direct |
| GDP per worker | World Bank | SL.GDP.PCAP.EM.KD | Direct |

Domain score = mean of normalized indicator scores.
```
With:
```markdown
### 2. Economic Concentration

Wealth inequality and the share of economic output captured by workers.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Gini Index | World Bank | SI.POV.GINI | Direct |
| Labour income share of GDP | ILO (ILOSTAT) | LAP_2GDP_NOC_RT | Inverted (higher = less extraction) |

Domain score = mean of normalized indicator scores.

**Why these indicators:**

- **Gini Index** measures income inequality — how unevenly income is distributed across the population.
- **Labour income share** measures what fraction of GDP goes to workers as compensation (wages, salaries, benefits, and imputed income for the self-employed). This is ILO SDG indicator 10.4.1. A declining labour share means a larger fraction of economic output is captured by capital owners rather than workers — a direct measure of economic extraction. This replaced an earlier GDP-per-worker indicator that measured productivity rather than distribution.
```

**Step 2: Update METHODOLOGY.md data sources table**

Add ILO row:
```markdown
| [ILO (ILOSTAT)](https://ilostat.ilo.org/) | API (automatic) | Economic concentration | 189 countries |
```

**Step 3: Update sources.md**

In the Economic Concentration section, replace:
```
| `wb_labor_share` | World Bank GDP per person employed | https://data.worldbank.org/ | 180+ countries | Annual |
```
with:
```
| `ilo_labor_share` | ILO Labour Income Share of GDP (SDG 10.4.1) | https://ilostat.ilo.org/ | 189 countries | Annual |
```

**Step 4: Update index.html methodology modal**

Line 52: Change `"labor share decline"` to `"declining worker income share"` in the Economic Concentration description.

Line 61-63: Update data sources list — change "four independent datasets" to "five independent datasets" and add ILO entry:
```html
<li><a href="https://ilostat.ilo.org/" target="_blank" rel="noopener"><strong>ILO</strong></a> — Labour income share of GDP (SDG 10.4.1)</li>
```
Also update the World Bank bullet to remove reference to labor share.

**Step 5: Update CLAUDE.md data pipeline table**

Add ILO row:
```markdown
| ILO | API (auto) | economic_concentration |
```

**Step 6: Commit**

```bash
git add METHODOLOGY.md sources.md index.html CLAUDE.md
git commit -m "docs: update all documentation for ILO labour share indicator"
```

---

### Task 5: Fetch data, regenerate scores, verify

**Step 1: Fetch ILO data**

```bash
source .venv/bin/activate && cd scripts
python fetch_all.py --source ilo
```

Expected: Records fetched, `raw_data/ilo/ilo_labor_share.csv` created.

**Step 2: Verify country code alignment**

Compare ILO country codes against existing scores.json:

```python
python3 -c "
import pandas as pd, json
ilo = pd.read_csv('../raw_data/ilo/ilo_labor_share.csv')
with open('../data/scores.json') as f:
    existing = set(json.load(f)['countries'].keys())
ilo_codes = set(ilo['country_code'].unique())
in_ilo_not_scores = ilo_codes - existing
in_scores_not_ilo = existing - ilo_codes
print(f'ILO codes not in scores.json ({len(in_ilo_not_scores)}): {sorted(in_ilo_not_scores)[:20]}')
print(f'scores.json codes not in ILO ({len(in_scores_not_ilo)}): {sorted(in_scores_not_ilo)[:20]}')
"
```

If there are mismatches, add mappings to `COUNTRY_CODE_OVERRIDES` in `ilo.py` and re-fetch.

**Step 3: Regenerate all scores**

```bash
python score_countries.py --overwrite
```

**Step 4: Spot-check key countries**

Verify economic_concentration scores now use ilo_labor_share. Check Canada specifically — should no longer show "GDP per worker: $110,184". Check Scandinavian countries and the US.

```python
python3 -c "
import json
with open('../data/scores.json') as f:
    data = json.load(f)
for code in ['CAN','USA','DNK','SWE','NOR','FIN','DEU','GBR','JPN','CHN']:
    c = data['countries'].get(code, {})
    ec = c.get('domains', {}).get('economic_concentration', {})
    print(f\"{code} ({c.get('name','')}): score={ec.get('score','N/A')}\")
    for ind in ec.get('indicators', []):
        print(f\"  {ind['key']}: {ind.get('facts',[''])[0][:70]}\")
"
```

**Step 5: Run full test suite**

```bash
make all
```

Expected: All tests pass, zero errors.

**Step 6: Commit regenerated scores**

```bash
git add data/scores.json raw_data/manifest.json
git commit -m "data: regenerate scores with ILO labour share replacing GDP per worker"
```

---

### Task 6: Write up findings in scratch/BOOK.md

Add a section documenting:
- What was wrong (GDP per worker ≠ labour share — productivity vs distribution)
- What the ILO indicator measures (SDG 10.4.1, adjusted labour income share including self-employed)
- How scores changed for key countries (Canada, US, Nordics)
- Norway's interesting low labour share (~45%) — likely oil wealth flowing to sovereign fund
- Why this matters for the extraction framing

---
