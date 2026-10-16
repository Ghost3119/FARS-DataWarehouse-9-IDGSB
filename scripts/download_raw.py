"""Download original release assets to their original directory structure."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases/download/'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', help='Optional year (e.g. 2023) or auxiliary group')
    parser.add_argument('--output', default='data/raw')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
    groups = sorted({x['group'] for x in manifest['files']})
    if args.group:
        if args.group not in groups:
            parser.error('Unknown group: ' + args.group)
        groups = [args.group]
    for group in groups:
        release = BASE + 'fars-raw-' + group + '/'
        with urllib.request.urlopen(release + 'SHA256SUMS.json', timeout=120) as r:
            records = json.load(r)
        for item in records:
            relative = Path(item['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe relative path')
            dest = Path(args.output) / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if hashlib.sha256(dest.read_bytes()).hexdigest() == item['sha256']:
                    print('Verified existing:', dest)
                    continue
                raise ValueError('Existing file differs; not overwriting: ' + str(dest))
            temp = dest.with_name(dest.name + '.partial')
            digest = hashlib.sha256()
            try:
                with urllib.request.urlopen(release + quote(item['asset']), timeout=180) as response, temp.open('wb') as f:
                    while block := response.read(1024 * 1024):
                        f.write(block)
                        digest.update(block)
                if digest.hexdigest() != item['sha256'] or temp.stat().st_size != item['size_bytes']:
                    raise ValueError('Integrity check failed: ' + item['path'])
                temp.rename(dest)
            finally:
                temp.unlink(missing_ok=True)
            print('Downloaded and verified:', dest)

if __name__ == '__main__':
    main()
