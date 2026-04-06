#!/usr/bin/env python3
"""
Extraction Index — Auto-Scorer

Reads raw indicator data from raw_data/, normalizes to 0–100 extraction
scores, and updates data/scores.json. Preserves hand-scored countries.

Usage:
    python score_countries.py                  # Score all countries from available data
    python score_countries.py --preview        # Show what would change without writing
    python score_countries.py --country USA    # Score a single country

The script only scores domains for which raw data exists. Domains without
data are omitted (not filled with placeholders). The composite score is
computed from available domains only.

Hand-scored countries (those already in scores.json) are preserved unless
--overwrite is passed.
"""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'raw_data'
SCORES_PATH = PROJECT_ROOT / 'data' / 'scores.json'
WB_DIR = RAW_DATA_DIR / 'worldbank'

# Map indicator files to domains, with normalization direction
# inverted=True means higher raw value = LESS extraction → we flip
INDICATOR_CONFIG = [
    {'file': 'wb_gini.csv',                 'domain': 'economic_concentration',    'inverted': False, 'source_key': 'wb_gini',        'name': 'Gini Index'},
    {'file': 'wb_gdp_per_worker.csv',       'domain': 'economic_concentration',    'inverted': False, 'source_key': 'wb_labor_share', 'name': 'GDP per worker'},
    {'file': 'wb_domestic_credit.csv',       'domain': 'financial_extraction',      'inverted': False, 'source_key': 'wb_domestic_credit', 'name': 'Domestic credit to private sector'},
    {'file': 'wb_natural_rents.csv',         'domain': 'resource_labor_extraction', 'inverted': False, 'source_key': 'wb_natural_rents',   'name': 'Natural resource rents'},
    {'file': 'wb_wgi_corruption.csv',        'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_wgi_corruption',  'name': 'WGI Control of Corruption'},
    {'file': 'wb_wgi_reg_quality.csv',       'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_reg_quality',     'name': 'WGI Regulatory Quality'},
    {'file': 'wb_wgi_gov_effectiveness.csv', 'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_wgi_gov_eff',     'name': 'WGI Government Effectiveness'},
]

# Country name overrides for codes where World Bank names are awkward
COUNTRY_NAME_OVERRIDES = {
    'KOR': 'South Korea',
    'PRK': 'North Korea',
    'IRN': 'Iran',
    'VEN': 'Venezuela',
    'BOL': 'Bolivia',
    'RUS': 'Russia',
    'SYR': 'Syria',
    'TZA': 'Tanzania',
    'VNM': 'Vietnam',
    'LAO': 'Laos',
    'MDA': 'Moldova',
    'MKD': 'North Macedonia',
    'CZE': 'Czechia',
    'COD': 'DR Congo',
    'COG': 'Congo',
    'CIV': 'Ivory Coast',
    'SWZ': 'Eswatini',
    'PSE': 'Palestine',
    'BRN': 'Brunei',
    'GBR': 'United Kingdom',
    'USA': 'United States',
}

# Aggregates and regions to exclude (World Bank includes these as "countries")
EXCLUDE_CODES = {
    'AFE', 'AFW', 'ARB', 'CEB', 'CSS', 'EAP', 'EAR', 'EAS', 'ECA', 'ECS',
    'EMU', 'FCS', 'HIC', 'HPC', 'IBD', 'IBT', 'IDA', 'IDB', 'IDX', 'INX',
    'LAC', 'LCN', 'LDC', 'LIC', 'LMC', 'LMY', 'LTE', 'MEA', 'MIC', 'MNA',
    'NAC', 'OED', 'OSS', 'PRE', 'PSS', 'PST', 'SAS', 'SSA', 'SSF', 'SST',
    'TEA', 'TEC', 'TLA', 'TMN', 'TSA', 'TSS', 'UMC', 'WLD',
    'EUU', 'SXZ', 'XKX',
}


def load_indicator(filepath):
    """Load a World Bank indicator CSV and return most recent value per country."""
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    # Filter out aggregates
    df = df[~df['country_code'].isin(EXCLUDE_CODES)]
    # Filter to valid 3-letter ISO codes
    df = df[df['country_code'].str.len() == 3]
    # Take most recent year per country
    df = df.sort_values('year', ascending=False).drop_duplicates('country_code', keep='first')
    return df[['country_code', 'country_name', 'year', 'value']].copy()


