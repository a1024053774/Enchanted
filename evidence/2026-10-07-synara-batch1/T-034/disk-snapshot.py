#!/usr/bin/env python3
"""Measure checkout, caches and unchanged default locations without checksums."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parent
before = json.loads((evidence / 'disk-before.json').read_text(encoding='utf-8'))
paths = set(before['paths'])
repo = Path('/Users/luckye/Documents/Code/synara')
cache = Path('/Volumes/WD-Elements/dev-cache/synara')
paths.update(str(path) for parent in [repo / 'apps', repo / 'packages']
             for path in parent.glob('*/node_modules'))
paths.add(str(repo / 'scripts/node_modules'))
paths.add(str(repo / 'node_modules'))
paths.update(str(p) for p in repo.iterdir() if p.is_dir() and p.name != 'node_modules')
paths.update(str(p) for p in cache.iterdir())
paths.update(str(p) for parent in [repo / 'apps', repo / 'packages'] for p in parent.glob('*/dist*'))
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'paths': {}}
for name in sorted(paths):
    path = Path(name)
    record['paths'][name] = {'exists': path.exists(),
        'du': subprocess.run(['du', '-sk', name], capture_output=True, text=True).stdout.strip(),
        'mtime_ns': path.stat().st_mtime_ns if path.exists() else None}
record['df'] = subprocess.check_output(['df', '-k', '/', '/System/Volumes/Data',
                                      '/Volumes/WD-Elements'], text=True)
with (evidence / f'disk-{sys.argv[1]}.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, indent=2)
    output.write('\n')
print(record['df'])
