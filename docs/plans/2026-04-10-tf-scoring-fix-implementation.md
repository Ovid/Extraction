# Transnational Facilitation Scoring Fix — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Switch TF domain scoring from FSI Value (secrecy × volume) to FSI secrecy score used raw (no min-max normalization), keeping FSI Value as a displayed context fact.

**Architecture:** Change the normalization/scoring path in `score_countries.py` so the secrecy score becomes the domain score. The FSI Value remains as a context fact. Add a new `tjn_fsi_secrecy` indicator key for the secrecy score. Update METHODOLOGY.md to document the change.

**Tech Stack:** Python (pandas), pytest, existing scoring pipeline

**Design doc:** `docs/plans/2026-04-10-tf-scoring-fix-design.md`

---

### Task 1: Add indicator metadata for the secrecy score

**Requirement:** Design §Change — new `tjn_fsi_secrecy` indicator key needs question and display config.

**Files:**
- Modify: `scripts/score_countries.py:102-126` (INDICATOR_QUESTIONS)
- Modify: `scripts/score_countries.py:278-283` (INDICATOR_DISPLAY)

#### RED

Write no test — this is pure config. The test in Task 2 will exercise it.

#### GREEN

**Step 1: Add `tjn_fsi_secrecy` to INDICATOR_QUESTIONS**

In `INDICATOR_QUESTIONS` dict (line ~125), add after the existing `tjn_fsi` entry:

```python
    "tjn_fsi_secrecy": "How much financial secrecy do this jurisdiction's laws enable?",
```

**Step 2: Add INDICATOR_DISPLAY entry for `tjn_fsi_secrecy`**

After the existing `tjn_fsi` entry in `INDICATOR_DISPLAY` (line ~283), add:

```python
    "tjn_fsi_secrecy": {
        "label": "Financial secrecy score",
        "format": "{:.0f}",
        "unit": "out of 100",
        "comparison_label": ["Most secretive among", "Least secretive among"],
    },
```

#### REFACTOR

Nothing to refactor — two dict entries added.

**Step 3: Commit**

```bash
git add scripts/score_countries.py
git commit -m "feat: add tjn_fsi_secrecy indicator metadata"
```

---

### Task 2: Write failing tests for secrecy-score-based TF scoring

**Requirement:** Design §Change — TF domain score must equal rounded raw secrecy score, not normalized FSI Value. Needs both a data availability test and an integration test.

**Files:**
- Modify: `tests/python/unit/test_fsi_parser.py`

#### RED

**Step 1: Write two tests**

Add to the end of `test_fsi_parser.py`:

```python
class TestFsiSecrecyScoring:
    """Tests that TF domain uses secrecy score (raw, no min-max) not FSI Value."""

    def test_all_countries_have_secrecy_score(self):
        """Every country returned by load_fsi_data must include a secrecy score."""
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        for code in result:
            assert "secrecy" in result[code], f"{code} missing secrecy score"

    def test_tf_domain_score_equals_rounded_secrecy(self):
        """The TF domain score should be the rounded raw secrecy score, not normalized FSI Value.

        USA fixture has secrecy=63.12 and FSI Value=1900.2. If the scoring
        still uses FSI Value with min-max normalization, the score will be ~100
        (highest in the dataset). If it correctly uses raw secrecy, it will be 63.
        """
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            fsi_data = load_fsi_data()

        # Build secrecy map the same way the scoring pipeline does
        fsi_secrecy = {k: v.get("secrecy") for k, v in fsi_data.items()}

        # USA secrecy is 63.12 in fixture -> rounded to 63
        assert fsi_secrecy["USA"] == 63.12
        assert int(round(fsi_secrecy["USA"])) == 63

        # Verify it's NOT the FSI Value (which would normalize to ~100)
        assert fsi_data["USA"]["value"] == 1900.2  # FSI Value is much higher
        assert int(round(fsi_secrecy["USA"])) < 70  # Secrecy score is moderate
```

**Step 2: Run tests to verify the first passes and second passes (data-level test)**

```bash
cd scripts && python -m pytest ../tests/python/unit/test_fsi_parser.py::TestFsiSecrecyScoring -v
```

Expected: Both PASS — they test data loading, not the scoring path. The real
verification that the scoring pipeline uses secrecy scores will come from the
Task 4 spot-check and the `make all` run.

#### GREEN

