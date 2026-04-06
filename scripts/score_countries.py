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

from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'raw_data'
SCORES_PATH = PROJECT_ROOT / 'data' / 'scores.json'
WB_DIR = RAW_DATA_DIR / 'worldbank'
RSF_DIR = RAW_DATA_DIR / 'rsf'
TJN_DIR = RAW_DATA_DIR / 'tjn'
VDEM_DIR = RAW_DATA_DIR / 'vdem'

# Map indicator files to domains, with normalization direction
# inverted=True means higher raw value = LESS extraction → we flip
INDICATOR_CONFIG = [
    {'file': 'wb_gini.csv',                 'domain': 'economic_concentration',    'inverted': False, 'source_key': 'wb_gini',        'name': 'Gini Index'},
    {'file': 'wb_gdp_per_worker.csv',       'domain': 'economic_concentration',    'inverted': False, 'source_key': 'wb_labor_share', 'name': 'GDP per worker'},
    {'file': 'wb_domestic_credit.csv',       'domain': 'financial_extraction',      'inverted': False, 'source_key': 'wb_domestic_credit', 'name': 'Domestic credit to private sector'},
    {'file': 'wb_natural_rents.csv',         'domain': 'resource_capture', 'inverted': False, 'source_key': 'wb_natural_rents',   'name': 'Natural resource rents'},
    {'file': 'wb_wgi_corruption.csv',        'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_wgi_corruption',  'name': 'WGI Control of Corruption'},
    {'file': 'wb_wgi_reg_quality.csv',       'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_reg_quality',     'name': 'WGI Regulatory Quality'},
    {'file': 'wb_wgi_gov_effectiveness.csv', 'domain': 'institutional_gatekeeping', 'inverted': True,  'source_key': 'wb_wgi_gov_eff',     'name': 'WGI Government Effectiveness'},
]

# Human-readable questions for each indicator (used in justifications)
INDICATOR_QUESTIONS = {
    # World Bank indicators
    'wb_gini':              'How unequal is income distribution?',
    'wb_labor_share':       'How little do workers get paid relative to what they produce?',
    'wb_domestic_credit':   'How much wealth is extracted through debt and financial fees?',
    'wb_natural_rents':     'How dependent is the economy on natural resources?',
    'wb_wgi_corruption':    'How well is corruption controlled?',
    'wb_reg_quality':       'How well do government regulations protect people?',
    'wb_wgi_gov_eff':       'How effective is the government?',
    # V-Dem indicators
    'vdem_political_corruption':  'How corrupt is the political system?',
    'vdem_clientelism':           'How common is vote-buying and patronage?',
    'vdem_electoral_democracy':   'How democratic are elections?',
    'vdem_physical_violence':     'How common is political violence?',
    'vdem_freedom_of_expression': 'How free is public expression?',
    'vdem_alternative_info_sources': 'How available are independent information sources?',
    'vdem_rule_of_law':           'How strong is the rule of law?',
    # RSF
    'rsf_press':            'How free is the press?',
    # TJN FSI
    'tjn_fsi':              'How much financial secrecy exists?',
}


def score_to_label(score):
    """Convert a 0-100 extraction score to a human-readable label."""
    if score <= 15:
        return 'Very low'
    elif score <= 35:
        return 'Low'
    elif score <= 55:
        return 'Moderate'
    elif score <= 75:
        return 'High'
    else:
        return 'Very high'


# Indicators whose questions ask about something positive (freedom, democracy, etc.)
# For these, the label should be flipped: a low extraction score means "High" freedom.
POSITIVE_QUESTION_INDICATORS = {
    'wb_wgi_corruption',    # "How well is corruption controlled?" — well = good
    'wb_reg_quality',       # "How well do government regulations protect people?"
    'wb_wgi_gov_eff',       # "How effective is the government?"
    'vdem_electoral_democracy',      # "How democratic are elections?"
    'vdem_freedom_of_expression',    # "How free is public expression?"
    'vdem_alternative_info_sources', # "How available are independent information sources?"
    'vdem_rule_of_law',              # "How strong is the rule of law?"
}


