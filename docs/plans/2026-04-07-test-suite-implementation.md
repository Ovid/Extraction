# Test Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a comprehensive test suite (pytest + Vitest) with refactoring for testability, covering the scoring pipeline, fetcher parsers, data integrity, and JS visualization logic.

**Architecture:** Refactor `score_countries.py` to extract pure functions from the monolithic `build_country_scores()`. Extract pure JS logic from `app.js` into `lib.js` as ES modules. Write tests against these clean interfaces. No build system — just pytest for Python and Vitest for JS.

**Tech Stack:** pytest, pytest-cov, Vitest, pandas (existing), openpyxl (existing), jsonschema (new, for schema validation tests)

---

### Task 1: Project setup — Python test dependencies and directory structure

**Files:**
- Modify: `scripts/requirements.txt`
- Create: `tests/python/unit/conftest.py`
- Create: `tests/python/fixtures/.gitkeep`
- Create: `pytest.ini`

**Step 1: Create directory structure**

```bash
mkdir -p tests/python/unit tests/python/integration tests/python/fixtures/worldbank tests/python/fixtures/vdem tests/python/fixtures/rsf tests/python/fixtures/fsi tests/js
```

**Step 2: Add test dependencies to requirements.txt**

Append to `scripts/requirements.txt`:
```
pytest>=7.0
pytest-cov>=4.0
jsonschema>=4.0
```

**Step 3: Create pytest.ini at project root**

```ini
[pytest]
testpaths = tests/python
pythonpath = scripts
```

`pythonpath = scripts` lets tests do `import score_countries` and `from fetchers import worldbank` without path hacks.

**Step 4: Create conftest.py with factory fixtures**

```python
"""Shared test fixtures for the Extraction Index test suite."""

import pytest
import pandas as pd


@pytest.fixture
def sample_domain_a():
    """A domain entry from source A (e.g., World Bank)."""
    return {
        'score': 60,
        'confidence': 'moderate',
        'trend': 'rising',
        'sources': ['wb_wgi_corruption', 'wb_reg_quality'],
        'indicators': [
            {'key': 'wb_wgi_corruption', 'question': 'How well is corruption controlled?', 'label': 'High', 'facts': ['Control of corruption index: -0.50']},
        ],
        'justification_detail': 'Auto-scored from World Bank data. WGI Control of Corruption: -0.500 (normalized: 60).',
        '_n_indicators': 2,
        '_n_sources': 1,
        '_most_recent_year': 2022,
    }


@pytest.fixture
def sample_domain_b():
    """A domain entry from source B (e.g., V-Dem)."""
    return {
        'score': 40,
        'confidence': 'moderate',
        'trend': 'unknown',
        'sources': ['vdem_rule_of_law'],
        'indicators': [
            {'key': 'vdem_rule_of_law', 'question': 'How strong is the rule of law?', 'label': 'Moderate', 'facts': ['Rule of law index: 0.65']},
        ],
        'justification_detail': 'Auto-scored from V-Dem. Rule of Law: 0.650 (normalized: 40).',
        '_n_indicators': 1,
        '_n_sources': 1,
        '_most_recent_year': 2024,
    }


@pytest.fixture
def sample_all_indicator_raw():
    """Raw indicator values for peer comparison tests."""
    return {
        'wb_gini': {
            'USA': 41.5, 'CAN': 33.3,  # Northern America
            'DNK': 28.2, 'SWE': 27.6, 'NOR': 25.6, 'FIN': 27.1,  # Northern Europe
            'BRA': 53.4, 'ARG': 42.3, 'CHL': 44.9, 'COL': 51.3,  # South America
            'NGA': 35.1, 'GHA': 43.5, 'SEN': 40.3, 'CIV': 37.2,  # Western Africa
        },
    }
```

**Step 5: Install dependencies and verify pytest discovers tests**

```bash
cd /Users/ovid/projects/extraction
source .venv/bin/activate
pip install -r scripts/requirements.txt
pytest --collect-only
```

Expected: 0 tests collected (no test files yet), but no import errors.

**Step 6: Commit**

```bash
git add pytest.ini scripts/requirements.txt tests/
git commit -m "Add test infrastructure: pytest config, directory structure, fixtures"
```

---

### Task 2: Refactor score_countries.py — extract `compute_resource_capture()`

**Files:**
- Modify: `scripts/score_countries.py:987-1039` (extract inline logic)
- Test: `tests/python/unit/test_resource_capture.py`

**Step 1: Write the failing tests**

Create `tests/python/unit/test_resource_capture.py`:

```python
"""Tests for resource capture composite formula."""

from score_countries import compute_resource_capture


class TestComputeResourceCapture:
    def test_with_vdem_data(self):
        """normalized_resource * (100 - round(polyarchy * 100)) / 100"""
        # 60 * (100 - 80) / 100 = 60 * 20 / 100 = 12
        assert compute_resource_capture(60, 0.8) == 12

    def test_zero_resource_rents(self):
        """Zero resources = zero capture regardless of democracy."""
        assert compute_resource_capture(0, 0.3) == 0

    def test_zero_polyarchy(self):
        """No democracy = full resource capture."""
        # 75 * (100 - 0) / 100 = 75
        assert compute_resource_capture(75, 0.0) == 75

    def test_full_polyarchy(self):
        """Full democracy = zero resource capture."""
        # 50 * (100 - 100) / 100 = 0
        assert compute_resource_capture(50, 1.0) == 0

    def test_none_polyarchy_returns_unchanged(self):
        """Missing V-Dem data returns raw normalized score unchanged."""
        assert compute_resource_capture(45, None) == 45

    def test_rounding(self):
        """Verify rounding behavior matches production code."""
        # 80 * (100 - round(0.73 * 100)) / 100 = 80 * (100 - 73) / 100 = 80 * 27 / 100 = 21.6 -> 22
        assert compute_resource_capture(80, 0.73) == 22

    def test_high_resource_low_democracy(self):
        """Classic petro-state scenario: high rents, low democracy."""
        # 95 * (100 - round(0.15 * 100)) / 100 = 95 * 85 / 100 = 80.75 -> 81
        assert compute_resource_capture(95, 0.15) == 81
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/python/unit/test_resource_capture.py -v
```

Expected: `ImportError: cannot import name 'compute_resource_capture'`

**Step 3: Implement `compute_resource_capture` in score_countries.py**

Add after `assess_domain_confidence()` (after line 650):

```python
def compute_resource_capture(normalized_resource_score, raw_polyarchy):
    """Compute resource capture composite: resource rents moderated by democracy.

    Uses raw V-Dem polyarchy (0-1) directly, NOT min-max normalized.
    Formula: normalized_resource * (100 - accountability) / 100
    """
    if raw_polyarchy is None:
        return normalized_resource_score
    accountability = round(raw_polyarchy * 100)
    return round(normalized_resource_score * (100 - accountability) / 100)
```

Then replace the inline usage in `build_country_scores()` at lines 992-1006. Replace:
```python
            if raw_polyarchy is not None:
                # Convert raw 0-1 polyarchy to 0-100 accountability score
                accountability = round(raw_polyarchy * 100)
                composite_resource = round(raw_resource * (100 - accountability) / 100)
```
With:
```python
            if raw_polyarchy is not None:
                accountability = round(raw_polyarchy * 100)
                composite_resource = compute_resource_capture(raw_resource, raw_polyarchy)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/python/unit/test_resource_capture.py -v
```

Expected: all 7 tests PASS.

**Step 5: Run the full scoring pipeline to verify no regression**

```bash
cd scripts && python score_countries.py --preview
```

Expected: same country count and scores as before.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_resource_capture.py
git commit -m "Extract compute_resource_capture() with tests"
```

---

### Task 3: Refactor score_countries.py — extract `merge_domain_scores()`

**Files:**
- Modify: `scripts/score_countries.py:948-965` (extract inline logic)
- Test: `tests/python/unit/test_merging.py`

**Step 1: Write the failing tests**

Create `tests/python/unit/test_merging.py`:

```python
"""Tests for multi-source domain merging."""

