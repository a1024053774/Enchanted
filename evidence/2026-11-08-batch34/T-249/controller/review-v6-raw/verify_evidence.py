from pathlib import Path
import subprocess,json
ROOT=Path.cwd(); OUT=ROOT/'.review-t249'; REPO='/Users/luckye/Documents/Code/a2a'
C='18c108fcaed1c4ecf51831f2272578a3b09427be'; OLD='1243bc15f979976967cfd2d5cdd3a2acce6df635'; BASE='05002a377914d52372a4cd46a08fa40229d70e1f'
P='evidence/2026-11-07-batch33/T-249/attempt-fence5/outside-controller-02/'
def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',REPO,*args])
def blob(c,p): return git('show',c+':'+p)
def doc(p): return json.loads(blob(C,P+p))
changes=git('diff','--name-only','-z',BASE,C).decode().split('\0')[:-1]
allow=lambda x: x.startswith(('workbench/app/','workbench/tests/','evidence/2026-11-07-batch33/T-249/')) or x=='workbench/README.md'
code=[p for p in changes if p.startswith('workbench/')]
checks=code+['acceptance/T-249/check_git_graph.py','REVIEW.md','workbench/tests/scripted_claude.py','workbench/tests/hc_evidence.py','workbench/tests/cdp.mjs','workbench/tests/cdp_launch.cjs']
actual=[dict(path=p,equal=(ROOT/p).read_bytes()==blob(C,p)) for p in checks]
source=doc('SOURCES.json'); imported=[]
for entry in source['files']:
 left=blob(C,entry['copied_path']); right=blob(entry['source_commit'],entry['source_path'])
 imported.append(dict(path=entry['copied_path'],source=entry['source_path'],commit=entry['source_commit'],equal=left==right,bytes=len(left),size_equal=len(left)==entry['bytes']))
comparison=subprocess.run(['git','--no-optional-locks','-C',REPO,'diff','--exit-code',OLD,C,'--','workbench','acceptance'],capture_output=True,text=True)
required={'no-panel':'侧边面板存在','no-details':'点击提交后详情可见','no-diff':'点击文件后单文件 diff 可见','parents':'每行父提交与 git rev-list --parents 一致','order':'提交顺序与 git rev-list --date-order --all 一致'}
runs=[]
for name in ['green','green-after-mutants',*required]:
 r=doc('window-details-cache-02/'+name+'/run.json'); failed=[x for x in r['checks'] if not x['ok']]
 good=r['status']=='PASS' and len(r['checks'])==142 and not failed if name not in required else r['status']=='FAIL' and len(failed)==1 and failed[0]['what']==required[name]
 safe=r.get('cleanup')=='PASS' and r.get('fixture_removed') is True and r.get('user_core_unchanged') is True
 runs.append(dict(name=name,status=r['status'],checks=len(r['checks']),failed=failed,expected=good,clean=safe,command=r['command'],scenarios=[s['case'] for s in r.get('detail_scenarios',[])]))
initial=[]
for name in ['e2e-green','e2e-red-no-panel','e2e-red-no-details','e2e-red-no-diff','e2e-red-parents','e2e-red-order']:
 r=doc('outside-details-01/'+name+'/run.json')
 initial.append(dict(name=name,status=r['status'],checks=len(r['checks']),cleanup=r.get('cleanup'),removed=r.get('fixture_removed'),core=r.get('user_core_unchanged'),error=r.get('error')))
result=dict(candidate=C,code_origin=OLD,code_diff_exit=comparison.returncode,code_diff_stdout=comparison.stdout,code_diff_stderr=comparison.stderr,changed_files=len(changes),code_files=len(code),out_of_card=[p for p in changes if not allow(p)],actual_files=actual,source_files=imported,window_runs=runs,initial_runs=initial)
(OUT/'evidence-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(code_diff_exit=comparison.returncode,changed_files=len(changes),code_files=len(code),out_of_card=result['out_of_card'],actual_compared=len(actual),actual_mismatches=[a for a in actual if not a['equal']],imported_files=len(imported),imported_bytes=sum(e['bytes'] for e in imported),imported_mismatches=[e for e in imported if not e['equal'] or not e['size_equal']],window_runs=[{k:v for k,v in r.items() if k!='command'} for r in runs],initial_runs=initial),ensure_ascii=False,indent=2))
assert comparison.returncode==0 and not result['out_of_card'] and all(x['equal'] for x in actual) and all(x['equal'] and x['size_equal'] for x in imported) and all(x['expected'] and x['clean'] for x in runs)
