# Coverage Refactoring: Extract Testable Functions from `build_country_scores()`

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Increase unit test coverage of `score_countries.py` from 40% by extracting 5 logic-dense blocks from the 400-line `build_country_scores()` orchestrator into standalone functions with unit tests.

**Architecture:** Pure refactoring — extract functions, replace inline code with calls, add tests. `build_country_scores()` remains the orchestrator; it just delegates to named helpers. No behavior changes.

**Tech Stack:** Python, pandas, pytest (with `--cov`)

---

### Task 1: Extract `cap_confidence_by_coverage`

The simplest extraction — a pure function with no dependencies beyond a dict lookup.

**Files:**
- Modify: `scripts/score_countries.py` (extract from lines ~1687-1698)
- Create: `tests/python/unit/test_cap_confidence.py`

**Step 1: Write the failing test**

Create `tests/python/unit/test_cap_confidence.py`:

```python
"""Tests for confidence capping by domain coverage."""

from score_countries import cap_confidence_by_coverage


class TestCapConfidenceByCoverage:
    def test_few_domains_caps_at_low(self):
        """3 or fewer domains -> cap at 'low'."""
        assert cap_confidence_by_coverage("high", 3) == "low"
        assert cap_confidence_by_coverage("moderate", 2) == "low"
        assert cap_confidence_by_coverage("low", 1) == "low"

    def test_medium_domains_caps_at_moderate(self):
        """4-5 domains -> cap at 'moderate'."""
        assert cap_confidence_by_coverage("high", 5) == "moderate"
        assert cap_confidence_by_coverage("high", 4) == "moderate"

    def test_many_domains_allows_high(self):
        """6+ domains -> no cap."""
        assert cap_confidence_by_coverage("high", 6) == "high"
        assert cap_confidence_by_coverage("high", 7) == "high"

    def test_already_below_cap_unchanged(self):
        """If confidence is already below cap, return unchanged."""
        assert cap_confidence_by_coverage("very_low", 3) == "very_low"
        assert cap_confidence_by_coverage("low", 5) == "low"

    def test_very_low_never_raised(self):
        """Capping never raises confidence."""
        assert cap_confidence_by_coverage("very_low", 7) == "very_low"
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_cap_confidence.py -v`
Expected: ImportError — `cap_confidence_by_coverage` doesn't exist yet.

**Step 3: Extract the function**

In `scripts/score_countries.py`, add this function after `compute_resource_capture` (~line 1231):

```python
def cap_confidence_by_coverage(confidence, n_domains):
    """Cap overall confidence based on how many of the 7 domains have data.

    <=3 domains: cap at 'low'
    <=5 domains: cap at 'moderate'
    6+  domains: cap at 'high' (no effective cap)
    """
    if n_domains <= 3:
        conf_cap = "low"
    elif n_domains <= 5:
        conf_cap = "moderate"
    else:
        conf_cap = "high"
    conf_rank = {"very_low": 0, "low": 1, "moderate": 2, "high": 3}
    if conf_rank[confidence] > conf_rank[conf_cap]:
        return conf_cap
    return confidence
```

Then in `build_country_scores()`, replace the inline block (lines ~1687-1698) with:

```python
        overall_confidence = cap_confidence_by_coverage(overall_confidence, n_domains)
```

Remove the old inline code (the `if n_domains <= 3:` block through `overall_confidence = conf_cap`).

**Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_cap_confidence.py -v`
Expected: All 5 tests PASS.

**Step 5: Run full test suite to verify no regressions**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: All existing tests still pass.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_cap_confidence.py
git commit -m "refactor: extract cap_confidence_by_coverage from build_country_scores"
```

---

### Task 2: Extract `assemble_country_entry`

Depends on Task 1 (`cap_confidence_by_coverage`). Handles composite score, overall confidence, overall trend, cleaning internal fields.

**Files:**
- Modify: `scripts/score_countries.py` (extract from lines ~1680-1727)
- Create: `tests/python/unit/test_assemble_country.py`

