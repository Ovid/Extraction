# Context Facts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add concrete raw values and peer comparisons under each indicator question in domain cards, using a structured `indicators` array that replaces the fragile `justification` string.

**Architecture:** Python scorer generates structured `indicators` arrays at scoring time using existing raw data + new region/income mappings. Each indicator carries its question, label, and context facts. Frontend iterates the array directly — no regex splitting. Special handling for `resource_capture` composite.

**Tech Stack:** Python (score_countries.py), vanilla JS (app.js), CSS (style.css)

**Alignment fixes incorporated:**
1. Inverted indicators use natural language ("Strongest rule of law among..." not "Highest among...")
2. Structured `indicators` array replaces index-based justification/facts matching
3. `resource_capture` indicators rebuilt after composite recalculation
4. `data/schema.json` updated
5. `METHODOLOGY.md` updated

---

### Task 1: Add region and income group mappings

**Files:**
- Modify: `scripts/score_countries.py` (insert after `COUNTRY_NAME_OVERRIDES` dict, ~line 198)

**Step 1: Add REGION_MAP and INCOME_GROUP_MAP dicts**

```python
# UN geoscheme region mapping for peer comparisons
REGION_MAP = {
    # Eastern Africa
    'BDI': 'Eastern Africa', 'COM': 'Eastern Africa', 'DJI': 'Eastern Africa',
    'ERI': 'Eastern Africa', 'ETH': 'Eastern Africa', 'KEN': 'Eastern Africa',
    'MDG': 'Eastern Africa', 'MWI': 'Eastern Africa', 'MUS': 'Eastern Africa',
    'MOZ': 'Eastern Africa', 'RWA': 'Eastern Africa', 'SYC': 'Eastern Africa',
    'SOM': 'Eastern Africa', 'SSD': 'Eastern Africa', 'TZA': 'Eastern Africa',
    'UGA': 'Eastern Africa', 'ZMB': 'Eastern Africa', 'ZWE': 'Eastern Africa',
    # Middle Africa
    'AGO': 'Middle Africa', 'CMR': 'Middle Africa', 'CAF': 'Middle Africa',
    'TCD': 'Middle Africa', 'COG': 'Middle Africa', 'COD': 'Middle Africa',
    'GNQ': 'Middle Africa', 'GAB': 'Middle Africa',
    # Northern Africa
    'DZA': 'Northern Africa', 'EGY': 'Northern Africa', 'LBY': 'Northern Africa',
    'MAR': 'Northern Africa', 'SDN': 'Northern Africa', 'TUN': 'Northern Africa',
    # Southern Africa
    'BWA': 'Southern Africa', 'SWZ': 'Southern Africa', 'LSO': 'Southern Africa',
    'NAM': 'Southern Africa', 'ZAF': 'Southern Africa',
    # Western Africa
    'BEN': 'Western Africa', 'BFA': 'Western Africa', 'CPV': 'Western Africa',
    'CIV': 'Western Africa', 'GMB': 'Western Africa', 'GHA': 'Western Africa',
    'GIN': 'Western Africa', 'GNB': 'Western Africa', 'LBR': 'Western Africa',
    'MLI': 'Western Africa', 'MRT': 'Western Africa', 'NER': 'Western Africa',
    'NGA': 'Western Africa', 'SEN': 'Western Africa', 'SLE': 'Western Africa',
    'TGO': 'Western Africa',
    # Caribbean
    'ATG': 'Caribbean', 'BHS': 'Caribbean', 'BRB': 'Caribbean', 'CUB': 'Caribbean',
    'DMA': 'Caribbean', 'DOM': 'Caribbean', 'GRD': 'Caribbean', 'HTI': 'Caribbean',
    'JAM': 'Caribbean', 'KNA': 'Caribbean', 'LCA': 'Caribbean', 'VCT': 'Caribbean',
    'TTO': 'Caribbean', 'PRI': 'Caribbean',
    # Central America
    'BLZ': 'Central America', 'CRI': 'Central America', 'SLV': 'Central America',
    'GTM': 'Central America', 'HND': 'Central America', 'MEX': 'Central America',
    'NIC': 'Central America', 'PAN': 'Central America',
    # South America
    'ARG': 'South America', 'BOL': 'South America', 'BRA': 'South America',
    'CHL': 'South America', 'COL': 'South America', 'ECU': 'South America',
    'GUY': 'South America', 'PRY': 'South America', 'PER': 'South America',
    'SUR': 'South America', 'URY': 'South America', 'VEN': 'South America',
    # Northern America
    'CAN': 'Northern America', 'USA': 'Northern America',
    # Central Asia
    'KAZ': 'Central Asia', 'KGZ': 'Central Asia', 'TJK': 'Central Asia',
    'TKM': 'Central Asia', 'UZB': 'Central Asia',
    # Eastern Asia
    'CHN': 'Eastern Asia', 'JPN': 'Eastern Asia', 'MNG': 'Eastern Asia',
    'PRK': 'Eastern Asia', 'KOR': 'Eastern Asia', 'TWN': 'Eastern Asia',
    'HKG': 'Eastern Asia', 'MAC': 'Eastern Asia',
    # South-eastern Asia
    'BRN': 'South-eastern Asia', 'KHM': 'South-eastern Asia', 'IDN': 'South-eastern Asia',
    'LAO': 'South-eastern Asia', 'MYS': 'South-eastern Asia', 'MMR': 'South-eastern Asia',
    'PHL': 'South-eastern Asia', 'SGP': 'South-eastern Asia', 'THA': 'South-eastern Asia',
    'TLS': 'South-eastern Asia', 'VNM': 'South-eastern Asia',
    # Southern Asia
    'AFG': 'Southern Asia', 'BGD': 'Southern Asia', 'BTN': 'Southern Asia',
    'IND': 'Southern Asia', 'IRN': 'Southern Asia', 'MDV': 'Southern Asia',
    'NPL': 'Southern Asia', 'PAK': 'Southern Asia', 'LKA': 'Southern Asia',
    # Western Asia
    'ARM': 'Western Asia', 'AZE': 'Western Asia', 'BHR': 'Western Asia',
    'CYP': 'Western Asia', 'GEO': 'Western Asia', 'IRQ': 'Western Asia',
    'ISR': 'Western Asia', 'JOR': 'Western Asia', 'KWT': 'Western Asia',
    'LBN': 'Western Asia', 'OMN': 'Western Asia', 'PSE': 'Western Asia',
    'QAT': 'Western Asia', 'SAU': 'Western Asia', 'SYR': 'Western Asia',
    'TUR': 'Western Asia', 'ARE': 'Western Asia', 'YEM': 'Western Asia',
    # Eastern Europe
    'BLR': 'Eastern Europe', 'BGR': 'Eastern Europe', 'CZE': 'Eastern Europe',
    'HUN': 'Eastern Europe', 'POL': 'Eastern Europe', 'MDA': 'Eastern Europe',
    'ROU': 'Eastern Europe', 'RUS': 'Eastern Europe', 'SVK': 'Eastern Europe',
    'UKR': 'Eastern Europe',
    # Northern Europe
    'DNK': 'Northern Europe', 'EST': 'Northern Europe', 'FIN': 'Northern Europe',
    'ISL': 'Northern Europe', 'IRL': 'Northern Europe', 'LVA': 'Northern Europe',
    'LTU': 'Northern Europe', 'NOR': 'Northern Europe', 'SWE': 'Northern Europe',
    'GBR': 'Northern Europe',
    # Southern Europe
    'ALB': 'Southern Europe', 'AND': 'Southern Europe', 'BIH': 'Southern Europe',
    'HRV': 'Southern Europe', 'GRC': 'Southern Europe', 'ITA': 'Southern Europe',
    'MLT': 'Southern Europe', 'MNE': 'Southern Europe', 'MKD': 'Southern Europe',
    'PRT': 'Southern Europe', 'SMR': 'Southern Europe', 'SRB': 'Southern Europe',
    'SVN': 'Southern Europe', 'ESP': 'Southern Europe',
    # Western Europe
    'AUT': 'Western Europe', 'BEL': 'Western Europe', 'FRA': 'Western Europe',
    'DEU': 'Western Europe', 'LIE': 'Western Europe', 'LUX': 'Western Europe',
    'MCO': 'Western Europe', 'NLD': 'Western Europe', 'CHE': 'Western Europe',
    # Oceania
    'AUS': 'Oceania', 'FJI': 'Oceania', 'NZL': 'Oceania', 'PNG': 'Oceania',
    'SLB': 'Oceania', 'VUT': 'Oceania', 'WSM': 'Oceania', 'TON': 'Oceania',
    'PLW': 'Oceania', 'MHL': 'Oceania', 'NRU': 'Oceania',
}

# World Bank income group classification (July 2024)
INCOME_GROUP_MAP = {
    # High income
    'AND': 'High income', 'ARE': 'High income', 'ATG': 'High income', 'AUS': 'High income',
    'AUT': 'High income', 'BEL': 'High income', 'BHR': 'High income', 'BHS': 'High income',
    'BRB': 'High income', 'BRN': 'High income', 'CAN': 'High income', 'CHE': 'High income',
    'CHL': 'High income', 'CYP': 'High income', 'CZE': 'High income', 'DEU': 'High income',
    'DNK': 'High income', 'ESP': 'High income', 'EST': 'High income', 'FIN': 'High income',
    'FRA': 'High income', 'GBR': 'High income', 'GRC': 'High income', 'GRD': 'High income',
    'GUY': 'High income', 'HKG': 'High income', 'HRV': 'High income', 'HUN': 'High income',
    'IRL': 'High income', 'ISL': 'High income', 'ISR': 'High income', 'ITA': 'High income',
    'JPN': 'High income', 'KNA': 'High income', 'KOR': 'High income', 'KWT': 'High income',
    'LIE': 'High income', 'LTU': 'High income', 'LUX': 'High income', 'LVA': 'High income',
    'MAC': 'High income', 'MCO': 'High income', 'MLT': 'High income', 'NLD': 'High income',
    'NOR': 'High income', 'NZL': 'High income', 'OMN': 'High income', 'PAN': 'High income',
    'POL': 'High income', 'PRT': 'High income', 'QAT': 'High income', 'ROU': 'High income',
    'SAU': 'High income', 'SGP': 'High income', 'SMR': 'High income', 'SVK': 'High income',
    'SVN': 'High income', 'SWE': 'High income', 'SYC': 'High income', 'TTO': 'High income',
    'URY': 'High income', 'USA': 'High income',
    # Upper middle income
    'ALB': 'Upper middle income', 'ARG': 'Upper middle income', 'ARM': 'Upper middle income',
    'AZE': 'Upper middle income', 'BGR': 'Upper middle income', 'BIH': 'Upper middle income',
    'BLR': 'Upper middle income', 'BLZ': 'Upper middle income', 'BOL': 'Upper middle income',
    'BRA': 'Upper middle income', 'BWA': 'Upper middle income', 'CHN': 'Upper middle income',
    'COL': 'Upper middle income', 'CRI': 'Upper middle income', 'CUB': 'Upper middle income',
    'DMA': 'Upper middle income', 'DOM': 'Upper middle income', 'ECU': 'Upper middle income',
    'GAB': 'Upper middle income', 'GEO': 'Upper middle income', 'GNQ': 'Upper middle income',
    'GTM': 'Upper middle income', 'IDN': 'Upper middle income', 'IRQ': 'Upper middle income',
    'JAM': 'Upper middle income', 'JOR': 'Upper middle income', 'KAZ': 'Upper middle income',
    'LBN': 'Upper middle income', 'LBY': 'Upper middle income', 'LCA': 'Upper middle income',
    'MDA': 'Upper middle income', 'MDV': 'Upper middle income', 'MEX': 'Upper middle income',
    'MKD': 'Upper middle income', 'MNE': 'Upper middle income', 'MUS': 'Upper middle income',
    'MYS': 'Upper middle income', 'NAM': 'Upper middle income', 'PER': 'Upper middle income',
    'PRY': 'Upper middle income', 'RUS': 'Upper middle income', 'SRB': 'Upper middle income',
    'SUR': 'Upper middle income', 'THA': 'Upper middle income', 'TUR': 'Upper middle income',
    'TKM': 'Upper middle income', 'VCT': 'Upper middle income', 'ZAF': 'Upper middle income',
    # Lower middle income
    'AGO': 'Lower middle income', 'BEN': 'Lower middle income', 'BGD': 'Lower middle income',
    'BTN': 'Lower middle income', 'CIV': 'Lower middle income',
    'CMR': 'Lower middle income', 'COG': 'Lower middle income', 'COM': 'Lower middle income',
    'CPV': 'Lower middle income', 'DJI': 'Lower middle income', 'DZA': 'Lower middle income',
    'EGY': 'Lower middle income', 'GHA': 'Lower middle income', 'HND': 'Lower middle income',
    'HTI': 'Lower middle income', 'IND': 'Lower middle income', 'IRN': 'Lower middle income',
    'KEN': 'Lower middle income', 'KGZ': 'Lower middle income', 'KHM': 'Lower middle income',
    'LAO': 'Lower middle income', 'LBR': 'Lower middle income', 'LKA': 'Lower middle income',
    'LSO': 'Lower middle income', 'MAR': 'Lower middle income', 'MMR': 'Lower middle income',
    'MNG': 'Lower middle income', 'MRT': 'Lower middle income', 'NGA': 'Lower middle income',
    'NIC': 'Lower middle income', 'NPL': 'Lower middle income', 'PAK': 'Lower middle income',
    'PHL': 'Lower middle income', 'PNG': 'Lower middle income', 'SEN': 'Lower middle income',
    'SLV': 'Lower middle income', 'SWZ': 'Lower middle income', 'TJK': 'Lower middle income',
    'TLS': 'Lower middle income', 'TUN': 'Lower middle income', 'TZA': 'Lower middle income',
    'UKR': 'Lower middle income', 'UZB': 'Lower middle income', 'VNM': 'Lower middle income',
    'ZMB': 'Lower middle income',
    # Low income
    'AFG': 'Low income', 'BDI': 'Low income', 'BFA': 'Low income', 'CAF': 'Low income',
    'COD': 'Low income', 'ERI': 'Low income', 'ETH': 'Low income', 'GIN': 'Low income',
    'GMB': 'Low income', 'GNB': 'Low income', 'MDG': 'Low income', 'MLI': 'Low income',
    'MOZ': 'Low income', 'MWI': 'Low income', 'NER': 'Low income', 'PRK': 'Low income',
    'RWA': 'Low income', 'SDN': 'Low income', 'SLE': 'Low income', 'SOM': 'Low income',
    'SSD': 'Low income', 'SYR': 'Low income', 'TCD': 'Low income', 'TGO': 'Low income',
    'UGA': 'Low income', 'YEM': 'Low income', 'ZWE': 'Low income',
}
```