def build_human_justification(indicators_info):
    """Build a human-readable justification from a list of indicator dicts.

    Each dict should have: 'source_key', 'normalized' (0-100 score).
    For indicators in POSITIVE_QUESTION_INDICATORS, the label is flipped
    so the answer matches the question (e.g. low extraction → "High" freedom).
    """
    parts = []
    for ind in indicators_info:
        key = ind['source_key']
        question = INDICATOR_QUESTIONS.get(key, key)
        score = ind['normalized']
        if key in POSITIVE_QUESTION_INDICATORS:
            label = score_to_label(100 - score)
        else:
            label = score_to_label(score)
        parts.append(f'{question} {label}.')
    return ' '.join(parts)


def build_technical_justification(source_label, indicators_info):
    """Build the technical detail string (raw values + normalized scores).

    Each dict should have: 'name', 'raw', 'normalized'.
    """
    parts = [f'{ind["name"]}: {ind["raw"]:.3f} (normalized: {ind["normalized"]})' for ind in indicators_info]
    return f'Auto-scored from {source_label}. {"; ".join(parts)}.'


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
    'AIA': 'Anguilla',
    'COK': 'Cook Islands',
    'GGY': 'Guernsey',
    'GIB': 'Gibraltar',
    'JEY': 'Jersey',
    'MSR': 'Montserrat',
    'VGB': 'British Virgin Islands',
    'TWN': 'Taiwan',
    'XKX': 'Kosovo',
    'IMN': 'Isle of Man',
    'CYM': 'Cayman Islands',
    'LIE': 'Liechtenstein',
    'MCO': 'Monaco',
    'SMR': 'San Marino',
    'MAC': 'Macao',
    'HKG': 'Hong Kong',
    'SYC': 'Seychelles',
    'MUS': 'Mauritius',
    'MDV': 'Maldives',
    'GRD': 'Grenada',
    'KNA': 'Saint Kitts and Nevis',
    'LCA': 'Saint Lucia',
    'DMA': 'Dominica',
    'VCT': 'Saint Vincent and the Grenadines',
    'ATG': 'Antigua and Barbuda',
    'BRB': 'Barbados',
    'NRU': 'Nauru',
    'PLW': 'Palau',
    'MHL': 'Marshall Islands',
    'TON': 'Tonga',
    'WSM': 'Samoa',
    'TCA': 'Turks and Caicos Islands',
    'BHS': 'Bahamas',
    'BMU': 'Bermuda',
    'ABW': 'Aruba',
    'CUW': 'Curaçao',
    'GUM': 'Guam',
    'ASM': 'American Samoa',
    'VIR': 'US Virgin Islands',
    'PRI': 'Puerto Rico',
    'MNP': 'Northern Mariana Islands',
    'GNB': 'Guinea-Bissau',
    'GNQ': 'Equatorial Guinea',
    'TLS': 'Timor-Leste',
}

# Aggregates and regions to exclude (World Bank includes these as "countries")
EXCLUDE_CODES = {
    'AFE', 'AFW', 'ARB', 'CEB', 'CSS', 'EAP', 'EAR', 'EAS', 'ECA', 'ECS',
    'EMU', 'FCS', 'HIC', 'HPC', 'IBD', 'IBT', 'IDA', 'IDB', 'IDX', 'INX',
    'LAC', 'LCN', 'LDC', 'LIC', 'LMC', 'LMY', 'LTE', 'MEA', 'MIC', 'MNA',
    'NAC', 'OED', 'OSS', 'PRE', 'PSS', 'PST', 'SAS', 'SSA', 'SSF', 'SST',
    'TEA', 'TEC', 'TLA', 'TMN', 'TSA', 'TSS', 'UMC', 'WLD',
    'EUU', 'SXZ', 'XKX',
    # Non-standard codes from RSF/V-Dem that aren't real ISO alpha-3
    'CS-KM',  # RSF's code for Kosovo (use XKX mapping instead)
    'CTU',    # RSF: Northern Cyprus (not a recognized country)
    'XCD',    # RSF: OECS (Organisation of Eastern Caribbean States — not a country)
    'PSG',    # V-Dem: Palestine/Gaza (use PSE instead)
    'SML',    # V-Dem: Somaliland (unrecognized territory)
    'ZZB',    # V-Dem: Zanzibar (part of Tanzania)
}