**Step 1: Write the failing test**

Create `tests/python/unit/test_assemble_country.py`:

```python
"""Tests for country entry assembly."""

from score_countries import assemble_country_entry


def _make_domain(score, trend="unknown", n_indicators=1, n_sources=1, most_recent_year=2023):
    """Helper to build a minimal domain dict with internal tracking fields."""
    return {
        "score": score,
        "confidence": "moderate",
        "trend": trend,
        "sources": ["test_src"],
        "indicators": [],
        "justification_detail": "test",
        "_n_indicators": n_indicators,
        "_n_sources": n_sources,
        "_most_recent_year": most_recent_year,
    }


class TestAssembleCountryEntry:
    def test_composite_is_average_of_domains(self):
        domains = {
            "political_capture": _make_domain(80),
            "economic_concentration": _make_domain(40),
        }
        result = assemble_country_entry("Testland", domains, ["Source A"])
        assert result["composite_score"] == 60

    def test_composite_rounds(self):
        domains = {
            "a": _make_domain(33),
            "b": _make_domain(33),
            "c": _make_domain(34),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["composite_score"] == 33  # (33+33+34)/3 = 33.33 -> 33

    def test_overall_trend_majority_vote(self):
        domains = {
            "a": _make_domain(50, trend="rising"),
            "b": _make_domain(50, trend="rising"),
            "c": _make_domain(50, trend="falling"),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["overall_trend"] == "rising"

    def test_overall_trend_all_unknown(self):
        domains = {
            "a": _make_domain(50, trend="unknown"),
            "b": _make_domain(50, trend="unknown"),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["overall_trend"] == "unknown"

    def test_internal_fields_cleaned(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Testland", domains, ["S"])
        domain = result["domains"]["a"]
        assert "_n_indicators" not in domain
        assert "_n_sources" not in domain
        assert "_most_recent_year" not in domain

    def test_confidence_capped_by_domain_count(self):
        """With only 2 domains, confidence should be capped at 'low'."""
        domains = {
            "a": _make_domain(50, n_indicators=5, n_sources=3, most_recent_year=2024),
            "b": _make_domain(50, n_indicators=5, n_sources=3, most_recent_year=2024),
        }
        result = assemble_country_entry("Testland", domains, ["S1", "S2", "S3"])
        assert result["overall_confidence"] == "low"

    def test_notes_include_source_names_and_count(self):
        domains = {
            "a": _make_domain(50),
            "b": _make_domain(50),
        }
        result = assemble_country_entry("Testland", domains, ["World Bank", "V-Dem"])
        assert "V-Dem" in result["notes"]
        assert "World Bank" in result["notes"]
        assert "2/7 domains" in result["notes"]

    def test_name_preserved(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["name"] == "Testland"
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_assemble_country.py -v`
Expected: ImportError — `assemble_country_entry` doesn't exist yet.

**Step 3: Extract the function**

In `scripts/score_countries.py`, add after `cap_confidence_by_coverage`:

```python
def assemble_country_entry(name, domains, source_names):
    """Assemble the final country dict from scored domains.

    Computes composite score (average), overall confidence (with domain-coverage cap),
    overall trend (majority vote), cleans internal tracking fields, and builds notes.
    """
    # Compute overall confidence from totals across all domains
    total_indicators = sum(d.get("_n_indicators", 1) for d in domains.values())
    total_sources = len(set(source_names))
    all_years = [d.get("_most_recent_year") for d in domains.values() if d.get("_most_recent_year")]
    overall_most_recent = max(all_years) if all_years else None
    overall_confidence = assess_domain_confidence(total_indicators, total_sources, overall_most_recent)

    # Cap confidence by domain coverage
    overall_confidence = cap_confidence_by_coverage(overall_confidence, len(domains))

    # Clean internal tracking fields from domain entries
    for d in domains.values():
        d.pop("_n_indicators", None)
        d.pop("_n_sources", None)
        d.pop("_most_recent_year", None)

    # Composite: average of available domains
    scores = [d["score"] for d in domains.values()]
    composite = round(sum(scores) / len(scores))

    # Overall trend: majority vote
    trends = [d["trend"] for d in domains.values() if d["trend"] != "unknown"]
    if trends:
        overall_trend = Counter(trends).most_common(1)[0][0]
    else:
        overall_trend = "unknown"

    unique_sources = sorted(set(source_names))
    return {
        "name": name,
        "domains": domains,
        "composite_score": composite,
        "overall_confidence": overall_confidence,
        "overall_trend": overall_trend,
        "notes": f"Auto-scored from {', '.join(unique_sources)} ({len(domains)}/7 domains covered).",
    }
```

