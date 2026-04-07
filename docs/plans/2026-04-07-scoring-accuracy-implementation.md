# Scoring Accuracy Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix RSF labels, resource capture formula, and institutional gatekeeping indicators so the index accurately reflects autocracies with competent bureaucracies.

**Architecture:** Four independent fixes to the scoring pipeline, plus METHODOLOGY.md updates and a validation step. No test framework exists — validation is spot-checking scorer output for benchmark countries.

**Tech Stack:** Python 3 (pandas), static JSON output, Markdown docs.

---

### Task 1: Capture before-state for benchmark countries

Before any code changes, record current scores for spot-checking later.

**Files:**
- Read: `data/scores.json`

**Step 1: Record current scores**

Run:
```bash
cd /Users/ovid/projects/extraction && python3 -c "
import json
with open('data/scores.json') as f:
    data = json.load(f)
for code in ['SAU', 'NOR', 'SGP', 'USA', 'PRK']:
    c = data['countries'].get(code)
    if not c:
        print(f'{code}: no data')
        continue
    domains = {k: v['score'] for k, v in c['domains'].items()}
    composite = round(sum(domains.values()) / len(domains))
    print(f'{code} composite={composite} domains={domains}')
"
```

Save the output — we'll compare after re-scoring.

---

### Task 2: Fix RSF label and comparison labels

**Files:**
- Modify: `scripts/score_countries.py:91-99` (POSITIVE_QUESTION_INDICATORS)
- Modify: `scripts/score_countries.py:143-144` (INDICATOR_DISPLAY comparison_label)

**Step 1: Add rsf_press to POSITIVE_QUESTION_INDICATORS**

In `scripts/score_countries.py`, add `'rsf_press'` to the `POSITIVE_QUESTION_INDICATORS` set (after line 98):

```python
POSITIVE_QUESTION_INDICATORS = {
    'wb_wgi_corruption',    # "How well is corruption controlled?" — well = good
    'wb_reg_quality',       # "How well do government regulations protect people?"
    'wb_wgi_gov_eff',       # "How effective is the government?"
    'vdem_electoral_democracy',      # "How democratic are elections?"
    'vdem_freedom_of_expression',    # "How free is public expression?"
    'vdem_alternative_info_sources', # "How available are independent information sources?"
    'vdem_rule_of_law',              # "How strong is the rule of law?"
    'rsf_press',                     # "How free is the press?" — free = good
}
```

**Step 2: Swap RSF comparison labels**

Change the `comparison_label` for `rsf_press` in `INDICATOR_DISPLAY` (line 144) from:

```python
'comparison_label': ['Least free press among', 'Freest press among']
```

to:

```python
'comparison_label': ['Freest press among', 'Least free press among']
```

**Step 3: Commit**

```bash
git add scripts/score_countries.py
git commit -m "Fix RSF label inversion and comparison label order"
```

---

### Task 3: Add V-Dem variables to fetcher

**Files:**
- Modify: `scripts/fetchers/vdem.py:36-47` (VARIABLES list)
- Modify: `scripts/fetchers/vdem.py:120-128` (metadata variables list)

**Step 1: Add v2x_egal and v2x_partipdem to VARIABLES**

In `scripts/fetchers/vdem.py`, add two entries to the `VARIABLES` list (after line 46):

```python
VARIABLES = [
    'country_text_id',
    'country_name',
    'year',
    'v2x_polyarchy',     # Electoral Democracy Index (0–1, higher = more democratic)
    'v2x_corr',          # Political Corruption Index (0–1, higher = more corrupt)
    'v2xnp_client',      # Clientelism Index (0–1, higher = more clientelist)
    'v2x_freexp_altinf',  # Freedom of Expression (0–1, higher = more free)
    'v2xme_altinf',      # Alternative Sources of Information (0–1, higher = more free)
    'v2x_clphy',         # Physical Violence Index (0–1, higher = less violence)
    'v2x_rule',          # Rule of Law Index (0–1, higher = stronger rule of law)
    'v2x_egal',          # Egalitarian Component Index (0–1, higher = more egalitarian)
    'v2x_partipdem',     # Participatory Democracy Index (0–1, higher = more participatory)
]
```

**Step 2: Add to metadata**

Add two entries to the `variables` list in the metadata dict (after line 127):

```python
{'name': 'v2x_egal',      'domain': 'institutional_gatekeeping', 'inverted': True, 'desc': 'Egalitarian Component Index (0-1)'},
{'name': 'v2x_partipdem', 'domain': 'institutional_gatekeeping', 'inverted': True, 'desc': 'Participatory Democracy Index (0-1)'},
```

**Step 3: Update the module docstring**

Add to the docstring at the top of vdem.py (after line 21):

