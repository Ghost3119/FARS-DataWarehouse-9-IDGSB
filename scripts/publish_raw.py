"""Copy official FARS bytes to GitHub Releases. No parsing or cleaning of data."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def gh(*args, check=True):
    return subprocess.run(['gh', *args], check=check, text=True, capture_output=True)

def download(item, directory):
    # Unique release asset names retain the complete original relative path in manifest.
    asset = item['path'].replace('/', '__').replace(' ', '_')
    dest = directory / asset
    for attempt in range(4):
        try:
            digest = hashlib.sha256()
            with urllib.request.urlopen(item['url'], timeout=180) as response, dest.open('wb') as out:
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    raise ValueError('Unexpected HTML instead of original file')
                while block := response.read(1024 * 1024):
                    out.write(block)
                    digest.update(block)
            if not dest.stat().st_size:
                raise ValueError('Empty file')
            return dict(item, asset=asset, sha256=digest.hexdigest(), size_bytes=dest.stat().st_size), dest
        except Exception:
            dest.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', required=True)
    args = parser.parse_args()
    repo = os.environ['GITHUB_REPOSITORY']
    manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
    items = [x for x in manifest['files'] if x['group'] == args.group]
    if not items:
        raise ValueError('Unknown or empty group')
    tag = 'fars-raw-' + args.group
    info = gh('release', 'view', tag, '--repo', repo, '--json', 'isDraft', check=False)
    # A completed immutable snapshot is never silently overwritten on rerun.
    if info.returncode == 0 and not json.loads(info.stdout)['isDraft']:
        print('Already published:', tag)
        return
    if info.returncode:
        gh('release', 'create', tag, '--repo', repo, '--target', os.environ['GITHUB_SHA'],
           '--draft', '--title', 'FARS original — ' + args.group,
           '--notes', 'Archivos originales de NHTSA, sin limpieza ni transformación. '
           'El archivo SHA256SUMS.json conserva las rutas originales, fuentes y verificaciones.')
    records = []
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        # Limit disk usage and retry per group without publishing incomplete snapshots.
        for start in range(0, len(items), 4):
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda x: download(x, folder), items[start:start+4]))
            for record, file in results:
                gh('release', 'upload', tag, str(file), '--repo', repo, '--clobber')
                records.append(record)
                file.unlink()
                print(record['path'], record['size_bytes'], flush=True)
        checksums = folder / 'SHA256SUMS.json'
        checksums.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
        gh('release', 'upload', tag, str(checksums), '--repo', repo, '--clobber')
    remote = json.loads(gh('release', 'view', tag, '--repo', repo, '--json', 'assets').stdout)['assets']
    actual = {a['name']: a['size'] for a in remote}
    for record in records:
        if actual.get(record['asset']) != record['size_bytes']:
            raise ValueError('Missing asset or remote size mismatch: ' + record['path'])
    gh('release', 'edit', tag, '--repo', repo, '--draft=false', '--latest=false')
    print('PUBLISHED', tag, len(records), 'original files', flush=True)

if __name__ == '__main__':
    main()
