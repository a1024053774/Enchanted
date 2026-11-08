from pathlib import Path
import subprocess, os, json, difflib, tempfile, concurrent.futures
ROOT=Path.cwd(); OUT=ROOT/'.review-t249'; TMP=OUT/'tmp'; TMP.mkdir()
NODE='/opt/homebrew/Cellar/node/26.5.0/bin/node'
COMMANDS={
 'acceptance':['/usr/bin/python3','acceptance/T-249/check_git_graph.py'],
 'host':[NODE,'--test','workbench/tests/test_t249_git_host.mjs'],
 'outside-safety':['/usr/bin/python3','workbench/tests/test_t249_outside_safety.py']}
def run(label, kind):
 t=Path(tempfile.mkdtemp(prefix=label+'-',dir=TMP))
 env=dict(os.environ,TMPDIR=str(t),TMP=str(t),TEMP=str(t),PYTHONDONTWRITEBYTECODE='1')
 env['PATH']=str(Path(NODE).parent)+':'+env['PATH']
 command=COMMANDS[kind]
 p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
 record=dict(command=command,cwd=str(ROOT),temporary=str(t),exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
 (OUT/(label+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (OUT/(label+'.txt')).write_text('$ '+' '.join(command)+'\n'+p.stdout+p.stderr+'\nexit='+str(p.returncode)+'\n',encoding='utf-8')
 remaining=list(t.rglob('*'))
 record['remaining']=[str(x.relative_to(t)) for x in remaining]
 if not remaining:t.rmdir()
 print(json.dumps(dict(label=label,exit=p.returncode,remaining=record['remaining'],tail=(p.stdout+p.stderr)[-1400:]),ensure_ascii=False),flush=True)
 return record
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures={kind:pool.submit(run,'baseline-'+kind,kind) for kind in COMMANDS}
 baseline={kind:f.result() for kind,f in futures.items()}
assert all(x['exit']==0 for x in baseline.values()), 'Baseline did not pass; stop before mutations'
mutants=[
 ('parents','workbench/app/panels/gitGraphModel.ts',"parents: parents ? parents.split(' ') : [],", "parents: parents ? parents.split(' ').reverse() : [],",'acceptance','FAIL [all] 每行父提交'),
 ('literal-pathspec','workbench/app/panels/gitGraphModel.ts','const file = `:(top,literal)${path}`;','const file = path;','host','another file leaked into the selected diff'),
 ('wrong-assertion','workbench/app/RUN-OUTSIDE-T249.sh',"'e2e-red-no-diff': '点击文件后单文件 diff 可见'", "'e2e-red-no-diff': '点击提交后详情可见'",'outside-safety','test_disconnected_ui_requires_its_specific_business_assertion')]
results=[]
for name,relative,before,after,kind,signal in mutants:
 path=ROOT/relative; original=path.read_bytes(); text=original.decode('utf-8')
 assert text.count(before)==1,(name,'mutation anchor not unique')
 modified=text.replace(before,after)
 (OUT/(name+'.patch')).write_text(''.join(difflib.unified_diff(text.splitlines(True),modified.splitlines(True),fromfile=relative,tofile=relative)),encoding='utf-8')
 (OUT/(name+'.original')).write_bytes(original)
 try:
  path.write_text(modified,encoding='utf-8')
  r=run(name+'-'+kind,kind)
  killed=r['exit']==1 and signal in (r['stdout']+r['stderr'])
  results.append(dict(name=name,path=relative,before=before,after=after,command=COMMANDS[kind],exit=r['exit'],killed=killed,signal=signal))
 finally:
  path.write_bytes(original)
  assert path.read_bytes()==original
 (OUT/'mutation-summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(x['killed'] for x in results)
print('MUTATION_SUMMARY '+json.dumps(results,ensure_ascii=False),flush=True)
cleanup=dict(files=[str(p.relative_to(TMP)) for p in TMP.rglob('*')],all_mutations_restored=True)
if not cleanup['files']:TMP.rmdir()
cleanup['tmp_removed']=not TMP.exists()
(OUT/'cleanup.json').write_text(json.dumps(cleanup,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