```
  - v2x_egal              Egalitarian Component Index        → institutional_gatekeeping (inverted)
  - v2x_partipdem         Participatory Democracy Index      → institutional_gatekeeping (inverted)
```

**Step 4: Re-run the V-Dem fetcher to regenerate the extract**

The full CSV is already cached. We just need to re-extract with the new columns:

```bash
cd /Users/ovid/projects/extraction && rm raw_data/vdem/vdem_extract.csv && source .venv/bin/activate && cd scripts && python fetch_all.py --source vdem
```

Verify the new columns appear:
```bash
head -1 /Users/ovid/projects/extraction/raw_data/vdem/vdem_extract.csv | tr ',' '\n' | grep -E 'v2x_egal|v2x_partipdem'
```

Expected: both `v2x_egal` and `v2x_partipdem` appear.

**Step 5: Commit**

```bash
git add scripts/fetchers/vdem.py
git commit -m "Add V-Dem egalitarian and participatory democracy variables to fetcher"
```

---

### Task 4: Add V-Dem variables to scorer

**Files:**
- Modify: `scripts/score_countries.py:51-72` (INDICATOR_QUESTIONS)
- Modify: `scripts/score_countries.py:91-99` (POSITIVE_QUESTION_INDICATORS)
- Modify: `scripts/score_countries.py:114-147` (INDICATOR_DISPLAY)
- Modify: `scripts/score_countries.py:575-576` (vdem_vars in load_vdem_data)
- Modify: `scripts/score_countries.py:738-746` (vdem_vars_config)
- Modify: `scripts/score_countries.py:773-785` (vdem_source_key_map)

**Step 1: Add questions for new indicators**

Add to `INDICATOR_QUESTIONS` (after line 67):

```python
'vdem_egalitarian':           'How equally are political power and resources distributed?',
'vdem_participatory_democracy': 'How much can citizens participate in governance?',
```

**Step 2: Add to POSITIVE_QUESTION_INDICATORS**

Add to the set:

```python
'vdem_egalitarian',                  # "How equally are...?" — equal = good
'vdem_participatory_democracy',      # "How much can citizens...?" — participation = good
```

**Step 3: Add INDICATOR_DISPLAY entries**

Add to `INDICATOR_DISPLAY` (before the `rsf_press` entry):

```python
'vdem_egalitarian':           {'label': 'Egalitarian component index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                               'comparison_label': ['Most egalitarian among', 'Least egalitarian among']},
'vdem_participatory_democracy': {'label': 'Participatory democracy index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                  'comparison_label': ['Most participatory among', 'Least participatory among']},
```

**Step 4: Add to vdem_vars in load_vdem_data()**

In `load_vdem_data()` (line 575), add the new variables to the list:

```python
vdem_vars = ['v2x_polyarchy', 'v2x_corr', 'v2xnp_client',
             'v2x_freexp_altinf', 'v2xme_altinf', 'v2x_clphy', 'v2x_rule',
             'v2x_egal', 'v2x_partipdem']
```

**Step 5: Add to vdem_vars_config**

In the `vdem_vars_config` dict (line 738), add:

```python
'v2x_egal':      {'domain': 'institutional_gatekeeping', 'inverted': True, 'name': 'Egalitarian Component'},
'v2x_partipdem': {'domain': 'institutional_gatekeeping', 'inverted': True, 'name': 'Participatory Democracy'},
```

**Step 6: Add to vdem_source_key_map**

In `vdem_source_key_map` (line 773), add:

```python
'v2x_egal': 'vdem_egalitarian',
'v2x_partipdem': 'vdem_participatory_democracy',
```

**Step 7: Commit**

```bash
git add scripts/score_countries.py
git commit -m "Add V-Dem egalitarian and participatory indicators to institutional gatekeeping"
```

**Note on equal weighting:** The design specifies equal weighting across all 6 indicators. The existing merge logic (`score_countries.py:934-951`) averages the WB group score with the V-Dem group score: `merged_score = round((existing['score'] + vdem_score) / 2)`. With 3 WB indicators and 3 V-Dem indicators (rule_of_law + egalitarian + participatory), each individual indicator gets 1/6 effective weight — achieving equal weighting by coincidence of group sizes. This is correct for the current indicator set but would break if either group's count changes. No code change needed now, but worth noting for future maintainers.

---

### Task 5: Replace resource capture formula

**Files:**
- Modify: `scripts/score_countries.py:973-1018` (resource capture composite block)

**Step 1: Replace the resource capture composite logic**

Replace the entire block from line 973 (`# Resource capture: composite of resource rents...`) through line 1018 (end of the `elif 'resource_capture'` block) with:

```python
        # Resource capture: resource rents moderated by democratic accountability
        # High resource rents + low democracy = high extraction (elites capture resources)
        # High resource rents + high democracy = low extraction (citizens hold resource management accountable)
        # Uses raw V-Dem polyarchy (0-1) directly, NOT min-max normalized, because the
        # raw scale has inherent meaning and normalization would distort absolute levels.
        if 'resource_capture' in domains:
            raw_resource = domains['resource_capture']['score']
            raw_polyarchy = vdem_raw.get(code, {}).get('v2x_polyarchy')

            if raw_polyarchy is not None:
                # Convert raw 0-1 polyarchy to 0-100 accountability score
                accountability = round(raw_polyarchy * 100)
                composite_resource = round(raw_resource * (100 - accountability) / 100)
                moderation_fact = f'Moderated by democratic accountability (V-Dem polyarchy: {raw_polyarchy:.2f})'
                domains['resource_capture']['score'] = composite_resource
                domains['resource_capture']['sources'] = domains['resource_capture']['sources'] + ['vdem_electoral_democracy']
                # Rebuild indicators for the composite
                resource_rents_facts = []
                for ind in domains['resource_capture'].get('indicators', []):
                    if ind['key'] == 'wb_natural_rents':
                        resource_rents_facts = ind['facts']
                        break
                domains['resource_capture']['indicators'] = [{
                    'key': 'resource_capture_composite',
                    'question': 'How vulnerable is resource wealth to elite capture?',
                    'label': score_to_label(composite_resource),
                    'facts': resource_rents_facts + [moderation_fact] if resource_rents_facts else [
                        f'Resource rents score: {raw_resource}, democratic accountability: {accountability}/100'
                    ],
                }]
                domains['resource_capture']['justification_detail'] = (
                    f'{domains["resource_capture"]["justification_detail"]} '
                    f'Composite: resource rents ({raw_resource}) × (100 - accountability ({accountability})) / 100 = {composite_resource}.'
                )
            else:
                # No V-Dem data — use raw rents unmoderated, mark low confidence
                domains['resource_capture']['confidence'] = 'low'
                score_val = domains['resource_capture']['score']
                resource_facts = []
                for ind in domains['resource_capture'].get('indicators', []):
                    if ind['key'] == 'wb_natural_rents':
                        resource_facts = ind['facts']
                        break
                domains['resource_capture']['indicators'] = [{
                    'key': 'resource_capture_composite',
                    'question': 'How dependent is the economy on natural resources?',
                    'label': score_to_label(score_val),
                    'facts': resource_facts + ['No democratic accountability data available to assess who benefits'],
                }]
```

**Step 2: Verify `vdem_raw` is in scope**

Check that `vdem_raw` (the dict from `load_vdem_data()`) is accessible at the point where the resource capture block runs. It's assigned at line 730 (`vdem_raw = load_vdem_data()`) and the resource capture block is inside the same `build_country_scores()` function, in the per-country loop — so it's in scope.

**Step 3: Commit**

```bash
git add scripts/score_countries.py
git commit -m "Replace resource capture formula: use democratic accountability instead of institutional strength"
```

---

### Task 6: Re-score all countries and validate

**Files:**
- Regenerate: `data/scores.json`

**Step 1: Re-run the scorer**

```bash
cd /Users/ovid/projects/extraction && source .venv/bin/activate && cd scripts && python score_countries.py --overwrite
```

**Step 2: Spot-check benchmark countries**

Run the same script from Task 1 to get after-scores:

```bash
cd /Users/ovid/projects/extraction && python3 -c "
import json
with open('data/scores.json') as f:
    data = json.load(f)
for code in ['SAU', 'NOR', 'SGP', 'USA', 'PRK']:
    c = data['countries'].get(code)
    if not c:
        print(f'{code}: no data')
        continue
    domains = {k: v['score'] for k, v in c['domains'].items()}
    composite = round(sum(domains.values()) / len(domains))
    print(f'{code} composite={composite} domains={domains}')
"
```

**Expected direction of changes:**
- Saudi Arabia: institutional_gatekeeping should increase (more extractive), resource_capture should increase (~41), composite should increase
- Norway: institutional_gatekeeping should decrease (less extractive), resource_capture stays very low, composite stays low
- Singapore: institutional_gatekeeping should increase (autocratic despite efficient), resource_capture stays low (minimal rents)
- USA: institutional_gatekeeping may shift slightly, resource_capture stays very low
- North Korea: may have limited V-Dem data — check what happens

**Step 3: Check Saudi Arabia's information_capture label**

```bash
cd /Users/ovid/projects/extraction && python3 -c "
import json
with open('data/scores.json') as f:
    data = json.load(f)
rsf = data['countries']['SAU']['domains']['information_capture']['indicators'][0]
print(f'RSF label: {rsf[\"label\"]}')
print(f'RSF facts: {rsf[\"facts\"]}')
"
```

