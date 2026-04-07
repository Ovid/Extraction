# Saudi Arabia Scoring Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix two scoring methodology issues that cause Saudi Arabia (and similar countries) to be under-scored on extraction: resource rents normalization and institutional gatekeeping indicator selection.

**Architecture:** Two independent changes to the scoring pipeline:
1. Log-transform resource rents before min-max normalization (fixes outlier compression)
2. Remove Government Effectiveness and Regulatory Quality from institutional_gatekeeping (they measure state capacity, not institutional capture)

Both changes flow through `scripts/score_countries.py` and require METHODOLOGY.md updates. A third change (WID fetcher for inequality data) is deferred to TODO.md.

**Tech Stack:** Python 3, pandas, numpy, pytest

**Test command:** `source .venv/bin/activate && pytest tests/python/ --tb=short -q`

---

### Task 1: Log-transform resource rents normalization

The current linear min-max normalization is dominated by Libya (61% of GDP), compressing Saudi Arabia's 25.6% to only 42/100. Log-transforming right-skewed economic data before min-max is standard practice.

**Files:**
- Modify: `scripts/score_countries.py:1340-1348` (normalize_minmax) and `scripts/score_countries.py:1542-1556` (build_country_scores indicator loading)
- Modify: `tests/python/unit/test_normalization.py`

**Step 1: Add log-transform normalization function and tests**

Add a new `normalize_minmax_log` function to `scripts/score_countries.py` below `normalize_minmax`:

```python
def normalize_minmax_log(series, inverted=False):
    """Normalize using log transform then min-max scaling.

    Use for right-skewed indicators (e.g., resource rents)
    where extreme outliers compress the rest of the distribution.
    Log transform is standard for right-skewed economic data.
    """
    log_series = np.log1p(series)
    return normalize_minmax(log_series, inverted=inverted)
```

Add `import numpy as np` at the top of `score_countries.py` (after the existing pandas import on line 27).

Add tests to `tests/python/unit/test_normalization.py`:

```python
from score_countries import normalize_minmax_log

class TestNormalizeMinmaxLog:
    def test_spreads_compressed_distribution(self):
        """Log transform gives middle values higher scores than linear."""
        s = pd.Series([0.0, 25.0, 61.0])  # Similar to resource rents distribution
        linear = normalize_minmax(s)
        log = normalize_minmax_log(s)
        # Middle value should score higher with log transform
        assert log.iloc[1] > linear.iloc[1]

    def test_extremes_unchanged(self):
        """Min still maps to 0, max still maps to 100."""
        s = pd.Series([0.0, 25.0, 61.0])
        result = normalize_minmax_log(s)
        assert result.iloc[0] == 0
        assert result.iloc[2] == 100

    def test_inverted(self):
        """Inverted log normalization flips correctly."""
        s = pd.Series([0.0, 25.0, 61.0])
        result = normalize_minmax_log(s, inverted=True)
        assert result.iloc[0] == 100
        assert result.iloc[2] == 0

    def test_all_identical_returns_50(self):
        """All same values -> all 50."""
        s = pd.Series([42.0, 42.0, 42.0])
        result = normalize_minmax_log(s)
        assert list(result) == [50, 50, 50]

    def test_all_zeros_returns_50(self):
        """All zeros -> log(1)=0 for all -> all 50."""
        s = pd.Series([0.0, 0.0, 0.0])
        result = normalize_minmax_log(s)
        assert list(result) == [50, 50, 50]
```

**Step 2: Run tests to verify new function works**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_normalization.py -v`
Expected: All new tests PASS, all existing tests still PASS.

**Step 3: Apply log normalization to resource rents indicator**

In `scripts/score_countries.py`, add a `log_transform` flag to INDICATOR_CONFIG for the resource rents entry (line 61-66):

```python
    {
        "file": "wb_natural_rents.csv",
        "domain": "resource_capture",
        "inverted": False,
        "source_key": "wb_natural_rents",
        "name": "Natural resource rents",
        "log_transform": True,
    },
