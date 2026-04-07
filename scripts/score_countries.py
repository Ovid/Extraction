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
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "raw_data"
SCORES_PATH = PROJECT_ROOT / "data" / "scores.json"
WB_DIR = RAW_DATA_DIR / "worldbank"
RSF_DIR = RAW_DATA_DIR / "rsf"
TJN_DIR = RAW_DATA_DIR / "tjn"
VDEM_DIR = RAW_DATA_DIR / "vdem"

# Map indicator files to domains, with normalization direction
# inverted=True means higher raw value = LESS extraction → we flip
INDICATOR_CONFIG = [
    {
        "file": "wb_gini.csv",
        "domain": "economic_concentration",
        "inverted": False,
        "source_key": "wb_gini",
        "name": "Gini Index",
    },
    {
        "file": "wb_gdp_per_worker.csv",
        "domain": "economic_concentration",
        "inverted": False,
        "source_key": "wb_labor_share",
        "name": "GDP per worker",
    },
    {
        "file": "wb_domestic_credit.csv",
        "domain": "financial_extraction",
        "inverted": False,
        "source_key": "wb_domestic_credit",
        "name": "Domestic credit to private sector",
    },
    {
        "file": "wb_natural_rents.csv",
        "domain": "resource_capture",
        "inverted": False,
        "source_key": "wb_natural_rents",
        "name": "Natural resource rents",
    },
    {
        "file": "wb_wgi_corruption.csv",
        "domain": "institutional_gatekeeping",
        "inverted": True,
        "source_key": "wb_wgi_corruption",
        "name": "WGI Control of Corruption",
    },
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
]

# Human-readable questions for each indicator (used in justifications)
INDICATOR_QUESTIONS = {
    # World Bank indicators
    "wb_gini": "How unequal is income distribution?",
    "wb_labor_share": "How little do workers get paid relative to what they produce?",
    "wb_domestic_credit": "How much wealth is extracted through debt and financial fees?",
    "wb_natural_rents": "How dependent is the economy on natural resources?",
    "wb_wgi_corruption": "How well is corruption controlled?",
    "wb_reg_quality": "How well do government regulations protect people?",
    "wb_wgi_gov_eff": "How effective is the government?",
    # V-Dem indicators
    "vdem_political_corruption": "How corrupt is the political system?",
    "vdem_clientelism": "How common is vote-buying and patronage?",
    "vdem_electoral_democracy": "How democratic are elections?",
    "vdem_physical_violence": "How common is political violence?",
    "vdem_freedom_of_expression": "How free is public expression?",
    "vdem_alternative_info_sources": "How available are independent information sources?",
    "vdem_rule_of_law": "How strong is the rule of law?",
    "vdem_egalitarian": "How equally are political power and resources distributed?",
    "vdem_participatory_democracy": "How much can citizens participate in governance?",
    # RSF
    "rsf_press": "How free is the press?",
    # TJN FSI
    "tjn_fsi": "How much financial secrecy exists?",
}


def score_to_label(score):
    """Convert a 0-100 extraction score to a human-readable label."""
    if score <= 15:
        return "Very low"
    elif score <= 35:
        return "Low"
    elif score <= 55:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Very high"


# Indicators whose questions ask about something positive (freedom, democracy, etc.)
# For these, the label should be flipped: a low extraction score means "High" freedom.
POSITIVE_QUESTION_INDICATORS = {
    "wb_wgi_corruption",  # "How well is corruption controlled?" — well = good
    "wb_reg_quality",  # "How well do government regulations protect people?"
    "wb_wgi_gov_eff",  # "How effective is the government?"
    "vdem_electoral_democracy",  # "How democratic are elections?"
    "vdem_freedom_of_expression",  # "How free is public expression?"
    "vdem_alternative_info_sources",  # "How available are independent information sources?"
    "vdem_rule_of_law",  # "How strong is the rule of law?"
    "vdem_egalitarian",  # "How equally are...?" — equal = good
    "vdem_participatory_democracy",  # "How much can citizens...?" — participation = good
    "rsf_press",  # "How free is the press?" — free = good
}


def build_technical_justification(source_label, indicators_info):
    """Build the technical detail string (raw values + normalized scores).

    Each dict should have: 'name', 'raw', 'normalized'.
    """
    parts = [f"{ind['name']}: {ind['raw']:.3f} (normalized: {ind['normalized']})" for ind in indicators_info]
    return f"Auto-scored from {source_label}. {'; '.join(parts)}."


# Display formatting for context facts
# comparison_label: [highest_phrase, lowest_phrase] for natural language at extremes
INDICATOR_DISPLAY = {
    "wb_gini": {
        "label": "Gini coefficient",
        "format": "{:.1f}",
        "unit": "",
        "comparison_label": ["Most unequal among", "Most equal among"],
    },
    "wb_labor_share": {
        "label": "GDP per worker",
        "format": "${:,.0f}",
        "unit": "",
        "comparison_label": ["Highest among", "Lowest among"],
    },
    "wb_domestic_credit": {
        "label": "Domestic credit to private sector",
        "format": "{:.1f}",
        "unit": "% of GDP",
        "comparison_label": ["Most financialized among", "Least financialized among"],
    },
    "wb_natural_rents": {
        "label": "Natural resource rents",
        "format": "{:.1f}",
        "unit": "% of GDP",
        "comparison_label": ["Most resource-dependent among", "Least resource-dependent among"],
    },
    "wb_wgi_corruption": {
        "label": "Control of corruption index",
        "format": "{:.2f}",
        "unit": "(scale: -2.5 to 2.5)",
        "comparison_label": ["Strongest corruption control among", "Weakest corruption control among"],
    },
    "wb_reg_quality": {
        "label": "Regulatory quality index",
        "format": "{:.2f}",
        "unit": "(scale: -2.5 to 2.5)",
        "comparison_label": ["Strongest regulatory quality among", "Weakest regulatory quality among"],
    },
    "wb_wgi_gov_eff": {
        "label": "Government effectiveness index",
        "format": "{:.2f}",
        "unit": "(scale: -2.5 to 2.5)",
        "comparison_label": ["Most effective government among", "Least effective government among"],
    },
    "vdem_political_corruption": {
        "label": "Political corruption index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most corrupt among", "Least corrupt among"],
    },
    "vdem_clientelism": {
        "label": "Clientelism index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most clientelistic among", "Least clientelistic among"],
    },
    "vdem_electoral_democracy": {
        "label": "Electoral democracy index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most democratic among", "Least democratic among"],
    },
    "vdem_physical_violence": {
        "label": "Physical violence index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Least political violence among", "Most political violence among"],
    },
    "vdem_freedom_of_expression": {
        "label": "Freedom of expression index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Freest expression among", "Least free expression among"],
    },
    "vdem_alternative_info_sources": {
        "label": "Alternative info sources index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most independent media among", "Least independent media among"],
    },
    "vdem_rule_of_law": {
        "label": "Rule of law index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Strongest rule of law among", "Weakest rule of law among"],
    },
    "vdem_egalitarian": {
        "label": "Egalitarian component index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most egalitarian among", "Least egalitarian among"],
    },
    "vdem_participatory_democracy": {
        "label": "Participatory democracy index",
        "format": "{:.2f}",
        "unit": "(scale: 0-1)",
        "comparison_label": ["Most participatory among", "Least participatory among"],
    },
    "rsf_press": {
        "label": "Press freedom score",
        "format": "{:.1f}",
        "unit": "out of 100",
        "comparison_label": ["Freest press among", "Least free press among"],
    },
    "tjn_fsi": {
        "label": "Financial Secrecy Index score",
        "format": "{:.0f}",
        "unit": "",
        "comparison_label": ["Most secretive among", "Least secretive among"],
    },
}


