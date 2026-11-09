from pathlib import Path
import json, subprocess, difflib, sys
root=Path('evidence/2026-11-08-batch34/T-249/terra')
out=root/'reviewer-audit'
if len(sys.argv) > 1:
 out=out/sys.argv[1]
 out.mkdir(exist_ok=False)
checker=root/'check_observations.py'
results_path=root/'parent-cases-results.json'
original=checker.read_bytes()
original_results=results_path.read_bytes()
(out/'candidate-checker.py').write_bytes(original)
(out/'candidate-parent-results.json').write_bytes(original_results)
source=original.decode('utf-8')
old=subprocess.check_output(['git','-C','/Users/luckye/Documents/Code/a2a','show','d9b75c077bbcc33ae9b77e7f188916d787f2c803:'+str(checker)]).decode('utf-8')
helper="return isinstance(short, str) and re.fullmatch(r'[0-9a-f]{10}', short) is not None and short == full[:10]"
variants=[
 ('candidate',source),
 ('M1-old-startswith',old),
 ('M2-format-without-identity',source.replace(helper,"return isinstance(short, str) and re.fullmatch(r'[0-9a-f]{10}', short) is not None")),
 ('M3-ignore-parent-order',source.replace("zip(revs[0][1:], obs['merge_parents'])", "zip(sorted(revs[0][1:]), sorted(obs['merge_parents']))")),
 ('M4-skip-normal-parent',source.replace(" and visible_parent_matches(obs['normal_parent'], revs[1][1])", "")),
 ('M5-truncate-overlong',source.replace(helper,"return isinstance(short, str) and re.fullmatch(r'[0-9a-f]{10,}', short) is not None and short[:10] == full[:10]")),
]
summary=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 return {'command':cmd,'cwd':str(Path.cwd()),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
try:
 for name, text in variants:
  directory=out/name
  directory.mkdir(exist_ok=False)
  changed=text.encode('utf-8')
  checker.write_bytes(changed)
  (directory/'check_observations.py').write_bytes(changed)
  (directory/'change.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),text.splitlines(True),fromfile='candidate',tofile=name)),encoding='utf-8')
  completion=run(['/usr/bin/python3',str(checker)])
  cases=run(['/usr/bin/python3',str(root/'check-parent-cases.py')])
  details=json.loads(results_path.read_text(encoding='utf-8'))
  (directory/'parent-cases-results.json').write_bytes(results_path.read_bytes())
  record={'name':name,'completion':completion,'new_tests':cases,'failed_cases':[r['case'] for r in details if not r['passed']]}
  if name=='M1-old-startswith':
   record['known_bad_empty']=run(['/usr/bin/python3',str(checker),'/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-249/controller-package/terra-bad-empty-parent.json'])
  (directory/'run.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  summary.append(record)
  print(json.dumps({'name':name,'completion_exit':completion['exit'],'test_exit':cases['exit'],'test_stdout':cases['stdout'].strip(),'failed_cases':record['failed_cases']},ensure_ascii=False),flush=True)
finally:
 checker.write_bytes(original)
 results_path.write_bytes(original_results)
 (out/'mutation-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert checker.read_bytes()==original
 assert results_path.read_bytes()==original_results
 print('RESTORED candidate checker and original results byte-for-byte')
