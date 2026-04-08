"""
World Bank Development Indicators fetcher.

Uses the World Bank API v2 to fetch country-level indicators.
Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Covers domains:
  - economic_concentration: Gini, labor share
  - financial_extraction: domestic credit to private sector, bank net interest margin
  - institutional_gatekeeping: regulatory quality (WGI), control of corruption (WGI)
  - resource_capture: total natural resource rents
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

API_BASE = "https://api.worldbank.org/v2"

# Indicators to fetch: (indicator_code, filename, description, domain, inverted)
# inverted=True means higher values = LESS extraction (need to flip for scoring)
INDICATORS = [
    ("SI.POV.GINI", "wb_gini.csv", "Gini Index", "economic_concentration", False),
    (
        "SL.GDP.PCAP.EM.KD",
        "wb_gdp_per_worker.csv",
        "GDP per person employed (constant 2017 $)",
        "economic_concentration",
        False,
    ),
    (
        "FS.AST.PRVT.GD.ZS",
        "wb_domestic_credit.csv",
        "Domestic credit to private sector (% GDP)",
        "financial_extraction",
        False,
    ),
    (
        "GFDD.EI.01",
        "wb_net_interest_margin.csv",
        "Bank net interest margin (%)",
        "financial_extraction",
        False,
    ),
    ("NY.GDP.TOTL.RT.ZS", "wb_natural_rents.csv", "Total natural resources rents (% GDP)", "resource_capture", False),
    ("CC.EST", "wb_wgi_corruption.csv", "WGI Control of Corruption", "institutional_gatekeeping", True),
    ("RQ.EST", "wb_wgi_reg_quality.csv", "WGI Regulatory Quality", "institutional_gatekeeping", True),
    ("GE.EST", "wb_wgi_gov_effectiveness.csv", "WGI Government Effectiveness", "institutional_gatekeeping", True),
]

# Fetch the most recent 15 years to allow trend computation
DATE_RANGE = "2010:2024"
PER_PAGE = 400  # Max per page


def fetch_indicator(indicator_code, output_path):
    """Fetch a single indicator for all countries."""
    all_records = []
    page = 1

    while True:
        url = (
            f"{API_BASE}/country/all/indicator/{indicator_code}"
            f"?format=json&per_page={PER_PAGE}&page={page}&date={DATE_RANGE}"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # API returns [metadata, records]
        if len(data) < 2 or data[1] is None:
            break

        metadata = data[0]
        records = data[1]

        for rec in records:
            if rec["value"] is not None:
                all_records.append(
                    {
                        "country_code": rec["countryiso3code"],
                        "country_name": rec["country"]["value"],
                        "year": int(rec["date"]),
                        "value": float(rec["value"]),
                        "indicator": indicator_code,
                    }
                )

        # Check pagination
        if page >= metadata.get("pages", 1):
            break
        page += 1
        time.sleep(0.3)  # Be polite

    df = pd.DataFrame(all_records)
    if not df.empty:
        # Sort for readability
        df = df.sort_values(["country_code", "year"]).reset_index(drop=True)
        df.to_csv(output_path, index=False)

    return len(df)


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch all World Bank indicators. Returns list of output filenames."""
    output_dir = raw_data_dir / "worldbank"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for indicator_code, filename, description, domain, inverted in INDICATORS:
        output_path = output_dir / filename
        print(f"    Fetching {indicator_code} ({description})...")
        try:
            n = fetch_indicator(indicator_code, output_path)
            print(f"      → {n} records")
            files.append(str(output_path.relative_to(raw_data_dir)))
        except Exception as e:
            print(f"      ✗ Failed: {e}")

        time.sleep(0.5)

    # Write a metadata file describing what was fetched
    meta = {
        "source": "World Bank Development Indicators",
        "api": API_BASE,
        "date_range": DATE_RANGE,
        "indicators": [
            {
                "code": code,
                "file": fname,
                "description": desc,
                "domain": domain,
                "inverted": inv,
                "note": "inverted=True means higher raw value = less extraction; flip when scoring",
            }
            for code, fname, desc, domain, inv in INDICATORS
        ],
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