```

Then in `build_country_scores()` (line 1551), change the normalization call to check for the flag:

```python
        if cfg.get("log_transform"):
            df["normalized"] = normalize_minmax_log(df["value"], inverted=cfg["inverted"])
        else:
            df["normalized"] = normalize_minmax(df["value"], inverted=cfg["inverted"])
```

**Step 4: Run tests to verify nothing broke**

The test `test_resource_capture.py` tests `compute_resource_capture()` which takes already-normalized values as input — those tests remain valid since the function itself doesn't change. The normalization change is upstream.

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_normalization.py
git commit -m "feat: log-transform resource rents normalization

Resource rents has extreme right skew (Libya 61% vs median ~5%).
Linear min-max compressed Saudi Arabia's 25.6% to 42/100.
Log transform is standard for right-skewed economic data and
spreads the distribution more evenly."
```

---

### Task 2: Remove GE and RQ from institutional_gatekeeping

Government Effectiveness and Regulatory Quality measure state capacity, not whether institutions serve the public. Their WGI definitions confirm this:
- GE: "quality of public services, civil service independence, policy implementation"
- RQ: "ability to formulate policies that promote private sector development"

Neither answers the gatekeeping question ("do institutions serve broad or narrow interests?"). Control of Corruption ("extent to which public power is exercised for private gain, including capture of the state by elites") does.

**Files:**
- Modify: `scripts/score_countries.py:75-88` (INDICATOR_CONFIG), `scripts/score_countries.py:92-100` (INDICATOR_QUESTIONS), `scripts/score_countries.py:133-138` (POSITIVE_QUESTION_INDICATORS), `scripts/score_countries.py:190-200` (INDICATOR_DETAIL)
- Modify: `scripts/fetch_all.py:31` (FETCHER_REGISTRY worldbank description)
- Modify: `tests/python/unit/test_build_wb_domain.py`
- Modify: `tests/python/unit/conftest.py`
- Modify: `tests/python/unit/test_merging.py` (uses sample_domain_a fixture — check and update any assertions that depend on old fixture shape)

**Step 1: Remove GE and RQ from INDICATOR_CONFIG**

Delete the two entries from `INDICATOR_CONFIG` (lines 75-88):

```python
    {
        "file": "wb_wgi_reg_quality.csv",
        "domain": "institutional_gatekeeping",
        "inverted": True,
        "source_key": "wb_reg_quality",
        "name": "WGI Regulatory Quality",
    },
    {
        "file": "wb_wgi_gov_effectiveness.csv",
        "domain": "institutional_gatekeeping",
        "inverted": True,
        "source_key": "wb_wgi_gov_eff",
        "name": "WGI Government Effectiveness",
    },
```

**Step 2: Remove GE and RQ from INDICATOR_QUESTIONS, POSITIVE_QUESTION_INDICATORS, and INDICATOR_DETAIL**

From `INDICATOR_QUESTIONS` (around line 99-100), remove:
```python
    "wb_reg_quality": "How well do government regulations protect people?",
    "wb_wgi_gov_eff": "How effective is the government?",
```

From `POSITIVE_QUESTION_INDICATORS` (around line 136-137), remove:
```python
    "wb_reg_quality",  # "How well do government regulations protect people?"
    "wb_wgi_gov_eff",  # "How effective is the government?"
```

From `INDICATOR_DETAIL` (around line 190-200), remove the `wb_reg_quality` and `wb_wgi_gov_eff` entries entirely.

**Step 3: Update worldbank fetcher description in fetch_all.py**

In `scripts/fetch_all.py` line 31, update the description to reflect what's actually scored:

```python
    "description": "World Bank Development Indicators (Gini, labor share, domestic credit, natural resource rents, corruption control)",
```

**Step 4: Update test fixtures and dependent tests**

In `tests/python/unit/conftest.py`, update `sample_domain_a` to only reference `wb_wgi_corruption` (not `wb_reg_quality`):

