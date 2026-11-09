"""Execute the reviewer-authored patches unchanged in the controller-owned candidate checkout."""
from pathlib import Path
import json, os, subprocess, sys
from datetime import datetime, timezone
base=Path(__file__).resolve().parent
workspace=Path('/private/tmp/t262-review-external-20261108')
candidate='6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5'
assert subprocess.check_output(['git','-C',str(workspace),'rev-parse','HEAD'],text=True).strip()==candidate
page=workspace/'workbench/app/RecordsPage.tsx'
original=page.read_bytes()
assert original==(base/'RecordsPage.original.tsx').read_bytes()
out=base/'external-01';out.mkdir()
report=dict(candidate=candidate,source='reviewer 4900e31c constructed the four .diff files; root executes unchanged patches outside native sandbox',workspace=str(workspace),results=[],started=datetime.now(timezone.utc).isoformat())
env={k:v for k,v in os.environ.items() if not k.startswith('A2A_')}
env['TMPDIR']='/private/tmp'
expected={'no-sort':'每区最新在前，同时间按记录身份稳定排列','receipt-task':'任务筛选同时约束双区','ignore-session':'同一 launch 的输入与回执一起筛选','no-full-receipt':'完整回执与原始存储一致'}
try:
 for case in ['candidate',*expected]:
  page.write_bytes(original)
  if case!='candidate':
   subprocess.run(['git','apply','--directory=workbench/app','-p1',str(base/(case+'.diff'))],cwd=workspace,check=True)
  summary=out/(case+'.json')
  command=['/usr/bin/python3','workbench/tests/test_t262_records_e2e.py','--summary',str(summary)]
  with (out/(case+'.stdout.log')).open('x') as log:
   r=subprocess.run(command,cwd=workspace,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
  data=json.loads(summary.read_text()) if summary.exists() else {}
  failures=[item['name'] for item in data.get('failed',[])]
  ok=(r.returncode==0 and data.get('status')=='PASS' and len(data.get('checks',[]))==38) if case=='candidate' else (r.returncode==1 and data.get('status')=='FAIL' and expected[case] in failures)
  ok=ok and data.get('cleanup',{}).get('removed') is True
  result=dict(case=case,command=command,exit=r.returncode,status=data.get('status'),checks=len(data.get('checks',[])),failed=failures,expected=expected.get(case),ok=ok,cleanup=data.get('cleanup'))
  report['results'].append(result)
  (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({k:result[k] for k in ['case','status','checks','failed','ok']},ensure_ascii=False),flush=True)
  if not ok:break
finally:
 page.write_bytes(original)
 report['source_restored_byte_for_byte']=page.read_bytes()==original
 report['status']='PASS' if len(report['results'])==5 and all(r['ok'] for r in report['results']) else 'INCOMPLETE'
 report['finished']=datetime.now(timezone.utc).isoformat()
 (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if report['status']=='PASS' else 1)