No implementation needed yet — these tests validate the data contract that
Task 3 will rely on.

#### REFACTOR

Nothing to refactor.

**Step 3: Commit**

```bash
git add tests/python/unit/test_fsi_parser.py
git commit -m "test: add secrecy score data contract tests for TF scoring"
```

---

### Task 3: Switch TF scoring from FSI Value to secrecy score

**Requirement:** Design §Change — core scoring change. Three locations in `score_countries.py` plus a docstring update.

**Files:**
- Modify: `scripts/score_countries.py:1183-1188` (load_fsi_data docstring)
- Modify: `scripts/score_countries.py:1728-1739` (FSI normalization setup)
- Modify: `scripts/score_countries.py:1780` (all_indicator_raw population)
- Modify: `scripts/score_countries.py:1859-1881` (per-country TF domain assembly)

#### RED

Tests from Task 2 already define the expected behavior. The spot-check in
Task 4 will serve as the integration-level verification.

#### GREEN

**Step 1: Update `load_fsi_data()` docstring (line 1184-1188)**

Replace:

```python
    """Load FSI data. Returns dict of {alpha3: {'value': fsi_value, 'secrecy': secrecy_score}}.

    Uses index_value (TJN's composite of secrecy laws × offshore finance volume)
    as the primary scoring indicator. Also returns index_score (secrecy-only)
    for display as a context fact.
    """
```

With:

```python
    """Load FSI data. Returns dict of {alpha3: {'value': fsi_value, 'secrecy': secrecy_score}}.

    The secrecy score (index_score) is the primary scoring indicator — used raw
    (no min-max normalization) as the TF domain score. The FSI Value (index_value)
    is retained as a displayed context fact only.
    """
```

**Step 2: Simplify FSI normalization setup (lines 1728-1739)**

Replace:

```python
    # Load FSI data (transnational_facilitation) — uses FSI Value (secrecy × volume)
    fsi_data = load_fsi_data()
    if fsi_data:
        print(f"  FSI: {len(fsi_data)} countries")
        fsi_value_series = pd.Series({k: v["value"] for k, v in fsi_data.items()})
        fsi_normalized = normalize_minmax(fsi_value_series, inverted=False)  # Linear, no log
        fsi_map = dict(zip(fsi_value_series.index, fsi_normalized))
        fsi_secrecy = {k: v.get("secrecy") for k, v in fsi_data.items()}
    else:
        fsi_data = {}
        fsi_map = {}
        fsi_secrecy = {}
```

With:

```python
    # Load FSI data (transnational_facilitation) — uses secrecy score (raw, not normalized)
    fsi_data = load_fsi_data()
    if fsi_data:
        print(f"  FSI: {len(fsi_data)} countries")
        fsi_secrecy = {k: v.get("secrecy") for k, v in fsi_data.items()}
    else:
        fsi_data = {}
        fsi_secrecy = {}
```

**Step 3: Add `tjn_fsi_secrecy` to `all_indicator_raw` (around line 1780)**

Find:

```python
    if fsi_data:
        all_indicator_raw["tjn_fsi"] = {k: v["value"] for k, v in fsi_data.items()}
```

Replace with:

```python
    if fsi_data:
        all_indicator_raw["tjn_fsi"] = {k: v["value"] for k, v in fsi_data.items()}
        all_indicator_raw["tjn_fsi_secrecy"] = {k: v["secrecy"] for k, v in fsi_data.items() if v.get("secrecy") is not None}
```

Note: `tjn_fsi` is kept because it populates FSI Value context facts via
`generate_context_facts`. `tjn_fsi_secrecy` is added for the new primary
indicator's peer comparison facts.

**Step 4: Rewrite per-country TF domain assembly (lines 1859-1881)**

Replace:

```python
        # Add FSI (transnational_facilitation) — FSI Value (secrecy × volume)
        if code in fsi_map:
            raw_value = fsi_data[code]["value"]
            fsi_confidence = assess_domain_confidence(1, 1, 2025)
            fsi_norm = int(fsi_map[code])
            fsi_entry = build_indicator_entry("tjn_fsi", raw_value, fsi_norm, code, all_indicator_raw)
            # Add secrecy score as an extra context fact
            secrecy = fsi_secrecy.get(code)
            if secrecy is not None and fsi_entry.get("facts") is not None:
                fsi_entry["facts"].append(f"Financial secrecy score: {secrecy:.0f} out of 100")
            fsi_ind = [{"name": "FSI Value", "raw": raw_value, "normalized": fsi_norm}]
            domains["transnational_facilitation"] = {
                "score": fsi_norm,
                "confidence": fsi_confidence,
                "trend": "unknown",
                "sources": ["tjn_fsi"],
                "indicators": [fsi_entry],
                "justification_detail": build_technical_justification("Tax Justice Network FSI", fsi_ind),
                "_n_indicators": 1,
                "_n_sources": 1,
                "_most_recent_year": 2025,
            }
            source_names.append("TJN")
```

