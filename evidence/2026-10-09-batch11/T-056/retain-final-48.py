import json,tarfile
from pathlib import Path
out=Path(__file__).resolve().parent;roots=[]
launches=[out/'server-retry-red-36-launch.json',out/'server-retry-red-37-launch.json',out/'server-retry-green-38-launch.json',out/'server-final-resume-44-launch.json',out/'server-boundaries-restart-46-launch.json',out/'server-native-replay-45-launch.json']+sorted(out.glob('server-retry-green-38-*-recovery-*-launch.json'))
for file in launches:
 root=Path(json.loads(file.read_text())['root'])
 if root not in roots:roots.append(root)
for suite in ['orchestration-resume-44','delivery-recovery-resume-44']:roots.append(Path(json.loads((out/suite/'command.json').read_text())['artifacts']))
entries=[];archive=out/'retained-final-git-gates-48.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
 for index,root in enumerate(roots):
  if root.name.startswith('a2a-t056-'):
   tar.add(root,arcname=f'root-{index}/{root.name}');coverage='complete acceptance scratch'
  else:
   for name in ['repo','userdata/a2a-gates']:
    path=root/name
    if path.exists():tar.add(path,arcname=f'root-{index}/{name}')
   coverage='Git repo/worktrees and complete gate store; raw provider journal/profile remain local'
  entries.append(dict(root=str(root),coverage=coverage))
with (out/'retained-final-index-48.json').open('x') as stream:json.dump(dict(archive=archive.name,fork='ddcff9a643e15dd68c18186782e688e492bb44a8',roots=entries,originals_retained=True,auth_included=False),stream,ensure_ascii=False,indent=2)
print('PASS retained',len(roots),'roots')
