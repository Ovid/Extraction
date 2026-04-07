"""
Tax Justice Network — Financial Secrecy Index & Corporate Tax Haven Index

Covers domains:
  - financial_extraction: secrecy scores
  - transnational_facilitation: haven scores, secrecy jurisdiction rankings

Data home: https://fsi.taxjustice.net/
CTHI: https://cthi.taxjustice.net/

Uses the TJN data API with the public token embedded in their website JS.
"""

import json
from pathlib import Path

import requests

TJN_API_BASE = "https://api.data.taxjustice.net/v1"
# Public token embedded in fsi-components JS on fsi.taxjustice.net
TJN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYXBwX2ZzaV93ZWJzaXRlIiwiaWF0IjoxNTE2MjM5MDIyfQ.RyRBMIV70I4wWKuGB2kjzIt7daX3OyFuGabyp992P38"


def _fetch_dataset(dataset, output_path, name):
    """Fetch a dataset from the TJN API as CSV."""
    try:
        resp = requests.get(
            f"{TJN_API_BASE}/query/{dataset}",
            params={"format": "csv"},
            headers={"Authorization": f"Bearer {TJN_TOKEN}"},
            timeout=30,
        )
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        # Count rows (subtract header)
        n_rows = resp.text.count("\n") - 1
        print(f"      → {name}: {n_rows} rows")
        return True
    except Exception as e:
        print(f"      ⚠ {name} failed: {e}")
        return False


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch Financial Secrecy Index and Corporate Tax Haven Index."""
    output_dir = raw_data_dir / "tjn"
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    # FSI jurisdictions (main rankings)
    fsi_path = output_dir / "fsi_jurisdictions.csv"
    if _fetch_dataset("fsi_jurisdictions", fsi_path, "FSI Jurisdictions"):
        files.append(str(fsi_path.relative_to(raw_data_dir)))

    # FSI scoring metadata (tells us which edition/year)
    scoring_path = output_dir / "fsi_scorings.csv"
    if _fetch_dataset("fsi_scorings", scoring_path, "FSI Scorings"):
        files.append(str(scoring_path.relative_to(raw_data_dir)))

    if not files:
        instructions = output_dir / "DOWNLOAD_INSTRUCTIONS.md"
        instructions.write_text(
            "# Tax Justice Network — Manual Download\n\n"
            "API was unavailable. Download manually:\n\n"
            "## Financial Secrecy Index\n"
            "1. Go to https://fsi.taxjustice.net/\n"
            '2. Click "Rankings" or "Download Data"\n'
            "3. Export as CSV/Excel\n"
            f"4. Save to: {output_dir}/fsi_jurisdictions.csv\n"
        )
        files.append(str(instructions.relative_to(raw_data_dir)))

    meta = {
        "source": "Tax Justice Network",
        "api": TJN_API_BASE,
        "datasets": [
            {
                "name": "Financial Secrecy Index",
                "url": "https://fsi.taxjustice.net/",
                "domain": "financial_extraction, transnational_facilitation",
                "inverted": False,
            },
        ],
        "note": "FSI index_score is 0-100 (higher = more secretive = more extractive). Uses public API token from fsi-components JS.",
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