def generate_context_facts(source_key, raw_value, normalized_score, country_code, all_indicator_values):
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
    formatted = display["format"].format(raw_value)
    unit_str = f" {display['unit']}" if display["unit"] else ""
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
        peers = {
            c: v for c, v in all_indicator_values.items() if (group_map.get(c) == group_name) and c != country_code
        }
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
            all_in_group = {c: v for c, v in all_indicator_values.items() if group_map.get(c) == group_name}
            sorted_vals = sorted(all_in_group.values())
            is_highest = raw_value >= sorted_vals[-1]
            is_lowest = raw_value <= sorted_vals[0]
            avg_formatted = display["format"].format(peer_avg)
            highest_phrase, lowest_phrase = display["comparison_label"]

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


def build_indicator_entry(source_key, raw_value, normalized_score, country_code, all_indicator_raw):
    """Build a structured indicator entry with question, label, and context facts.

    Returns dict: {key, question, label, facts}
    """
    question = INDICATOR_QUESTIONS.get(source_key, source_key)
    if source_key in POSITIVE_QUESTION_INDICATORS:
        label = score_to_label(100 - normalized_score)
    else:
        label = score_to_label(normalized_score)
    facts = generate_context_facts(
        source_key, raw_value, normalized_score, country_code, all_indicator_raw.get(source_key, {})
    )
    return {
        "key": source_key,
        "question": question,
        "label": label,
        "facts": facts,
    }


# Country name overrides for codes where World Bank names are awkward
COUNTRY_NAME_OVERRIDES = {
    "KOR": "South Korea",
    "PRK": "North Korea",
    "IRN": "Iran",
    "VEN": "Venezuela",
    "BOL": "Bolivia",
    "RUS": "Russia",
    "SYR": "Syria",
    "TZA": "Tanzania",
    "VNM": "Vietnam",
    "LAO": "Laos",
    "MDA": "Moldova",
    "MKD": "North Macedonia",
    "CZE": "Czechia",
    "COD": "DR Congo",
    "COG": "Congo",
    "CIV": "Ivory Coast",
    "SWZ": "Eswatini",
    "PSE": "Palestine",
    "BRN": "Brunei",
    "GBR": "United Kingdom",
    "USA": "United States",
    "AIA": "Anguilla",
    "COK": "Cook Islands",
    "GGY": "Guernsey",
    "GIB": "Gibraltar",
    "JEY": "Jersey",
    "MSR": "Montserrat",
    "VGB": "British Virgin Islands",
    "TWN": "Taiwan",
    "XKX": "Kosovo",
    "IMN": "Isle of Man",
    "CYM": "Cayman Islands",
    "LIE": "Liechtenstein",
    "MCO": "Monaco",
    "SMR": "San Marino",
    "MAC": "Macao",
    "HKG": "Hong Kong",
    "SYC": "Seychelles",
    "MUS": "Mauritius",
    "MDV": "Maldives",
    "GRD": "Grenada",
    "KNA": "Saint Kitts and Nevis",
    "LCA": "Saint Lucia",
    "DMA": "Dominica",
    "VCT": "Saint Vincent and the Grenadines",
    "ATG": "Antigua and Barbuda",
    "BRB": "Barbados",
    "NRU": "Nauru",
    "PLW": "Palau",
    "MHL": "Marshall Islands",
    "TON": "Tonga",
    "WSM": "Samoa",
    "TCA": "Turks and Caicos Islands",
    "BHS": "Bahamas",
    "BMU": "Bermuda",
    "ABW": "Aruba",
    "CUW": "Curaçao",
    "GUM": "Guam",
    "ASM": "American Samoa",
    "VIR": "US Virgin Islands",
    "PRI": "Puerto Rico",
    "MNP": "Northern Mariana Islands",
    "GNB": "Guinea-Bissau",
    "GNQ": "Equatorial Guinea",
    "TLS": "Timor-Leste",
}

