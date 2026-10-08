"""Archive retained test-created fixtures without registering embedded gitlinks."""
import json
from pathlib import Path
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
manifest = []
with tarfile.open(out / 'retained-fixtures.tar.gz', 'x:gz') as archive:
    for index, root in enumerate(sorted(roots)):
        if not root.is_dir():
            raise RuntimeError('Retained fixture missing: ' + str(root))
        name = 'fixture-%03d-%s' % (index, root.name)
        archive.add(root, arcname=name)
        manifest.append(dict(original=str(root), archive_path=name))
with (out / 'retained-fixtures.json').open('x', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')
print('Archived fixture roots:', len(manifest))