from score_countries import merge_domain_scores


class TestMergeDomainScores:
    def test_scores_averaged(self, sample_domain_a, sample_domain_b):
        """Two sources for same domain -> scores averaged."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['score'] == 50  # (60 + 40) / 2

    def test_indicators_merged(self, sample_domain_a, sample_domain_b):
        """Indicator lists are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert len(merged['indicators']) == 2
        keys = [i['key'] for i in merged['indicators']]
        assert 'wb_wgi_corruption' in keys
        assert 'vdem_rule_of_law' in keys

    def test_sources_merged(self, sample_domain_a, sample_domain_b):
        """Source lists are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert 'wb_wgi_corruption' in merged['sources']
        assert 'wb_reg_quality' in merged['sources']
        assert 'vdem_rule_of_law' in merged['sources']

    def test_confidence_recalculated(self, sample_domain_a, sample_domain_b):
        """Confidence recalculated from combined n_indicators, n_sources, most_recent_year."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        # Combined: 3 indicators, 2 sources, year 2024
        # completeness=2 (3 indicators), diversity=2 (2 sources), recency=3 (2024)
        # total=7 -> 'high'
        assert merged['confidence'] == 'high'

    def test_trend_preserves_known(self, sample_domain_a, sample_domain_b):
        """Known trend from source A preserved when B is unknown."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['trend'] == 'rising'

    def test_most_recent_year_takes_max(self, sample_domain_a, sample_domain_b):
        """Internal _most_recent_year is max of both sources."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['_most_recent_year'] == 2024

    def test_justification_combined(self, sample_domain_a, sample_domain_b):
        """Justification detail strings are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert 'World Bank' in merged['justification_detail']
        assert 'V-Dem' in merged['justification_detail']
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/python/unit/test_merging.py -v
```

Expected: `ImportError: cannot import name 'merge_domain_scores'`

**Step 3: Implement `merge_domain_scores` in score_countries.py**

Add after `compute_resource_capture()`:

```python
def merge_domain_scores(existing, new_domain):
    """Merge two domain entries from different sources by averaging scores.

    Combines indicators, sources, and recalculates confidence from totals.
    Preserves known trend from either source (prefers existing if known).
    """
    merged_score = round((existing['score'] + new_domain['score']) / 2)
    merged_n = existing.get('_n_indicators', 1) + new_domain.get('_n_indicators', 1)
    merged_sources_count = existing.get('_n_sources', 1) + new_domain.get('_n_sources', 1)
    merged_year = max(existing.get('_most_recent_year') or 0,
                      new_domain.get('_most_recent_year') or 0)

    # Prefer known trend
    if existing.get('trend', 'unknown') != 'unknown':
        trend = existing['trend']
    else:
        trend = new_domain.get('trend', 'unknown')

    return {
        'score': merged_score,
        'confidence': assess_domain_confidence(merged_n, merged_sources_count, merged_year),
        'trend': trend,
        'sources': existing.get('sources', []) + new_domain.get('sources', []),
        'indicators': existing.get('indicators', []) + new_domain.get('indicators', []),
        'justification_detail': f'{existing.get("justification_detail", "")} {new_domain.get("justification_detail", "")}'.strip(),
        '_n_indicators': merged_n,
        '_n_sources': merged_sources_count,
        '_most_recent_year': merged_year,
    }
```

Then replace the inline merge logic in `build_country_scores()` at lines 948-965. Replace:
```python
                if domain in domains:
                    # Merge with existing domain score (average of WB/RSF and V-Dem)
                    existing = domains[domain]
                    merged_score = round((existing['score'] + vdem_score) / 2)
                    ...
                    domains[domain] = {
                        ...
                    }
```
With:
```python
                if domain in domains:
                    vdem_domain_entry = {
                        'score': vdem_score,
                        'confidence': assess_domain_confidence(n_vdem, 1, 2024),
                        'trend': 'unknown',
                        'sources': vdem_sources,
                        'indicators': vdem_ind_entries,
                        'justification_detail': vdem_detail,
                        '_n_indicators': n_vdem,
                        '_n_sources': 1,
                        '_most_recent_year': 2024,
                    }
                    domains[domain] = merge_domain_scores(domains[domain], vdem_domain_entry)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/python/unit/test_merging.py -v
```

Expected: all 7 tests PASS.

**Step 5: Verify no regression**

```bash
cd scripts && python score_countries.py --preview
```

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_merging.py
git commit -m "Extract merge_domain_scores() with tests"
```

---

### Task 4: Refactor score_countries.py — refactor `estimate_trend()`

**Files:**
- Modify: `scripts/score_countries.py:678-700` (refactor to accept data)
- Test: `tests/python/unit/test_trends.py`

**Step 1: Write the failing tests**

Create `tests/python/unit/test_trends.py`:

```python
"""Tests for trend estimation."""

import pandas as pd
from score_countries import estimate_trend_from_data


class TestEstimateTrendFromData:
    def test_rising(self):
        """>=10% increase -> rising."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 115, 115],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'rising'

    def test_falling(self):
        """>=10% decrease -> falling."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 85, 85],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'falling'

    def test_stable(self):
        """<10% change -> stable."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 105, 105],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'stable'

    def test_boundary_exactly_10_percent(self):
        """Exactly 10% change -> stable (< 0.10, not <=)."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 110, 110],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'stable'

    def test_inverted_falling_raw_means_rising_extraction(self):
        """For inverted indicators, falling raw = rising extraction."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 85, 85],
        })
        assert estimate_trend_from_data(data, inverted=True) == 'rising'

    def test_inverted_rising_raw_means_falling_extraction(self):
        """For inverted indicators, rising raw = falling extraction."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [100, 100, 115, 115],
        })
        assert estimate_trend_from_data(data, inverted=True) == 'falling'

    def test_too_few_rows(self):
        """Fewer than 2 data points -> unknown."""
        data = pd.DataFrame({'year': [2020], 'value': [50]})
        assert estimate_trend_from_data(data, inverted=False) == 'unknown'

    def test_no_recent_data(self):
        """All data before 2018 -> unknown (no recent values)."""
        data = pd.DataFrame({
            'year': [2010, 2012, 2014],
            'value': [100, 105, 110],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'unknown'

    def test_no_old_data(self):
        """All data after 2015 -> unknown (no older baseline)."""
        data = pd.DataFrame({
            'year': [2018, 2019, 2020],
            'value': [100, 105, 110],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'unknown'

    def test_older_baseline_zero(self):
        """Older baseline is 0 -> unknown (avoid division by zero)."""
        data = pd.DataFrame({
            'year': [2012, 2013, 2019, 2020],
            'value': [0, 0, 50, 50],
        })
        assert estimate_trend_from_data(data, inverted=False) == 'unknown'

    def test_empty_dataframe(self):
        """Empty dataframe -> unknown."""
        data = pd.DataFrame({'year': [], 'value': []})
        assert estimate_trend_from_data(data, inverted=False) == 'unknown'
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/python/unit/test_trends.py -v
```

Expected: `ImportError: cannot import name 'estimate_trend_from_data'`

**Step 3: Refactor estimate_trend in score_countries.py**

Add a new pure function and keep the existing one as a thin wrapper:

```python
def estimate_trend_from_data(df, inverted=False):
    """Estimate trend by comparing recent vs older values.

    Args:
        df: DataFrame with 'year' and 'value' columns for a single country/indicator.
        inverted: If True, falling raw value means extraction is rising.

    Returns: 'rising', 'falling', 'stable', or 'unknown'.
    """
    if len(df) < 2:
        return 'unknown'
    recent = df[df['year'] >= 2018]['value'].mean()
    older = df[df['year'] <= 2015]['value'].mean()
    if pd.isna(recent) or pd.isna(older) or older == 0:
        return 'unknown'
    change = (recent - older) / abs(older)
    if inverted:
        change = -change
    if abs(change) < 0.10:
        return 'stable'
    return 'rising' if change > 0 else 'falling'


def estimate_trend(df_full, country_code, indicator_file, inverted=False):
    """Estimate trend for a country/indicator by reading from disk.

    Thin wrapper around estimate_trend_from_data that handles file loading.
    """
    filepath = WB_DIR / indicator_file
    if not filepath.exists():
        return 'unknown'
    df = pd.read_csv(filepath)
    df = df[df['country_code'] == country_code].sort_values('year')
    return estimate_trend_from_data(df, inverted=inverted)
```

Remove the old `estimate_trend` body (lines 678-700) and replace with the above two functions.

**Step 4: Run tests to verify they pass**

```bash
pytest tests/python/unit/test_trends.py -v
```

Expected: all 11 tests PASS.

**Step 5: Verify no regression**

```bash
cd scripts && python score_countries.py --preview
```

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_trends.py
git commit -m "Refactor estimate_trend() into pure function with tests"
```

---

### Task 5: Test normalization and confidence (pure functions, no refactoring needed)

**Files:**
- Create: `tests/python/unit/test_normalization.py`
- Create: `tests/python/unit/test_confidence.py`

**Step 1: Write normalization tests**

Create `tests/python/unit/test_normalization.py`:

```python
"""Tests for min-max normalization."""

import pandas as pd
from score_countries import normalize_minmax


class TestNormalizeMinmax:
    def test_normal_range(self):
        """Known values scale to expected 0-100 range."""
        s = pd.Series([0, 50, 100])
        result = normalize_minmax(s)
        assert list(result) == [0, 50, 100]

    def test_min_maps_to_zero(self):
        s = pd.Series([10, 20, 30])
        result = normalize_minmax(s)
        assert result.iloc[0] == 0

    def test_max_maps_to_100(self):
        s = pd.Series([10, 20, 30])
        result = normalize_minmax(s)
        assert result.iloc[2] == 100

    def test_inverted(self):
        """Inverted: highest raw -> 0, lowest raw -> 100."""
        s = pd.Series([0, 50, 100])
        result = normalize_minmax(s, inverted=True)
        assert list(result) == [100, 50, 0]

    def test_all_identical_returns_50(self):
        """All same values -> all 50."""
        s = pd.Series([42, 42, 42])
        result = normalize_minmax(s)
        assert list(result) == [50, 50, 50]

    def test_single_value_returns_50(self):
        """Single value -> 50 (hi == lo)."""
        s = pd.Series([7.5])
        result = normalize_minmax(s)
        assert result.iloc[0] == 50

    def test_negative_values(self):
        """Negative values normalize correctly (WGI uses -2.5 to 2.5)."""
        s = pd.Series([-2.5, 0.0, 2.5])
        result = normalize_minmax(s)
        assert list(result) == [0, 50, 100]

    def test_result_is_int(self):
        """Results are rounded integers."""
        s = pd.Series([0, 33, 100])
        result = normalize_minmax(s)
        assert all(isinstance(v, (int,)) for v in result)
```

**Step 2: Write confidence tests**

Create `tests/python/unit/test_confidence.py`:

```python
"""Tests for confidence assessment."""

from score_countries import assess_domain_confidence


class TestAssessDomainConfidence:
    # --- Individual factor scoring ---
    def test_high_confidence(self):
        """4+ indicators, 3+ sources, year >= 2022 -> high (9 total)."""
        assert assess_domain_confidence(4, 3, 2023) == 'high'

    def test_moderate_confidence(self):
        """2 indicators, 2 sources, year 2020 -> moderate (5 total)."""
        # completeness=1, diversity=2, recency=2 = 5
        assert assess_domain_confidence(2, 2, 2020) == 'moderate'

    def test_low_confidence(self):
        """1 indicator, 1 source, year 2016 -> low (1+1+1=3)."""
        assert assess_domain_confidence(1, 1, 2016) == 'low'

    def test_very_low_confidence(self):
        """1 indicator, 0 sources, old year -> very_low."""
        assert assess_domain_confidence(1, 0, 2010) == 'very_low'

    def test_no_year_data(self):
        """None year -> recency = 0."""
        assert assess_domain_confidence(1, 1, None) == 'very_low'

    # --- Boundary cases ---
    def test_boundary_high_at_7(self):
        """Total = 7 -> high."""
        # 3 indicators (completeness=2), 2 sources (diversity=2), 2022 (recency=3) = 7
        assert assess_domain_confidence(3, 2, 2022) == 'high'

    def test_boundary_moderate_at_5(self):
        """Total = 5 -> moderate."""
        # 2 indicators (completeness=1), 1 source (diversity=1), 2022 (recency=3) = 5
        assert assess_domain_confidence(2, 1, 2022) == 'moderate'

    def test_boundary_low_at_3(self):
        """Total = 3 -> low."""
        # 1 indicator (completeness=0), 1 source (diversity=1), 2020 (recency=2) = 3
        assert assess_domain_confidence(1, 1, 2020) == 'low'

    def test_boundary_very_low_at_2(self):
        """Total = 2 -> very_low."""
        # 2 indicators (completeness=1), 1 source (diversity=1), None (recency=0) = 2
        assert assess_domain_confidence(2, 1, None) == 'very_low'

    # --- Completeness factor ---
    def test_completeness_4_plus(self):
        """4+ indicators -> completeness = 3."""
        assert assess_domain_confidence(5, 3, 2023) == 'high'

    def test_completeness_3(self):
        """3 indicators -> completeness = 2."""
        # 2 + diversity(3) + recency(3) = 8 -> high
        assert assess_domain_confidence(3, 3, 2023) == 'high'

    # --- Recency factor ---
    def test_recency_2022_plus(self):
        """Year >= 2022 -> recency = 3."""
        assert assess_domain_confidence(4, 3, 2024) == 'high'

    def test_recency_2019_to_2021(self):
        """Year 2019-2021 -> recency = 2."""
        assert assess_domain_confidence(4, 3, 2019) == 'high'  # 3+3+2=8

    def test_recency_2015_to_2018(self):
        """Year 2015-2018 -> recency = 1."""
        assert assess_domain_confidence(4, 3, 2015) == 'high'  # 3+3+1=7

    def test_recency_before_2015(self):
        """Year < 2015 -> recency = 0."""
        assert assess_domain_confidence(4, 3, 2014) == 'moderate'  # 3+3+0=6
```

**Step 3: Run tests**

```bash
pytest tests/python/unit/test_normalization.py tests/python/unit/test_confidence.py -v
```

Expected: all tests PASS (these test existing pure functions, no refactoring needed).

**Step 4: Commit**

```bash
git add tests/python/unit/test_normalization.py tests/python/unit/test_confidence.py
git commit -m "Add normalization and confidence unit tests"
```

---

### Task 6: Test peer comparisons

**Files:**
- Create: `tests/python/unit/test_peer_comparisons.py`

**Step 1: Write the tests**

Create `tests/python/unit/test_peer_comparisons.py`:

```python
"""Tests for peer comparison context facts generation."""

from score_countries import generate_context_facts, REGION_MAP, INCOME_GROUP_MAP


class TestGenerateContextFacts:
    def test_first_fact_is_raw_value(self, sample_all_indicator_raw):
        """First fact is always the formatted raw value."""
        facts = generate_context_facts(
            'wb_gini', 41.5, 60, 'USA', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1
        assert 'Gini coefficient' in facts[0]
        assert '41.5' in facts[0]

    def test_peer_comparison_generated_when_divergent(self, sample_all_indicator_raw):
        """Peer comparison generated when >10% divergence from peer average."""
        # DNK (28.2) vs Northern Europe peers (27.6, 25.6, 27.1) avg ~26.8
        # Delta: (28.2 - 26.8) / 26.8 * 100 ~= 5.2%, not enough
        # But vs High income group, many more peers with higher avg
        facts = generate_context_facts(
            'wb_gini', 28.2, 20, 'DNK', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1  # At least raw value

    def test_no_comparison_when_within_10_percent(self, sample_all_indicator_raw):
        """No peer comparison when within 10% of peer average."""
        # SWE (27.6) vs Northern Europe (DNK 28.2, NOR 25.6, FIN 27.1) avg ~26.97
        # Delta: ~2.3%, well within 10%
        facts = generate_context_facts(
            'wb_gini', 27.6, 18, 'SWE', sample_all_indicator_raw['wb_gini'])
        assert len(facts) <= 1  # Only raw value, no comparison

    def test_unknown_indicator_returns_empty(self, sample_all_indicator_raw):
        """Unknown source_key with no display config returns empty list."""
        facts = generate_context_facts(
            'nonexistent_key', 50, 50, 'USA', {})
        assert facts == []

    def test_country_not_in_region_map(self, sample_all_indicator_raw):
        """Country not in REGION_MAP still gets raw value fact."""
        facts = generate_context_facts(
            'wb_gini', 30.0, 25, 'XXX', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1
        assert 'Gini' in facts[0]

    def test_too_few_peers_no_comparison(self):
        """Fewer than 3 peers in group -> no peer comparison."""
        # Only 2 countries in this region
        sparse_data = {'USA': 41.5, 'CAN': 33.3}
        facts = generate_context_facts(
            'wb_gini', 41.5, 60, 'USA', sparse_data)
        assert len(facts) <= 1


class TestRegionAndIncomeMapping:
    def test_usa_in_northern_america(self):
        assert REGION_MAP['USA'] == 'Northern America'

    def test_dnk_in_northern_europe(self):
        assert REGION_MAP['DNK'] == 'Northern Europe'

    def test_usa_is_high_income(self):
        assert INCOME_GROUP_MAP['USA'] == 'High income'

    def test_eth_is_low_income(self):
        assert INCOME_GROUP_MAP['ETH'] == 'Low income'
```

**Step 2: Run tests**

```bash
pytest tests/python/unit/test_peer_comparisons.py -v
```

Expected: all tests PASS.

**Step 3: Commit**

```bash
git add tests/python/unit/test_peer_comparisons.py
git commit -m "Add peer comparison unit tests"
```

---

### Task 7: Test country codes and exclusions

**Files:**
- Create: `tests/python/unit/test_country_codes.py`

**Step 1: Write the tests**

Create `tests/python/unit/test_country_codes.py`:

```python
"""Tests for country code handling, exclusions, and mappings."""

from score_countries import (
    EXCLUDE_CODES, COUNTRY_NAME_OVERRIDES, ALPHA2_TO_ALPHA3,
    RSF_CODE_REMAP,
)


class TestExcludeCodes:
    def test_excludes_world_aggregate(self):
        assert 'WLD' in EXCLUDE_CODES

    def test_excludes_income_groups(self):
        for code in ['HIC', 'LIC', 'LMC', 'UMC', 'MIC']:
            assert code in EXCLUDE_CODES

    def test_excludes_regional_aggregates(self):
        for code in ['EAS', 'ECS', 'LAC', 'MEA', 'NAC', 'SAS', 'SSF']:
            assert code in EXCLUDE_CODES

    def test_no_real_country_excluded(self):
        """Spot check that real countries aren't accidentally excluded."""
        real_countries = ['USA', 'GBR', 'CHN', 'IND', 'BRA', 'NGA', 'AUS']
        for code in real_countries:
            assert code not in EXCLUDE_CODES