# ISO alpha-2 → alpha-3 mapping for FSI data (which uses 2-letter codes)
ALPHA2_TO_ALPHA3 = {
    'AD': 'AND', 'AE': 'ARE', 'AG': 'ATG', 'AI': 'AIA', 'AL': 'ALB', 'AO': 'AGO',
    'AR': 'ARG', 'AS': 'ASM', 'AT': 'AUT', 'AU': 'AUS', 'AW': 'ABW', 'AZ': 'AZE',
    'BA': 'BIH', 'BB': 'BRB', 'BD': 'BGD', 'BE': 'BEL', 'BG': 'BGR', 'BH': 'BHR',
    'BM': 'BMU', 'BN': 'BRN', 'BO': 'BOL', 'BR': 'BRA', 'BS': 'BHS', 'BW': 'BWA',
    'BZ': 'BLZ', 'CA': 'CAN', 'CH': 'CHE', 'CK': 'COK', 'CL': 'CHL', 'CM': 'CMR',
    'CN': 'CHN', 'CO': 'COL', 'CR': 'CRI', 'CU': 'CUB', 'CW': 'CUW', 'CY': 'CYP',
    'CZ': 'CZE', 'DE': 'DEU', 'DJ': 'DJI', 'DK': 'DNK', 'DM': 'DMA', 'DO': 'DOM',
    'DZ': 'DZA', 'EC': 'ECU', 'EG': 'EGY', 'ER': 'ERI', 'ES': 'ESP', 'ET': 'ETH',
    'FI': 'FIN', 'FR': 'FRA', 'GB': 'GBR', 'GD': 'GRD', 'GE': 'GEO', 'GG': 'GGY',
    'GH': 'GHA', 'GI': 'GIB', 'GM': 'GMB', 'GR': 'GRC', 'GT': 'GTM', 'GU': 'GUM',
    'GW': 'GNB', 'GY': 'GUY', 'HK': 'HKG', 'HN': 'HND', 'HR': 'HRV', 'HU': 'HUN',
    'ID': 'IDN', 'IE': 'IRL', 'IL': 'ISR', 'IM': 'IMN', 'IN': 'IND', 'IQ': 'IRQ',
    'IR': 'IRN', 'IS': 'ISL', 'IT': 'ITA', 'JE': 'JEY', 'JM': 'JAM', 'JO': 'JOR',
    'JP': 'JPN', 'KE': 'KEN', 'KG': 'KGZ', 'KH': 'KHM', 'KN': 'KNA', 'KR': 'KOR',
    'KW': 'KWT', 'KY': 'CYM', 'KZ': 'KAZ', 'LA': 'LAO', 'LB': 'LBN', 'LC': 'LCA',
    'LI': 'LIE', 'LK': 'LKA', 'LR': 'LBR', 'LS': 'LSO', 'LT': 'LTU', 'LU': 'LUX',
    'LV': 'LVA', 'LY': 'LBY', 'MA': 'MAR', 'MC': 'MCO', 'ME': 'MNE', 'MG': 'MDG',
    'MH': 'MHL', 'MK': 'MKD', 'ML': 'MLI', 'MM': 'MMR', 'MN': 'MNG', 'MO': 'MAC',
    'MR': 'MRT', 'MS': 'MSR', 'MT': 'MLT', 'MU': 'MUS', 'MV': 'MDV', 'MW': 'MWI',
    'MX': 'MEX', 'MY': 'MYS', 'MZ': 'MOZ', 'NA': 'NAM', 'NG': 'NGA', 'NI': 'NIC',
    'NL': 'NLD', 'NO': 'NOR', 'NP': 'NPL', 'NR': 'NRU', 'NZ': 'NZL', 'OM': 'OMN',
    'PA': 'PAN', 'PE': 'PER', 'PG': 'PNG', 'PH': 'PHL', 'PK': 'PAK', 'PL': 'POL',
    'PR': 'PRI', 'PT': 'PRT', 'PW': 'PLW', 'PY': 'PRY', 'QA': 'QAT', 'RO': 'ROU',
    'RS': 'SRB', 'RU': 'RUS', 'RW': 'RWA', 'SA': 'SAU', 'SC': 'SYC', 'SD': 'SDN',
    'SE': 'SWE', 'SG': 'SGP', 'SI': 'SVN', 'SK': 'SVK', 'SL': 'SLE', 'SM': 'SMR',
    'SN': 'SEN', 'SO': 'SOM', 'SR': 'SUR', 'SS': 'SSD', 'SV': 'SLV', 'SZ': 'SWZ',
    'TC': 'TCA', 'TD': 'TCD', 'TG': 'TGO', 'TH': 'THA', 'TN': 'TUN', 'TO': 'TON',
    'TR': 'TUR', 'TT': 'TTO', 'TW': 'TWN', 'TZ': 'TZA', 'UA': 'UKR', 'UG': 'UGA',
    'US': 'USA', 'UY': 'URY', 'UZ': 'UZB', 'VC': 'VCT', 'VE': 'VEN', 'VG': 'VGB',
    'VI': 'VIR', 'VN': 'VNM', 'VU': 'VUT', 'WS': 'WSM', 'ZA': 'ZAF', 'ZM': 'ZMB',
    'ZW': 'ZWE',
    'EE': 'EST', 'FJ': 'FJI', 'XK': 'XKX',
}


