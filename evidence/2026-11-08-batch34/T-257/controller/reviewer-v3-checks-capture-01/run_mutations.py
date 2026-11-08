import argparse, difflib, json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--out', required=True, type=Path)
a = p.parse_args()
out = a.out.resolve(); out.mkdir(exist_ok=False)
deps = Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules')
assert deps.is_dir()
original = (ROOT/'workbench/src/panes.ts').read_text()
binding = '          if (pane.active) pane.active.nativeTurn = value.turn_id;'
assert original.count(binding)==1
stop_line = 'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : pane.interrupted ? "busy" : "idle";'
assert original.count(stop_line)==2
cases = [
 ('baseline', original, '候选原样'),
 ('m1-no-binding', original.replace(binding, ''), '删除已认领 UPS 的 nativeTurn 绑定'),
 ('m2-session-as-turn', original.replace(binding, '          if (pane.active) pane.active.nativeTurn = value.session_id;'), '将 turn_id 错绑为 session_id'),
 ('m3-idle-at-ups', original.replace(binding, binding+'\n          pane.state = "idle";'), '在已认领 UPS 提前置 idle'),
 ('m4-ignore-interruption', original.replace(stop_line, 'pane.active = null; pane.state = pane.failed && !protocolFailure ? "unknown" : "idle";', 1), 'Codex Stop 完成忽略 interrupted 保持 busy 的条件'),
]
report={'candidate':'045e815ff390a0e2e50b7788966e2a5bf655fbdb','scope':'L1/L2 Panes、SQLite、rollout；不是 CLI/门禁变异','node':subprocess.check_output(['node','--version'],text=True).strip(),'cases':[]}
for name, product, description in cases:
 source = out/(name+'-source')
 shutil.copytree(ROOT/'workbench/src',source/'workbench/src')
 shutil.copy2(ROOT/'workbench/package.json',source/'workbench/package.json')
 (source/'workbench/node_modules').symlink_to(deps,target_is_directory=True)
 (source/'workbench/src/panes.ts').write_text(product)
 diff=''.join(difflib.unified_diff(original.splitlines(True),product.splitlines(True),fromfile='candidate/workbench/src/panes.ts',tofile=name+'/workbench/src/panes.ts'))
 (out/(name+'.patch')).write_text(diff)
 summary=out/(name+'-schedules.json')
 command=['node',str(ROOT/'workbench/tests/test_t257_codex_stop_continuation.ts'),str(source),str(summary)]
 result=subprocess.run(command,capture_output=True,text=True,timeout=60)
 (out/(name+'.stdout.txt')).write_text(result.stdout)
 (out/(name+'.stderr.txt')).write_text(result.stderr)
 data=json.loads(summary.read_text()) if summary.exists() else {}
 row={'name':name,'change':description,'command':command,'exit':result.returncode,'status':data.get('status','INCOMPLETE'),'cases':len(data.get('results',[])),'failures':len(data.get('failed',[])),'examples':data.get('failed',[])[:2],'patch':str(out/(name+'.patch')),'summary':str(summary)}
 files=[x for x in source.rglob('*') if x.is_file() and not x.is_symlink()]
 row['cleanup']={'path':str(source),'files':len(files),'bytes':sum(x.stat().st_size for x in files),'time':datetime.now(timezone.utc).isoformat(),'removed':False}
 report['cases'].append(row)
 (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 shutil.rmtree(source)
 row['cleanup']['removed']=True
 (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(row,ensure_ascii=False),flush=True)
assert report['cases'][0]['status']=='PASS' and report['cases'][0]['exit']==0
assert all(r['status']=='FAIL' and r['exit']==1 and r['failures'] for r in report['cases'][1:])