**Step 2: Verify dicts load**

Run: `cd /Users/ovid/projects/extraction/scripts && python -c "exec(open('score_countries.py').read()); print(f'Regions: {len(REGION_MAP)}, Income groups: {len(INCOME_GROUP_MAP)}')"` 

Expected: prints counts, no errors.

**Step 3: Commit**

```bash
git add scripts/score_countries.py
git commit -m "Add region and income group mappings for peer comparisons"
```

---

### Task 2: Add generate_context_facts() with clear inverted-indicator phrasing

**Files:**
- Modify: `scripts/score_countries.py` (insert after `build_technical_justification`, ~line 128)

**Step 1: Add INDICATOR_DISPLAY config and generate_context_facts()**

The `comparison_label` field provides natural language for extremes. For inverted indicators (where high raw = low extraction), comparisons use domain-appropriate phrasing — "Strongest rule of law among..." rather than misleading "Highest among...".

```python
# Display formatting for context facts
# comparison_label: [highest_phrase, lowest_phrase] for natural language at extremes
INDICATOR_DISPLAY = {
    'wb_gini':              {'label': 'Gini coefficient', 'format': '{:.1f}', 'unit': '',
                             'comparison_label': ['Most unequal among', 'Most equal among']},
    'wb_labor_share':       {'label': 'GDP per worker', 'format': '${:,.0f}', 'unit': '',
                             'comparison_label': ['Highest among', 'Lowest among']},
    'wb_domestic_credit':   {'label': 'Domestic credit to private sector', 'format': '{:.1f}', 'unit': '% of GDP',
                             'comparison_label': ['Most financialized among', 'Least financialized among']},
    'wb_natural_rents':     {'label': 'Natural resource rents', 'format': '{:.1f}', 'unit': '% of GDP',
                             'comparison_label': ['Most resource-dependent among', 'Least resource-dependent among']},
    'wb_wgi_corruption':    {'label': 'Control of corruption index', 'format': '{:.2f}', 'unit': '(scale: -2.5 to 2.5)',
                             'comparison_label': ['Strongest corruption control among', 'Weakest corruption control among']},
    'wb_reg_quality':       {'label': 'Regulatory quality index', 'format': '{:.2f}', 'unit': '(scale: -2.5 to 2.5)',
                             'comparison_label': ['Strongest regulatory quality among', 'Weakest regulatory quality among']},
    'wb_wgi_gov_eff':       {'label': 'Government effectiveness index', 'format': '{:.2f}', 'unit': '(scale: -2.5 to 2.5)',
                             'comparison_label': ['Most effective government among', 'Least effective government among']},
    'vdem_political_corruption':  {'label': 'Political corruption index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Most corrupt among', 'Least corrupt among']},
    'vdem_clientelism':           {'label': 'Clientelism index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Most clientelistic among', 'Least clientelistic among']},
    'vdem_electoral_democracy':   {'label': 'Electoral democracy index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Most democratic among', 'Least democratic among']},
    'vdem_physical_violence':     {'label': 'Physical violence index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Least political violence among', 'Most political violence among']},
    'vdem_freedom_of_expression': {'label': 'Freedom of expression index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Freest expression among', 'Least free expression among']},
    'vdem_alternative_info_sources': {'label': 'Alternative info sources index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                      'comparison_label': ['Most independent media among', 'Least independent media among']},
    'vdem_rule_of_law':           {'label': 'Rule of law index', 'format': '{:.2f}', 'unit': '(scale: 0-1)',
                                   'comparison_label': ['Strongest rule of law among', 'Weakest rule of law among']},
    'rsf_press':            {'label': 'Press freedom score', 'format': '{:.1f}', 'unit': 'out of 100',
                             'comparison_label': ['Least free press among', 'Freest press among']},
    'tjn_fsi':              {'label': 'Financial Secrecy Index score', 'format': '{:.0f}', 'unit': '',
                             'comparison_label': ['Most secretive among', 'Least secretive among']},
}


def generate_context_facts(source_key, raw_value, normalized_score, country_code,
                           all_indicator_values):
    """Generate 1-2 context facts for a single indicator.

    Args:
        source_key: indicator key (e.g. 'wb_gini')
        raw_value: the actual raw data value
        normalized_score: 0-100 normalized score
        country_code: ISO alpha-3 code
        all_indicator_values: dict of {country_code: raw_value} for this indicator

    Returns:
        list of fact strings (1-2 items), or empty list if no display config.
    """
    display = INDICATOR_DISPLAY.get(source_key)
    if not display:
        return []

    facts = []

    # Fact 1: raw value with units
    formatted = display['format'].format(raw_value)
    unit_str = f" {display['unit']}" if display['unit'] else ''
    facts.append(f"{display['label']}: {formatted}{unit_str}")

    # Fact 2: peer comparison (if meaningful)
    region = REGION_MAP.get(country_code)
    income = INCOME_GROUP_MAP.get(country_code)

    best_comparison = None
    best_delta = 0

    for group_name, group_map, group_label in [
        (region, REGION_MAP, region),
        (income, INCOME_GROUP_MAP, f"{income.lower()} countries" if income else None),
    ]:
        if not group_name or not group_label:
            continue
        peers = {c: v for c, v in all_indicator_values.items()
                 if (group_map.get(c) == group_name) and c != country_code}
        if len(peers) < 3:
            continue
        peer_avg = sum(peers.values()) / len(peers)
        if peer_avg == 0:
            continue
        delta_pct = abs(raw_value - peer_avg) / abs(peer_avg) * 100
        if delta_pct <= 10:
            continue

        if delta_pct > best_delta:
            best_delta = delta_pct
            all_in_group = {c: v for c, v in all_indicator_values.items()
                           if group_map.get(c) == group_name}
            sorted_vals = sorted(all_in_group.values())
            is_highest = raw_value >= sorted_vals[-1]
            is_lowest = raw_value <= sorted_vals[0]
            avg_formatted = display['format'].format(peer_avg)
            highest_phrase, lowest_phrase = display['comparison_label']

            if is_highest:
                best_comparison = f"{highest_phrase} {group_label} (avg: {avg_formatted})"
            elif is_lowest:
                best_comparison = f"{lowest_phrase} {group_label} (avg: {avg_formatted})"
            elif raw_value > peer_avg:
                best_comparison = f"{delta_pct:.0f}% above {group_label} average ({avg_formatted})"
            else:
                best_comparison = f"{delta_pct:.0f}% below {group_label} average ({avg_formatted})"

    if best_comparison:
        facts.append(best_comparison)

    return facts
```

