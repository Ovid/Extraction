"""
Transparency International — Corruption Perceptions Index

Covers domain: institutional_gatekeeping (partially)

Data home: https://www.transparency.org/en/cpi
Scale: 0–100 (0 = highly corrupt, 100 = very clean)

Downloads the full CPI Excel dataset and extracts scores to CSV.

NOTE: CPI measures *perceived corruption*, not extraction. A country can score
well on CPI while extracting heavily through legal channels (e.g. USA). The CPI
is a supporting indicator, not a primary one. Use with V-Dem and WGI data.
"""

import json
from pathlib import Path

import pandas as pd
import requests

# Direct download URL for CPI results (year in filename changes annually)
CPI_XLSX_URL = "https://images.transparencycdn.org/images/CPI2025_Results.xlsx"


def fetch(raw_data_dir: Path) -> list[str]:
    """Download CPI Excel and extract scores to CSV."""
    output_dir = raw_data_dir / "cpi"
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    xlsx_path = output_dir / "cpi_full.xlsx"

    try:
        print("      Downloading CPI Excel...")
        resp = requests.get(
            CPI_XLSX_URL,
            timeout=60,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
        )
        resp.raise_for_status()
        xlsx_path.write_bytes(resp.content)
        print(f"      → Downloaded {len(resp.content) / 1_000_000:.1f} MB")

        # Parse the Excel file — CPI usually has a "CPI Timeseries" or main sheet
        # Try to find the right sheet and extract latest scores
        xl = pd.ExcelFile(xlsx_path)
        print(f"      Sheets: {xl.sheet_names}")

        # Try common sheet names
        df = None
        for sheet_name in xl.sheet_names:
            candidate = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            # Look for a sheet with ISO3 codes and score columns
            cols_lower = [str(c).lower() for c in candidate.columns]
            if any("iso" in c for c in cols_lower) or any("country" in c for c in cols_lower):
                df = candidate
                print(f"      Using sheet: {sheet_name}")
                break

        if df is None:
            # Fall back to first sheet
            df = pd.read_excel(xlsx_path, sheet_name=0)
            print(f"      Using first sheet: {xl.sheet_names[0]}")

        # Save raw parsed data
        csv_path = output_dir / "cpi_scores.csv"
        df.to_csv(csv_path, index=False)
        files.append(str(csv_path.relative_to(raw_data_dir)))
        print(f"      → {len(df)} rows extracted to CSV")

        files.append(str(xlsx_path.relative_to(raw_data_dir)))

    except Exception as e:
        print(f"      ⚠ CPI download failed: {e}")
        instructions = output_dir / "DOWNLOAD_INSTRUCTIONS.md"
        instructions.write_text(
            "# Transparency International CPI — Manual Download\n\n"
            f"Automatic download failed: {e}\n\n"
            "1. Go to https://www.transparency.org/en/cpi\n"
            '2. Click "Download the full data set"\n'
            "3. Save the Excel file to this directory\n"
            f"4. Expected location: {xlsx_path}\n"
        )
        files.append(str(instructions.relative_to(raw_data_dir)))

    meta = {
        "source": "Transparency International",
        "url": "https://www.transparency.org/en/cpi",
        "domain": "institutional_gatekeeping",
        "inverted": True,
        "note": "CPI scale: 0 = highly corrupt, 100 = very clean. INVERT for extraction scoring. WARNING: CPI measures perceived corruption, not extraction.",
    }
    meta_path = output_dir / "_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
