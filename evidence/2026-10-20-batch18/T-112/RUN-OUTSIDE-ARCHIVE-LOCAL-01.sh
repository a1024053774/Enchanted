#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t112
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 -B - <<'PY'
from pathlib import Path
import json
import shutil

evidence = Path('evidence/2026-10-20-batch18/T-112').resolve()
manifest = evidence / 'local-fixtures.archive.json'
assert not manifest.exists(), 'Preserve earlier manifests'
disk = Path('/Volumes/WD-Elements')
assert disk.is_mount(), 'Evidence archive disk is not mounted; no internal-disk fallback'
paths = {Path('/private/tmp/t112-focused-0wjbsql4'), Path('/private/tmp/t112-frozen-a0v7hoiy')}

def collect(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('fixture', 'retained_fixture') and isinstance(item, str):
                path = Path(item)
                if path.parent == Path('/private/tmp') and path.name.startswith(('t112-', 't108-')):
                    paths.add(path)
            collect(item)
    elif isinstance(value, list):
        for item in value:
            collect(item)

for file in evidence.glob('*.json'):
    collect(json.loads(file.read_text(encoding='utf-8')))
for root in list(paths):
    if root.is_dir() and root.name.startswith('t112-mutants-'):
        for file in root.glob('*.json'):
            collect(json.loads(file.read_text(encoding='utf-8')))
rows = []
for source in sorted(paths):
    if not source.exists():
        rows.append(dict(original=str(source), status='already_absent', note='如实保留缺失；不补造归档'))
        continue
    assert source.is_dir() and not source.is_symlink()
    target = disk / 'a2a-evidence/2026-10-20-batch18/T-112/local' / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    original = [file for file in source.rglob('*') if file.is_file()]
    count, size = len(original), sum(file.stat().st_size for file in original)
    shutil.copytree(source, target)
    copied = [file for file in target.rglob('*') if file.is_file()]
    assert len(copied) == count and sum(file.stat().st_size for file in copied) == size
    rows.append(dict(original=str(source), archive=str(target), files=count, bytes=size,
                     replay='See RESULTS.md, run.json and individual command summaries', status='archived'))
    manifest.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.rmtree(source)
manifest.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'archived': sum(row['status'] == 'archived' for row in rows),
                  'already_absent': sum(row['status'] == 'already_absent' for row in rows), 'manifest': str(manifest)}))
PY