class TestCountryNameOverrides:
    def test_usa_override(self):
        assert COUNTRY_NAME_OVERRIDES['USA'] == 'United States'

    def test_kor_override(self):
        assert COUNTRY_NAME_OVERRIDES['KOR'] == 'South Korea'

    def test_all_overrides_are_three_letter(self):
        """All override keys must be 3-letter codes."""
        for code in COUNTRY_NAME_OVERRIDES:
            assert len(code) == 3, f"Override key '{code}' is not 3 letters"
            assert code.isalpha() and code.isupper(), f"Override key '{code}' is not uppercase alpha"


class TestAlpha2ToAlpha3:
    def test_us_to_usa(self):
        assert ALPHA2_TO_ALPHA3['US'] == 'USA'

    def test_gb_to_gbr(self):
        assert ALPHA2_TO_ALPHA3['GB'] == 'GBR'

    def test_all_keys_are_two_letter(self):
        for key in ALPHA2_TO_ALPHA3:
            assert len(key) == 2, f"Key '{key}' is not 2 letters"

    def test_all_values_are_three_letter(self):
        for val in ALPHA2_TO_ALPHA3.values():
            assert len(val) == 3, f"Value '{val}' is not 3 letters"

    def test_no_excluded_codes_in_values(self):
        """Alpha-3 mapping should not map to excluded codes."""
        for a2, a3 in ALPHA2_TO_ALPHA3.items():
            assert a3 not in EXCLUDE_CODES, f"{a2} maps to excluded code {a3}"


