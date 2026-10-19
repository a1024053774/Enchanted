"""只读真实复验输出与冻结测试：定位 shell_io 的流式读回边界。"""
import ast
import base64
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

root=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/reviewer-02-replay-01')
review=json.loads((root/'run.json').read_text(encoding='utf-8'))
candidate=json.loads((root/'candidate/run.json').read_text(encoding='utf-8'))
revision=review['target']
test_path='workbench/tests/test_t104_shell_e2e.py'
source=subprocess.check_output(['git','show',revision+':'+test_path],text=True)
tree=ast.parse(source)
reader=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='output_lines')
assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and
    any(isinstance(t,ast.Name) and t.id=='lines' for t in n.targets) and isinstance(n.value,ast.Call) and
    isinstance(n.value.func,ast.Name) and n.value.func.id=='wait_for')
entries=[json.loads(line) for line in (root/'candidate/transport.jsonl').read_text(encoding='utf-8').splitlines()]
reads=[(number,row) for number,row in enumerate(entries,1) if row['request']['input']['command']=='pane_output']
number,last=reads[-1]
launch=last['request']['input']['launch']
def request(command,**fields):
    assert command=='pane_output' and fields==dict(launch=launch,offset=0)
    return last['reply']
context=dict(re=re,request=request,cwd=Path(candidate['fixture'])/'项目 alpha space',first=dict(record=dict(id=launch)))
exec(compile(ast.Module(body=[reader],type_ignores=[]),test_path,'exec'),context)
lines=context['output_lines'](context['first'])
predicate=eval(compile(ast.Expression(body=assignment.value.args[0]),test_path,'eval'),context)
ready=bool(predicate())
prefix=base64.b64decode(last['reply']['data_base64'])
trace=(root/'candidate/state/traces'/launch/'pty.raw').read_bytes()
clean=re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))','',trace.decode('utf-8')).splitlines()
partial_env=[line for line in lines if line.startswith('A2A_')]
final_env=[line for line in clean if line.startswith('A2A_')]
expected=['A2A_PROJECT=t104-alpha']
assert ready and partial_env==[] and final_env==expected
assert trace[:len(prefix)]==prefix and trace.index(b'A2A_PROJECT=')==len(prefix)
files=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'workbench/src'],text=True).splitlines()+[test_path]
copied=Path(review['scratch'])/'candidate'
assert all((copied/name).read_bytes()==subprocess.check_output(['git','show',revision+':'+name]) for name in files)
databases=[]
for path in [root/'candidate/state/state.sqlite3',Path(review['scratch'])/'candidate-db/state.sqlite3']:
    assert path.is_file() and not Path(str(path)+'-wal').exists()
    with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        events=db.execute('SELECT count(*) FROM orchestration_events').fetchone()[0]
    databases.append(dict(path=str(path),bytes=path.stat().st_size,header_versions=list(path.read_bytes()[18:20]),
                          wal_exists=False,shm_exists=Path(str(path)+'-shm').exists(),events=events,immutable_read='PASS'))
report=dict(status='PASS',scope='只读诊断；不代表可选复验或整票验收通过',target=revision,
            finding='等待条件在 env 输出到达前已满足；当时不是多出变量，而是尚无 A2A 行',
            failing_snapshot=dict(transport_line=number,next_offset=last['reply']['next_offset'],total_bytes=last['reply']['total_bytes'],
                                  wait_predicate_ready=ready,a2a_lines=partial_env),
            completed_trace=dict(bytes=len(trace),env_offset=trace.index(b'A2A_PROJECT='),a2a_lines=final_env),
            frozen_source=dict(files=len(files),byte_equal=True),databases=databases,
            review_script_error=dict(error=review.get('error'),traceback=review.get('traceback')),
            changes='未改产品、现有测试、审查脚本或原始证据')
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
print(json.dumps(report,ensure_ascii=False))