# UN geoscheme region mapping for peer comparisons
REGION_MAP = {
    # Eastern Africa
    "BDI": "Eastern Africa",
    "COM": "Eastern Africa",
    "DJI": "Eastern Africa",
    "ERI": "Eastern Africa",
    "ETH": "Eastern Africa",
    "KEN": "Eastern Africa",
    "MDG": "Eastern Africa",
    "MWI": "Eastern Africa",
    "MUS": "Eastern Africa",
    "MOZ": "Eastern Africa",
    "RWA": "Eastern Africa",
    "SYC": "Eastern Africa",
    "SOM": "Eastern Africa",
    "SSD": "Eastern Africa",
    "TZA": "Eastern Africa",
    "UGA": "Eastern Africa",
    "ZMB": "Eastern Africa",
    "ZWE": "Eastern Africa",
    # Middle Africa
    "AGO": "Middle Africa",
    "CMR": "Middle Africa",
    "CAF": "Middle Africa",
    "TCD": "Middle Africa",
    "COG": "Middle Africa",
    "COD": "Middle Africa",
    "GNQ": "Middle Africa",
    "GAB": "Middle Africa",
    # Northern Africa
    "DZA": "Northern Africa",
    "EGY": "Northern Africa",
    "LBY": "Northern Africa",
    "MAR": "Northern Africa",
    "SDN": "Northern Africa",
    "TUN": "Northern Africa",
    # Southern Africa
    "BWA": "Southern Africa",
    "SWZ": "Southern Africa",
    "LSO": "Southern Africa",
    "NAM": "Southern Africa",
    "ZAF": "Southern Africa",
    # Western Africa
    "BEN": "Western Africa",
    "BFA": "Western Africa",
    "CPV": "Western Africa",
    "CIV": "Western Africa",
    "GMB": "Western Africa",
    "GHA": "Western Africa",
    "GIN": "Western Africa",
    "GNB": "Western Africa",
    "LBR": "Western Africa",
    "MLI": "Western Africa",
    "MRT": "Western Africa",
    "NER": "Western Africa",
    "NGA": "Western Africa",
    "SEN": "Western Africa",
    "SLE": "Western Africa",
    "TGO": "Western Africa",
    # Caribbean
    "ATG": "Caribbean",
    "BHS": "Caribbean",
    "BRB": "Caribbean",
    "CUB": "Caribbean",
    "DMA": "Caribbean",
    "DOM": "Caribbean",
    "GRD": "Caribbean",
    "HTI": "Caribbean",
    "JAM": "Caribbean",
    "KNA": "Caribbean",
    "LCA": "Caribbean",
    "VCT": "Caribbean",
    "TTO": "Caribbean",
    "PRI": "Caribbean",
    # Central America
    "BLZ": "Central America",
    "CRI": "Central America",
    "SLV": "Central America",
    "GTM": "Central America",
    "HND": "Central America",
    "MEX": "Central America",
    "NIC": "Central America",
    "PAN": "Central America",
    # South America
    "ARG": "South America",
    "BOL": "South America",
    "BRA": "South America",
    "CHL": "South America",
    "COL": "South America",
    "ECU": "South America",
    "GUY": "South America",
    "PRY": "South America",
    "PER": "South America",
    "SUR": "South America",
    "URY": "South America",
    "VEN": "South America",
    # Northern America
    "CAN": "Northern America",
    "USA": "Northern America",
    # Central Asia
    "KAZ": "Central Asia",
    "KGZ": "Central Asia",
    "TJK": "Central Asia",
    "TKM": "Central Asia",
    "UZB": "Central Asia",
    # Eastern Asia
    "CHN": "Eastern Asia",
    "JPN": "Eastern Asia",
    "MNG": "Eastern Asia",
    "PRK": "Eastern Asia",
    "KOR": "Eastern Asia",
    "TWN": "Eastern Asia",
    "HKG": "Eastern Asia",
    "MAC": "Eastern Asia",
    # South-eastern Asia
    "BRN": "South-eastern Asia",
    "KHM": "South-eastern Asia",
    "IDN": "South-eastern Asia",
    "LAO": "South-eastern Asia",
    "MYS": "South-eastern Asia",
    "MMR": "South-eastern Asia",
    "PHL": "South-eastern Asia",
    "SGP": "South-eastern Asia",
    "THA": "South-eastern Asia",
    "TLS": "South-eastern Asia",
    "VNM": "South-eastern Asia",
    # Southern Asia
    "AFG": "Southern Asia",
    "BGD": "Southern Asia",
    "BTN": "Southern Asia",
    "IND": "Southern Asia",
    "IRN": "Southern Asia",
    "MDV": "Southern Asia",
    "NPL": "Southern Asia",
    "PAK": "Southern Asia",
    "LKA": "Southern Asia",
    # Western Asia
    "ARM": "Western Asia",
    "AZE": "Western Asia",
    "BHR": "Western Asia",
    "CYP": "Western Asia",
    "GEO": "Western Asia",
    "IRQ": "Western Asia",
    "ISR": "Western Asia",
    "JOR": "Western Asia",
    "KWT": "Western Asia",
    "LBN": "Western Asia",
    "OMN": "Western Asia",
    "PSE": "Western Asia",
    "QAT": "Western Asia",
    "SAU": "Western Asia",
    "SYR": "Western Asia",
    "TUR": "Western Asia",
    "ARE": "Western Asia",
    "YEM": "Western Asia",
    # Eastern Europe
    "BLR": "Eastern Europe",
    "BGR": "Eastern Europe",
    "CZE": "Eastern Europe",
    "HUN": "Eastern Europe",
    "POL": "Eastern Europe",
    "MDA": "Eastern Europe",
    "ROU": "Eastern Europe",
    "RUS": "Eastern Europe",
    "SVK": "Eastern Europe",
    "UKR": "Eastern Europe",
    # Northern Europe
    "DNK": "Northern Europe",
    "EST": "Northern Europe",
    "FIN": "Northern Europe",
    "ISL": "Northern Europe",
    "IRL": "Northern Europe",
    "LVA": "Northern Europe",
    "LTU": "Northern Europe",
    "NOR": "Northern Europe",
    "SWE": "Northern Europe",
    "GBR": "Northern Europe",
    # Southern Europe
    "ALB": "Southern Europe",
    "AND": "Southern Europe",
    "BIH": "Southern Europe",
    "HRV": "Southern Europe",
    "GRC": "Southern Europe",
    "ITA": "Southern Europe",
    "MLT": "Southern Europe",
    "MNE": "Southern Europe",
    "MKD": "Southern Europe",
    "PRT": "Southern Europe",
    "SMR": "Southern Europe",
    "SRB": "Southern Europe",
    "SVN": "Southern Europe",
    "ESP": "Southern Europe",
    # Western Europe
    "AUT": "Western Europe",
    "BEL": "Western Europe",
    "FRA": "Western Europe",
    "DEU": "Western Europe",
    "LIE": "Western Europe",
    "LUX": "Western Europe",
    "MCO": "Western Europe",
    "NLD": "Western Europe",
    "CHE": "Western Europe",
    # Oceania
    "AUS": "Oceania",
    "FJI": "Oceania",
    "NZL": "Oceania",
    "PNG": "Oceania",
    "SLB": "Oceania",
    "VUT": "Oceania",
    "WSM": "Oceania",
    "TON": "Oceania",
    "PLW": "Oceania",
    "MHL": "Oceania",
    "NRU": "Oceania",
}

