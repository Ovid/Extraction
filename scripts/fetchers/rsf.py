"""
Reporters Without Borders (RSF) — World Press Freedom Index

Covers domain: information_capture

Data home: https://rsf.org/en/index
The index scores 180+ countries on press freedom.

RSF embeds ranking data as GeoJSON in the page's drupalSettings JSON.
This fetcher parses that to extract country scores.
"""

import json
import re
from pathlib import Path

import requests
import pandas as pd

RSF_PAGE_URL = 'https://rsf.org/en/index'


def fetch(raw_data_dir: Path) -> list[str]:
    """Fetch RSF Press Freedom Index by scraping embedded page data."""
    output_dir = raw_data_dir / 'rsf'
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []

    try:
        resp = requests.get(RSF_PAGE_URL, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        })
        resp.raise_for_status()

        # Extract drupalSettings JSON from script tag
        match = re.search(
            r'<script[^>]*data-drupal-selector="drupal-settings-json"[^>]*>(.*?)</script>',
            resp.text
        )
        if not match:
            raise ValueError('Could not find drupalSettings JSON in page')

        settings = json.loads(match.group(1))
        classement = settings.get('rsf_classement', {})
        features = classement.get('countries', {}).get('features', [])

        if not features:
            raise ValueError('No country features found in rsf_classement')

        # Extract country data
        records = []
        for feat in features:
            props = feat.get('properties', {})
            iso3 = feat.get('id')  # ISO alpha-3 is in the feature id, not properties
            name = props.get('name')
            score = props.get('score')
            if iso3 and score is not None:
                records.append({
                    'country_code': iso3,
                    'country_name': name,
                    'score': float(score),
                })

        df = pd.DataFrame(records)
        csv_path = output_dir / 'rsf_scores.csv'
        df.to_csv(csv_path, index=False)
        files.append(str(csv_path.relative_to(raw_data_dir)))
        print(f'      → {len(df)} countries with press freedom scores')

        # Also save the raw JSON
        raw_path = output_dir / 'rsf_raw.json'
        with open(raw_path, 'w') as f:
            json.dump(features, f, indent=2)
        files.append(str(raw_path.relative_to(raw_data_dir)))

    except Exception as e:
        print(f'      ⚠ RSF fetch failed: {e}')
        instructions = output_dir / 'DOWNLOAD_INSTRUCTIONS.md'
        instructions.write_text(
            '# RSF Press Freedom Index — Manual Download\n\n'
            f'Automatic fetch failed: {e}\n\n'
            '1. Go to https://rsf.org/en/index\n'
            '2. Look for a "Download" or "Data" link\n'
            '3. Download the full rankings as CSV or Excel\n'
            f'4. Save to: {output_dir}/rsf_scores.csv\n'
        )
        files.append(str(instructions.relative_to(raw_data_dir)))

    meta = {
        'source': 'Reporters Without Borders',
        'url': 'https://rsf.org/en/index',
        'domain': 'information_capture',
        'inverted': False,
        'note': 'RSF scores: higher = less free (more extractive). Extracted from page-embedded GeoJSON.'
    }
    meta_path = output_dir / '_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    files.append(str(meta_path.relative_to(raw_data_dir)))

    return files