RSF_CODE_REMAP = {
    'SEY': 'SYC',  # Seychelles
}

def load_rsf_data():
    """Load RSF press freedom scores. Returns dict of {alpha3: score}."""
    csv_path = RSF_DIR / 'rsf_scores.csv'
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty or 'score' not in df.columns:
        return {}
    df['country_code'] = df['country_code'].replace(RSF_CODE_REMAP)
    # Filter out excluded codes
    df = df[~df['country_code'].isin(EXCLUDE_CODES)]
    return dict(zip(df['country_code'], df['score']))


def load_fsi_data():
    """Load FSI financial secrecy scores. Returns dict of {alpha3: score}."""
    csv_path = TJN_DIR / 'fsi_jurisdictions.csv'
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty:
        return {}
    # Take most recent edition
    latest_scoring = df['methodology_id'].unique()[-1]
    df = df[df['methodology_id'] == latest_scoring]
    # Map alpha-2 to alpha-3
    result = {}
    for _, row in df.iterrows():
        a3 = ALPHA2_TO_ALPHA3.get(row['jurisdiction_id'])
        if a3 and pd.notna(row['index_score']):
            result[a3] = float(row['index_score'])
    return result


def load_vdem_data():
    """Load V-Dem indicators. Returns dict of {alpha3: {var: value}} for most recent year."""
    csv_path = VDEM_DIR / 'vdem_extract.csv'
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty:
        return {}
    # Filter out excluded codes
    df = df[~df['country_text_id'].isin(EXCLUDE_CODES)]
    # Take most recent year per country
    df = df.sort_values('year', ascending=False).drop_duplicates('country_text_id', keep='first')
    result = {}
    vdem_vars = ['v2x_polyarchy', 'v2x_corr', 'v2xnp_client',
                 'v2x_freexp_altinf', 'v2xme_altinf', 'v2x_clphy', 'v2x_rule']
    for _, row in df.iterrows():
        code = row['country_text_id']
        vals = {}
        for v in vdem_vars:
            if v in row and pd.notna(row[v]):
                vals[v] = float(row[v])
        if vals:
            result[code] = vals
    return result