Then in `build_country_scores()`, replace lines ~1680-1727 (from `# Compute overall confidence` through the end of the `countries[code] = {…}` block) with:

```python
        countries[code] = assemble_country_entry(name, domains, source_names)
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_assemble_country.py tests/python/unit/test_cap_confidence.py -v`
Expected: All PASS.

**Step 5: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: No regressions.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_assemble_country.py
git commit -m "refactor: extract assemble_country_entry from build_country_scores"
```

---

### Task 3: Extract `apply_resource_moderation`

The most complex extraction — handles two branches (with/without V-Dem polyarchy), rebuilds indicators, caps confidence.

**Files:**
- Modify: `scripts/score_countries.py` (extract from lines ~1624-1678)
- Create: `tests/python/unit/test_resource_moderation.py`

**Step 1: Write the failing test**

Create `tests/python/unit/test_resource_moderation.py`:

```python
"""Tests for resource capture moderation by democratic accountability."""

from score_countries import apply_resource_moderation


def _make_resource_domain(score, confidence="moderate", facts=None):
    """Build a minimal resource_capture domain entry."""
    return {
        "score": score,
        "confidence": confidence,
        "trend": "unknown",
        "sources": ["wb_natural_rents"],
        "indicators": [
            {
                "key": "wb_natural_rents",
                "question": "How dependent is the economy on natural resources?",
                "label": "High",
                "facts": facts or ["Natural resource rents: 25.0% of GDP"],
            }
        ],
        "justification_detail": "Auto-scored from World Bank data.",
        "_n_indicators": 1,
        "_n_sources": 1,
        "_most_recent_year": 2022,
    }