**Step 2: Verify**

Run: `cd /Users/ovid/projects/extraction/scripts && python -c "exec(open('score_countries.py').read()); print('generate_context_facts OK')"`

**Step 3: Commit**

```bash
git add scripts/score_countries.py
git commit -m "Add generate_context_facts() with clear inverted-indicator phrasing"
```

---

### Task 3: Replace justification string with structured indicators array

**Files:**
- Modify: `scripts/score_countries.py`

This is the core restructuring. Instead of building a `justification` string and separately generating `context_facts`, each domain emits an `indicators` array where each entry carries question, label, and facts together.

**Step 1: Add build_indicator_entry() helper**

Insert after `generate_context_facts()`. This replaces both `build_human_justification()` and the separate context facts generation with a single structured builder:

```python
def build_indicator_entry(source_key, raw_value, normalized_score, country_code,
                          all_indicator_raw):
    """Build a structured indicator entry with question, label, and context facts.

    Returns dict: {key, question, label, facts}
    """
    question = INDICATOR_QUESTIONS.get(source_key, source_key)
    if source_key in POSITIVE_QUESTION_INDICATORS:
        label = score_to_label(100 - normalized_score)
    else:
        label = score_to_label(normalized_score)
    facts = generate_context_facts(
        source_key, raw_value, normalized_score, country_code,
        all_indicator_raw.get(source_key, {}))
    return {
        'key': source_key,
        'question': question,
        'label': label,
        'facts': facts,
    }
```