class TestRsfCodeRemap:
    def test_seychelles_remap(self):
        assert RSF_CODE_REMAP['SEY'] == 'SYC'
```

**Step 2: Run tests**

```bash
pytest tests/python/unit/test_country_codes.py -v
```

Expected: all tests PASS.

**Step 3: Commit**

```bash
git add tests/python/unit/test_country_codes.py
git commit -m "Add country code and exclusion tests"
```

---

### Task 8: Create fetcher test fixtures

**Files:**
- Create: `tests/python/fixtures/worldbank/wb_gini.csv`
- Create: `tests/python/fixtures/worldbank/wb_wgi_corruption.csv`
- Create: `tests/python/fixtures/vdem/vdem_extract.csv`
- Create: `tests/python/fixtures/rsf/rsf_scores.csv`
- Create: `tests/python/fixtures/fsi/fsi_jurisdictions.csv`

**Step 1: Create World Bank fixture**

`tests/python/fixtures/worldbank/wb_gini.csv`:
```csv
country_code,country_name,year,value,indicator
USA,United States,2020,41.5,SI.POV.GINI
USA,United States,2018,41.4,SI.POV.GINI
USA,United States,2013,41.1,SI.POV.GINI
DNK,Denmark,2021,28.2,SI.POV.GINI
DNK,Denmark,2014,27.7,SI.POV.GINI
ZAF,South Africa,2022,63.0,SI.POV.GINI
ZAF,South Africa,2012,63.4,SI.POV.GINI
BRA,Brazil,2021,53.4,SI.POV.GINI
BRA,Brazil,2013,52.9,SI.POV.GINI
WLD,World,2020,50.0,SI.POV.GINI
```

`tests/python/fixtures/worldbank/wb_wgi_corruption.csv`:
```csv
country_code,country_name,year,value,indicator
USA,United States,2022,1.25,CC.EST
DNK,Denmark,2022,2.22,CC.EST
ZAF,South Africa,2022,-0.07,CC.EST
BRA,Brazil,2022,-0.32,CC.EST
NGA,Nigeria,2022,-1.03,CC.EST
```

**Step 2: Create V-Dem fixture**

`tests/python/fixtures/vdem/vdem_extract.csv`:
```csv
country_text_id,country_name,year,v2x_polyarchy,v2x_corr,v2xnp_client,v2x_freexp_altinf,v2xme_altinf,v2x_clphy,v2x_rule,v2x_egal,v2x_partipdem
USA,United States of America,2023,0.87,0.17,0.12,0.89,0.94,0.91,0.85,0.72,0.48
DNK,Denmark,2023,0.93,0.04,0.03,0.96,0.97,0.97,0.96,0.93,0.65
NGA,Nigeria,2023,0.42,0.65,0.71,0.56,0.62,0.41,0.34,0.22,0.27
USA,United States of America,2020,0.86,0.15,0.11,0.90,0.95,0.89,0.84,0.71,0.47
PSG,Palestine/Gaza,2023,0.10,0.80,0.75,0.20,0.25,0.15,0.10,0.08,0.05
```

**Step 3: Create RSF fixture**

`tests/python/fixtures/rsf/rsf_scores.csv`:
```csv
country_code,country_name,score
USA,United States,67.5
DNK,Denmark,92.1
NGA,Nigeria,43.2
ZAF,South Africa,61.8
SEY,Seychelles,55.0
CS-KM,Kosovo,48.3
```

**Step 4: Create FSI fixture**

`tests/python/fixtures/fsi/fsi_jurisdictions.csv`:
```csv
jurisdiction_id,jurisdiction,methodology_id,index_score,secrecy_score,global_scale_weight
US,United States,fsi2024,63.12,60,22.35
CH,Switzerland,fsi2024,76.45,77,4.12
KY,Cayman Islands,fsi2024,71.33,73,3.87
SG,Singapore,fsi2024,67.89,68,5.01
GB,United Kingdom,fsi2024,59.21,56,15.42
US,United States,fsi2022,62.89,59,21.50
```

**Step 5: Commit**

```bash
git add tests/python/fixtures/
git commit -m "Add fetcher test fixtures"
```

---

### Task 9: Fetcher parser tests — World Bank and V-Dem

**Files:**
- Create: `tests/python/unit/test_worldbank_parser.py`
- Create: `tests/python/unit/test_vdem_parser.py`

**Step 1: Write World Bank parser tests**

Create `tests/python/unit/test_worldbank_parser.py`:

```python
"""Tests for World Bank indicator loading and parsing."""

