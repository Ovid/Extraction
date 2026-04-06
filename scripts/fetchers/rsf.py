"""
Reporters Without Borders (RSF) — World Press Freedom Index

Covers domain: information_capture

Data home: https://rsf.org/en/index
The index scores 180 countries on press freedom (0–100, lower = more free).

RSF publishes downloadable data but the URLs change annually.
This fetcher attempts known API endpoints; falls back to manual instructions.
"""

import json
from pathlib import Path

import requests

RSF_API_URL = 'https://rsf.org/index/result'


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch RSF Press Freedom Index."""
    output_dir = raw_data_dir / 'rsf'
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    # RSF sometimes exposes a JSON API; try it
    try:
        resp = requests.get(RSF_API_URL, timeout=30, headers={
            'Accept': 'application/json',
            'User-Agent': 'ExtractionIndex/0.1 (research)',
        })
        if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('application/json'):
            data = resp.json()
            out_path = output_dir / 'rsf_index.json'
            with open(out_path, 'w') as f:
                json.dump(data, f, indent=2)
            files.append(str(out_path.relative_to(raw_data_dir)))
            print(f'      → RSF data fetched via API')
        else:
            raise ValueError(f'Unexpected response: {resp.status_code}')
    except Exception as e:
        print(f'      ⚠ RSF API unavailable: {e}')
        instructions = output_dir / 'DOWNLOAD_INSTRUCTIONS.md'
        instructions.write_text(
            '# RSF Press Freedom Index — Manual Download\n\n'
            '1. Go to https://rsf.org/en/index\n'
            '2. Look for a "Download" or "Data" link\n'
            '3. Download the full rankings as CSV or Excel\n'
            f'4. Save to: {output_dir}/rsf_index.csv\n\n'
            'Alternative: The data is also available via V-Dem\'s media indicators,\n'
            'which may be easier to work with programmatically.\n'
        )
        files.append(str(instructions.relative_to(raw_data_dir)))

    meta = {
        'source': 'Reporters Without Borders',
        'url': 'https://rsf.org/en/index',
        'domain': 'information_capture',
        'inverted': False,
        'note': 'RSF scores: higher = less free (more extractive). Scale 0-100.'
    }
    meta_path = output_dir / '_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
