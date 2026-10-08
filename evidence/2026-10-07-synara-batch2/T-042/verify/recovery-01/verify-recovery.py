import json,subprocess,sys,time,shutil
from pathlib import Path
out=Path(__file__).resolve().parent
repo=Path('/Users/luckye/Documents/Code/synara')
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01')
while not (out/'install-result.json').exists():time.sleep(2)
assert json.loads((out/'install-result.json').read_text())['exit_code']==0
checks=[]
for package in ['.',*[str(p.relative_to(repo)) for group in ['apps','packages'] for p in (repo/group).iterdir() if (p/'package.json').exists()],'scripts']:
 d=repo/package;pkg=json.loads((d/'package.json').read_text());missing=[]
 for name in {**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}:
  if not any((p/'node_modules'/name/'package.json').is_file() for p in [d,*d.parents] if p.is_relative_to(repo)):missing.append(name)
 checks.append({'package':package,'missing_package_json':missing})
(out/'dependencies-after-install.json').write_text(json.dumps(checks,indent=2)+'\n')
assert not any(x['missing_package_json'] for x in checks),checks
print('all declared workspace dependency manifests present',flush=True)
for label in ['lint','orchestration','delivery','typecheck','build:desktop']:
 if label=='build:desktop':
  moves=[]
  for group in ['apps','packages']:
   for package in (repo/group).iterdir():
    if not package.is_dir():continue
    for name in ['dist','dist-electron']:
     path=package/name
     if not path.exists() and not path.is_symlink():continue
     target=base/'generated-before-rebuild'/path.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True)
     shutil.move(str(path),str(target));moves.append({'source':str(path),'retained':str(target)})
  (out/'generated-output-preservation.json').write_text(json.dumps(moves,indent=2)+'\n')
 print('starting '+label,flush=True)
 r=subprocess.run([sys.executable,str(out/'run-check.py'),label])
 if r.returncode:sys.exit(r.returncode)
(out/'product-status-after-checks.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=repo,text=True))
print('recovery verification completed',flush=True)