# World Bank income group classification (July 2024)
INCOME_GROUP_MAP = {
    # High income
    "AND": "High income",
    "ARE": "High income",
    "ATG": "High income",
    "AUS": "High income",
    "AUT": "High income",
    "BEL": "High income",
    "BHR": "High income",
    "BHS": "High income",
    "BRB": "High income",
    "BRN": "High income",
    "CAN": "High income",
    "CHE": "High income",
    "CHL": "High income",
    "CYP": "High income",
    "CZE": "High income",
    "DEU": "High income",
    "DNK": "High income",
    "ESP": "High income",
    "EST": "High income",
    "FIN": "High income",
    "FRA": "High income",
    "GBR": "High income",
    "GRC": "High income",
    "GRD": "High income",
    "GUY": "High income",
    "HKG": "High income",
    "HRV": "High income",
    "HUN": "High income",
    "IRL": "High income",
    "ISL": "High income",
    "ISR": "High income",
    "ITA": "High income",
    "JPN": "High income",
    "KNA": "High income",
    "KOR": "High income",
    "KWT": "High income",
    "LIE": "High income",
    "LTU": "High income",
    "LUX": "High income",
    "LVA": "High income",
    "MAC": "High income",
    "MCO": "High income",
    "MLT": "High income",
    "NLD": "High income",
    "NOR": "High income",
    "NZL": "High income",
    "OMN": "High income",
    "PAN": "High income",
    "POL": "High income",
    "PRT": "High income",
    "QAT": "High income",
    "ROU": "High income",
    "SAU": "High income",
    "SGP": "High income",
    "SMR": "High income",
    "SVK": "High income",
    "SVN": "High income",
    "SWE": "High income",
    "SYC": "High income",
    "TTO": "High income",
    "URY": "High income",
    "USA": "High income",
    # Upper middle income
    "ALB": "Upper middle income",
    "ARG": "Upper middle income",
    "ARM": "Upper middle income",
    "AZE": "Upper middle income",
    "BGR": "Upper middle income",
    "BIH": "Upper middle income",
    "BLR": "Upper middle income",
    "BLZ": "Upper middle income",
    "BOL": "Upper middle income",
    "BRA": "Upper middle income",
    "BWA": "Upper middle income",
    "CHN": "Upper middle income",
    "COL": "Upper middle income",
    "CRI": "Upper middle income",
    "CUB": "Upper middle income",
    "DMA": "Upper middle income",
    "DOM": "Upper middle income",
    "ECU": "Upper middle income",
    "GAB": "Upper middle income",
    "GEO": "Upper middle income",
    "GNQ": "Upper middle income",
    "GTM": "Upper middle income",
    "IDN": "Upper middle income",
    "IRQ": "Upper middle income",
    "JAM": "Upper middle income",
    "JOR": "Upper middle income",
    "KAZ": "Upper middle income",
    "LBN": "Upper middle income",
    "LBY": "Upper middle income",
    "LCA": "Upper middle income",
    "MDA": "Upper middle income",
    "MDV": "Upper middle income",
    "MEX": "Upper middle income",
    "MKD": "Upper middle income",
    "MNE": "Upper middle income",
    "MUS": "Upper middle income",
    "MYS": "Upper middle income",
    "NAM": "Upper middle income",
    "PER": "Upper middle income",
    "PRY": "Upper middle income",
    "RUS": "Upper middle income",
    "SRB": "Upper middle income",
    "SUR": "Upper middle income",
    "THA": "Upper middle income",
    "TUR": "Upper middle income",
    "TKM": "Upper middle income",
    "VCT": "Upper middle income",
    "ZAF": "Upper middle income",
    # Lower middle income
    "AGO": "Lower middle income",
    "BEN": "Lower middle income",
    "BGD": "Lower middle income",
    "BTN": "Lower middle income",
    "CIV": "Lower middle income",
    "CMR": "Lower middle income",
    "COG": "Lower middle income",
    "COM": "Lower middle income",
    "CPV": "Lower middle income",
    "DJI": "Lower middle income",
    "DZA": "Lower middle income",
    "EGY": "Lower middle income",
    "GHA": "Lower middle income",
    "HND": "Lower middle income",
    "HTI": "Lower middle income",
    "IND": "Lower middle income",
    "IRN": "Lower middle income",
    "KEN": "Lower middle income",
    "KGZ": "Lower middle income",
    "KHM": "Lower middle income",
    "LAO": "Lower middle income",
    "LBR": "Lower middle income",
    "LKA": "Lower middle income",
    "LSO": "Lower middle income",
    "MAR": "Lower middle income",
    "MMR": "Lower middle income",
    "MNG": "Lower middle income",
    "MRT": "Lower middle income",
    "NGA": "Lower middle income",
    "NIC": "Lower middle income",
    "NPL": "Lower middle income",
    "PAK": "Lower middle income",
    "PHL": "Lower middle income",
    "PNG": "Lower middle income",
    "SEN": "Lower middle income",
    "SLV": "Lower middle income",
    "SWZ": "Lower middle income",
    "TJK": "Lower middle income",
    "TLS": "Lower middle income",
    "TUN": "Lower middle income",
    "TZA": "Lower middle income",
    "UKR": "Lower middle income",
    "UZB": "Lower middle income",
    "VNM": "Lower middle income",
    "ZMB": "Lower middle income",
    # Low income
    "AFG": "Low income",
    "BDI": "Low income",
    "BFA": "Low income",
    "CAF": "Low income",
    "COD": "Low income",
    "ERI": "Low income",
    "ETH": "Low income",
    "GIN": "Low income",
    "GMB": "Low income",
    "GNB": "Low income",
    "MDG": "Low income",
    "MLI": "Low income",
    "MOZ": "Low income",
    "MWI": "Low income",
    "NER": "Low income",
    "PRK": "Low income",
    "RWA": "Low income",
    "SDN": "Low income",
    "SLE": "Low income",
    "SOM": "Low income",
    "SSD": "Low income",
    "SYR": "Low income",
    "TCD": "Low income",
    "TGO": "Low income",
    "UGA": "Low income",
    "YEM": "Low income",
    "ZWE": "Low income",
}

