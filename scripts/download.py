"""Download publisher-provided datasets; this script never crawls Mountain Project."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import argparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
KAGGLE = 'matthiasgalban/mountain-project-rock-climbing-routes'
RATINGS_COMMIT = '51a0461a44078148135561c651d25a9203330609'
EXPORT_TAG = 'v2026-10-04'


def download_all(refresh=False):
    session = requests.Session()
    session.headers['User-Agent'] = 'climbing-popularity-research/0.1 (published dataset downloads)'
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    manifest_path = ROOT / 'data/raw/manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    def fetch(url, relative):
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = manifest.get(relative, {})
        if target.exists() and not refresh:
            if existing.get('sha256') and existing['sha256'] != hashlib.sha256(target.read_bytes()).hexdigest():
                raise ValueError(f'Checksum mismatch: {relative}; use --refresh to download again')
        else:
            with session.get(url, timeout=(20, 180), stream=True) as response:
                response.raise_for_status()
                temporary = target.with_suffix(target.suffix + '.part')
                with temporary.open('wb') as output:
                    for chunk in response.iter_content(1024 * 1024):
                        output.write(chunk)
                temporary.replace(target)
        manifest[relative] = {
            'url': url, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'bytes': target.stat().st_size,
            'downloaded_at_utc': existing.get('downloaded_at_utc') if existing and not refresh else datetime.now(timezone.utc).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        print(relative, target.stat().st_size, flush=True)
        return target

    fetch(f'https://www.kaggle.com/api/v1/datasets/download/{KAGGLE}?datasetVersionNumber=2', 'data/raw/kaggle/routes-v2.zip')
    fetch(f'https://www.kaggle.com/api/v1/datasets/list?search=mountain-project-rock-climbing-routes', 'data/raw/kaggle/search-metadata.json')
    tree_path = fetch(f'https://api.github.com/repos/OpenBeta/climbing-data/git/trees/{RATINGS_COMMIT}?recursive=1', 'data/raw/openbeta/ratings-tree.json')
    for item in json.loads(tree_path.read_text())['tree']:
        if item['path'].startswith('ratings/') and item['path'].endswith('.csv.zip'):
            fetch(f"https://raw.githubusercontent.com/OpenBeta/climbing-data/{RATINGS_COMMIT}/{item['path']}", 'data/raw/openbeta/' + item['path'])
    fetch(f'https://github.com/OpenBeta/parquet-exporter/releases/download/{EXPORT_TAG}/openbeta-climbs.parquet', f'data/raw/openbeta/openbeta-climbs-{EXPORT_TAG}.parquet')
    fetch(f'https://api.github.com/repos/OpenBeta/parquet-exporter/releases/tags/{EXPORT_TAG}', 'data/raw/openbeta/export-release.json')
    fetch(f'https://raw.githubusercontent.com/OpenBeta/climbing-data/{RATINGS_COMMIT}/LICENSE', 'data/raw/openbeta/LICENSE-CC0.txt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Re-download pinned source versions')
    download_all(parser.parse_args().refresh)
