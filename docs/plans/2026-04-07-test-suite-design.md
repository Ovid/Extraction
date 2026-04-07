# Test Suite Design

**Date:** 2026-04-07
**Status:** Approved (updated after pushback review)

## Overview

Add a comprehensive test suite to the Extraction Index project covering the Python
data pipeline (scoring, fetcher parsing, data integrity) and JavaScript visualization
logic (composite scoring, weight normalization, country mappings).

## Decisions

- **Python:** pytest + pytest-cov
- **JavaScript:** Vitest
- **Fetcher tests:** Mock/fixture-based (no network calls)
- **JS architecture:** Extract pure logic into `js/lib.js` (ES modules, no build step)

## Step 0: Refactor for Testability

Before writing tests, extract inline logic from monolithic functions into standalone
pure functions that can be unit tested in isolation.

### Python: `score_countries.py`

The `build_country_scores()` function is ~400 lines with resource capture, merging,
and other logic inline. Extract the following:

1. **`compute_resource_capture(normalized_resource_score, raw_polyarchy)`**
   - Implements: `round(normalized_resource_score * (100 - round(raw_polyarchy * 100)) / 100)`
   - Returns composite score
   - When `raw_polyarchy` is None, returns `normalized_resource_score` unchanged

2. **`merge_domain_scores(domain_a, domain_b)`**
   - Averages scores from two sources for the same domain
   - Merges indicator and source lists (no duplicates)
   - Recalculates confidence from combined totals

3. **`estimate_trend(data, inverted=False)`** (refactor existing)
   - Currently reads CSVs from disk via hardcoded `WB_DIR` path
   - Refactor to accept a DataFrame or series of (year, value) pairs
   - Remove unused `df_full` parameter
   - Keep a thin wrapper for the file-reading call site

### JavaScript: `app.js` -> `lib.js` extraction

1. **`computeComposite(domains, weights, domainKeys)`** (signature change)
   - Currently reads `currentWeights` and `DOMAIN_KEYS` from closure
   - Extract as a pure function accepting all three as parameters
   - Update all call sites in `app.js` to pass `currentWeights` and `DOMAIN_KEYS`

2. **`normalizeWeights(sliderValues)`** (new function)
   - Currently inline in slider event handler (divides each value by sum)
   - Extract as a pure function: takes array/object of slider values, returns normalized weights
   - Update slider handler to call this function

3. **Move data constants** to `lib.js`:
   - `NUMERIC_MAP`
   - `COUNTRY_NAMES`
   - `DOMAIN_KEYS`
   - `DOMAIN_LABELS`

4. **ES module switch:**
   - Change `<script src="js/app.js">` to `<script type="module" src="js/app.js">`
   - `lib.js` uses `export`, `app.js` uses `import`
   - No bundler needed — browsers support ES modules natively

## Directory Structure

```
tests/
├── python/
│   ├── unit/
│   │   ├── conftest.py                # Shared fixtures (factory functions, sample data)
│   │   ├── test_normalization.py      # Min-max scaling, inversion, edge cases
│   │   ├── test_confidence.py         # 3-factor confidence + domain coverage cap
│   │   ├── test_trends.py            # Rising/falling/stable thresholds
│   │   ├── test_peer_comparisons.py   # Region/income grouping, divergence threshold
│   │   ├── test_resource_capture.py   # Composite formula, V-Dem fallback
│   │   ├── test_merging.py           # Multi-source domain averaging
│   │   ├── test_country_codes.py      # Code remapping, exclusion filtering
│   │   ├── test_worldbank_parser.py   # World Bank CSV parsing
│   │   ├── test_vdem_parser.py        # V-Dem extract parsing
│   │   ├── test_rsf_parser.py         # RSF GeoJSON parsing
│   │   ├── test_fsi_parser.py         # FSI JSON parsing
│   │   └── test_cpi_parser.py         # CPI Excel parsing
│   ├── integration/
│   │   ├── test_schema_compliance.py  # scores.json vs schema.json
│   │   └── test_pipeline.py           # End-to-end: fixtures -> score -> validate
│   └── fixtures/
│       ├── worldbank/                 # Sample CSV responses
│       ├── vdem/                      # Sample extract CSV
│       ├── rsf/                       # Sample GeoJSON
│       └── fsi/                       # Sample API JSON
├── js/
│   ├── test_composite.test.js         # computeComposite() logic
│   ├── test_weights.test.js           # normalizeWeights() logic
│   └── test_country_mapping.test.js   # NUMERIC_MAP / COUNTRY_NAMES consistency
```

