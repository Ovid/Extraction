#!/usr/bin/env python3
"""
Extraction Index — Data Fetcher

Fetches raw indicator data from public APIs and bulk downloads.
Stores results in ../raw_data/ with provenance tracking in manifest.json.

Usage:
    python fetch_all.py                     # Fetch all sources
    python fetch_all.py --source worldbank  # Fetch one source
    python fetch_all.py --list              # List available sources
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add fetchers directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fetchers'))

RAW_DATA_DIR = Path(__file__).parent.parent / 'raw_data'
MANIFEST_PATH = RAW_DATA_DIR / 'manifest.json'

# Registry of available fetchers
FETCHER_REGISTRY = {
    'worldbank': {
        'module': 'worldbank',
        'description': 'World Bank Development Indicators (Gini, labor share, domestic credit, natural resource rents, regulatory quality)',
        'type': 'api',
    },
    'vdem': {
        'module': 'vdem',
        'description': 'V-Dem democracy, corruption, clientelism, and media indicators (bulk CSV)',
        'type': 'bulk_download',
    },
    'fsi': {
        'module': 'fsi',
        'description': 'Tax Justice Network Financial Secrecy Index',
        'type': 'download',
    },
    'rsf': {
        'module': 'rsf',
        'description': 'Reporters Without Borders Press Freedom Index',
        'type': 'download',
    },
    'cpi': {
        'module': 'cpi',
        'description': 'Transparency International Corruption Perceptions Index',
        'type': 'download',
    },
}


def load_manifest():
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {'fetches': []}


def save_manifest(manifest):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def record_fetch(manifest, source_key, files, status, note=''):
    manifest['fetches'].append({
        'source': source_key,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'files': files,
        'status': status,
        'note': note,
    })
    save_manifest(manifest)


def run_fetcher(source_key, manifest):
    entry = FETCHER_REGISTRY[source_key]
    print(f'\n{"="*60}')
    print(f'Fetching: {source_key}')
    print(f'  {entry["description"]}')
    print(f'  Type: {entry["type"]}')
    print(f'{"="*60}')

    try:
        mod = __import__(entry['module'])
        files = mod.fetch(RAW_DATA_DIR)
        record_fetch(manifest, source_key, files, 'success')
        print(f'  ✓ Saved {len(files)} file(s)')
        for f in files:
            print(f'    → {f}')
    except Exception as e:
        record_fetch(manifest, source_key, [], 'error', str(e))
        print(f'  ✗ Error: {e}')


def main():
    parser = argparse.ArgumentParser(description='Extraction Index data fetcher')
    parser.add_argument('--source', help='Fetch a single source by key')
    parser.add_argument('--list', action='store_true', help='List available sources')
    args = parser.parse_args()

    if args.list:
        print('\nAvailable data sources:\n')
        for key, entry in FETCHER_REGISTRY.items():
            print(f'  {key:15s}  [{entry["type"]:15s}]  {entry["description"]}')
        print()
        return

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    if args.source:
        if args.source not in FETCHER_REGISTRY:
            print(f'Unknown source: {args.source}')
            print(f'Available: {", ".join(FETCHER_REGISTRY.keys())}')
            sys.exit(1)
        run_fetcher(args.source, manifest)
    else:
        for key in FETCHER_REGISTRY:
            run_fetcher(key, manifest)

    print(f'\nManifest updated: {MANIFEST_PATH}')


if __name__ == '__main__':
    main()
