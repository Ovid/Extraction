"""
V-Dem (Varieties of Democracy) fetcher.

V-Dem publishes the most comprehensive democracy dataset globally.
It covers political capture, clientelism, corruption, and media freedom
in a single dataset — making it the richest single source for this project.

IMPORTANT: V-Dem requires filling out a form before downloading.
The dataset cannot be fetched automatically.

Data home: https://www.v-dem.net/data/the-v-dem-dataset/
Codebook:  https://www.v-dem.net/documents/38/V-Dem_Codebook_v14.pdf

Key variables we need:
  - v2x_polyarchy       Electoral Democracy Index         → political_capture (inverted)
  - v2x_corr            Political Corruption Index        → political_capture
  - v2xnp_client        Clientelism Index                 → political_capture
  - v2x_freexp_altinf   Freedom of Expression Index       → information_capture (inverted)
  - v2xme_altinf        Alternative Sources of Info Index → information_capture (inverted)
  - v2x_clphy           Physical Violence Index           → political_capture
  - v2x_rule             Rule of Law Index                 → institutional_gatekeeping (inverted)
  - v2x_egal             Egalitarian Component Index       → institutional_gatekeeping (inverted)
  - v2x_partipdem        Participatory Democracy Index     → institutional_gatekeeping (inverted)
"""

import json
from pathlib import Path

import pandas as pd

# Variables to extract (keeps the download manageable if we filter)
VARIABLES = [
    "country_text_id",  # ISO alpha-3ish (V-Dem uses its own codes; need mapping)
    "country_name",
    "year",
    "v2x_polyarchy",  # Electoral Democracy Index (0–1, higher = more democratic)
    "v2x_corr",  # Political Corruption Index (0–1, higher = more corrupt)
    "v2xnp_client",  # Clientelism Index (0–1, higher = more clientelist)
    "v2x_freexp_altinf",  # Freedom of Expression (0–1, higher = more free)
    "v2xme_altinf",  # Alternative Sources of Information (0–1, higher = more free)
    "v2x_clphy",  # Physical Violence Index (0–1, higher = less violence)
    "v2x_rule",  # Rule of Law Index (0–1, higher = stronger rule of law)
    "v2x_egal",  # Egalitarian Component Index (0–1, higher = more egalitarian)
    "v2x_partipdem",  # Participatory Democracy Index (0–1, higher = more participatory)
    "v2lgcrrpt",  # Legislature corrupt activities (ordinal, higher = less corrupt)
]

# V-Dem uses its own country codes; this maps common ones to ISO alpha-3
# A full mapping table is in the V-Dem codebook appendix
VDEM_TO_ISO = {
    # This is a subset — extend as needed from the codebook
    # V-Dem country_text_id is usually close to ISO alpha-3 but not always
}


def fetch(raw_data_dir: Path) -> list[str]:
    """Download V-Dem core dataset and extract relevant variables."""
    output_dir = raw_data_dir / "vdem"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "vdem_core_full.csv"
    extract_path = output_dir / "vdem_extract.csv"

    # The full V-Dem Core CSV is large (~200MB) and not committed to the repo.
    # It must be downloaded manually (requires filling out a form on the V-Dem site).
    if not csv_path.exists():
        print()
        print("    ✗ V-Dem Core dataset not found.")
        print()
        print("      This file must be downloaded manually (requires filling out a form):")
        print()
        print("      1. Go to https://www.v-dem.net/data/the-v-dem-dataset/")
        print('      2. Select "Country-Year: V-Dem Core" (CSV format)')
        print("      3. Fill out the required form and download")
        print(f"      4. Extract the CSV to: {csv_path}")
        print("      5. Re-run this fetcher")
        print()
        return []
    else:
        print(f"    Using cached V-Dem data ({csv_path.stat().st_size / 1_000_000:.1f} MB)")

    # Extract relevant variables and recent years
    print("    Extracting relevant variables...")
    try:
        df = pd.read_csv(csv_path, low_memory=False)

        # Filter to available variables (some may not exist in all versions)
        available_vars = [v for v in VARIABLES if v in df.columns]
        missing_vars = [v for v in VARIABLES if v not in df.columns]
        if missing_vars:
            print(f"      ⚠ Missing variables: {missing_vars}")

        df_extract = df[available_vars].copy()

        # Filter to 2010+ for manageable size
        if "year" in df_extract.columns:
            df_extract = df_extract[df_extract["year"] >= 2010]

        df_extract.to_csv(extract_path, index=False)
        print(f"      → {len(df_extract)} rows, {len(available_vars)} variables")

    except Exception as e:
        print(f"      ✗ Extraction failed: {e}")
        return [str(csv_path.relative_to(raw_data_dir))]

    # Metadata
    meta = {
        "source": "V-Dem Varieties of Democracy",
        "url": "https://www.v-dem.net/",
        "version": "v14 (or latest available)",
        "variables": [
            {
                "name": "v2x_polyarchy",
                "domain": "political_capture",
                "inverted": True,
                "desc": "Electoral Democracy Index (0-1)",
            },
            {
                "name": "v2x_corr",
                "domain": "political_capture",
                "inverted": False,
                "desc": "Political Corruption Index (0-1)",
            },
            {
                "name": "v2xnp_client",
                "domain": "political_capture",
                "inverted": False,
                "desc": "Clientelism Index (0-1)",
            },
            {
                "name": "v2x_freexp_altinf",
                "domain": "information_capture",
                "inverted": True,
                "desc": "Freedom of Expression (0-1)",
            },
            {
                "name": "v2xme_altinf",
                "domain": "information_capture",
                "inverted": True,
                "desc": "Alternative Sources of Information (0-1)",
            },
            {
                "name": "v2x_clphy",
                "domain": "political_capture",
                "inverted": True,
                "desc": "Physical Violence Index (0-1)",
            },
            {
                "name": "v2x_rule",
                "domain": "institutional_gatekeeping",
                "inverted": True,
                "desc": "Rule of Law Index (0-1)",
            },
            {
                "name": "v2x_egal",
                "domain": "institutional_gatekeeping",
                "inverted": True,
                "desc": "Egalitarian Component Index (0-1)",
            },
            {
                "name": "v2x_partipdem",
                "domain": "institutional_gatekeeping",
                "inverted": True,
                "desc": "Participatory Democracy Index (0-1)",
            },
            {
                "name": "v2lgcrrpt",
                "domain": "political_capture",
                "inverted": True,
                "desc": "Legislature corrupt activities (ordinal, higher = less corrupt)",
            },
        ],
        "note": "inverted=True means higher raw value = less extraction; flip when scoring. V-Dem country_text_id is usually ISO alpha-3 but check the codebook for exceptions.",
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    files = [
        str(extract_path.relative_to(raw_data_dir)),
        str(meta_path.relative_to(raw_data_dir)),
    ]

    # Keep full file reference but don't list it as a "result" (it's a cache)
    return files