**Step 2: Build all_indicator_raw lookup in build_country_scores()**

After all data is loaded and normalized (after the `vdem_normalized` block, ~line 491), add:

```python
    # Build per-indicator raw value lookup for peer comparisons
    all_indicator_raw = {}  # {source_key: {country_code: raw_value}}
    for cfg in INDICATOR_CONFIG:
        key = cfg['source_key']
        if cfg['file'] in indicators:
            df = indicators[cfg['file']]
            all_indicator_raw[key] = dict(zip(df['country_code'], df['value']))
    if rsf_scores:
        all_indicator_raw['rsf_press'] = dict(rsf_scores)
    if fsi_scores:
        all_indicator_raw['tjn_fsi'] = dict(fsi_scores)
    vdem_source_key_map = {
        'v2x_corr': 'vdem_political_corruption',
        'v2xnp_client': 'vdem_clientelism',
        'v2x_polyarchy': 'vdem_electoral_democracy',
        'v2x_clphy': 'vdem_physical_violence',
        'v2x_freexp_altinf': 'vdem_freedom_of_expression',
        'v2xme_altinf': 'vdem_alternative_info_sources',
        'v2x_rule': 'vdem_rule_of_law',
    }
    for var, source_key in vdem_source_key_map.items():
        values = {code: vals[var] for code, vals in vdem_raw.items() if var in vals}
        if values:
            all_indicator_raw[source_key] = values
```