# Aggregates and regions to exclude (World Bank includes these as "countries")
EXCLUDE_CODES = {
    "AFE",
    "AFW",
    "ARB",
    "CEB",
    "CSS",
    "EAP",
    "EAR",
    "EAS",
    "ECA",
    "ECS",
    "EMU",
    "FCS",
    "HIC",
    "HPC",
    "IBD",
    "IBT",
    "IDA",
    "IDB",
    "IDX",
    "INX",
    "LAC",
    "LCN",
    "LDC",
    "LIC",
    "LMC",
    "LMY",
    "LTE",
    "MEA",
    "MIC",
    "MNA",
    "NAC",
    "OED",
    "OSS",
    "PRE",
    "PSS",
    "PST",
    "SAS",
    "SSA",
    "SSF",
    "SST",
    "TEA",
    "TEC",
    "TLA",
    "TMN",
    "TSA",
    "TSS",
    "UMC",
    "WLD",
    "EUU",
    "SXZ",
    # Non-standard codes from RSF/V-Dem that aren't real ISO alpha-3
    "CS-KM",  # RSF's code for Kosovo (use XKX mapping instead)
    "CTU",  # RSF: Northern Cyprus (not a recognized country)
    "XCD",  # RSF: OECS (Organisation of Eastern Caribbean States — not a country)
    "PSG",  # V-Dem: Palestine/Gaza (use PSE instead)
    "SML",  # V-Dem: Somaliland (unrecognized territory)
    "ZZB",  # V-Dem: Zanzibar (part of Tanzania)
}


# ISO alpha-2 → alpha-3 mapping for FSI data (which uses 2-letter codes)
ALPHA2_TO_ALPHA3 = {
    "AD": "AND",
    "AE": "ARE",
    "AG": "ATG",
    "AI": "AIA",
    "AL": "ALB",
    "AO": "AGO",
    "AR": "ARG",
    "AS": "ASM",
    "AT": "AUT",
    "AU": "AUS",
    "AW": "ABW",
    "AZ": "AZE",
    "BA": "BIH",
    "BB": "BRB",
    "BD": "BGD",
    "BE": "BEL",
    "BG": "BGR",
    "BH": "BHR",
    "BM": "BMU",
    "BN": "BRN",
    "BO": "BOL",
    "BR": "BRA",
    "BS": "BHS",
    "BW": "BWA",
    "BZ": "BLZ",
    "CA": "CAN",
    "CH": "CHE",
    "CK": "COK",
    "CL": "CHL",
    "CM": "CMR",
    "CN": "CHN",
    "CO": "COL",
    "CR": "CRI",
    "CU": "CUB",
    "CW": "CUW",
    "CY": "CYP",
    "CZ": "CZE",
    "DE": "DEU",
    "DJ": "DJI",
    "DK": "DNK",
    "DM": "DMA",
    "DO": "DOM",
    "DZ": "DZA",
    "EC": "ECU",
    "EG": "EGY",
    "ER": "ERI",
    "ES": "ESP",
    "ET": "ETH",
    "FI": "FIN",
    "FR": "FRA",
    "GB": "GBR",
    "GD": "GRD",
    "GE": "GEO",
    "GG": "GGY",
    "GH": "GHA",
    "GI": "GIB",
    "GM": "GMB",
    "GR": "GRC",
    "GT": "GTM",
    "GU": "GUM",
    "GW": "GNB",
    "GY": "GUY",
    "HK": "HKG",
    "HN": "HND",
    "HR": "HRV",
    "HU": "HUN",
    "ID": "IDN",
    "IE": "IRL",
    "IL": "ISR",
    "IM": "IMN",
    "IN": "IND",
    "IQ": "IRQ",
    "IR": "IRN",
    "IS": "ISL",
    "IT": "ITA",
    "JE": "JEY",
    "JM": "JAM",
    "JO": "JOR",
    "JP": "JPN",
    "KE": "KEN",
    "KG": "KGZ",
    "KH": "KHM",
    "KN": "KNA",
    "KR": "KOR",
    "KW": "KWT",
    "KY": "CYM",
    "KZ": "KAZ",
    "LA": "LAO",
    "LB": "LBN",
    "LC": "LCA",
    "LI": "LIE",
    "LK": "LKA",
    "LR": "LBR",
    "LS": "LSO",
    "LT": "LTU",
    "LU": "LUX",
    "LV": "LVA",
    "LY": "LBY",
    "MA": "MAR",
    "MC": "MCO",
    "ME": "MNE",
    "MG": "MDG",
    "MH": "MHL",
    "MK": "MKD",
    "ML": "MLI",
    "MM": "MMR",
    "MN": "MNG",
    "MO": "MAC",
    "MR": "MRT",
    "MS": "MSR",
    "MT": "MLT",
    "MU": "MUS",
    "MV": "MDV",
    "MW": "MWI",
    "MX": "MEX",
    "MY": "MYS",
    "MZ": "MOZ",
    "NA": "NAM",
    "NG": "NGA",
    "NI": "NIC",
    "NL": "NLD",
    "NO": "NOR",
    "NP": "NPL",
    "NR": "NRU",
    "NZ": "NZL",
    "OM": "OMN",
    "PA": "PAN",
    "PE": "PER",
    "PG": "PNG",
    "PH": "PHL",
    "PK": "PAK",
    "PL": "POL",
    "PR": "PRI",
    "PT": "PRT",
    "PW": "PLW",
    "PY": "PRY",
    "QA": "QAT",
    "RO": "ROU",
    "RS": "SRB",
    "RU": "RUS",
    "RW": "RWA",
    "SA": "SAU",
    "SC": "SYC",
    "SD": "SDN",
    "SE": "SWE",
    "SG": "SGP",
    "SI": "SVN",
    "SK": "SVK",
    "SL": "SLE",
    "SM": "SMR",
    "SN": "SEN",
    "SO": "SOM",
    "SR": "SUR",
    "SS": "SSD",
    "SV": "SLV",
    "SZ": "SWZ",
    "TC": "TCA",
    "TD": "TCD",
    "TG": "TGO",
    "TH": "THA",
    "TN": "TUN",
    "TO": "TON",
    "TR": "TUR",
    "TT": "TTO",
    "TW": "TWN",
    "TZ": "TZA",
    "UA": "UKR",
    "UG": "UGA",
    "US": "USA",
    "UY": "URY",
    "UZ": "UZB",
    "VC": "VCT",
    "VE": "VEN",
    "VG": "VGB",
    "VI": "VIR",
    "VN": "VNM",
    "VU": "VUT",
    "WS": "WSM",
    "ZA": "ZAF",
    "ZM": "ZMB",
    "ZW": "ZWE",
    "EE": "EST",
    "FJ": "FJI",
    "XK": "XKX",
}


RSF_CODE_REMAP = {
    "SEY": "SYC",  # Seychelles
}