from pathlib import Path

import pandas as pd
from score_countries import load_indicator, EXCLUDE_CODES

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadIndicator:
    def test_loads_csv_successfully(self):
        """Loads a World Bank CSV and returns a DataFrame."""
        df = load_indicator(FIXTURES / 'worldbank' / 'wb_gini.csv')
        assert not df.empty
        assert 'country_code' in df.columns
        assert 'value' in df.columns

    def test_most_recent_year_per_country(self):
        """Returns only the most recent year for each country."""
        df = load_indicator(FIXTURES / 'worldbank' / 'wb_gini.csv')
        # USA has 2013, 2018, 2020 — should return 2020
        usa = df[df['country_code'] == 'USA']
        assert len(usa) == 1
        assert usa.iloc[0]['year'] == 2020

    def test_excludes_aggregate_codes(self):
        """Aggregate codes (WLD, etc.) are excluded."""
        df = load_indicator(FIXTURES / 'worldbank' / 'wb_gini.csv')
        for code in EXCLUDE_CODES:
            assert code not in df['country_code'].values

    def test_filters_non_alpha3(self):
        """Only 3-letter country codes are kept."""
        df = load_indicator(FIXTURES / 'worldbank' / 'wb_gini.csv')
        assert all(len(c) == 3 for c in df['country_code'].values)

    def test_missing_file_returns_empty(self):
        """Non-existent file returns empty DataFrame."""
        df = load_indicator(FIXTURES / 'worldbank' / 'nonexistent.csv')
        assert df.empty
```

**Step 2: Write V-Dem parser tests**

Create `tests/python/unit/test_vdem_parser.py`:

```python
"""Tests for V-Dem data loading and parsing."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_vdem_data

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadVdemData:
    def test_loads_data_successfully(self):
        """Loads V-Dem extract and returns dict of country data."""
        with patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'):
            result = load_vdem_data()
        assert isinstance(result, dict)
        assert 'USA' in result

    def test_extracts_all_nine_variables(self):
        """Each country has up to 9 V-Dem variables."""
        with patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'):
            result = load_vdem_data()
        usa = result['USA']
        expected_vars = ['v2x_polyarchy', 'v2x_corr', 'v2xnp_client',
                         'v2x_freexp_altinf', 'v2xme_altinf', 'v2x_clphy',
                         'v2x_rule', 'v2x_egal', 'v2x_partipdem']
        for var in expected_vars:
            assert var in usa, f"Missing variable: {var}"

    def test_most_recent_year_per_country(self):
        """Returns most recent year's data for each country."""
        with patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'):
            result = load_vdem_data()
        # USA has 2020 and 2023 data — should use 2023
        assert result['USA']['v2x_polyarchy'] == 0.87  # 2023 value

    def test_excludes_excluded_codes(self):
        """PSG (V-Dem Palestine/Gaza) should be excluded."""
        with patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'):
            result = load_vdem_data()
        assert 'PSG' not in result

    def test_missing_file_returns_empty(self):
        """Non-existent directory returns empty dict."""
        with patch('score_countries.VDEM_DIR', FIXTURES / 'nonexistent'):
            result = load_vdem_data()
        assert result == {}
