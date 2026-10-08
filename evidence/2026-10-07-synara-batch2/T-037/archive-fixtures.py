"""Archive only retained fixtures created by this ticket; preserve originals."""
import datetime
import json
from pathlib import Path
import tarfile

out=Path(__file__).resolve().parent
roots=set()
for path in out.rglob('command.json'):
 try:
  value=json.loads(path.read_text(encoding='utf-8'))
  if value.get('artifacts'):roots.add(Path(value['artifacts']))
 except json.JSONDecodeError:raise
for path in out.glob('*.log'):
 for line in path.read_text(encoding='utf-8').splitlines():
  if not line.startswith('{"fixture_root":'):continue
  value=json.loads(line)
  roots.add(Path(value['fixture_root']))
for path in (out/'mutants').glob('*/runtime.json'):
 roots.add(Path(json.loads(path.read_text(encoding='utf-8'))['runtime']))
selected=[]
for root in sorted(roots):
 if not (root.name.startswith('a2a-t037-') or root.name.startswith('a2a-history-contract-')):
  raise RuntimeError('Unowned fixture rejected: '+str(root))
 if root.exists():selected.append(root)
manifest={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':[str(p) for p in selected],'missing_roots':[str(p) for p in roots if not p.exists()],'preserved_originals':True,'scope':'T-037-created CLI/engine/Git/SQLite fixtures and isolated mutants only; no user data or credentials'}
with (out/'retained-fixtures.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
with tarfile.open(out/'retained-fixtures.tar.gz','x:gz',compresslevel=3) as tar:
 for index,path in enumerate(selected):tar.add(path,arcname=f'{index:03d}-{path.name}',recursive=True)
print(json.dumps({'roots':len(selected),'archive':str(out/'retained-fixtures.tar.gz')}))