def load_rsf_data():
    """Load RSF press freedom scores. Returns dict of {alpha3: score}."""
    csv_path = RSF_DIR / "rsf_scores.csv"
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty or "score" not in df.columns:
        return {}
    df["country_code"] = df["country_code"].replace(RSF_CODE_REMAP)
    # Filter out excluded codes
    df = df[~df["country_code"].isin(EXCLUDE_CODES)]
    return dict(zip(df["country_code"], df["score"]))


def load_fsi_data():
    """Load FSI financial secrecy scores. Returns dict of {alpha3: score}."""
    csv_path = TJN_DIR / "fsi_jurisdictions.csv"
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty:
        return {}
    # Take most recent edition
    latest_scoring = df["methodology_id"].unique()[-1]
    df = df[df["methodology_id"] == latest_scoring]
    # Map alpha-2 to alpha-3
    result = {}
    for _, row in df.iterrows():
        a3 = ALPHA2_TO_ALPHA3.get(row["jurisdiction_id"])
        if a3 and pd.notna(row["index_score"]):
            result[a3] = float(row["index_score"])
    return result


def load_vdem_data():
    """Load V-Dem indicators. Returns dict of {alpha3: {var: value}} for most recent year."""
    csv_path = VDEM_DIR / "vdem_extract.csv"
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty:
        return {}
    # Filter out excluded codes
    df = df[~df["country_text_id"].isin(EXCLUDE_CODES)]
    # Take most recent year per country
    df = df.sort_values("year", ascending=False).drop_duplicates("country_text_id", keep="first")
    result = {}
    vdem_vars = [
        "v2x_polyarchy",
        "v2x_corr",
        "v2xnp_client",
        "v2x_freexp_altinf",
        "v2xme_altinf",
        "v2x_clphy",
        "v2x_rule",
        "v2x_egal",
        "v2x_partipdem",
    ]
    for _, row in df.iterrows():
        code = row["country_text_id"]
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
        return "high"
    elif total >= 5:
        return "moderate"
    elif total >= 3:
        return "low"
    else:
        return "very_low"


def compute_resource_capture(normalized_resource_score, raw_polyarchy):
    """Compute resource capture composite: resource rents moderated by democracy.

    Uses raw V-Dem polyarchy (0-1) directly, NOT min-max normalized.
    Formula: normalized_resource * (100 - accountability) / 100
    """
    if raw_polyarchy is None:
        return normalized_resource_score
    accountability = round(raw_polyarchy * 100)
    return round(normalized_resource_score * (100 - accountability) / 100)


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


def merge_domain_scores(existing, new_domain):
    """Merge two domain entries from different sources by averaging scores.

    Combines indicators, sources, and recalculates confidence from totals.
    Preserves known trend from either source (prefers existing if known).
    """
    merged_score = round((existing["score"] + new_domain["score"]) / 2)
    merged_n = existing.get("_n_indicators", 1) + new_domain.get("_n_indicators", 1)
    merged_sources_count = existing.get("_n_sources", 1) + new_domain.get("_n_sources", 1)
    merged_year = max(existing.get("_most_recent_year") or 0, new_domain.get("_most_recent_year") or 0)

    # Prefer known trend
    if existing.get("trend", "unknown") != "unknown":
        trend = existing["trend"]
    else:
        trend = new_domain.get("trend", "unknown")

    return {
        "score": merged_score,
        "confidence": assess_domain_confidence(merged_n, merged_sources_count, merged_year),
        "trend": trend,
        "sources": existing.get("sources", []) + new_domain.get("sources", []),
        "indicators": existing.get("indicators", []) + new_domain.get("indicators", []),
        "justification_detail": f"{existing.get('justification_detail', '')} {new_domain.get('justification_detail', '')}".strip(),
        "_n_indicators": merged_n,
        "_n_sources": merged_sources_count,
        "_most_recent_year": merged_year,
    }


def load_indicator(filepath):
    """Load a World Bank indicator CSV and return most recent value per country."""
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    # Filter out aggregates
    df = df[~df["country_code"].isin(EXCLUDE_CODES)]
    # Filter to valid 3-letter ISO codes
    df = df[df["country_code"].str.len() == 3]
    # Take most recent year per country
    df = df.sort_values("year", ascending=False).drop_duplicates("country_code", keep="first")
    return df[["country_code", "country_name", "year", "value"]].copy()