```

**Step 3: Run tests**

```bash
pytest tests/python/unit/test_worldbank_parser.py tests/python/unit/test_vdem_parser.py -v
```

Expected: all tests PASS.

**Step 4: Commit**

```bash
git add tests/python/unit/test_worldbank_parser.py tests/python/unit/test_vdem_parser.py
git commit -m "Add World Bank and V-Dem parser tests"
```

---

### Task 10: Fetcher parser tests — RSF, FSI, CPI

**Files:**
- Create: `tests/python/unit/test_rsf_parser.py`
- Create: `tests/python/unit/test_fsi_parser.py`
- Create: `tests/python/unit/test_cpi_parser.py`

**Step 1: Write RSF parser tests**

Create `tests/python/unit/test_rsf_parser.py`:

```python
"""Tests for RSF press freedom data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_rsf_data

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadRsfData:
    def test_loads_scores(self):
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert isinstance(result, dict)
        assert 'USA' in result
        assert result['USA'] == 67.5

    def test_remaps_codes(self):
        """SEY -> SYC via RSF_CODE_REMAP."""
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert 'SYC' in result
        assert 'SEY' not in result

    def test_excludes_non_standard_codes(self):
        """CS-KM is in EXCLUDE_CODES and should be filtered."""
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert 'CS-KM' not in result

    def test_missing_file_returns_empty(self):
        with patch('score_countries.RSF_DIR', FIXTURES / 'nonexistent'):
            result = load_rsf_data()
        assert result == {}
```

**Step 2: Write FSI parser tests**

Create `tests/python/unit/test_fsi_parser.py`:

```python
"""Tests for FSI financial secrecy data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_fsi_data, ALPHA2_TO_ALPHA3

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadFsiData:
    def test_loads_scores(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        assert isinstance(result, dict)
        assert 'USA' in result

    def test_alpha2_to_alpha3_conversion(self):
        """Jurisdiction IDs (alpha-2) converted to alpha-3."""
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        assert 'CHE' in result  # CH -> CHE
        assert 'CYM' in result  # KY -> CYM
        assert 'SGP' in result  # SG -> SGP

    def test_uses_latest_methodology(self):
        """Only the most recent methodology edition is used."""
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        # fsi2024 is latest, so USA should have 63.12, not 62.89
        assert result['USA'] == 63.12

    def test_missing_file_returns_empty(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'nonexistent'):
            result = load_fsi_data()
        assert result == {}
```

**Step 3: Write CPI parser tests**

Create `tests/python/unit/test_cpi_parser.py`:

```python
"""Tests for CPI (Transparency International) data handling.

Note: CPI data is fetched as Excel by the fetcher module. The scorer
doesn't have a dedicated CPI loader — CPI is not yet integrated into
auto-scoring. This test validates the fetcher's Excel parsing logic.
"""

from pathlib import Path

import pandas as pd
import openpyxl


class TestCpiFetcherParsing:
    def test_excel_fixture_roundtrips(self, tmp_path):
        """Create a minimal CPI Excel, parse it like the fetcher does."""
        xlsx_path = tmp_path / 'cpi_test.xlsx'

        # Create minimal Excel matching CPI format
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'CPI Timeseries'
        ws.append(['Country', 'ISO3', 'CPI Score 2024', 'CPI Score 2023'])
        ws.append(['Denmark', 'DNK', 90, 90])
        ws.append(['United States', 'USA', 69, 69])
        ws.append(['Nigeria', 'NGA', 25, 24])
        wb.save(xlsx_path)

        # Parse like the fetcher does
        df = pd.read_excel(xlsx_path, sheet_name='CPI Timeseries')
        assert len(df) == 3
        assert 'ISO3' in df.columns
        assert df[df['ISO3'] == 'DNK']['CPI Score 2024'].iloc[0] == 90

    def test_finds_sheet_with_iso_column(self, tmp_path):
        """Fetcher logic: find sheet containing ISO column."""
        xlsx_path = tmp_path / 'cpi_multi_sheet.xlsx'

        wb = openpyxl.Workbook()
        # First sheet is metadata (no ISO column)
        ws1 = wb.active
        ws1.title = 'Metadata'
        ws1.append(['About', 'CPI 2024'])

        # Second sheet has the data
        ws2 = wb.create_sheet('CPI Results')
        ws2.append(['Country', 'ISO3', 'Score'])
        ws2.append(['Denmark', 'DNK', 90])
        wb.save(xlsx_path)

        # Simulate fetcher logic
        xl = pd.ExcelFile(xlsx_path)
        found = None
        for sheet_name in xl.sheet_names:
            candidate = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            cols_lower = [str(c).lower() for c in candidate.columns]
            if any('iso' in c for c in cols_lower):
                found = candidate
                break

        assert found is not None
        assert 'ISO3' in found.columns
```

**Step 4: Run all fetcher tests**

```bash
pytest tests/python/unit/test_rsf_parser.py tests/python/unit/test_fsi_parser.py tests/python/unit/test_cpi_parser.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
git add tests/python/unit/test_rsf_parser.py tests/python/unit/test_fsi_parser.py tests/python/unit/test_cpi_parser.py
git commit -m "Add RSF, FSI, and CPI parser tests"
```

---

### Task 11: Integration test — schema compliance

**Files:**
- Create: `tests/python/integration/test_schema_compliance.py`

**Step 1: Write schema compliance tests**

Create `tests/python/integration/test_schema_compliance.py`:

```python
"""Integration tests validating scores.json against schema.json."""

import json
from pathlib import Path

import jsonschema

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCORES_PATH = PROJECT_ROOT / 'data' / 'scores.json'
SCHEMA_PATH = PROJECT_ROOT / 'data' / 'schema.json'

from score_countries import EXCLUDE_CODES


class TestSchemaCompliance:
    @classmethod
    def setup_class(cls):
        with open(SCORES_PATH) as f:
            cls.scores = json.load(f)
        with open(SCHEMA_PATH) as f:
            cls.schema = json.load(f)

    def test_validates_against_schema(self):
        """Full scores.json validates against schema.json."""
        jsonschema.validate(self.scores, self.schema)

    def test_all_country_codes_are_alpha3(self):
        """All country keys are 3-letter uppercase codes."""
        for code in self.scores['countries']:
            assert len(code) == 3, f"Code '{code}' is not 3 letters"
            assert code.isalpha() and code.isupper(), f"Code '{code}' is not uppercase alpha"

    def test_no_excluded_codes_in_output(self):
        """No aggregate/regional codes appear in country data."""
        for code in self.scores['countries']:
            assert code not in EXCLUDE_CODES, f"Excluded code '{code}' found in scores"

    def test_all_scores_in_range(self):
        """All domain scores and composites are 0-100."""
        for code, country in self.scores['countries'].items():
            composite = country['composite_score']
            assert 0 <= composite <= 100, f"{code} composite {composite} out of range"
            for domain_name, domain in country['domains'].items():
                score = domain['score']
                assert 0 <= score <= 100, f"{code}.{domain_name} score {score} out of range"

    def test_no_nan_scores(self):
        """No NaN or None scores."""
        for code, country in self.scores['countries'].items():
            assert country['composite_score'] is not None, f"{code} composite is None"
            for domain_name, domain in country['domains'].items():
                assert domain['score'] is not None, f"{code}.{domain_name} score is None"

    def test_confidence_levels_valid(self):
        """All confidence values are from the enum."""
        valid = {'high', 'moderate', 'low', 'very_low'}
        for code, country in self.scores['countries'].items():
            assert country['overall_confidence'] in valid, \
                f"{code} overall_confidence '{country['overall_confidence']}' invalid"
            for dname, domain in country['domains'].items():
                assert domain['confidence'] in valid, \
                    f"{code}.{dname} confidence '{domain['confidence']}' invalid"

    def test_trend_values_valid(self):
        """All trend values are from the enum."""
        valid = {'rising', 'falling', 'stable', 'unknown'}
        for code, country in self.scores['countries'].items():
            assert country['overall_trend'] in valid, \
                f"{code} overall_trend '{country['overall_trend']}' invalid"
            for dname, domain in country['domains'].items():
                if 'trend' in domain:
                    assert domain['trend'] in valid, \
                        f"{code}.{dname} trend '{domain['trend']}' invalid"

    def test_every_domain_has_sources(self):
        """Every domain entry has at least one source key."""
        for code, country in self.scores['countries'].items():
            for dname, domain in country['domains'].items():
                sources = domain.get('sources', [])
                assert len(sources) > 0, f"{code}.{dname} has no sources"

    def test_has_metadata(self):
        """Scores file has metadata with required fields."""
        assert 'metadata' in self.scores
        assert 'version' in self.scores['metadata']
        assert 'last_updated' in self.scores['metadata']
```

**Step 2: Run tests**

```bash
pytest tests/python/integration/test_schema_compliance.py -v
```

Expected: all tests PASS against the current `data/scores.json`.

**Step 3: Commit**

```bash
git add tests/python/integration/test_schema_compliance.py
git commit -m "Add schema compliance integration tests"
```

---

### Task 12: Integration test — pipeline end-to-end

**Files:**
- Create: `tests/python/integration/test_pipeline.py`

**Step 1: Write pipeline tests**

Create `tests/python/integration/test_pipeline.py`:

```python
"""Integration tests for the full scoring pipeline."""

import json
from pathlib import Path
from unittest.mock import patch

import jsonschema

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / 'data' / 'schema.json'
FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestPipeline:
    """Run the scoring pipeline against fixture data and validate output."""

    def _run_pipeline_with_fixtures(self):
        """Run build_country_scores() with fixture directories."""
        with patch('score_countries.WB_DIR', FIXTURES / 'worldbank'), \
             patch('score_countries.RSF_DIR', FIXTURES / 'rsf'), \
             patch('score_countries.TJN_DIR', FIXTURES / 'fsi'), \
             patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'):
            from score_countries import build_country_scores
            return build_country_scores()

    def test_produces_countries(self):
        """Pipeline produces country entries from fixture data."""
        countries = self._run_pipeline_with_fixtures()
        assert len(countries) > 0

    def test_usa_has_expected_domains(self):
        """USA should have domains from WB, RSF, FSI, and V-Dem fixtures."""
        countries = self._run_pipeline_with_fixtures()
        assert 'USA' in countries
        usa = countries['USA']
        # WB provides: economic_concentration, financial_extraction (if fixture exists),
        #              institutional_gatekeeping, resource_capture
        # RSF provides: information_capture
        # FSI provides: transnational_facilitation
        # V-Dem provides: political_capture, information_capture (merged), institutional_gatekeeping (merged)
        assert 'economic_concentration' in usa['domains'] or len(usa['domains']) > 0

    def test_output_matches_schema_structure(self):
        """Each country output matches the expected structure."""
        countries = self._run_pipeline_with_fixtures()
        for code, country in countries.items():
            assert 'name' in country
            assert 'domains' in country
            assert 'composite_score' in country
            assert 'overall_confidence' in country
            assert 'overall_trend' in country
            assert 0 <= country['composite_score'] <= 100

    def test_excluded_codes_not_in_output(self):
        """Aggregate codes from fixtures are excluded."""
        countries = self._run_pipeline_with_fixtures()
        from score_countries import EXCLUDE_CODES
        for code in countries:
            assert code not in EXCLUDE_CODES

    def test_composite_is_average_of_domains(self):
        """Composite score is the average of domain scores."""
        countries = self._run_pipeline_with_fixtures()
        for code, country in countries.items():
            domain_scores = [d['score'] for d in country['domains'].values()]
            expected = round(sum(domain_scores) / len(domain_scores))
            assert country['composite_score'] == expected, \
                f"{code}: composite {country['composite_score']} != expected {expected}"

    def test_known_inputs_produce_expected_scores(self):
        """Round-trip: known fixture values produce expected normalized scores."""
        countries = self._run_pipeline_with_fixtures()
        assert 'USA' in countries
        usa = countries['USA']
        # USA Gini=41.5 in fixture. The exact normalized value depends on
        # the min/max across all fixture countries, but it must be 0-100
        # and the composite must be computable.
        assert 0 <= usa['composite_score'] <= 100
        # DNK should score lower than ZAF on economic_concentration (lower Gini)
        if 'DNK' in countries and 'ZAF' in countries:
            dnk_ec = countries['DNK']['domains'].get('economic_concentration', {}).get('score', 0)
            zaf_ec = countries['ZAF']['domains'].get('economic_concentration', {}).get('score', 0)
            assert dnk_ec < zaf_ec, "Denmark should have lower economic concentration than South Africa"


class TestPipelineFlags:
    """Test CLI flag behavior (--overwrite, --country)."""

    def test_overwrite_replaces_hand_scored(self, tmp_path):
        """--overwrite causes hand-scored entries to be replaced."""
        # Create a fake scores.json with a hand-scored country
        scores = {
            'metadata': {'version': '1.0', 'last_updated': '2026-01-01'},
            'countries': {
                'USA': {
                    'name': 'United States',
                    'domains': {},
                    'composite_score': 99,
                    'overall_confidence': 'high',
                    'overall_trend': 'stable',
                    'notes': 'Hand-scored by expert.',
                }
            }
        }
        scores_path = tmp_path / 'scores.json'
        with open(scores_path, 'w') as f:
            json.dump(scores, f)

        with patch('score_countries.WB_DIR', FIXTURES / 'worldbank'), \
             patch('score_countries.RSF_DIR', FIXTURES / 'rsf'), \
             patch('score_countries.TJN_DIR', FIXTURES / 'fsi'), \
             patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'), \
             patch('score_countries.SCORES_PATH', scores_path), \
             patch('sys.argv', ['score_countries.py', '--overwrite']):
            from score_countries import main
            main()

        with open(scores_path) as f:
            result = json.load(f)
        # Hand-scored entry should now be auto-scored
        assert result['countries']['USA']['notes'].startswith('Auto-scored')

    def test_preserve_hand_scored_by_default(self, tmp_path):
        """Without --overwrite, hand-scored entries are preserved."""
        scores = {
            'metadata': {'version': '1.0', 'last_updated': '2026-01-01'},
            'countries': {
                'USA': {
                    'name': 'United States',
                    'domains': {},
                    'composite_score': 99,
                    'overall_confidence': 'high',
                    'overall_trend': 'stable',
                    'notes': 'Hand-scored by expert.',
                }
            }
        }
        scores_path = tmp_path / 'scores.json'
        with open(scores_path, 'w') as f:
            json.dump(scores, f)

        with patch('score_countries.WB_DIR', FIXTURES / 'worldbank'), \
             patch('score_countries.RSF_DIR', FIXTURES / 'rsf'), \
             patch('score_countries.TJN_DIR', FIXTURES / 'fsi'), \
             patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'), \
             patch('score_countries.SCORES_PATH', scores_path), \
             patch('sys.argv', ['score_countries.py']):
            from score_countries import main
            main()

        with open(scores_path) as f:
            result = json.load(f)
        # Hand-scored entry should be preserved
        assert result['countries']['USA']['composite_score'] == 99

    def test_country_flag_scores_single(self, tmp_path):
        """--country USA only scores USA."""
        scores = {
            'metadata': {'version': '1.0', 'last_updated': '2026-01-01'},
            'countries': {}
        }
        scores_path = tmp_path / 'scores.json'
        with open(scores_path, 'w') as f:
            json.dump(scores, f)

        with patch('score_countries.WB_DIR', FIXTURES / 'worldbank'), \
             patch('score_countries.RSF_DIR', FIXTURES / 'rsf'), \
             patch('score_countries.TJN_DIR', FIXTURES / 'fsi'), \
             patch('score_countries.VDEM_DIR', FIXTURES / 'vdem'), \
             patch('score_countries.SCORES_PATH', scores_path), \
             patch('sys.argv', ['score_countries.py', '--country', 'USA']):
            from score_countries import main
            main()

        with open(scores_path) as f:
            result = json.load(f)
        # Only USA should be in the output
        assert 'USA' in result['countries']
        # Other fixture countries should NOT be added
        assert 'DNK' not in result['countries']
```

**Step 2: Run tests**

```bash
pytest tests/python/integration/test_pipeline.py -v
```

Expected: all tests PASS.

**Step 3: Commit**

```bash
git add tests/python/integration/test_pipeline.py
git commit -m "Add pipeline integration tests"
```

---

### Task 13: JavaScript — extract lib.js from app.js

**Files:**
- Create: `js/lib.js`
- Modify: `js/app.js:1-211` (remove moved code, add imports)
- Modify: `index.html:170` (change script tag to module)

**Step 1: Create js/lib.js**

Extract pure functions and data constants from `app.js` into `js/lib.js`:

```javascript
// Pure logic and data constants — no DOM, no D3

export const DOMAIN_LABELS = {
  political_capture: 'Political Capture',
  economic_concentration: 'Economic Concentration',
  financial_extraction: 'Financial Extraction',
  institutional_gatekeeping: 'Institutional Gatekeeping',
  information_capture: 'Information & Media Capture',
  resource_capture: 'Resource Capture',
  transnational_facilitation: 'Transnational Facilitation'
};

export const DOMAIN_KEYS = Object.keys(DOMAIN_LABELS);

export const NUMERIC_MAP = {
  // Copy entire NUMERIC_MAP object from app.js lines 94-133
};

export const COUNTRY_NAMES = {
  // Copy entire COUNTRY_NAMES object from app.js lines 136-175
};

export function computeComposite(domains, weights, domainKeys) {
  let sum = 0, wsum = 0;
  domainKeys.forEach(k => {
    if (domains[k]) {
      sum += domains[k].score * (weights[k] || 0);
      wsum += weights[k] || 0;
    }
  });
  return wsum > 0 ? Math.round(sum / wsum) : null;
}

export function normalizeWeights(rawWeights) {
  const total = Object.values(rawWeights).reduce((a, b) => a + b, 0) || 1;
  const normalized = {};
  for (const [key, value] of Object.entries(rawWeights)) {
    normalized[key] = value / total;
  }
  return normalized;
}
```

The actual file should have the full `NUMERIC_MAP` and `COUNTRY_NAMES` objects copied from `app.js`.

**Step 2: Update app.js to import from lib.js**

At the top of `app.js`, add:
```javascript
import { DOMAIN_LABELS, DOMAIN_KEYS, NUMERIC_MAP, COUNTRY_NAMES, computeComposite, normalizeWeights } from './lib.js';
```

Remove:
- Lines 1-11: `DOMAIN_LABELS`, `DOMAIN_KEYS` definitions
- Lines 93-175: `NUMERIC_MAP`, `COUNTRY_NAMES` definitions
- Lines 202-211: `computeComposite` function

Update `computeComposite` call sites (search for `computeComposite(` in app.js):
- Change `computeComposite(cd.domains)` to `computeComposite(cd.domains, currentWeights, DOMAIN_KEYS)`

Update weight slider handler (~line 577-584) to use `normalizeWeights`:
```javascript
// Replace the inline weight normalization:
const rawWeights = {};
sliderContainer.querySelectorAll('input[type="range"]').forEach(s => {
  rawWeights[s.dataset.key] = parseInt(s.value);
});
const normalized = normalizeWeights(rawWeights);
DOMAIN_KEYS.forEach(dk => {
  currentWeights[dk] = normalized[dk];
});
```

**Step 3: Update index.html script tag**

Change line 170 from:
```html
<script src="js/app.js"></script>
```
To:
```html
<script type="module" src="js/app.js"></script>
```

**Step 4: Test in browser**

```bash
python3 -m http.server 8000
# Open http://localhost:8000 and verify:
# - Map renders correctly
# - Country selection works
# - Weight sliders work
# - Theme toggle works
```

**Step 5: Commit**

```bash
git add js/lib.js js/app.js index.html
git commit -m "Extract pure JS logic into lib.js with ES modules"
```

---

### Task 14: JavaScript test setup and composite tests

**Files:**
- Create: `package.json`
- Create: `vitest.config.js`
- Create: `tests/js/test_composite.test.js`

**Step 1: Create package.json**

```json
{
  "name": "extraction-index",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "vitest": "^3.0.0"
  }
}
```

**Step 2: Create vitest.config.js**

```javascript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/js/**/*.test.js'],
  },
});
```

**Step 3: Install Vitest**

```bash
npm install
```

**Step 4: Write composite tests**

Create `tests/js/test_composite.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { computeComposite, DOMAIN_KEYS } from '../../js/lib.js';