Expected: RSF label should be "Very low" (not "Very high"), reflecting Saudi Arabia's poor press freedom.

**Step 4: Review results and sanity check**

If any benchmark country's scores look wrong, investigate before committing. Common issues:
- V-Dem variable not loading (check `load_vdem_data` for the new vars)
- Wrong inversion direction
- Raw polyarchy value not available for a country

**Step 5: Commit**

```bash
git add data/scores.json
git commit -m "Re-score all countries with fixed RSF labels, resource capture, and institutional gatekeeping"
```

---

### Task 7: Update METHODOLOGY.md

**Files:**
- Modify: `METHODOLOGY.md:49-88` (institutional gatekeeping + resource capture sections)

**Step 1: Update institutional gatekeeping section**

Replace the institutional gatekeeping section (lines 49-60) with:

```markdown
### 4. Institutional Gatekeeping

Whether institutions serve the broad population or narrow interests. This domain balances two dimensions: bureaucratic competence (can the state deliver?) and democratic accountability (who does it deliver for?).

| Indicator | Source | Variable | Direction |
|-----------|--------|----------|-----------|
| Control of Corruption | World Bank (WGI) | CC.EST | Inverted |
| Regulatory Quality | World Bank (WGI) | RQ.EST | Inverted |
| Government Effectiveness | World Bank (WGI) | GE.EST | Inverted |
| Rule of Law | V-Dem | v2x_rule | Inverted |
| Egalitarian Component | V-Dem | v2x_egal | Inverted |
| Participatory Democracy | V-Dem | v2x_partipdem | Inverted |

The World Bank WGI indicators measure state capacity — how effectively a government controls corruption, regulates, and delivers services. The V-Dem indicators measure democratic accountability — how equally power and resources are distributed and how much citizens participate in governance. Both dimensions matter: a competent autocracy scores well on WGI but poorly on V-Dem accountability metrics, resulting in a higher extraction score than the WGI alone would suggest.

When both World Bank and V-Dem data are available for this domain, the domain score is the average of the World Bank group score and the V-Dem group score.
```

**Step 2: Update resource capture section**

Replace the resource capture section (lines 74-88) with:

```markdown
### 6. Resource Capture

How vulnerable resource wealth is to elite capture. This is a **composite score**:

```
resource_capture = resource_rents × (100 - democratic_accountability) / 100
```

Where:
- `resource_rents` = normalized World Bank natural resource rents (% GDP), indicator NY.GDP.TOTL.RT.ZS
- `democratic_accountability` = raw V-Dem electoral democracy index (v2x_polyarchy) × 100

This formula uses the **raw** V-Dem polyarchy value (0-1 scale), not a min-max normalized score. Min-max normalization is relative to the dataset and would distort absolute levels — a country with polyarchy 0.50 (a hybrid regime) would appear to have majority accountability under normalization, when in reality 0.50 indicates genuinely weak democratic checks.

The justification is a first-principles argument supported by the resource curse literature (Ross 2012, Karl 1997): resource wealth is captured by elites to the extent that democratic accountability is absent. In a full autocracy, elites face no check on resource capture. In a full democracy, citizens can hold resource management accountable, reducing elite capture.

**Important limitations of this approach:**
- V-Dem polyarchy measures *electoral* democracy specifically, not all forms of accountability. Some non-electoral accountability mechanisms (tribal councils, traditional authority structures, religious checks on power) are not captured.
- The raw 0-1 scale assumes equal intervals — moving from 0.4 to 0.5 is treated as equivalent to moving from 0.8 to 0.9 — which may not reflect political reality.
- A country's formal democratic institutions may not reflect actual power dynamics. Elections can coexist with elite resource capture.
- Raw scores are guidelines. They cannot always explain reality.

When V-Dem data is unavailable, the raw resource rents score is used unmoderated, with confidence capped at "low" and a note that democratic accountability data is unavailable.
```

**Step 3: Commit**

```bash
git add METHODOLOGY.md
git commit -m "Update methodology: document new resource capture formula and institutional gatekeeping rebalancing"
```

---

### Task 8: Final review

**Step 1: Run the site locally and check Saudi Arabia's panel**

```bash
cd /Users/ovid/projects/extraction && python3 -m http.server 8000
```

Open http://localhost:8000, select Saudi Arabia, and verify:
- RSF label says "Very low" (not "Very high")
- Resource capture score is significantly higher than 21
- Institutional gatekeeping score is higher than 50
- New indicators (Egalitarian Component, Participatory Democracy) appear in the institutional gatekeeping domain card
- Composite score reflects the changes

**Step 2: Check Norway for regression**

Select Norway and verify:
- Resource capture remains very low
- Institutional gatekeeping remains very low
- No broken labels or missing data
