"""
Transparency International — Corruption Perceptions Index

Covers domain: institutional_gatekeeping (partially)

Data home: https://www.transparency.org/en/cpi
Scale: 0–100 (0 = highly corrupt, 100 = very clean)

NOTE: CPI measures *perceived corruption*, not extraction. A country can score
well on CPI while extracting heavily through legal channels (e.g. USA). The CPI
is a supporting indicator, not a primary one. Use with V-Dem and WGI data.
"""

import json
from pathlib import Path

import requests


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch CPI data. Falls back to manual download instructions."""
    output_dir = raw_data_dir / 'cpi'
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    # TI publishes CPI as downloadable Excel files; URLs change annually
    # There's no stable public API. Provide manual download instructions.
    instructions = output_dir / 'DOWNLOAD_INSTRUCTIONS.md'
    instructions.write_text(
        '# Transparency International CPI — Manual Download\n\n'
        'CPI does not have a stable public API.\n\n'
        '1. Go to https://www.transparency.org/en/cpi\n'
        '2. Click "Download the full data set"\n'
        '3. Save the Excel file to this directory\n'
        f'4. Expected location: {output_dir}/cpi_full.xlsx\n\n'
        '## Important Note for Scoring\n\n'
        'CPI measures *perceived corruption*, which is NOT the same as extraction.\n'
        'The USA scores ~67/100 (relatively clean) despite high extraction through\n'
        'legal channels. Use CPI as ONE input to institutional_gatekeeping,\n'
        'not as the primary indicator.\n'
    )
    files.append(str(instructions.relative_to(raw_data_dir)))

    meta = {
        'source': 'Transparency International',
        'url': 'https://www.transparency.org/en/cpi',
        'domain': 'institutional_gatekeeping',
        'inverted': True,
        'note': 'CPI scale: 0 = highly corrupt, 100 = very clean. INVERT for extraction scoring. WARNING: CPI measures perceived corruption, not extraction. Legal extraction is invisible to CPI.'
    }
    meta_path = output_dir / '_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