def normalize_minmax(series, inverted=False):
    """Normalize a series to 0–100 using min-max scaling."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(50.0, index=series.index)
    normalized = (series - lo) / (hi - lo) * 100
    if inverted:
        normalized = 100 - normalized
    return normalized.round(0).astype(int)


def estimate_trend(df_full, country_code, indicator_file):
    """Estimate trend by comparing recent vs older values."""
    filepath = WB_DIR / indicator_file
    if not filepath.exists():
        return 'unknown'
    df = pd.read_csv(filepath)
    df = df[df['country_code'] == country_code].sort_values('year')
    if len(df) < 2:
        return 'unknown'
    recent = df[df['year'] >= 2018]['value'].mean()
    older = df[df['year'] <= 2015]['value'].mean()
    if pd.isna(recent) or pd.isna(older) or older == 0:
        return 'unknown'
    change = (recent - older) / abs(older)
    if abs(change) < 0.05:
        return 'stable'
    return 'rising' if change > 0 else 'falling'


def build_country_scores():
    """Build normalized scores for all countries from World Bank data."""
    # Load and normalize each indicator
    indicators = {}
    for cfg in INDICATOR_CONFIG:
        filepath = WB_DIR / cfg['file']
        df = load_indicator(filepath)
        if df.empty:
            continue
        df['normalized'] = normalize_minmax(df['value'], inverted=cfg['inverted'])
        df['domain'] = cfg['domain']
        df['source_key'] = cfg['source_key']
        df['indicator_name'] = cfg['name']
        df['indicator_file'] = cfg['file']
        indicators[cfg['file']] = df

    if not indicators:
        print('No indicator data found in raw_data/worldbank/')
        return {}

    # Combine all indicators
    all_data = pd.concat(indicators.values(), ignore_index=True)

    # Get unique country codes
    country_codes = all_data['country_code'].unique()

    countries = {}
    for code in sorted(country_codes):
        country_data = all_data[all_data['country_code'] == code]

        # Get country name
        name = COUNTRY_NAME_OVERRIDES.get(code,
            country_data['country_name'].iloc[0])

        # Group by domain
        domains = {}
        for domain, group in country_data.groupby('domain'):
            score = int(group['normalized'].mean().round(0))
            sources = group['source_key'].tolist()
            n_indicators = len(group)

            # Confidence based on indicator count within domain
            if n_indicators >= 3:
                confidence = 'moderate'
            elif n_indicators >= 2:
                confidence = 'low'
            else:
                confidence = 'very_low'

            # Estimate trend from the first indicator in this domain
            first_file = group['indicator_file'].iloc[0]
            trend = estimate_trend(all_data, code, first_file)

            # Build justification from actual values
            parts = []
            for _, row in group.iterrows():
                parts.append(f'{row["indicator_name"]}: {row["value"]:.1f} (normalized: {row["normalized"]})')
            justification = f'Auto-scored from World Bank data. {"; ".join(parts)}.'

            domains[domain] = {
                'score': score,
                'confidence': confidence,
                'trend': trend,
                'sources': sources,
                'justification': justification,
            }

        if not domains:
            continue

        # Composite: average of available domains
        scores = [d['score'] for d in domains.values()]
        composite = round(sum(scores) / len(scores))

        # Overall confidence: lowest of domain confidences
        conf_rank = {'very_low': 0, 'low': 1, 'moderate': 2, 'high': 3}
        min_conf = min(domains.values(), key=lambda d: conf_rank[d['confidence']])
        overall_confidence = min_conf['confidence']

        # Overall trend: majority vote
        trends = [d['trend'] for d in domains.values() if d['trend'] != 'unknown']
        if trends:
            from collections import Counter
            overall_trend = Counter(trends).most_common(1)[0][0]
        else:
            overall_trend = 'unknown'

        countries[code] = {
            'name': name,
            'domains': domains,
            'composite_score': composite,
            'overall_confidence': overall_confidence,
            'overall_trend': overall_trend,
            'notes': f'Auto-scored from World Bank indicators ({len(domains)}/7 domains covered).',
        }

    return countries


def main():
    parser = argparse.ArgumentParser(description='Score countries from raw indicator data')
    parser.add_argument('--preview', action='store_true', help='Show changes without writing')
    parser.add_argument('--country', help='Score a single country (ISO alpha-3)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite hand-scored countries')
    args = parser.parse_args()

    # Load existing scores
    with open(SCORES_PATH) as f:
        scores = json.load(f)

    existing_countries = set(scores['countries'].keys())
    print(f'Existing hand-scored countries: {len(existing_countries)} ({", ".join(sorted(existing_countries))})')

    # Build new scores
    print('Loading and normalizing World Bank indicators...')
    new_countries = build_country_scores()
    print(f'Generated scores for {len(new_countries)} countries')

    if args.country:
        code = args.country.upper()
        if code not in new_countries:
            print(f'No data available for {code}')
            return
        new_countries = {code: new_countries[code]}

    # Merge: preserve hand-scored, add auto-scored
    added = 0
    skipped = 0
    overwritten = 0
    for code, data in new_countries.items():
        if code in existing_countries and not args.overwrite:
            skipped += 1
            continue
        if code in existing_countries:
            overwritten += 1
        else:
            added += 1
        if not args.preview:
            scores['countries'][code] = data

    # Update metadata
    if not args.preview:
        scores['metadata']['last_updated'] = str(date.today())
        with open(SCORES_PATH, 'w') as f:
            json.dump(scores, f, indent=2)

    print(f'\nResults:')
    print(f'  Added:       {added} new countries')
    print(f'  Preserved:   {skipped} hand-scored countries')
    if overwritten:
        print(f'  Overwritten: {overwritten} countries')
    print(f'  Total:       {len(scores["countries"])} countries in scores.json')

    if args.preview:
        print('\n(Preview mode — no files written)')
        # Show a sample
        sample_codes = sorted(new_countries.keys())[:5]
        for code in sample_codes:
            c = new_countries[code]
            domains_str = ', '.join(f'{d}={v["score"]}' for d, v in c['domains'].items())
            print(f'  {code} ({c["name"]}): composite={c["composite_score"]} [{domains_str}]')
        if len(new_countries) > 5:
            print(f'  ... and {len(new_countries) - 5} more')


if __name__ == '__main__':
    main()
