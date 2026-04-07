"""
V-Dem (Varieties of Democracy) fetcher.

V-Dem publishes the most comprehensive democracy dataset globally.
It covers political capture, clientelism, corruption, and media freedom
in a single dataset — making it the richest single source for this project.

IMPORTANT: V-Dem requires accepting terms of use. The direct download URL
changes with each version release. This fetcher attempts to download the
current version but may need the URL updated manually.

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

import requests
import pandas as pd

# V-Dem Country-Year Core dataset — this URL points to the latest version.
# If it breaks, check https://www.v-dem.net/data/the-v-dem-dataset/ for updated links.
# The full dataset is ~300MB; the "core" version is smaller and sufficient.
VDEM_CSV_URL = 'https://v-dem.net/media/datasets/V-Dem-CY-Core-v14.csv'

# Variables to extract (keeps the download manageable if we filter)
VARIABLES = [
    'country_text_id',   # ISO alpha-3ish (V-Dem uses its own codes; need mapping)
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

# V-Dem uses its own country codes; this maps common ones to ISO alpha-3
# A full mapping table is in the V-Dem codebook appendix
VDEM_TO_ISO = {
    # This is a subset — extend as needed from the codebook
    # V-Dem country_text_id is usually close to ISO alpha-3 but not always
}


def fetch(raw_data_dir: Path) -> list[str]:
    """Download V-Dem core dataset and extract relevant variables."""
    output_dir = raw_data_dir / 'vdem'
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / 'vdem_core_full.csv'
    extract_path = output_dir / 'vdem_extract.csv'

    # Download if not already cached (file is ~50MB for core)
    if not csv_path.exists():
        print('    Downloading V-Dem Core dataset (this may take a minute)...')
        try:
            resp = requests.get(VDEM_CSV_URL, timeout=120, stream=True)
            resp.raise_for_status()
            with open(csv_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f'      → Downloaded {csv_path.stat().st_size / 1_000_000:.1f} MB')
        except requests.exceptions.RequestException as e:
            # If download fails, write instructions for manual download
            instructions_path = output_dir / 'DOWNLOAD_INSTRUCTIONS.md'
            instructions_path.write_text(
                '# V-Dem Manual Download\n\n'
                f'Automatic download failed: {e}\n\n'
                '1. Go to https://www.v-dem.net/data/the-v-dem-dataset/\n'
                '2. Download "V-Dem-CY-Core" (CSV format)\n'
                f'3. Save as: {csv_path}\n'
                '4. Re-run this fetcher\n'
            )
            print(f'      ✗ Download failed. See {instructions_path}')
            return [str(instructions_path.relative_to(raw_data_dir))]
    else:
        print(f'    Using cached V-Dem data ({csv_path.stat().st_size / 1_000_000:.1f} MB)')

    # Extract relevant variables and recent years
    print('    Extracting relevant variables...')
    try:
        df = pd.read_csv(csv_path, low_memory=False)

        # Filter to available variables (some may not exist in all versions)
        available_vars = [v for v in VARIABLES if v in df.columns]
        missing_vars = [v for v in VARIABLES if v not in df.columns]
        if missing_vars:
            print(f'      ⚠ Missing variables: {missing_vars}')

        df_extract = df[available_vars].copy()

        # Filter to 2010+ for manageable size
        if 'year' in df_extract.columns:
            df_extract = df_extract[df_extract['year'] >= 2010]

        df_extract.to_csv(extract_path, index=False)
        print(f'      → {len(df_extract)} rows, {len(available_vars)} variables')

    except Exception as e:
        print(f'      ✗ Extraction failed: {e}')
        return [str(csv_path.relative_to(raw_data_dir))]

    # Metadata
    meta = {
        'source': 'V-Dem Varieties of Democracy',
        'url': 'https://www.v-dem.net/',
        'version': 'v14 (or latest available)',
        'variables': [
            {'name': 'v2x_polyarchy',    'domain': 'political_capture',  'inverted': True,  'desc': 'Electoral Democracy Index (0-1)'},
            {'name': 'v2x_corr',         'domain': 'political_capture',  'inverted': False, 'desc': 'Political Corruption Index (0-1)'},
            {'name': 'v2xnp_client',     'domain': 'political_capture',  'inverted': False, 'desc': 'Clientelism Index (0-1)'},
            {'name': 'v2x_freexp_altinf', 'domain': 'information_capture', 'inverted': True, 'desc': 'Freedom of Expression (0-1)'},
            {'name': 'v2xme_altinf',     'domain': 'information_capture', 'inverted': True,  'desc': 'Alternative Sources of Information (0-1)'},
            {'name': 'v2x_clphy',        'domain': 'political_capture',  'inverted': True,  'desc': 'Physical Violence Index (0-1)'},
            {'name': 'v2x_rule',         'domain': 'institutional_gatekeeping', 'inverted': True, 'desc': 'Rule of Law Index (0-1)'},
            {'name': 'v2x_egal',      'domain': 'institutional_gatekeeping', 'inverted': True, 'desc': 'Egalitarian Component Index (0-1)'},
            {'name': 'v2x_partipdem', 'domain': 'institutional_gatekeeping', 'inverted': True, 'desc': 'Participatory Democracy Index (0-1)'},
        ],
        'note': 'inverted=True means higher raw value = less extraction; flip when scoring. V-Dem country_text_id is usually ISO alpha-3 but check the codebook for exceptions.'
    }
    meta_path = output_dir / '_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)

    files = [
        str(extract_path.relative_to(raw_data_dir)),
        str(meta_path.relative_to(raw_data_dir)),
    ]

    # Keep full file reference but don't list it as a "result" (it's a cache)
    return files