## Python Unit Tests

### test_normalization.py
- Normal case: known values scale to expected 0-100 range
- Inversion: democracy/rule-of-law indicators flip correctly
- Edge cases: all identical values (should return 50), single value, negative values
- Empty dataset: no crash

### test_confidence.py
- Each factor (completeness, source diversity, recency) scores 0-3
- Total 0-9 maps to correct label: high (7+), moderate (5-6), low (3-4), very_low (0-2)
- Domain coverage cap: <=3 domains -> max "low", <=5 -> max "moderate"
- Boundary cases: exactly 3, 5, and 7 domains

### test_trends.py
- >=10% increase -> "rising"
- >=10% decrease -> "falling"
- <10% change -> "stable"
- Missing old or recent data -> "unknown"
- Boundary: exactly 10% change
- Tests against the refactored pure function (accepts data, not file paths)

### test_peer_comparisons.py
- Country correctly assigned to region and income group
- Divergence >10% from peer average -> fact generated
- Divergence <=10% -> no fact
- Country with no peers -> handled gracefully

### test_resource_capture.py
- Formula: `round(normalized_resource_score * (100 - round(raw_polyarchy * 100)) / 100)`
- With V-Dem data: correct composite
- Without V-Dem (raw_polyarchy=None): returns normalized score unchanged, confidence capped at "low"
- Zero resource rents -> zero score
- Tests against extracted `compute_resource_capture()` function

### test_merging.py
- Two sources for same domain -> scores averaged
- Indicators and source lists merged (no duplicates)
- Confidence recalculated from combined totals
- Single source -> no change
- Tests against extracted `merge_domain_scores()` function

### test_country_codes.py
- EXCLUDE_CODES entries never in output
- COUNTRY_NAME_OVERRIDES applied correctly
- ALPHA2_TO_ALPHA3 covers all FSI codes
- Invalid/unknown codes skipped

### Fetcher Parser Tests (one file per fetcher)

#### test_worldbank_parser.py
- Multi-indicator CSV parsing, missing values, year filtering
- Fixture: small CSV with ~5 countries, 3 years, including gaps

#### test_vdem_parser.py
- 9 variables extracted, most recent year per country, missing variable handling
- Fixture: subset CSV with ~5 countries, mixed year coverage

#### test_rsf_parser.py
- GeoJSON parsing, non-standard code remapping
- Fixture: GeoJSON with ~5 features including non-standard code

#### test_fsi_parser.py
- JSON parsing, alpha-2 to alpha-3 conversion
- Fixture: sample CSV with ~5 jurisdictions

#### test_cpi_parser.py
- Excel parsing (programmatically generated fixture via openpyxl)

## Python Integration Tests

### test_schema_compliance.py
- Validates real data/scores.json against data/schema.json
- All scores 0-100, no NaN/null
- Confidence and trend values match enums
- Every domain has at least one source key
- No excluded codes in output

### test_pipeline.py
- Runs scoring pipeline end-to-end with fixture data
- Verifies output structure matches schema
- Known inputs produce expected scores (round-trip)
- --overwrite flag behavior (hand-scored preservation)
- --country flag (single country scoring)

## JavaScript Tests (Vitest)

### test_composite.test.js
- Equal weights across 7 domains
- Custom weights with some zeroed out
- Missing domains excluded (not zero)
- All domains missing -> graceful handling (returns null)
- Single domain -> composite equals that score
- Tests the pure `computeComposite(domains, weights, domainKeys)` signature

### test_weights.test.js
- Slider values normalize to sum 1.0
- All sliders at 0 -> no division by zero
- One at max, rest at 0 -> weight 1.0
- Reset -> equal weights
- Tests the new `normalizeWeights(sliderValues)` function extracted from inline handler

### test_country_mapping.test.js
- All NUMERIC_MAP values are valid 3-letter alpha-3
- No duplicate numeric IDs
- Every scores.json country has COUNTRY_NAMES entry
- COUNTRY_NAMES keys are valid alpha-3

## Fixtures Strategy

- Static files for fetcher parsers (small CSV/JSON/GeoJSON, committed)
- Factory fixtures in conftest.py for scoring (controllable parameters)
- No binary fixtures — CPI Excel generated via openpyxl in pytest fixture
- JS tests: inline sample data, cross-check against scores.json via fs

## Dependencies

**Python** (add to scripts/requirements.txt):
- pytest
- pytest-cov
- jsonschema

**JavaScript** (new package.json at project root):
- vitest (dev dependency)

## Post-Implementation

- Use /ovid-make to create Makefile with test/coverage targets