**Step 3: Modify World Bank domain construction**

In the per-domain loop (~line 543), replace the `ind_info` / `build_human_justification()` / `build_technical_justification()` block. Instead of building `justification` and `justification_detail` strings, build an `indicators` array:

```python
                ind_entries = []
                for _, row in group.iterrows():
                    entry = build_indicator_entry(
                        row['source_key'], row['value'], int(row['normalized']),
                        code, all_indicator_raw)
                    ind_entries.append(entry)

                # Keep justification_detail for "Show raw data" (technical breakdown)
                ind_info = []
                for _, row in group.iterrows():
                    ind_info.append({
                        'name': row['indicator_name'],
                        'raw': row['value'],
                        'normalized': int(row['normalized']),
                    })
                justification_detail = build_technical_justification('World Bank data', ind_info)
```

Then the domain dict becomes:

```python
                domains[domain] = {
                    'score': score,
                    'confidence': confidence,
                    'trend': trend,
                    'sources': sources,
                    'indicators': ind_entries,
                    'justification_detail': justification_detail,
                    '_n_indicators': n_indicators,
                    '_n_sources': 1,
                    '_most_recent_year': most_recent,
                }
```

Note: `justification` string is removed. `justification_detail` is kept for the "Show raw data" toggle.

**Step 4: Modify RSF domain construction**