def assess_domain_confidence(n_indicators, n_sources, most_recent_year):
    """Assess confidence for a domain based on data reliability.

    Factors:
      1. Completeness — number of indicators with data
      2. Source diversity — number of independent data sources
      3. Recency — how recent the most recent data point is

    Returns one of: 'high', 'moderate', 'low', 'very_low'
    """
    # Score each factor 0-3
    # Completeness
    if n_indicators >= 4:
        completeness = 3
    elif n_indicators >= 3:
        completeness = 2
    elif n_indicators >= 2:
        completeness = 1
    else:
        completeness = 0

    # Source diversity (how many independent datasets contribute)
    if n_sources >= 3:
        diversity = 3
    elif n_sources >= 2:
        diversity = 2
    elif n_sources >= 1:
        diversity = 1
    else:
        diversity = 0

    # Recency
    if most_recent_year is None:
        recency = 0
    elif most_recent_year >= 2022:
        recency = 3
    elif most_recent_year >= 2019:
        recency = 2
    elif most_recent_year >= 2015:
        recency = 1
    else:
        recency = 0

    total = completeness + diversity + recency  # 0-9

    if total >= 7:
        return 'high'
    elif total >= 5:
        return 'moderate'
    elif total >= 3:
        return 'low'
    else:
        return 'very_low'


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


