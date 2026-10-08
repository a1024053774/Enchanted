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
 ('observer-failure-final-03', [python,'-B',str(out/'run-fork-check.py'),'observer-failure-final-03',str(out/'observer-failure-check.ts')],{},0),
 ('inflight-observer-final-03', [python,'-B',str(out/'run-fork-check.py'),'inflight-observer-final-03',str(out/'inflight-observer-check.ts')],{},0),
 ('runtime-refusal-final-03', [python,'-B',str(out/'run-fork-check.py'),'runtime-refusal-final-03',str(out/'runtime-refusal-check.ts')],{},0),
 ('human-input-final-03', [python,'-B',str(out/'run-fork-check.py'),'human-input-final-03',str(out/'human-input-check.ts')],{},0),
 ('native-service-final-03', [python,'-B',str(out/'run-fork-check.py'),'native-service-final-03',str(out/'native-service-check.ts')],{},0),
 ('final-run-03', [python,'-B',str(out/'run-acceptance.py'),'final-run-03',str(out/'test_run_native_e2e.py')],{'COOP_SCRIPT':str(out/'native-entry.py')},0),
 ('mutant-done-final-03', [python,'-B',str(out/'run-mutant.py'),'done-no-submit','mutant-done-final-03'],{},1),
 ('mutant-attempt-final-03', [python,'-B',str(out/'run-mutant.py'),'ignore-expected-attempt','mutant-attempt-final-03'],{},1),
 ('final-delivery-recovery-03', [python,'-B',str(out/'run-acceptance.py'),'final-delivery-recovery-03',str(root/'evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py')],{'COOP_NATIVE_ENTRY':str(fork/'packages/a2a-gates/src/cli.ts')},0),
 ('final-core-test-03', [python,'-B',str(out/'run-fork-check.py'),'final-core-test-03','run','--cwd','packages/a2a-gates','test'],{},0),
 ('final-fmt-check-03', [python,'-B',str(out/'run-fork-check.py'),'final-fmt-check-03','run','fmt:check'],{},0),
 ('final-lint-03', [python,'-B',str(out/'run-fork-check.py'),'final-lint-03','run','lint'],{},0),
 ('final-typecheck-03', [python,'-B',str(out/'run-fork-check.py'),'final-typecheck-03','run','typecheck'],{},0),
 ('final-windows-runtime-03', [python,'-B',str(out/'run-fork-check.py'),'final-windows-runtime-03','run','windows-runtime:check'],{},0),
 ('final-migrations-03', [python,'-B',str(out/'run-fork-check.py'),'final-migrations-03','run','migrations:check'],{},0),
 ('final-workspace-test-03', [python,'-B',str(out/'run-fork-check.py'),'final-workspace-test-03','run','test','--concurrency=1'],{},0),
]
summary=[]
with (out/'final-verification-03.jsonl').open('x',encoding='utf-8') as log:
 for label,argv,extra,expected in steps:
  before=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
  assert before=='fa3fc3352805d00e41c454fa6f810807528de3a9','Candidate changed before '+label
  started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  print('START '+label,flush=True)
  p=subprocess.run(argv,cwd=root,env=dict(base,**extra))
  record=dict(label=label,argv=argv,cwd=str(root),started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=before,exit_code=p.returncode,expected_exit=expected)
  log.write(json.dumps(record,ensure_ascii=False)+'\n');log.flush();summary.append(record)
  print('FINISH '+label+' exit='+str(p.returncode),flush=True)
(out/'final-verification-summary-03.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ALL STAGES RECORDED',flush=True)