Replace the RSF block (~line 568) to use `build_indicator_entry()`:

```python
            rsf_entry = build_indicator_entry('rsf_press', raw_score, rsf_norm, code, all_indicator_raw)
            rsf_ind = [{'name': 'Press Freedom Index', 'raw': raw_score, 'normalized': rsf_norm}]
            domains['information_capture'] = {
                'score': rsf_norm,
                'confidence': rsf_confidence,
                'trend': 'unknown',
                'sources': ['rsf_press'],
                'indicators': [rsf_entry],
                'justification_detail': build_technical_justification('RSF Press Freedom Index', rsf_ind),
                '_n_indicators': 1,
                '_n_sources': 1,
                '_most_recent_year': 2025,
            }
```

**Step 5: Modify FSI domain construction**

Same pattern for FSI (~line 586):

```python
            fsi_entry = build_indicator_entry('tjn_fsi', raw_score, fsi_norm, code, all_indicator_raw)
            fsi_ind = [{'name': 'Financial Secrecy Index', 'raw': raw_score, 'normalized': fsi_norm}]
            domains['transnational_facilitation'] = {
                'score': fsi_norm,
                'confidence': fsi_confidence,
                'trend': 'unknown',
                'sources': ['tjn_fsi'],
                'indicators': [fsi_entry],
                'justification_detail': build_technical_justification('Tax Justice Network FSI', fsi_ind),
                '_n_indicators': 1,
                '_n_sources': 1,
                '_most_recent_year': 2025,
            }
```

**Step 6: Modify V-Dem domain construction**

In the V-Dem per-domain loop (~line 616):

```python
                vdem_ind_entries = []
                vdem_ind_info = []
                for i in indicators_list:
                    src_key = 'vdem_' + i['name'].lower().replace(' ', '_')
                    entry = build_indicator_entry(src_key, i['raw'], i['score'], code, all_indicator_raw)
                    vdem_ind_entries.append(entry)
                    vdem_ind_info.append({
                        'source_key': src_key,
                        'name': i['name'],
                        'raw': i['raw'],
                        'normalized': i['score'],
                    })
                vdem_detail = build_technical_justification('V-Dem', vdem_ind_info)
```

For the **new V-Dem domain** case:

```python
                    domains[domain] = {
                        'score': vdem_score,
                        'confidence': vdem_confidence,
                        'trend': 'unknown',
                        'sources': vdem_sources,
                        'indicators': vdem_ind_entries,
                        'justification_detail': vdem_detail,
                        '_n_indicators': n_vdem,
                        '_n_sources': 1,
                        '_most_recent_year': 2024,
                    }
```

For the **merge with existing** case:

```python
                    domains[domain] = {
                        'score': merged_score,
                        'confidence': assess_domain_confidence(merged_n, merged_sources, merged_year),
                        'trend': existing['trend'] if existing['trend'] != 'unknown' else 'unknown',
                        'sources': existing['sources'] + vdem_sources,
                        'indicators': existing.get('indicators', []) + vdem_ind_entries,
                        'justification_detail': f'{existing.get("justification_detail", "")} {vdem_detail}'.strip(),
                        '_n_indicators': merged_n,
                        '_n_sources': merged_sources,
                        '_most_recent_year': merged_year,
                    }
```

**Step 7: Handle resource_capture composite recalculation**

In the resource_capture composite block (~line 675), after computing `composite_resource`, rebuild the indicators array:

```python
        if 'resource_capture' in domains and 'institutional_gatekeeping' in domains:
            raw_resource = domains['resource_capture']['score']
            inst_weakness = domains['institutional_gatekeeping']['score']
            composite_resource = round(raw_resource * inst_weakness / 100)
            domains['resource_capture']['score'] = composite_resource
            domains['resource_capture']['sources'] = domains['resource_capture']['sources'] + ['wb_wgi_corruption', 'wb_reg_quality', 'wb_wgi_gov_eff']

            # Rebuild indicators for the composite
            # Keep original resource rents fact for context, add composite explanation
            resource_rents_facts = []
            for ind in domains['resource_capture'].get('indicators', []):
                if ind['key'] == 'wb_natural_rents':
                    resource_rents_facts = ind['facts']
                    break
            domains['resource_capture']['indicators'] = [{
                'key': 'resource_capture_composite',
                'question': 'How vulnerable is resource wealth to elite capture?',
                'label': score_to_label(composite_resource),
                'facts': resource_rents_facts + [
                    f'Moderated by institutional strength (score: {100 - inst_weakness}/100)'
                ] if resource_rents_facts else [
                    f'Resource rents score: {raw_resource}, institutional strength: {100 - inst_weakness}/100'
                ],
            }]

            domains['resource_capture']['justification_detail'] = (
                f'{domains["resource_capture"]["justification_detail"]} '
                f'Composite: resource rents ({raw_resource}) \u00d7 institutional weakness ({inst_weakness}) / 100 = {composite_resource}.'
            )
```

And the `elif 'resource_capture' in domains` branch:

```python
        elif 'resource_capture' in domains:
            domains['resource_capture']['confidence'] = 'low'
            score = domains['resource_capture']['score']
            resource_facts = []
            for ind in domains['resource_capture'].get('indicators', []):
                if ind['key'] == 'wb_natural_rents':
                    resource_facts = ind['facts']
                    break
            domains['resource_capture']['indicators'] = [{
                'key': 'resource_capture_composite',
                'question': 'How dependent is the economy on natural resources?',
                'label': score_to_label(score),
                'facts': resource_facts + ['No institutional data available to assess who benefits'],
            }]
```

**Step 8: Remove build_human_justification()**

The function `build_human_justification()` (~line 102-119) is no longer called. Delete it. Keep `build_technical_justification()` since it's still used for `justification_detail`.

**Step 9: Run scorer and verify**

Run: `cd /Users/ovid/projects/extraction/scripts && source ../.venv/bin/activate && python score_countries.py --country USA --preview`

Expected: no errors.

Then run for real and verify JSON structure:

```bash
source ../.venv/bin/activate && python score_countries.py --country USA
python -c "
import json
d = json.load(open('../data/scores.json'))
usa = d['countries']['USA']['domains']
ec = usa['economic_concentration']
print('indicators' in ec)  # True
print('justification' not in ec)  # True
for ind in ec['indicators']:
    print(f\"  {ind['question']} {ind['label']}\")
    for f in ind['facts']:
        print(f'    {f}')
"
```

Then run full scorer:

```bash
python score_countries.py
```

**Step 10: Commit**

```bash
git add scripts/score_countries.py data/scores.json
git commit -m "Replace justification string with structured indicators array

Each domain now emits an indicators array with question, label, and
context facts per indicator. resource_capture indicators are rebuilt
after composite recalculation. build_human_justification() removed."
```

---

### Task 4: Render structured indicators in the frontend

**Files:**
- Modify: `css/style.css` (~line 406, after `ul.domain-justification li`)
- Modify: `js/app.js` (~line 453, the justification rendering)

**Step 1: Add CSS for context facts**

In `css/style.css`, after the `ul.domain-justification li` rule (line 406), add:

```css
ul.domain-justification li .context-fact {
  display: block;
  font-size: 0.65rem;
  color: var(--text-secondary);
  margin-top: 0.1rem;
  font-style: italic;
}
```

**Step 2: Replace justification rendering in app.js**

Replace line 453 (the justification `<ul>` that splits the `justification` string on sentences) with rendering that iterates the `indicators` array:

