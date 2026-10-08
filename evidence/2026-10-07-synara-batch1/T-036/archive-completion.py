"""Preserve the final native and regression fixtures as a separate archive."""
import datetime
import json
from pathlib import Path
import re
import tarfile

out = Path(__file__).resolve().parent
roots = set()
for command in out.glob('*/command.json'):
    value = json.loads(command.read_text(encoding='utf-8'))
    if value.get('artifacts'):
        roots.add(Path(value['artifacts']))
for meta in out.glob('*-runtime.json'):
    value = json.loads(meta.read_text(encoding='utf-8'))
    if value.get('runtime'):
        roots.add(Path(value['runtime']))
for log in out.glob('*.log'):
    for root in re.findall(r'\{"fixture_root":"([^"]+)"\}', log.read_text(encoding='utf-8')):
        roots.add(Path(root))
# The initial red tests predate fixture_root logging. Bind their distinctive
# fixture prefix to the preserved exact command time windows before archiving.
tmp = Path('/Volumes/WD-Elements/dev-cache/synara/tmp/t036')
for meta in out.glob('history-contract*.json'):
    value = json.loads(meta.read_text(encoding='utf-8'))
    start = datetime.datetime.fromisoformat(value['started']).timestamp()
    end = datetime.datetime.fromisoformat(value['finished']).timestamp()
    for root in tmp.glob('a2a-history-contract-*'):
        if start <= root.stat().st_birthtime <= end and (root / 'repo/input.txt').read_text(encoding='utf-8') == 'Sentinel input\n':
            roots.add(root)
manifest = []
with tarfile.open(out / 'retained-fixtures-final.tar.gz', 'x:gz') as archive:
    for index, root in enumerate(sorted(roots)):
        if not root.is_dir():
            raise RuntimeError('Retained fixture missing: ' + str(root))
        name = 'fixture-%03d-%s' % (index, root.name)
        archive.add(root, arcname=name)
        manifest.append(dict(original=str(root), archive_path=name))
with (out / 'retained-fixtures-final.json').open('x', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')
print('Archived fixture roots:', len(manifest))
