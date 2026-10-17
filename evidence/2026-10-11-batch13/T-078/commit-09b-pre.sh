#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json, os, subprocess
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='d63611ea24212922e62fd8c690ce923748d481c3'
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'])
assert not git('diff','--cached','--name-only')
paths=json.loads((base/'09b-pre-allowlist.json').read_bytes())
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode().split('\0'):
    if row:
        name=row[3:];assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; no mutation',name)
assert all(Path(p).exists() for p in paths)
for p in ['09b-pre-source-freeze.json','09b-pre-commit-run']:
    assert not (base/p).exists(),('Existing output; preserve it, no retry',p)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','fix(T-078): isolate controller profiles and allow six Claude roots'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-pre-source-freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'revision':revision,'parent_revision':before,'product_scope':['workbench/src/claudeLaunch.ts','workbench/src/panes.ts'],
               'turn_limit':{'min':1,'max':6},'role_paths':'roles/<preset>/{home,claude,tmp,shell,requests,hooks,user-data,debug}',
               'shared_paths':['broker/state','repo'],'real_model_turns':0,'launch':'NO_GO'},f,indent=2);f.write('\n')
run=base/'09b-pre-commit-run';run.mkdir()
with (run/'command.json').open('x',encoding='utf-8') as f:json.dump({'status':'PASS','revision':revision,'scope':'Product pre-slice commit only; no service/CLI/API/target start'},f,indent=2);f.write('\n')
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:
    f.write('\n## 09B 前置产品切片提交冻结\n\n代码提交 `'+revision+'`，角色隔离目录、6根Claude信号预算、P1生成／续跑同步及红绿／slice1回归证据已冻结；未启动服务、CLI、API或目标。双角色驱动／独立oracle及可执行launch包留待下一段，当前launch NO_GO。\n')
second=[str(base/'09b-pre-source-freeze.json'),str(run),str(base/'RESULTS.md')]
subprocess.run(['git','add','--',*second],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze 09B profile precondition evidence'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'launch':'NO_GO','next':'Implement double-role fake API/driver/oracle after review'},ensure_ascii=False))
PY