def normalize_minmax(series, inverted=False):
    """Normalize a series to 0–100 using min-max scaling."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(50.0, index=series.index)
    normalized = (series - lo) / (hi - lo) * 100
    if inverted:
        normalized = 100 - normalized
    return normalized.round(0).astype(int)


def estimate_trend_from_data(df, inverted=False):
    """Estimate trend by comparing recent vs older values.

    Args:
        df: DataFrame with 'year' and 'value' columns for a single country/indicator.
        inverted: If True, falling raw value means extraction is rising.

    Returns: 'rising', 'falling', 'stable', or 'unknown'.
    """
    if len(df) < 2:
        return "unknown"
    recent = df[df["year"] >= 2018]["value"].mean()
    older = df[df["year"] <= 2015]["value"].mean()
    if pd.isna(recent) or pd.isna(older) or older == 0:
        return "unknown"
    change = (recent - older) / abs(older)
    if inverted:
        change = -change  # Falling raw value = rising extraction
    if abs(change) <= 0.10:
        return "stable"
    return "rising" if change > 0 else "falling"


def estimate_trend(df_full, country_code, indicator_file, inverted=False):
    """Estimate trend for a country/indicator by reading from disk.

    Thin wrapper around estimate_trend_from_data that handles file loading.
    """
    filepath = WB_DIR / indicator_file
    if not filepath.exists():
        return "unknown"
    df = pd.read_csv(filepath)
    df = df[df["country_code"] == country_code].sort_values("year")
    return estimate_trend_from_data(df, inverted=inverted)


def build_country_scores():
    """Build normalized scores for all countries from World Bank data."""
    # Load and normalize each indicator
    indicators = {}
    for cfg in INDICATOR_CONFIG:
        filepath = WB_DIR / cfg["file"]
        df = load_indicator(filepath)
        if df.empty:
            continue
        df["normalized"] = normalize_minmax(df["value"], inverted=cfg["inverted"])
        df["domain"] = cfg["domain"]
        df["source_key"] = cfg["source_key"]
        df["indicator_name"] = cfg["name"]
        df["indicator_file"] = cfg["file"]
        indicators[cfg["file"]] = df

    # Load RSF data (information_capture)
    rsf_scores = load_rsf_data()
    if rsf_scores:
        print(f"  RSF: {len(rsf_scores)} countries")
        rsf_series = pd.Series(rsf_scores)
        rsf_normalized = normalize_minmax(
            rsf_series, inverted=True
        )  # Higher RSF = more free = less extraction (post-2022 methodology)
        rsf_map = dict(zip(rsf_series.index, rsf_normalized))
    else:
        rsf_map = {}

    # Load FSI data (transnational_facilitation)
    fsi_scores = load_fsi_data()
    if fsi_scores:
        print(f"  FSI: {len(fsi_scores)} countries")
        fsi_series = pd.Series(fsi_scores)
        fsi_normalized = normalize_minmax(fsi_series, inverted=False)  # Higher FSI = more secretive = more extraction
        fsi_map = dict(zip(fsi_series.index, fsi_normalized))
    else:
        fsi_map = {}

    # Load V-Dem data (political_capture + information_capture)
    vdem_raw = load_vdem_data()
    if vdem_raw:
        print(f"  V-Dem: {len(vdem_raw)} countries")
        # Normalize each V-Dem variable across all countries
        # political_capture indicators: v2x_corr (direct), v2xnp_client (direct),
        #   v2x_polyarchy (inverted), v2x_clphy (inverted)
        # information_capture: v2x_freexp_altinf (inverted), v2xme_altinf (inverted)
        # institutional_gatekeeping: v2x_rule (inverted), v2x_egal (inverted), v2x_partipdem (inverted)
        vdem_vars_config = {
            "v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Political Corruption"},
            "v2xnp_client": {"domain": "political_capture", "inverted": False, "name": "Clientelism"},
            "v2x_polyarchy": {"domain": "political_capture", "inverted": True, "name": "Electoral Democracy"},
            "v2x_clphy": {"domain": "political_capture", "inverted": True, "name": "Physical Violence"},
            "v2x_freexp_altinf": {"domain": "information_capture", "inverted": True, "name": "Freedom of Expression"},
            "v2xme_altinf": {"domain": "information_capture", "inverted": True, "name": "Alternative Info Sources"},
            "v2x_rule": {"domain": "institutional_gatekeeping", "inverted": True, "name": "Rule of Law"},
            "v2x_egal": {"domain": "institutional_gatekeeping", "inverted": True, "name": "Egalitarian Component"},
            "v2x_partipdem": {
                "domain": "institutional_gatekeeping",
                "inverted": True,
                "name": "Participatory Democracy",
            },
        }
        # Build per-variable series for normalization
        vdem_normalized = {}  # {country: {var: normalized_score}}
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
    else:
        vdem_normalized = {}

    # Build per-indicator raw value lookup for peer comparisons
    all_indicator_raw = {}  # {source_key: {country_code: raw_value}}
    for cfg in INDICATOR_CONFIG:
        key = cfg["source_key"]
        if cfg["file"] in indicators:
            df = indicators[cfg["file"]]
            all_indicator_raw[key] = dict(zip(df["country_code"], df["value"]))
    if rsf_scores:
        all_indicator_raw["rsf_press"] = dict(rsf_scores)
    if fsi_scores:
        all_indicator_raw["tjn_fsi"] = dict(fsi_scores)
    vdem_source_key_map = {
        "v2x_corr": "vdem_political_corruption",
        "v2xnp_client": "vdem_clientelism",
        "v2x_polyarchy": "vdem_electoral_democracy",
        "v2x_clphy": "vdem_physical_violence",
        "v2x_freexp_altinf": "vdem_freedom_of_expression",
        "v2xme_altinf": "vdem_alternative_info_sources",
        "v2x_rule": "vdem_rule_of_law",
        "v2x_egal": "vdem_egalitarian",
        "v2x_partipdem": "vdem_participatory_democracy",
    }
    for var, source_key in vdem_source_key_map.items():
        values = {code: vals[var] for code, vals in vdem_raw.items() if var in vals}
        if values:
            all_indicator_raw[source_key] = values

    if not indicators and not rsf_map and not fsi_map and not vdem_normalized:
        print("No indicator data found!")
        return {}

    # Combine all World Bank indicators
    all_data = pd.concat(indicators.values(), ignore_index=True) if indicators else pd.DataFrame()

    # Get unique country codes from all sources
    country_codes = set()
    if not all_data.empty:
        country_codes.update(all_data["country_code"].unique())
    country_codes.update(rsf_map.keys())
    country_codes.update(fsi_map.keys())
    country_codes.update(vdem_normalized.keys())

    countries = {}
    for code in sorted(country_codes):
        country_data = all_data[all_data["country_code"] == code] if not all_data.empty else pd.DataFrame()

        # Get country name
        if not country_data.empty:
            name = COUNTRY_NAME_OVERRIDES.get(code, country_data["country_name"].iloc[0])
        else:
            name = COUNTRY_NAME_OVERRIDES.get(code, code)

        # Group World Bank indicators by domain
        domains = {}
        source_names = []
        if not country_data.empty:
            for domain, group in country_data.groupby("domain"):
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
                    t = estimate_trend(all_data, code, row["indicator_file"], inverted=inv)
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

                domains[domain] = {
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
            source_names.append("World Bank")

        # Add RSF (information_capture) — RSF 2025 data
        if code in rsf_map:
            raw_score = rsf_scores[code]
            rsf_confidence = assess_domain_confidence(1, 1, 2025)
            rsf_norm = int(rsf_map[code])
            rsf_entry = build_indicator_entry("rsf_press", raw_score, rsf_norm, code, all_indicator_raw)
            rsf_ind = [{"name": "Press Freedom Index", "raw": raw_score, "normalized": rsf_norm}]
            domains["information_capture"] = {
                "score": rsf_norm,
                "confidence": rsf_confidence,
                "trend": "unknown",
                "sources": ["rsf_press"],
                "indicators": [rsf_entry],
                "justification_detail": build_technical_justification("RSF Press Freedom Index", rsf_ind),
                "_n_indicators": 1,
                "_n_sources": 1,
                "_most_recent_year": 2025,
            }
            source_names.append("RSF")

        # Add FSI (transnational_facilitation) — FSI 2025 data
        if code in fsi_map:
            raw_score = fsi_scores[code]
            fsi_confidence = assess_domain_confidence(1, 1, 2025)
            fsi_norm = int(fsi_map[code])
            fsi_entry = build_indicator_entry("tjn_fsi", raw_score, fsi_norm, code, all_indicator_raw)
            fsi_ind = [{"name": "Financial Secrecy Index", "raw": raw_score, "normalized": fsi_norm}]
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

        # Add V-Dem indicators (political_capture, information_capture, institutional_gatekeeping)
        if code in vdem_normalized:
            vdem_country = vdem_normalized[code]
            # Group V-Dem indicators by domain
            vdem_by_domain = {}
            for var, info in vdem_country.items():
                domain = info["domain"]
                if domain not in vdem_by_domain:
                    vdem_by_domain[domain] = []
                vdem_by_domain[domain].append(info)

            for domain, indicators_list in vdem_by_domain.items():
                vdem_score = round(sum(i["score"] for i in indicators_list) / len(indicators_list))
                vdem_sources = [vdem_source_key_map[i["var"]] for i in indicators_list]
                n_vdem = len(indicators_list)

                vdem_ind_entries = []
                vdem_ind_info = []
                for i in indicators_list:
                    src_key = vdem_source_key_map[i["var"]]
                    entry = build_indicator_entry(src_key, i["raw"], i["score"], code, all_indicator_raw)
                    vdem_ind_entries.append(entry)
                    vdem_ind_info.append(
                        {
                            "source_key": src_key,
                            "name": i["name"],
                            "raw": i["raw"],
                            "normalized": i["score"],
                        }
                    )
                vdem_detail = build_technical_justification("V-Dem", vdem_ind_info)

                if domain in domains:
                    vdem_domain_entry = {
                        "score": vdem_score,
                        "confidence": assess_domain_confidence(n_vdem, 1, 2024),
                        "trend": "unknown",
                        "sources": vdem_sources,
                        "indicators": vdem_ind_entries,
                        "justification_detail": vdem_detail,
                        "_n_indicators": n_vdem,
                        "_n_sources": 1,
                        "_most_recent_year": 2024,
                    }
                    domains[domain] = merge_domain_scores(domains[domain], vdem_domain_entry)
                else:
                    vdem_confidence = assess_domain_confidence(n_vdem, 1, 2024)
                    domains[domain] = {
                        "score": vdem_score,
                        "confidence": vdem_confidence,
                        "trend": "unknown",
                        "sources": vdem_sources,
                        "indicators": vdem_ind_entries,
                        "justification_detail": vdem_detail,
                        "_n_indicators": n_vdem,
                        "_n_sources": 1,
                        "_most_recent_year": 2024,
                    }
            source_names.append("V-Dem")

        # Similarly merge V-Dem info_capture with RSF if both exist
        # (already handled by the merge logic above)

        if not domains:
            continue

        # Resource capture: resource rents moderated by democratic accountability
        # High resource rents + low democracy = high extraction (elites capture resources)
        # High resource rents + high democracy = low extraction (citizens hold resource management accountable)
        # Uses raw V-Dem polyarchy (0-1) directly, NOT min-max normalized, because the
        # raw scale has inherent meaning and normalization would distort absolute levels.
        if "resource_capture" in domains:
            raw_resource = domains["resource_capture"]["score"]
            raw_polyarchy = vdem_raw.get(code, {}).get("v2x_polyarchy")

            # Extract resource rents facts before rebuilding indicators
            resource_rents_facts = []
            for ind in domains["resource_capture"].get("indicators", []):
                if ind["key"] == "wb_natural_rents":
                    resource_rents_facts = ind["facts"]
                    break

            if raw_polyarchy is not None:
                # Convert raw 0-1 polyarchy to 0-100 accountability score
                accountability = round(raw_polyarchy * 100)
                composite_resource = compute_resource_capture(raw_resource, raw_polyarchy)
                moderation_fact = f"Moderated by democratic accountability (V-Dem polyarchy: {raw_polyarchy:.2f})"
                domains["resource_capture"]["score"] = composite_resource
                domains["resource_capture"]["sources"] = domains["resource_capture"]["sources"] + [
                    "vdem_electoral_democracy"
                ]
                # Rebuild indicators for the composite
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
                # No V-Dem data — use raw rents unmoderated, cap confidence at low
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

        countries[code] = assemble_country_entry(name, domains, source_names)

    return countries


def main():
    parser = argparse.ArgumentParser(description="Score countries from raw indicator data")
    parser.add_argument("--preview", action="store_true", help="Show changes without writing")
    parser.add_argument("--country", help="Score a single country (ISO alpha-3)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite hand-scored countries")
    args = parser.parse_args()

    # Load existing scores
    with open(SCORES_PATH) as f:
        scores = json.load(f)

    # Distinguish hand-scored from auto-scored
    hand_scored = {k for k, v in scores["countries"].items() if not v.get("notes", "").startswith("Auto-scored")}
    print(f"Hand-scored countries: {len(hand_scored)} ({', '.join(sorted(hand_scored))})")

    # Build new scores
    print("Loading and normalizing World Bank indicators...")
    new_countries = build_country_scores()
    print(f"Generated scores for {len(new_countries)} countries")

    if args.country:
        code = args.country.upper()
        if code not in new_countries:
            print(f"No data available for {code}")
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
        if code in scores["countries"]:
            overwritten += 1
        else:
            added += 1
        if not args.preview:
            scores["countries"][code] = data

    # Update metadata
    if not args.preview:
        scores["metadata"]["last_updated"] = str(date.today())
        with open(SCORES_PATH, "w") as f:
            json.dump(scores, f, indent=2)

    print("\nResults:")
    print(f"  Added:       {added} new countries")
    print(f"  Preserved:   {skipped} hand-scored countries")
    if overwritten:
        print(f"  Overwritten: {overwritten} countries")
    print(f"  Total:       {len(scores['countries'])} countries in scores.json")

    if args.preview:
        print("\n(Preview mode — no files written)")
        # Show a sample
        sample_codes = sorted(new_countries.keys())[:5]
        for code in sample_codes:
            c = new_countries[code]
            domains_str = ", ".join(f"{d}={v['score']}" for d, v in c["domains"].items())
            print(f"  {code} ({c['name']}): composite={c['composite_score']} [{domains_str}]")
        if len(new_countries) > 5:
            print(f"  ... and {len(new_countries) - 5} more")


if __name__ == "__main__":
    main()
