"""
ILO (International Labour Organization) data fetcher.

Uses the ILO SDMX REST API to fetch labour income share of GDP.
Docs: https://ilostat.ilo.org/data/sdmx-api/

Covers domains:
  - economic_concentration: labour income share of GDP
"""

import csv
import io
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ILO_API_URL = (
    f"https://sdmx.ilo.org/rest/data/ILO,DF_LAP_2GDP_NOC_RT/.A.?startPeriod=2010&endPeriod={date.today().year}"
)

COUNTRY_CODE_OVERRIDES = {}


def parse_sdmx_csv(csv_text):
    """Parse ILO SDMX CSV response into records.

    The ILO SDMX CSV has 17 columns. We extract REF_AREA, TIME_PERIOD,
    and OBS_VALUE, skipping rows with missing values.
    """
    records = []
    reader = csv.DictReader(io.StringIO(csv_text))
    required = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        return records
    for row in reader:
        obs_value = row.get("OBS_VALUE", "").strip()
        if not obs_value:
            continue
        code = row["REF_AREA"]
        code = COUNTRY_CODE_OVERRIDES.get(code, code)
        records.append(
            {
                "country_code": code,
                "year": int(row["TIME_PERIOD"]),
                "value": float(obs_value),
            }
        )
    return records


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch ILO labour income share data. Returns list of output filenames."""
    output_dir = raw_data_dir / "ilo"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("    Fetching LAP_2GDP_NOC_RT (Labour income share of GDP)...")
    resp = requests.get(
        ILO_API_URL,
        headers={"Accept": "application/vnd.sdmx.data+csv"},
        timeout=60,
    )
    resp.raise_for_status()

    records = parse_sdmx_csv(resp.text)
    print(f"      → {len(records)} records")

    df = pd.DataFrame(records)
    if not df.empty:
        df["country_name"] = ""
        df["indicator"] = "LAP_2GDP_NOC_RT"
        df = df.sort_values(["country_code", "year"]).reset_index(drop=True)
        df = df[["country_code", "country_name", "year", "value", "indicator"]]

    output_path = output_dir / "ilo_labor_share.csv"
    files = []
    if not df.empty:
        df.to_csv(output_path, index=False)
        files.append(str(output_path.relative_to(raw_data_dir)))
    else:
        print("      WARNING: No records returned from ILO API")
        if output_path.exists():
            output_path.unlink()

    meta = {
        "source": "International Labour Organization (ILO) — ILOSTAT",
        "api": ILO_API_URL,
        "indicator": "LAP_2GDP_NOC_RT",
        "description": "Labour income share as a percent of GDP (ILO modelled estimates, SDG 10.4.1)",
        "note": "Inverted for scoring: higher labour share = less extraction",
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
