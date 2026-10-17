#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - <<'PY'
import json,os,subprocess,sys
from pathlib import Path
base=Path('evidence/2026-10-11-batch13/T-078');before='b5b8b165d06c5cc5ab341c965679d7932d74c8a3'
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==before and git('branch','--show-current')=='exec/t078'
assert os.environ.get('CODEX_THREAD_ID')=='01a13a72-892d-7e33-8237-a592c9652c35'
assert os.environ.get('A2A_TASK')=='T-078-1' and os.environ.get('A2A_ROLE')=='worker'
assert not any(k in os.environ for k in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'])
assert not git('diff','--cached','--name-only')
assert not git('diff','--','workbench/src','workbench/app','workbench/hooks','workbench/bin','acceptance','scripts')
cleanup=json.loads((base/'p1-materials-slice1-green-3/cleanup-185/result.json').read_bytes())
assert cleanup['status']=='PASS' and cleanup['owned_exits_confirmed']==[49173,49190,49211,49210]
assert cleanup['root_removed'] is True and cleanup['root_retained'] is False and cleanup['byte_readback']=='PASS' and cleanup['slots_removed']==[]
assert cleanup['signals_sent'] in [[],[{'pid':49173,'signal':'SIGTERM'}]]
readback=json.loads((base/'slice1-green-3-closeout/readback.json').read_bytes());assert readback['status']=='PASS' and readback['main_Messages']==3
paths=json.loads((base/'09b-handoff-paths.json').read_bytes())
cleanup_dir=base/'p1-materials-slice1-green-3/cleanup-185'
assert cleanup_dir.is_dir(), 'Completed cleanup evidence directory is required'
# Cleanup is an independently authorized, fixed-instance evidence tree. Keep
# its exact root in this allowlist; every file below it is preserved verbatim.
cleanup_prefix=str(cleanup_dir)
if cleanup_prefix not in paths: paths.append(cleanup_prefix)
for row in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']).decode('utf-8').split('\0'):
    if row:
        name=row[3:];assert any(name==p or name.startswith(p+'/') for p in paths),('Unowned work; no mutation',name)
assert all(Path(p).exists() for p in paths)
for name in ['09b-source-freeze.json','09b-materials-01','09b-preparation-run']:assert not (base/name).exists(),('Preserve existing output; no retry',name)
subprocess.run(['git','diff','--check'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): close real controller slice and prepare 09B review'],check=True)
revision=git('rev-parse','HEAD')
with (base/'09b-source-freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'revision':revision,'parent_revision':before,'green3_scene':'PASS','cleanup':'PASS','09B_stage':'plan-review only','09B_launch':'NO_GO','real_model_turns':0},f,indent=2);f.write('\n')
out=base/'09b-preparation-run';out.mkdir()
argv=[sys.executable,'-B',str((base/'prepare-09b-plan.py').resolve())]
with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:r=subprocess.run(argv,stdout=stdout,stderr=stderr)
with (out/'command.json').open('x',encoding='utf-8') as f:json.dump({'argv':argv,'revision':revision,'exit_code':r.returncode,'scope':'Review-only static proposals; no launches'},f,indent=2);f.write('\n')
assert r.returncode==0,'Preserve failed packet/commit; no retry'
packet=base/'09b-materials-01';facts=json.loads((packet/'static-check.json').read_bytes())
assert facts['status']=='PASS' and facts['revision']==revision and facts['launch_status']=='NO_GO'
with (base/'RESULTS.md').open('a',encoding='utf-8') as f:
    f.write('\n## green-3成功清理与09B计划包冻结（脚本执行读回）\n\n')
    f.write('[cleanup-185](p1-materials-slice1-green-3/cleanup-185/result.json) **PASS**：原进程退出、最多仅API49173一次SIGTERM、外置归档字节读回后删除成功根；slot仍保留。source `'+revision+'`。\n\n')
    f.write('[09B计划包](09b-materials-01/static-check.json) 静态 **PASS**，root `'+facts['root']+'`，source/Git/tar逐文件相同；包含独立角色目录／拟argv/env、协议、oracle、task卡和空审批模板。明确 **launch NO_GO**：当前profile与双角色阶段驱动前置未完成；未创建Git repo／broker／角色／目标，实际09B、09C、独立reviewer、整票仍INCOMPLETE。\n')
subprocess.run(['git','add','--',str(packet),str(out),str(base/'09b-source-freeze.json'),str(base/'RESULTS.md')],check=True)
subprocess.run(['git','diff','--cached','--stat'],check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze two-controller 09B plan review packet'],check=True)
assert not git('status','--porcelain')
print(json.dumps({'status':'PASS','source_revision':revision,'materials_revision':git('rev-parse','HEAD'),'packet':str(packet),'launch':'NO_GO','next':'Plan review first; no process started'},ensure_ascii=False))
PY