With:

```python
        # Add FSI (transnational_facilitation) — secrecy score (raw, no normalization)
        secrecy = fsi_secrecy.get(code)
        if secrecy is not None:
            secrecy_rounded = int(round(secrecy))
            fsi_confidence = assess_domain_confidence(1, 1, 2025)
            # Primary indicator: secrecy score (used for domain score)
            secrecy_entry = build_indicator_entry(
                "tjn_fsi_secrecy", secrecy, secrecy_rounded, code, all_indicator_raw
            )
            # Context fact: FSI Value (secrecy × volume) for analysts
            fsi_value = fsi_data[code].get("value")
            if fsi_value is not None and secrecy_entry.get("facts") is not None:
                secrecy_entry["facts"].append(f"FSI Value (secrecy × scale): {fsi_value:.0f}")
            fsi_ind = [{"name": "Financial secrecy score", "raw": secrecy, "normalized": secrecy_rounded}]
            domains["transnational_facilitation"] = {
                "score": secrecy_rounded,
                "confidence": fsi_confidence,
                "trend": "unknown",
                "sources": ["tjn_fsi"],
                "indicators": [secrecy_entry],
                "justification_detail": build_technical_justification("Tax Justice Network FSI", fsi_ind),
                "_n_indicators": 1,
                "_n_sources": 1,
                "_most_recent_year": 2025,
            }
            source_names.append("TJN")
```

**Step 5: Run tests**

```bash
cd scripts && python -m pytest ../tests/python/unit/ -v
```

Expected: All pass.

#### REFACTOR

Check: is `fsi_map` still referenced anywhere after removal? Search for
`fsi_map` — if any remaining references exist, the test run in Step 5 will
catch them as NameError. No manual refactoring expected.

**Step 6: Commit**

```bash
git add scripts/score_countries.py
git commit -m "feat: switch TF scoring from FSI Value to secrecy score (raw)"
```

---

### Task 4: Regenerate scores.json and spot-check

**Requirement:** Design §Validation — regenerate and verify key countries match expected values from real data.

**Files:**
- Modify: `data/scores.json` (regenerated)

#### RED

No test — this is a pipeline run with manual verification.

#### GREEN

**Step 1: Regenerate scores**

```bash
cd scripts && source ../.venv/bin/activate && python score_countries.py
```

**Step 2: Spot-check key countries against real-data expected values**

```bash
cd scripts && python3 -c "
import json
with open('../data/scores.json') as f:
    data = json.load(f)
countries = data['countries']
expected = {'USA': 69, 'CHE': 75, 'PAN': 78, 'CYM': 73, 'DNK': 39}
all_ok = True
for code, exp in expected.items():
    tf = countries[code]['domains']['transnational_facilitation']
    actual = tf['score']
    ok = 'OK' if abs(actual - exp) <= 3 else 'MISMATCH'
    if ok == 'MISMATCH':
        all_ok = False
    print(f'{code}: expected ~{exp}, got {actual} [{ok}]')
    # Verify FSI Value is still in facts
    facts = tf['indicators'][0].get('facts', [])
    has_fsi = any('FSI Value' in f for f in facts)
    print(f'  FSI Value context fact: {\"present\" if has_fsi else \"MISSING\"}')
# Structural checks
usa_tf = countries['USA']['domains']['transnational_facilitation']['score']
pan_tf = countries['PAN']['domains']['transnational_facilitation']['score']
assert usa_tf < 100, f'USA should not be 100, got {usa_tf}'
assert pan_tf > usa_tf, f'Panama ({pan_tf}) should score higher than USA ({usa_tf})'
print()
print('All structural checks passed' if all_ok else 'SOME MISMATCHES — review above')
"
```

Expected: All within ±3 of expected, FSI Value context fact present, USA < 100,
Panama > USA.

#### REFACTOR