def estimate_trend(df_full, country_code, indicator_file, inverted=False):
    """Estimate trend by comparing recent vs older values.

    For inverted indicators (higher raw value = less extraction), a falling
    raw value means extraction is rising, so we flip the direction.
    """
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
    if inverted:
        change = -change  # Falling raw value = rising extraction
    if abs(change) < 0.10:
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

    # Load RSF data (information_capture)
    rsf_scores = load_rsf_data()
    if rsf_scores:
        print(f'  RSF: {len(rsf_scores)} countries')
        rsf_series = pd.Series(rsf_scores)
        rsf_normalized = normalize_minmax(rsf_series, inverted=False)  # Higher RSF = less free = more extraction
        rsf_map = dict(zip(rsf_series.index, rsf_normalized))
    else:
        rsf_map = {}

    # Load FSI data (transnational_facilitation)
    fsi_scores = load_fsi_data()
    if fsi_scores:
        print(f'  FSI: {len(fsi_scores)} countries')
        fsi_series = pd.Series(fsi_scores)
        fsi_normalized = normalize_minmax(fsi_series, inverted=False)  # Higher FSI = more secretive = more extraction
        fsi_map = dict(zip(fsi_series.index, fsi_normalized))
    else:
        fsi_map = {}

    # Load V-Dem data (political_capture + information_capture)
    vdem_raw = load_vdem_data()
    if vdem_raw:
        print(f'  V-Dem: {len(vdem_raw)} countries')
        # Normalize each V-Dem variable across all countries
        # political_capture indicators: v2x_corr (direct), v2xnp_client (direct),
        #   v2x_polyarchy (inverted), v2x_clphy (inverted)
        # information_capture: v2x_freexp_altinf (inverted), v2xme_altinf (inverted)
        # institutional_gatekeeping: v2x_rule (inverted)
        vdem_vars_config = {
            'v2x_corr':          {'domain': 'political_capture',       'inverted': False, 'name': 'Political Corruption'},
            'v2xnp_client':      {'domain': 'political_capture',       'inverted': False, 'name': 'Clientelism'},
            'v2x_polyarchy':     {'domain': 'political_capture',       'inverted': True,  'name': 'Electoral Democracy'},
            'v2x_clphy':         {'domain': 'political_capture',       'inverted': True,  'name': 'Physical Violence'},
            'v2x_freexp_altinf': {'domain': 'information_capture',     'inverted': True,  'name': 'Freedom of Expression'},
            'v2xme_altinf':      {'domain': 'information_capture',     'inverted': True,  'name': 'Alternative Info Sources'},
            'v2x_rule':          {'domain': 'institutional_gatekeeping', 'inverted': True, 'name': 'Rule of Law'},
        }
        # Build per-variable series for normalization
        vdem_normalized = {}  # {country: {var: normalized_score}}
        for var, cfg in vdem_vars_config.items():
            values = {code: vals[var] for code, vals in vdem_raw.items() if var in vals}
            if not values:
                continue
            series = pd.Series(values)
            normed = normalize_minmax(series, inverted=cfg['inverted'])
            for code, score in normed.items():
                if code not in vdem_normalized:
                    vdem_normalized[code] = {}
                vdem_normalized[code][var] = {'score': int(score), 'raw': values[code], 'name': cfg['name'], 'domain': cfg['domain']}
    else:
        vdem_normalized = {}

    if not indicators and not rsf_map and not fsi_map and not vdem_normalized:
        print('No indicator data found!')
        return {}

    # Combine all World Bank indicators
    all_data = pd.concat(indicators.values(), ignore_index=True) if indicators else pd.DataFrame()

    # Get unique country codes from all sources
    country_codes = set()
    if not all_data.empty:
        country_codes.update(all_data['country_code'].unique())
    country_codes.update(rsf_map.keys())
    country_codes.update(fsi_map.keys())
    country_codes.update(vdem_normalized.keys())

    countries = {}
    for code in sorted(country_codes):
        country_data = all_data[all_data['country_code'] == code] if not all_data.empty else pd.DataFrame()

        # Get country name
        if not country_data.empty:
            name = COUNTRY_NAME_OVERRIDES.get(code, country_data['country_name'].iloc[0])
        else:
            name = COUNTRY_NAME_OVERRIDES.get(code, code)

        # Group World Bank indicators by domain
        domains = {}
        source_names = []
        if not country_data.empty:
            for domain, group in country_data.groupby('domain'):
                score = int(group['normalized'].mean().round(0))
                sources = group['source_key'].tolist()
                n_indicators = len(group)
                most_recent = int(group['year'].max())

                confidence = assess_domain_confidence(n_indicators, 1, most_recent)

                # Estimate trend using majority vote across all indicators in domain
                trend_votes = []
                for _, row in group.iterrows():
                    cfg = next((c for c in INDICATOR_CONFIG if c['file'] == row['indicator_file']), None)
                    inv = cfg['inverted'] if cfg else False
                    t = estimate_trend(all_data, code, row['indicator_file'], inverted=inv)
                    if t != 'unknown':
                        trend_votes.append(t)
                if trend_votes:
                    trend = Counter(trend_votes).most_common(1)[0][0]
                else:
                    trend = 'unknown'

                ind_info = []
                for _, row in group.iterrows():
                    ind_info.append({
                        'source_key': row['source_key'],
                        'name': row['indicator_name'],
                        'raw': row['value'],
                        'normalized': int(row['normalized']),
                    })
                justification = build_human_justification(ind_info)
                justification_detail = build_technical_justification('World Bank data', ind_info)

                domains[domain] = {
                    'score': score,
                    'confidence': confidence,
                    'trend': trend,
                    'sources': sources,
                    'justification': justification,
                    'justification_detail': justification_detail,
                    '_n_indicators': n_indicators,
                    '_n_sources': 1,
                    '_most_recent_year': most_recent,
                }
            source_names.append('World Bank')

        # Add RSF (information_capture) — RSF 2025 data
        if code in rsf_map:
            raw_score = rsf_scores[code]
            rsf_confidence = assess_domain_confidence(1, 1, 2025)
            rsf_norm = int(rsf_map[code])
            rsf_ind = [{'source_key': 'rsf_press', 'name': 'Press Freedom Index', 'raw': raw_score, 'normalized': rsf_norm}]
            domains['information_capture'] = {
                'score': rsf_norm,
                'confidence': rsf_confidence,
                'trend': 'unknown',
                'sources': ['rsf_press'],
                'justification': build_human_justification(rsf_ind),
                'justification_detail': build_technical_justification('RSF Press Freedom Index', rsf_ind),
                '_n_indicators': 1,
                '_n_sources': 1,
                '_most_recent_year': 2025,
            }
            source_names.append('RSF')

        # Add FSI (transnational_facilitation) — FSI 2025 data
        if code in fsi_map:
            raw_score = fsi_scores[code]
            fsi_confidence = assess_domain_confidence(1, 1, 2025)
            fsi_norm = int(fsi_map[code])
            fsi_ind = [{'source_key': 'tjn_fsi', 'name': 'Financial Secrecy Index', 'raw': raw_score, 'normalized': fsi_norm}]
            domains['transnational_facilitation'] = {
                'score': fsi_norm,
                'confidence': fsi_confidence,
                'trend': 'unknown',
                'sources': ['tjn_fsi'],
                'justification': build_human_justification(fsi_ind),
                'justification_detail': build_technical_justification('Tax Justice Network FSI', fsi_ind),
                '_n_indicators': 1,
                '_n_sources': 1,
                '_most_recent_year': 2025,
            }
            source_names.append('TJN')

        # Add V-Dem indicators (political_capture, information_capture, institutional_gatekeeping)
        if code in vdem_normalized:
            vdem_country = vdem_normalized[code]
            # Group V-Dem indicators by domain
            vdem_by_domain = {}
            for var, info in vdem_country.items():
                domain = info['domain']
                if domain not in vdem_by_domain:
                    vdem_by_domain[domain] = []
                vdem_by_domain[domain].append(info)

            for domain, indicators_list in vdem_by_domain.items():
                vdem_score = round(sum(i['score'] for i in indicators_list) / len(indicators_list))
                vdem_sources = ['vdem_' + i['name'].lower().replace(' ', '_') for i in indicators_list]
                n_vdem = len(indicators_list)

                vdem_ind_info = []
                for i in indicators_list:
                    src_key = 'vdem_' + i['name'].lower().replace(' ', '_')
                    vdem_ind_info.append({
                        'source_key': src_key,
                        'name': i['name'],
                        'raw': i['raw'],
                        'normalized': i['score'],
                    })
                vdem_justification = build_human_justification(vdem_ind_info)
                vdem_detail = build_technical_justification('V-Dem', vdem_ind_info)

                if domain in domains:
                    # Merge with existing domain score (average of WB/RSF and V-Dem)
                    existing = domains[domain]
                    merged_score = round((existing['score'] + vdem_score) / 2)
                    merged_n = existing.get('_n_indicators', 1) + n_vdem
                    merged_sources = existing.get('_n_sources', 1) + 1
                    merged_year = max(existing.get('_most_recent_year') or 0, 2024)
                    domains[domain] = {
                        'score': merged_score,
                        'confidence': assess_domain_confidence(merged_n, merged_sources, merged_year),
                        'trend': existing['trend'] if existing['trend'] != 'unknown' else 'unknown',
                        'sources': existing['sources'] + vdem_sources,
                        'justification': f'{existing["justification"]} {vdem_justification}',
                        'justification_detail': f'{existing.get("justification_detail", "")} {vdem_detail}'.strip(),
                        '_n_indicators': merged_n,
                        '_n_sources': merged_sources,
                        '_most_recent_year': merged_year,
                    }
                else:
                    vdem_confidence = assess_domain_confidence(n_vdem, 1, 2024)
                    domains[domain] = {
                        'score': vdem_score,
                        'confidence': vdem_confidence,
                        'trend': 'unknown',
                        'sources': vdem_sources,
                        'justification': vdem_justification,
                        'justification_detail': vdem_detail,
                        '_n_indicators': n_vdem,
                        '_n_sources': 1,
                        '_most_recent_year': 2024,
                    }
            source_names.append('V-Dem')

        # Similarly merge V-Dem info_capture with RSF if both exist
        # (already handled by the merge logic above)

        if not domains:
            continue

        # Resource capture: composite of resource rents × institutional weakness
        # High resource rents + weak institutions = high extraction risk
        # High resource rents + strong institutions (e.g. Norway) = low extraction risk
        if 'resource_capture' in domains and 'institutional_gatekeeping' in domains:
            raw_resource = domains['resource_capture']['score']
            inst_weakness = domains['institutional_gatekeeping']['score']
            # Multiply resource dependence by institutional weakness (both 0-100)
            # Scale back to 0-100
            composite_resource = round(raw_resource * inst_weakness / 100)
            domains['resource_capture']['score'] = composite_resource
            domains['resource_capture']['sources'] = domains['resource_capture']['sources'] + ['wb_wgi_corruption', 'wb_reg_quality', 'wb_wgi_gov_eff']
            domains['resource_capture']['justification'] = (
                f'How vulnerable is resource wealth to elite capture? {score_to_label(composite_resource)}.'
            )
            domains['resource_capture']['justification_detail'] = (
                f'{domains["resource_capture"]["justification_detail"]} '
                f'Composite: resource rents ({raw_resource}) × institutional weakness ({inst_weakness}) / 100 = {composite_resource}.'
            )
        elif 'resource_capture' in domains:
            # No institutional data to weight against — mark low confidence
            domains['resource_capture']['confidence'] = 'low'
            domains['resource_capture']['justification'] = (
                f'How dependent is the economy on natural resources? {score_to_label(domains["resource_capture"]["score"])}. '
                f'(No institutional data available to assess who benefits.)'
            )

        # Compute overall confidence from totals across all domains
        total_indicators = sum(d.get('_n_indicators', 1) for d in domains.values())
        total_sources = len(set(source_names))
        all_years = [d.get('_most_recent_year') for d in domains.values() if d.get('_most_recent_year')]
        overall_most_recent = max(all_years) if all_years else None
        overall_confidence = assess_domain_confidence(total_indicators, total_sources, overall_most_recent)

        # Downgrade overall confidence based on domain coverage
        n_domains = len(domains)
        if n_domains <= 3:
            # Cap at 'low' if less than half domains covered
            conf_cap = 'low'
        elif n_domains <= 5:
            conf_cap = 'moderate'
        else:
            conf_cap = 'high'
        conf_rank = {'very_low': 0, 'low': 1, 'moderate': 2, 'high': 3}
        if conf_rank[overall_confidence] > conf_rank[conf_cap]:
            overall_confidence = conf_cap

        # Clean internal tracking fields from domain entries
        for d in domains.values():
            d.pop('_n_indicators', None)
            d.pop('_n_sources', None)
            d.pop('_most_recent_year', None)

        # Composite: average of available domains
        scores = [d['score'] for d in domains.values()]
        composite = round(sum(scores) / len(scores))

        # Overall trend: majority vote
        trends = [d['trend'] for d in domains.values() if d['trend'] != 'unknown']
        if trends:
            overall_trend = Counter(trends).most_common(1)[0][0]
        else:
            overall_trend = 'unknown'

        unique_sources = sorted(set(source_names))
        countries[code] = {
            'name': name,
            'domains': domains,
            'composite_score': composite,
            'overall_confidence': overall_confidence,
            'overall_trend': overall_trend,
            'notes': f'Auto-scored from {", ".join(unique_sources)} ({len(domains)}/7 domains covered).',
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

    # Distinguish hand-scored from auto-scored
    hand_scored = {k for k, v in scores['countries'].items()
                   if not v.get('notes', '').startswith('Auto-scored')}
    print(f'Hand-scored countries: {len(hand_scored)} ({", ".join(sorted(hand_scored))})')

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

    # Merge: always preserve hand-scored, update auto-scored
    added = 0
    skipped = 0
    overwritten = 0
    for code, data in new_countries.items():
        if code in hand_scored and not args.overwrite:
            skipped += 1
            continue
        if code in scores['countries']:
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