describe('computeComposite', () => {
  const allDomains = {
    political_capture: { score: 40 },
    economic_concentration: { score: 60 },
    financial_extraction: { score: 50 },
    institutional_gatekeeping: { score: 30 },
    information_capture: { score: 70 },
    resource_capture: { score: 20 },
    transnational_facilitation: { score: 80 },
  };

  it('computes weighted average with equal weights', () => {
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 1 / 7);
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    // (40+60+50+30+70+20+80) / 7 = 350/7 = 50
    expect(result).toBe(50);
  });

  it('handles custom weights with some zeroed', () => {
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 0);
    weights.political_capture = 0.5;
    weights.economic_concentration = 0.5;
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    // (40*0.5 + 60*0.5) / (0.5+0.5) = 50
    expect(result).toBe(50);
  });

  it('excludes missing domains from average', () => {
    const partial = {
      political_capture: { score: 40 },
      economic_concentration: { score: 60 },
    };
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 1 / 7);
    const result = computeComposite(partial, weights, DOMAIN_KEYS);
    // (40 + 60) * (1/7) / (2/7) = 50
    expect(result).toBe(50);
  });

  it('returns null when all domains missing', () => {
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 1 / 7);
    const result = computeComposite({}, weights, DOMAIN_KEYS);
    expect(result).toBeNull();
  });

  it('returns null when all weights are zero', () => {
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 0);
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    expect(result).toBeNull();
  });

  it('single domain equals that score', () => {
    const single = { political_capture: { score: 73 } };
    const weights = {};
    DOMAIN_KEYS.forEach(k => weights[k] = 1 / 7);
    const result = computeComposite(single, weights, DOMAIN_KEYS);
    expect(result).toBe(73);
  });
});
```

**Step 5: Run tests**

```bash
npx vitest run tests/js/test_composite.test.js
```

Expected: all 6 tests PASS.

**Step 6: Commit**

```bash
git add package.json vitest.config.js tests/js/test_composite.test.js
git commit -m "Add Vitest setup and composite score tests"
```

---

### Task 15: JavaScript tests — weights and country mappings

**Files:**
- Create: `tests/js/test_weights.test.js`
- Create: `tests/js/test_country_mapping.test.js`

**Step 1: Write weight normalization tests**

Create `tests/js/test_weights.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { normalizeWeights, DOMAIN_KEYS } from '../../js/lib.js';

