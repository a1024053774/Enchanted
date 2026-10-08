"""Run the frozen candidate sequentially; retain every stage and raw failure."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

out=Path(__file__).resolve().parent
root=out.parents[2]
fork=root.parent/'synara'
python=sys.executable
base=dict(os.environ,PYTHONPATH=str(root/'acceptance'),A2A_SYNARA_SLOT='t037')
steps=[
 ('runtime-refusal-final', [python,'-B',str(out/'run-fork-check.py'),'runtime-refusal-final',str(out/'runtime-refusal-check.ts')],{},0),
 ('human-input-final', [python,'-B',str(out/'run-fork-check.py'),'human-input-final',str(out/'human-input-check.ts')],{},0),
 ('native-service-final', [python,'-B',str(out/'run-fork-check.py'),'native-service-final',str(out/'native-service-check.ts')],{},0),
 ('final-run-02', [python,'-B',str(out/'run-acceptance.py'),'final-run-02',str(out/'test_run_native_e2e.py')],{'COOP_SCRIPT':str(out/'native-entry.py')},0),
 ('mutant-done-final-02', [python,'-B',str(out/'run-mutant.py'),'done-no-submit','mutant-done-final-02'],{},1),
 ('mutant-attempt-final-02', [python,'-B',str(out/'run-mutant.py'),'ignore-expected-attempt','mutant-attempt-final-02'],{},1),
 ('final-delivery-recovery-02', [python,'-B',str(out/'run-acceptance.py'),'final-delivery-recovery-02',str(root/'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py')],{'COOP_NATIVE_ENTRY':str(fork/'packages/a2a-gates/src/cli.ts')},0),
 ('final-core-test', [python,'-B',str(out/'run-fork-check.py'),'final-core-test','run','--cwd','packages/a2a-gates','test'],{},0),
 ('final-fmt-check', [python,'-B',str(out/'run-fork-check.py'),'final-fmt-check','run','fmt:check'],{},0),
 ('final-lint', [python,'-B',str(out/'run-fork-check.py'),'final-lint','run','lint'],{},0),
 ('final-typecheck', [python,'-B',str(out/'run-fork-check.py'),'final-typecheck','run','typecheck'],{},0),
 ('final-windows-runtime', [python,'-B',str(out/'run-fork-check.py'),'final-windows-runtime','run','windows-runtime:check'],{},0),
 ('final-migrations', [python,'-B',str(out/'run-fork-check.py'),'final-migrations','run','migrations:check'],{},0),
 ('final-workspace-test', [python,'-B',str(out/'run-fork-check.py'),'final-workspace-test','run','test','--concurrency=1'],{},0),
]
summary=[]
with (out/'final-verification.jsonl').open('x',encoding='utf-8') as log:
 for label,argv,extra,expected in steps:
  before=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
  assert before=='a493421898f6d6d30bf846f2fe0bf7d4007cb119','Candidate changed before '+label
  started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  print('START '+label,flush=True)
  p=subprocess.run(argv,cwd=root,env=dict(base,**extra))
  record=dict(label=label,argv=argv,cwd=str(root),started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=before,exit_code=p.returncode,expected_exit=expected)
  log.write(json.dumps(record,ensure_ascii=False)+'\n');log.flush();summary.append(record)
  print('FINISH '+label+' exit='+str(p.returncode),flush=True)
(out/'final-verification-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ALL STAGES RECORDED',flush=True)