class TestApplyResourceModeration:
    def test_with_polyarchy_moderates_score(self):
        """High democracy reduces resource capture score."""
        domains = {"resource_capture": _make_resource_domain(80)}
        apply_resource_moderation(domains, raw_polyarchy=0.8)
        # 80 * (100 - 80) / 100 = 16
        assert domains["resource_capture"]["score"] == 16

    def test_with_polyarchy_adds_vdem_source(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        assert "vdem_electoral_democracy" in domains["resource_capture"]["sources"]

    def test_with_polyarchy_rebuilds_indicators(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        inds = domains["resource_capture"]["indicators"]
        assert len(inds) == 1
        assert inds[0]["key"] == "resource_capture_composite"
        assert inds[0]["question"] == "How vulnerable is resource wealth to elite capture?"

    def test_with_polyarchy_preserves_rents_facts(self):
        """Original resource rents facts should appear in moderated indicator."""
        domains = {"resource_capture": _make_resource_domain(60, facts=["Rents: 15.0% of GDP"])}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        facts = domains["resource_capture"]["indicators"][0]["facts"]
        assert "Rents: 15.0% of GDP" in facts
        assert any("Moderated by democratic accountability" in f for f in facts)

    def test_with_polyarchy_updates_justification(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        j = domains["resource_capture"]["justification_detail"]
        assert "Composite:" in j
        assert "accountability" in j

    def test_without_polyarchy_keeps_score(self):
        """No V-Dem data -> score unchanged."""
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["score"] == 60

    def test_without_polyarchy_caps_confidence(self):
        """No V-Dem data -> confidence capped at 'low'."""
        domains = {"resource_capture": _make_resource_domain(60, confidence="high")}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["confidence"] == "low"

    def test_without_polyarchy_low_confidence_unchanged(self):
        """Already low confidence stays low."""
        domains = {"resource_capture": _make_resource_domain(60, confidence="very_low")}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["confidence"] == "very_low"

    def test_without_polyarchy_adds_no_data_fact(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=None)
        facts = domains["resource_capture"]["indicators"][0]["facts"]
        assert any("No democratic accountability data" in f for f in facts)

    def test_no_resource_capture_domain_is_noop(self):
        """If resource_capture not in domains, function does nothing."""
        domains = {"economic_concentration": {"score": 50}}
        apply_resource_moderation(domains, raw_polyarchy=0.8)
        assert "resource_capture" not in domains

    def test_zero_polyarchy_full_capture(self):
        """Authoritarian state: polyarchy 0 -> score unchanged."""
        domains = {"resource_capture": _make_resource_domain(75)}
        apply_resource_moderation(domains, raw_polyarchy=0.0)
        assert domains["resource_capture"]["score"] == 75
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_resource_moderation.py -v`
Expected: ImportError.

**Step 3: Extract the function**

In `scripts/score_countries.py`, add after `assemble_country_entry`:

```python
def apply_resource_moderation(domains, raw_polyarchy):
    """Moderate resource_capture score by democratic accountability.

    High resource rents + low democracy = high extraction.
    High resource rents + high democracy = low extraction.

    Mutates domains["resource_capture"] in-place. No-op if key absent.
    """
    if "resource_capture" not in domains:
        return

    raw_resource = domains["resource_capture"]["score"]

    # Extract resource rents facts before rebuilding indicators
    resource_rents_facts = []
    for ind in domains["resource_capture"].get("indicators", []):
        if ind["key"] == "wb_natural_rents":
            resource_rents_facts = ind["facts"]
            break

    if raw_polyarchy is not None:
        accountability = round(raw_polyarchy * 100)
        composite_resource = compute_resource_capture(raw_resource, raw_polyarchy)
        moderation_fact = f"Moderated by democratic accountability (V-Dem polyarchy: {raw_polyarchy:.2f})"
        domains["resource_capture"]["score"] = composite_resource
        domains["resource_capture"]["sources"] = domains["resource_capture"]["sources"] + [
            "vdem_electoral_democracy"
        ]
        domains["resource_capture"]["indicators"] = [
            {
                "key": "resource_capture_composite",
                "question": "How vulnerable is resource wealth to elite capture?",
                "label": score_to_label(composite_resource),
                "facts": (resource_rents_facts + [moderation_fact])
                if resource_rents_facts
                else [f"Resource rents score: {raw_resource}, democratic accountability: {accountability}/100"],
            }
        ]
        domains["resource_capture"]["justification_detail"] = (
            f"{domains['resource_capture']['justification_detail']} "
            f"Composite: resource rents ({raw_resource}) x (100 - accountability ({accountability})) / 100 = {composite_resource}."
        )
    else:
        conf_rank = {"very_low": 0, "low": 1, "moderate": 2, "high": 3}
        current_conf = domains["resource_capture"]["confidence"]
        if conf_rank.get(current_conf, 0) > conf_rank.get("low", 1):
            domains["resource_capture"]["confidence"] = "low"
        score_val = domains["resource_capture"]["score"]
        domains["resource_capture"]["indicators"] = [
            {
                "key": "resource_capture_composite",
                "question": "How dependent is the economy on natural resources?",
                "label": score_to_label(score_val),
                "facts": resource_rents_facts
                + ["No democratic accountability data available to assess who benefits"],
            }
        ]
        domains["resource_capture"]["justification_detail"] = (
            f"{domains['resource_capture']['justification_detail']} "
            f"No V-Dem data available — score reflects unmoderated resource rents ({score_val})."
        )
```

Then in `build_country_scores()`, replace the entire `if "resource_capture" in domains:` block (lines ~1624-1678) with:

```python
        raw_polyarchy = vdem_raw.get(code, {}).get("v2x_polyarchy")
        apply_resource_moderation(domains, raw_polyarchy)
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_resource_moderation.py -v`
Expected: All 11 tests PASS.

**Step 5: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: No regressions.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_resource_moderation.py
git commit -m "refactor: extract apply_resource_moderation from build_country_scores"
```

---

### Task 4: Extract `normalize_vdem_indicators`

Handles the V-Dem normalization loop and per-country dict assembly.

**Files:**
- Modify: `scripts/score_countries.py` (extract from lines ~1387-1405)
- Create: `tests/python/unit/test_vdem_normalization.py`

**Step 1: Write the failing test**

Create `tests/python/unit/test_vdem_normalization.py`:

```python
"""Tests for V-Dem indicator normalization."""

from score_countries import normalize_vdem_indicators


VDEM_VARS_CONFIG = {
    "v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Political Corruption"},
    "v2x_polyarchy": {"domain": "political_capture", "inverted": True, "name": "Electoral Democracy"},
}


class TestNormalizeVdemIndicators:
    def test_basic_normalization(self):
        """Two countries, one variable — normalized to 0-100."""
        vdem_raw = {
            "USA": {"v2x_corr": 0.2},
            "NGA": {"v2x_corr": 0.8},
        }
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        assert "USA" in result
        assert "NGA" in result
        # USA has lower corruption -> lower normalized score
        assert result["USA"]["v2x_corr"]["score"] < result["NGA"]["v2x_corr"]["score"]

    def test_inverted_variable(self):
        """Inverted: higher raw = less extraction -> lower score."""
        vdem_raw = {
            "USA": {"v2x_polyarchy": 0.9},
            "NGA": {"v2x_polyarchy": 0.4},
        }
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        # USA more democratic -> less extraction -> lower score
        assert result["USA"]["v2x_polyarchy"]["score"] < result["NGA"]["v2x_polyarchy"]["score"]

    def test_output_structure(self):
        """Each entry has score, raw, name, domain, var."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}, "DNK": {"v2x_corr": 0.1}}
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        entry = result["USA"]["v2x_corr"]
        assert set(entry.keys()) == {"score", "raw", "name", "domain", "var"}
        assert entry["raw"] == 0.5
        assert entry["name"] == "Corruption"
        assert entry["domain"] == "political_capture"
        assert entry["var"] == "v2x_corr"

    def test_missing_variable_skipped(self):
        """Country missing a variable -> variable absent from output."""
        vdem_raw = {
            "USA": {"v2x_corr": 0.2},
            "NGA": {"v2x_corr": 0.8, "v2x_polyarchy": 0.4},
        }
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        assert "v2x_polyarchy" not in result.get("USA", {})

    def test_single_country_gets_score_50(self):
        """When min == max, normalize_minmax returns 50."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}}
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        assert result["USA"]["v2x_corr"]["score"] == 50

    def test_empty_input(self):
        vdem_raw = {}
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        assert result == {}

    def test_variable_not_in_any_country(self):
        """Config has a variable that no country reports -> skip it."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}}
        config = {
            "v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"},
            "v2x_missing": {"domain": "political_capture", "inverted": False, "name": "Missing"},
        }
        result = normalize_vdem_indicators(vdem_raw, config)
        assert "v2x_missing" not in result.get("USA", {})
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_vdem_normalization.py -v`
Expected: ImportError.

**Step 3: Extract the function**

In `scripts/score_countries.py`, add after `apply_resource_moderation`:

```python
def normalize_vdem_indicators(vdem_raw, vdem_vars_config):
    """Normalize raw V-Dem indicators across all countries.

    Args:
        vdem_raw: {country_code: {var_name: raw_value}}
        vdem_vars_config: {var_name: {"domain": str, "inverted": bool, "name": str}}

    Returns:
        {country_code: {var_name: {"score": int, "raw": float, "name": str, "domain": str, "var": str}}}
    """
    vdem_normalized = {}
    for var, cfg in vdem_vars_config.items():
        values = {code: vals[var] for code, vals in vdem_raw.items() if var in vals}
        if not values:
            continue
        series = pd.Series(values)
        normed = normalize_minmax(series, inverted=cfg["inverted"])
        for code, score in normed.items():
            if code not in vdem_normalized:
                vdem_normalized[code] = {}
            vdem_normalized[code][var] = {
                "score": int(score),
                "raw": values[code],
                "name": cfg["name"],
                "domain": cfg["domain"],
                "var": var,
            }
    return vdem_normalized
```

Then in `build_country_scores()`, replace lines ~1387-1405 (the `vdem_normalized = {}` / for-loop block) with:

```python
        vdem_normalized = normalize_vdem_indicators(vdem_raw, vdem_vars_config)
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_vdem_normalization.py -v`
Expected: All 7 tests PASS.

**Step 5: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: No regressions.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_vdem_normalization.py
git commit -m "refactor: extract normalize_vdem_indicators from build_country_scores"
```

---

### Task 5: Extract `build_wb_domain`

The World Bank domain assembly block — computes score, trend majority vote, indicator entries, confidence.

**Files:**
- Modify: `scripts/score_countries.py` (extract from lines ~1463-1510)
- Create: `tests/python/unit/test_build_wb_domain.py`

**Step 1: Write the failing test**

Create `tests/python/unit/test_build_wb_domain.py`:

```python
"""Tests for World Bank domain entry construction."""

import pandas as pd

from score_countries import build_wb_domain


def _make_wb_group():
    """Build a minimal pandas DataFrame resembling a WB domain group.

    Two indicators for institutional_gatekeeping, as if from groupby('domain').
    """
    return pd.DataFrame({
        "country_code": ["USA", "USA"],
        "country_name": ["United States", "United States"],
        "year": [2022, 2021],
        "value": [-0.5, 0.8],
        "normalized": [60, 30],
        "domain": ["institutional_gatekeeping", "institutional_gatekeeping"],
        "source_key": ["wb_wgi_corruption", "wb_reg_quality"],
        "indicator_name": ["WGI Control of Corruption", "WGI Regulatory Quality"],
        "indicator_file": ["wb_wgi_corruption.csv", "wb_wgi_reg_quality.csv"],
    })


class TestBuildWbDomain:
    def test_score_is_mean_of_normalized(self):
        group = _make_wb_group()
        all_indicator_raw = {"wb_wgi_corruption": {"USA": -0.5}, "wb_reg_quality": {"USA": 0.8}}
        result = build_wb_domain(group, "USA", all_indicator_raw)
        assert result["score"] == 45  # (60 + 30) / 2

    def test_has_required_keys(self):
        group = _make_wb_group()
        all_indicator_raw = {}
        result = build_wb_domain(group, "USA", all_indicator_raw)
        for key in ["score", "confidence", "trend", "sources", "indicators",
                     "justification_detail", "_n_indicators", "_n_sources", "_most_recent_year"]:
            assert key in result, f"Missing key: {key}"

    def test_n_indicators_matches_group_size(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert result["_n_indicators"] == 2

    def test_sources_list(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert "wb_wgi_corruption" in result["sources"]
        assert "wb_reg_quality" in result["sources"]

    def test_most_recent_year(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert result["_most_recent_year"] == 2022

    def test_single_indicator(self):
        group = pd.DataFrame({
            "country_code": ["USA"],
            "country_name": ["United States"],
            "year": [2023],
            "value": [41.5],
            "normalized": [72],
            "domain": ["economic_concentration"],
            "source_key": ["wb_gini"],
            "indicator_name": ["Gini Index"],
            "indicator_file": ["wb_gini.csv"],
        })
        result = build_wb_domain(group, "USA", {})
        assert result["score"] == 72
        assert result["_n_indicators"] == 1
```

**Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_build_wb_domain.py -v`
Expected: ImportError.

**Step 3: Extract the function**

In `scripts/score_countries.py`, add after `normalize_vdem_indicators`:

```python
def build_wb_domain(group, code, all_indicator_raw):
    """Build a domain entry from a World Bank indicator group.

    Args:
        group: pandas DataFrame — rows for one country+domain from groupby('domain').
            Must have columns: normalized, source_key, year, indicator_file, value, indicator_name.
        code: ISO alpha-3 country code.
        all_indicator_raw: {source_key: {country_code: raw_value}} for peer comparisons.

    Returns:
        Domain dict with score, confidence, trend, sources, indicators, justification_detail,
        and internal tracking fields (_n_indicators, _n_sources, _most_recent_year).
    """
    score = int(group["normalized"].mean().round(0))
    sources = group["source_key"].tolist()
    n_indicators = len(group)
    most_recent = int(group["year"].max())

    confidence = assess_domain_confidence(n_indicators, 1, most_recent)

    # Estimate trend using majority vote across all indicators in domain
    trend_votes = []
    for _, row in group.iterrows():
        cfg = next((c for c in INDICATOR_CONFIG if c["file"] == row["indicator_file"]), None)
        inv = cfg["inverted"] if cfg else False
        t = estimate_trend(None, code, row["indicator_file"], inverted=inv)
        if t != "unknown":
            trend_votes.append(t)
    if trend_votes:
        trend = Counter(trend_votes).most_common(1)[0][0]
    else:
        trend = "unknown"

    ind_entries = []
    ind_info = []
    for _, row in group.iterrows():
        entry = build_indicator_entry(
            row["source_key"], row["value"], int(row["normalized"]), code, all_indicator_raw
        )
        ind_entries.append(entry)
        ind_info.append(
            {
                "name": row["indicator_name"],
                "raw": row["value"],
                "normalized": int(row["normalized"]),
            }
        )
    justification_detail = build_technical_justification("World Bank data", ind_info)

    return {
        "score": score,
        "confidence": confidence,
        "trend": trend,
        "sources": sources,
        "indicators": ind_entries,
        "justification_detail": justification_detail,
        "_n_indicators": n_indicators,
        "_n_sources": 1,
        "_most_recent_year": most_recent,
    }
```

Note: `estimate_trend` reads from disk and the first arg (`df_full`) is unused in the current implementation — it uses `WB_DIR / indicator_file` directly. The tests will get `trend="unknown"` because there are no WB files on disk during testing, which is fine — trend estimation is already tested separately.

Then in `build_country_scores()`, replace the domain-building loop (lines ~1463-1510, the `for domain, group in country_data.groupby("domain"):` block) with:

```python
            for domain, group in country_data.groupby("domain"):
                domains[domain] = build_wb_domain(group, code, all_indicator_raw)
            source_names.append("World Bank")
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/python/unit/test_build_wb_domain.py -v`
Expected: All 6 tests PASS.

**Step 5: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/python/ --tb=short -q`
Expected: No regressions.

**Step 6: Commit**

```bash
git add scripts/score_countries.py tests/python/unit/test_build_wb_domain.py
git commit -m "refactor: extract build_wb_domain from build_country_scores"
```

---

### Task 6: Verify coverage improvement

**Step 1: Run coverage**

Run: `source .venv/bin/activate && pytest tests/python/unit/ --cov=score_countries --cov-report=term-missing --tb=short -q`

Expected: Coverage should increase significantly from 40%. The extracted functions (cap_confidence_by_coverage, assemble_country_entry, apply_resource_moderation, normalize_vdem_indicators, build_wb_domain) add ~120 lines of now-tested code. The remaining uncovered code will be the wiring in `build_country_scores()` (loading data, iterating countries) and `main()`.

**Step 2: Commit any final adjustments if needed**

If coverage is satisfactory, no action needed. If there are minor gaps in the extracted functions, add targeted tests.