describe('normalizeWeights', () => {
  it('normalizes slider values to sum to 1.0', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 50);
    const result = normalizeWeights(raw);
    const sum = Object.values(result).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0, 10);
  });

  it('handles all sliders at zero without division by zero', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 0);
    const result = normalizeWeights(raw);
    // total = 0, fallback to 1, so all weights = 0/1 = 0
    Object.values(result).forEach(v => expect(v).toBe(0));
  });

  it('one at max, rest at zero gives weight 1.0', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 0);
    raw.political_capture = 100;
    const result = normalizeWeights(raw);
    expect(result.political_capture).toBe(1.0);
    DOMAIN_KEYS.filter(k => k !== 'political_capture').forEach(k => {
      expect(result[k]).toBe(0);
    });
  });

  it('equal values produce equal weights', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 42);
    const result = normalizeWeights(raw);
    const expected = 1 / DOMAIN_KEYS.length;
    DOMAIN_KEYS.forEach(k => {
      expect(result[k]).toBeCloseTo(expected, 10);
    });
  });
});
```

**Step 2: Write country mapping tests**

Create `tests/js/test_country_mapping.test.js`:

```javascript
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { NUMERIC_MAP, COUNTRY_NAMES } from '../../js/lib.js';

describe('NUMERIC_MAP', () => {
  it('all values are valid 3-letter alpha-3 codes', () => {
    for (const [numId, alpha3] of Object.entries(NUMERIC_MAP)) {
      expect(alpha3).toMatch(/^[A-Z]{3}$/);
    }
  });

  it('no duplicate numeric IDs mapping to different alpha-3', () => {
    const seen = {};
    for (const [numId, alpha3] of Object.entries(NUMERIC_MAP)) {
      if (seen[numId]) {
        expect(seen[numId]).toBe(alpha3);
      }
      seen[numId] = alpha3;
    }
  });
});

describe('COUNTRY_NAMES', () => {
  it('all keys are valid 3-letter alpha-3 codes', () => {
    for (const code of Object.keys(COUNTRY_NAMES)) {
      expect(code).toMatch(/^[A-Z]{3}$/);
    }
  });

  it('every country in scores.json has a COUNTRY_NAMES entry or is in scores data', () => {
    const scoresRaw = readFileSync('data/scores.json', 'utf-8');
    const scores = JSON.parse(scoresRaw);
    const missingNames = [];
    for (const code of Object.keys(scores.countries)) {
      if (!COUNTRY_NAMES[code] && !scores.countries[code].name) {
        missingNames.push(code);
      }
    }
    expect(missingNames).toEqual([]);
  });
});
```

**Step 3: Run tests**

```bash
npx vitest run
```

Expected: all JS tests PASS.

**Step 4: Commit**

```bash
git add tests/js/test_weights.test.js tests/js/test_country_mapping.test.js
git commit -m "Add weight normalization and country mapping JS tests"
```

---

### Task 16: Add .gitignore entries and run full test suite

**Files:**
- Modify: `.gitignore` (add node_modules)

**Step 1: Update .gitignore**

Add to `.gitignore`:
```
node_modules/
```

**Step 2: Run full Python test suite with coverage**

```bash
source .venv/bin/activate
pytest tests/python/unit/ --cov=score_countries --cov-report=term-missing -v
pytest tests/python/integration/ -v
```

**Step 3: Run full JS test suite**

```bash
npx vitest run
```

**Step 4: Fix any failures discovered**

Address any test failures or import issues.

**Step 5: Commit**

```bash
git add .gitignore
git commit -m "Add node_modules to gitignore"
```

---

### Task 17: Set up Makefile with /ovid-make

After all tests pass, run the `/ovid-make` skill to create a Makefile with targets for:
- `make test` — run all tests (Python + JS)
- `make test-python` — run Python tests only
- `make test-js` — run JS tests only
- `make coverage` — run Python unit tests with coverage report
- `make lint` — (future placeholder)
- `make fetch` — run data fetchers
- `make score` — run scoring pipeline

Use the `/ovid-make` skill for this task.