```javascript
      ${d.indicators?.length ? `<ul class="domain-justification">${d.indicators.map(ind => {
        const factsHtml = (ind.facts || []).map(f => `<span class="context-fact">${f}</span>`).join('');
        return `<li>${ind.question} ${ind.label}${factsHtml}</li>`;
      }).join('')}</ul>` : (d.justification ? `<ul class="domain-justification">${d.justification.split(/(?<=\.)\s+/).filter(s => s.trim()).map(s => `<li>${s.replace(/\.$/, '')}</li>`).join('')}</ul>` : '')}
```

Note: the fallback to `d.justification` handles hand-scored countries that may still use the old format.

**Step 3: Verify visually**

Run: `cd /Users/ovid/projects/extraction && python3 -m http.server 8000`

Open http://localhost:8000, select United States, verify:
- Economic Concentration card shows indicator questions with labels AND context facts below each
- Resource Capture shows the composite question with resource rents fact + institutional moderation note
- Financial Extraction shows domestic credit value
- Both themes render context facts legibly

**Step 4: Commit**

```bash
git add js/app.js css/style.css
git commit -m "Render structured indicators with context facts in domain cards"
```

---

### Task 5: Update schema.json

**Files:**
- Modify: `data/schema.json`

**Step 1: Update the domain_score definition**

In the `definitions.domain_score` object, replace the `justification` property with `indicators` and add `justification_detail`:

```json
    "domain_score": {
      "type": "object",
      "properties": {
        "score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "0 = no extraction detected, 100 = extreme extraction"
        },
        "confidence": {
          "$ref": "#/definitions/confidence_level"
        },
        "trend": {
          "$ref": "#/definitions/trend"
        },
        "sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Source keys referencing the sources documentation"
        },
        "indicators": {
          "type": "array",
          "description": "Structured indicator entries with questions, labels, and context facts",
          "items": {
            "type": "object",
            "properties": {
              "key": { "type": "string", "description": "Source key for this indicator" },
              "question": { "type": "string", "description": "Human-readable question" },
              "label": { "type": "string", "description": "Answer label (Very low to Very high)" },
              "facts": {
                "type": "array",
                "items": { "type": "string" },
                "description": "1-2 concrete facts: raw value and optional peer comparison"
              }
            },
            "required": ["key", "question", "label"]
          }
        },
        "justification_detail": {
          "type": "string",
          "description": "Technical breakdown with raw values and normalized scores"
        }
      },
      "required": ["score", "confidence"]
    }
```

**Step 2: Commit**

```bash
git add data/schema.json
git commit -m "Update schema.json: replace justification with indicators array"
```

---

### Task 6: Update METHODOLOGY.md

**Files:**
- Modify: `METHODOLOGY.md`

**Step 1: Add a section about context facts and peer comparisons**

Add after the existing scoring methodology section. Keep it concise:

```markdown
## Context Facts

Each indicator displays 1-2 concrete facts beneath its score to make abstract numbers meaningful.

**Fact 1 — Raw value:** Always shown. The actual indicator value with units (e.g., "Gini coefficient: 41.8").

**Fact 2 — Peer comparison:** Shown when the country differs meaningfully (>10%) from its peer group average. The scorer compares against both:
- **Regional peers** (UN geoscheme regions: Eastern Africa, Northern Europe, South America, etc.)
- **Income peers** (World Bank income groups: High income, Upper middle income, Lower middle income, Low income)

Whichever comparison produces the larger divergence is shown. If fewer than 3 peers have data, that comparison is skipped.

At extremes, comparisons use natural language appropriate to the indicator — e.g., "Strongest rule of law among high-income countries" rather than generic "Highest among."

For the resource capture domain, context facts reflect the composite calculation (resource rents moderated by institutional strength) rather than raw resource rents alone.
```

**Step 2: Commit**

```bash
git add METHODOLOGY.md
git commit -m "Document context facts and peer comparison methodology"
```

---

### Task 7: End-to-end verification

**Files:** None (verification only)

**Step 1: Spot-check USA**

Verify Economic Concentration shows Gini and GDP per worker facts with peer comparisons.

**Step 2: Spot-check Norway**

Resource Capture should show low composite with "Moderated by institutional strength" fact.

**Step 3: Spot-check a sparse-data country**

Pick a country with 3-4 domains. Verify facts appear where available, no rendering errors.

**Step 4: Spot-check a country missing from REGION_MAP/INCOME_GROUP_MAP**

Verify it gets fact #1 (raw value) but gracefully skips fact #2.

**Step 5: Toggle light/dark theme**

Verify `.context-fact` text is legible in both.

**Step 6: Check hand-scored countries still render**

If any hand-scored countries exist with the old `justification` format, verify the fallback rendering works.
