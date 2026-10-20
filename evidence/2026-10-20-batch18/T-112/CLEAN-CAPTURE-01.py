"""Controller-only cleanup of the single failed local capture; no broad tmp glob."""
import json,os,shutil,subprocess,sys
from pathlib import Path
source=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(source/'workbench/tests'))
from t108_cleanup import observe,stop_owned
root=Path('/private/tmp/t112-request-capture-ejczqfcb')
out=Path(__file__).with_name('capture-cleanup-01.json');assert not out.exists()
report={'status':'INCOMPLETE','root':str(root),'processes':[]}
try:
 p=subprocess.run(['/bin/ps','-ww','-axo','pid=,command='],env={**os.environ,'LC_ALL':'C'},text=True,capture_output=True)
 assert p.returncode==0,p.stderr
 for line in p.stdout.splitlines():
  fields=line.strip().split(None,1)
  if len(fields)!=2 or str(root) not in fields[1]:continue
  assert fields[1].startswith('/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex '),fields
  assert str(root/'candidate') in fields[1] and '--no-daemon' in fields[1],fields
  pid=int(fields[0]);owner=observe(pid)
  if owner is None:continue
  snap=subprocess.run(['/usr/bin/python3','-I','-S','-B',str(source/'workbench/src/processSnapshot.py'),str(pid)],text=True,capture_output=True)
  assert snap.returncode==0,snap.stderr
  children=[observe(row['pid']) for row in json.loads(snap.stdout)['rows']]
  for child in reversed([row for row in children if row]):report['processes'].append(stop_owned(child))
 if root.exists():shutil.rmtree(root)
 report.update(status='PASS',fixture_removed=not root.exists())
except Exception as error:report['error']=str(error)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report));raise SystemExit(0 if report['status']=='PASS' else 1)