Nothing to refactor.

**Step 3: Commit**

```bash
git add data/scores.json
git commit -m "data: regenerate scores with secrecy-score-based TF domain"
```

---

### Task 5: Update METHODOLOGY.md

**Requirement:** Design §Additional Changes — document TF indicator switch and political capture limitations.

**Files:**
- Modify: `METHODOLOGY.md:124-132` (Transnational Facilitation section)
- Modify: `METHODOLOGY.md:25` (Political Capture section — add limitation)

#### RED

No test — documentation only.

#### GREEN

**Step 1: Rewrite the Transnational Facilitation section**

Replace lines 124-132:

```markdown
### 7. Transnational Facilitation

Enabling extraction elsewhere through financial secrecy, tax havens, and profit shifting.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Financial Secrecy Index | Tax Justice Network | (composite score) | Direct |

Domain score = normalized indicator score.
```

With:

```markdown
### 7. Transnational Facilitation

Enabling extraction elsewhere through financial secrecy, tax havens, and profit shifting.

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Financial Secrecy Score | Tax Justice Network | index_score | Direct (raw, not min-max normalized) |

Domain score = raw secrecy score (TJN's 0-100 scale, used without min-max normalization).

**Why the secrecy score, not the FSI Value:**

The TJN Financial Secrecy Index publishes two measures per jurisdiction:

- **Secrecy score** (0-100): how much secrecy a jurisdiction's laws and regulations enable, based on ~20 indicators of financial transparency. Measures *policy choice*.
- **FSI Value** (secrecy × global scale weight): how much total global financial secrecy this jurisdiction facilitates, accounting for the size of its financial sector. Measures *total impact*.

Earlier versions of this index used FSI Value with min-max normalization. This produced distorted results: the United States scored 100 (the maximum) while the Cayman Islands scored 25 and Panama scored 29. The distortion arose because FSI Value conflates economic scale with secrecy policy — the US has the world's largest financial sector, so even moderate secrecy laws produce a large FSI Value. Min-max normalization then mapped this outlier to 100, compressing all other countries.

The secrecy score measures what the extraction index cares about: structural choices that enable financial secrecy. It is used raw (without min-max normalization) because it is already on a 0-100 scale consistent with the index's convention, and because its empirical range (29-80) reflects TJN's considered assessment that no jurisdiction is at either extreme.

The FSI Value is retained as a displayed context fact for each country, so analysts can still see the scale-adjusted impact measure.

**Limitations:**

- **Scale is not captured in the score.** The US facilitates more total secrecy than Bermuda by virtue of its financial sector size, but this is not reflected in the domain score. The FSI Value context fact partially compensates.
- **Single-source dependency.** This domain relies entirely on TJN's Financial Secrecy Index. Adding complementary indicators (e.g., FATF compliance, beneficial ownership transparency, tax treaty network quality) would improve construct validity.
- **Secrecy score range is narrow.** TJN's secrecy scores cluster between 50-75 for most countries, limiting the domain's ability to discriminate in the middle of the distribution.
```

**Step 2: Add known limitation to Political Capture section**

After the Political Capture indicator table and "Domain score = mean of normalized indicator scores." line (around line 25), add:

```markdown
**Known limitations:**

- V-Dem measures formal democratic quality well but systematically underweights legal capture mechanisms — campaign finance deregulation (e.g., Citizens United in the US), lobbying industry scale, and revolving door dynamics — that are the primary mode of political capture in advanced democracies. Countries with strong electoral democracy but weak regulation of money in politics may have understated scores.
```

#### REFACTOR

Nothing to refactor.

**Step 3: Commit**

```bash
git add METHODOLOGY.md
git commit -m "docs: update methodology for secrecy score TF and political capture limitations"
```

---

### Task 6: Run `make all` and verify

**Requirement:** Design §Validation and CLAUDE.md Definition of Done — zero errors from `make all`.

**Step 1: Run full validation**

```bash
make all
```

Expected: All Python tests pass, all JS tests pass, zero errors.

**Step 2: If any tests fail, fix them**

The most likely failure is in `tests/python/unit/test_fsi_parser.py` or
other tests that check for specific FSI Value-based scoring. Fix by
updating expectations to match secrecy-score-based scoring.

**Step 3: Final commit (if any fixes needed)**

```bash
git add -u
git commit -m "fix: update test expectations for secrecy-score-based TF"
```
