"""
Tax Justice Network — Financial Secrecy Index & Corporate Tax Haven Index

Covers domains:
  - financial_extraction: secrecy scores
  - transnational_facilitation: haven scores, secrecy jurisdiction rankings

Data home: https://fsi.taxjustice.net/
CTHI: https://cthi.taxjustice.net/

The FSI ranks jurisdictions by financial secrecy. The CTHI ranks them by
how aggressively they facilitate corporate profit shifting.

Note: TJN data is published as interactive databases with downloadable
Excel files, but URLs are not stable across editions. This fetcher attempts
known URLs; if they fail, it provides manual download instructions.
"""

import json
from pathlib import Path

import requests

# These URLs may need updating when new editions are published
FSI_URL = 'https://fsi.taxjustice.net/api/fsi/rankings'
CTHI_URL = 'https://cthi.taxjustice.net/api/cthi/rankings'


def _try_api(url, output_path, name):
    """Try to fetch from TJN API. Returns True on success."""
    try:
        resp = requests.get(url, timeout=30, headers={'Accept': 'application/json'})
        resp.raise_for_status()
        data = resp.json()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'      → {name}: {len(data) if isinstance(data, list) else "?"} entries')
        return True
    except Exception as e:
        print(f'      ⚠ {name} API failed: {e}')
        return False


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch Financial Secrecy Index and Corporate Tax Haven Index."""
    output_dir = raw_data_dir / 'tjn'
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []

    fsi_path = output_dir / 'fsi_rankings.json'
    if _try_api(FSI_URL, fsi_path, 'FSI'):
        files.append(str(fsi_path.relative_to(raw_data_dir)))

    cthi_path = output_dir / 'cthi_rankings.json'
    if _try_api(CTHI_URL, cthi_path, 'CTHI'):
        files.append(str(cthi_path.relative_to(raw_data_dir)))

    if not files:
        instructions = output_dir / 'DOWNLOAD_INSTRUCTIONS.md'
        instructions.write_text(
            '# Tax Justice Network — Manual Download\n\n'
            'API endpoints were unavailable. Download manually:\n\n'
            '## Financial Secrecy Index\n'
            '1. Go to https://fsi.taxjustice.net/\n'
            '2. Click "Rankings" or "Download Data"\n'
            '3. Export as CSV/Excel\n'
            f'4. Save to: {output_dir}/fsi_rankings.csv\n\n'
            '## Corporate Tax Haven Index\n'
            '1. Go to https://cthi.taxjustice.net/\n'
            '2. Click "Rankings" or "Download Data"\n'
            '3. Export as CSV/Excel\n'
            f'4. Save to: {output_dir}/cthi_rankings.csv\n'
        )
        files.append(str(instructions.relative_to(raw_data_dir)))

    # Metadata
    meta = {
        'source': 'Tax Justice Network',
        'datasets': [
            {'name': 'Financial Secrecy Index', 'url': 'https://fsi.taxjustice.net/', 'domain': 'financial_extraction, transnational_facilitation', 'inverted': False},
            {'name': 'Corporate Tax Haven Index', 'url': 'https://cthi.taxjustice.net/', 'domain': 'transnational_facilitation', 'inverted': False},
        ]
    }
    meta_path = output_dir / '_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