```python
@pytest.fixture
def sample_domain_a():
    """A domain entry from source A (e.g., World Bank)."""
    return {
        "score": 60,
        "confidence": "moderate",
        "trend": "rising",
        "sources": ["wb_wgi_corruption"],
        "indicators": [
            {
                "key": "wb_wgi_corruption",
                "question": "How well is corruption controlled?",
                "label": "High",
                "facts": ["Control of corruption index: -0.50"],
            },
        ],
        "justification_detail": "Auto-scored from World Bank data. WGI Control of Corruption: -0.500 (normalized: 60).",
        "_n_indicators": 1,
        "_n_sources": 1,
        "_most_recent_year": 2022,
    }
```

In `tests/python/unit/test_build_wb_domain.py`, update `_make_wb_group()` to use only one WGI indicator for institutional_gatekeeping:

```python
def _make_wb_group():
    """Build a minimal pandas DataFrame resembling a WB domain group.

    One indicator for institutional_gatekeeping (Control of Corruption only —
    GE and RQ were removed as they measure state capacity, not institutional capture).
    """
    return pd.DataFrame({
        "country_code": ["USA"],
        "country_name": ["United States"],
        "year": [2022],
        "value": [-0.5],
        "normalized": [60],
        "domain": ["institutional_gatekeeping"],
        "source_key": ["wb_wgi_corruption"],
        "indicator_name": ["WGI Control of Corruption"],
        "indicator_file": ["wb_wgi_corruption.csv"],
    })
```

Update the tests that depend on this fixture:
- `test_score_is_mean_of_normalized`: now expects 60 (single indicator, not avg of 60+30)
- `test_n_indicators_matches_group_size`: now expects 1
- `test_sources_list`: only assert `wb_wgi_corruption`, remove `wb_reg_quality` assertion

In `tests/python/unit/test_merging.py`, check all assertions that depend on `sample_domain_a` and update any that assume `_n_indicators: 2` or `sources: ["wb_wgi_corruption", "wb_reg_quality"]`. The fixture now has `_n_indicators: 1` and `sources: ["wb_wgi_corruption"]`.

**Step 5: Run tests**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: All tests PASS.

**Step 6: Commit**

```bash
git add scripts/score_countries.py scripts/fetch_all.py tests/python/unit/test_build_wb_domain.py tests/python/unit/conftest.py tests/python/unit/test_merging.py
git commit -m "refactor: remove GE and RQ from institutional_gatekeeping

Government Effectiveness measures bureaucratic competence, not who
institutions serve. Regulatory Quality measures pro-business policy
orientation. Neither answers the gatekeeping question. Control of
Corruption ('capture of the state by elites') remains."
```

---

### Task 3: Update METHODOLOGY.md

**Files:**
- Modify: `METHODOLOGY.md:49-64` (institutional gatekeeping section)
- Modify: `METHODOLOGY.md:82-100` (resource capture section)
- Modify: `METHODOLOGY.md:112-127` (normalization section)

**Step 1: Update institutional gatekeeping section**

Replace lines 49-64 with:

```markdown
### 4. Institutional Gatekeeping

Whether institutions serve the broad population or narrow interests.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Control of Corruption | World Bank (WGI) | CC.EST | Inverted |
| Rule of Law | V-Dem | v2x_rule | Inverted |
| Egalitarian Component | V-Dem | v2x_egal | Inverted |
| Participatory Democracy | V-Dem | v2x_partipdem | Inverted |

The World Bank WGI Control of Corruption indicator measures the extent to which public power is exercised for private gain, including capture of the state by elites — directly relevant to institutional gatekeeping. The V-Dem indicators measure how equally power and resources are distributed and how much citizens can participate in governance.

**Why Government Effectiveness and Regulatory Quality are excluded:** These WGI indicators measure state capacity (bureaucratic competence, pro-business regulatory environment) rather than who institutions serve. An efficient autocracy scores well on both — high government effectiveness and strong regulatory quality — without its institutions serving broad interests. Including them would systematically understate extraction in competent autocracies.

When both World Bank and V-Dem data are available for this domain, the domain score is the average of the World Bank group score and the V-Dem group score.
```

**Step 2: Update resource capture section**

Replace the formula on line 83 and update the description below:

```markdown
```
resource_capture = log_normalized_resource_rents × (100 - democratic_accountability) / 100
```

Where:
- `log_normalized_resource_rents` = World Bank natural resource rents (% GDP), indicator NY.GDP.TOTL.RT.ZS, log-transformed then min-max normalized to 0-100
- `democratic_accountability` = raw V-Dem electoral democracy index (v2x_polyarchy) × 100

Resource rents are log-transformed before min-max normalization because the raw distribution is heavily right-skewed (a few countries exceed 50% of GDP while most are under 5%). Without log transformation, linear min-max normalization compresses most countries into the lower range, understating resource capture vulnerability. Log transformation of right-skewed economic data is standard practice in economics research.
```

Keep the existing limitations paragraphs and "Important limitations" section that follow — they remain valid.

**Step 3: Update normalization section**

After line 126 ("This ensures all scores follow the convention: **0 = no extraction, 100 = extreme extraction**."), add:

```markdown
### Log-Transformed Normalization

For indicators with extreme right skew (currently: natural resource rents), a log transform is applied before min-max scaling:

```
log_normalized = (log(1 + value) - log(1 + min)) / (log(1 + max) - log(1 + min)) × 100
```

This spreads the compressed middle of the distribution while preserving the 0-100 range and relative ordering. The choice of which indicators receive log transformation is based on distributional analysis — resource rents has a skewness that compresses most countries below the 50th percentile under linear scaling.
```

**Step 4: Commit**

```bash
git add METHODOLOGY.md
git commit -m "docs: update methodology for log normalization and gatekeeping indicator changes"
```

---

### Task 4: Regenerate scores and verify

After all code changes, regenerate `data/scores.json` and verify the impact.

**Step 1: Save current scores for comparison**

```bash
cp data/scores.json data/scores_before.json
```

**Step 2: Regenerate all scores**

```bash
source .venv/bin/activate && cd scripts
python score_countries.py --overwrite
```

**Step 3: Compare before/after across all countries**

Run a diff script to flag countries whose composite score moved more than 10 points:

```bash
python3 -c "
import json
with open('../data/scores_before.json') as f:
    before = json.load(f)
with open('../data/scores.json') as f:
    after = json.load(f)
print('Countries with composite change > 10 points:')
changes = []
for code in sorted(before['countries']):
    b = before['countries'][code].get('composite_score', 0)
    a = after['countries'].get(code, {}).get('composite_score', 0)
    delta = a - b
    if abs(delta) > 10:
        changes.append((code, b, a, delta))
for code, b, a, delta in sorted(changes, key=lambda x: -abs(x[3])):
    print(f'  {code}: {b} -> {a} ({delta:+d})')
print(f'Total: {len(changes)} countries moved > 10 points')
"
```

Review the output for surprises. Some movement is expected (all countries with resource rents or WGI data are affected), but large unexpected shifts should be investigated.

**Step 4: Verify key countries**

```bash
python3 -c "
import json
with open('../data/scores.json') as f:
    d = json.load(f)
for code in ['SAU', 'NOR', 'SGP', 'RUS', 'DNK', 'USA']:
    c = d['countries'][code]
    print(f\"{code}: composite={c['composite_score']}\")
    for domain in ['resource_capture', 'institutional_gatekeeping', 'economic_concentration']:
        dd = c['domains'].get(domain, {})
        print(f\"  {domain}: {dd.get('score')}\")
"
```

Expected directional changes:
- SAU resource_capture: 41 → ~77 (log normalization)
- SAU institutional_gatekeeping: 55 → higher (without GE/RQ pulling it down)
- NOR resource_capture: 2 → ~6 (slight increase from log spread, still low)
- SGP institutional_gatekeeping: 19 → higher (without extreme GE/RQ boost)

**Step 5: Run full test suite**

```bash
source .venv/bin/activate && pytest tests/python/ --tb=short -q
```

**Step 6: Clean up and commit**

```bash
rm data/scores_before.json
git add data/scores.json
git commit -m "data: regenerate scores with log normalization and gatekeeping fixes"
```
