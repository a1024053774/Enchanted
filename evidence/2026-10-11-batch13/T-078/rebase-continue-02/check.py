"""Read-only guards for one fixed rebase stop. No Git mutation or model run."""
import json
from pathlib import Path
import re
import subprocess

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
HERE=Path(__file__).resolve().parent
HEAD='888d83795ce3d46cdc4629c90f927eed8417c902'
REBASE_HEAD='8166e391c677179d483d886ad7a1d4279e0bc564'
FILES=['workbench/src/daemon.ts','workbench/src/gates/cli.ts','workbench/src/panes.ts']
r={'status':'INCOMPLETE','scope':'固定变基停点与源码语法；不是行为验收','expected_head':HEAD,
   'expected_rebase_head':REBASE_HEAD,'expected_conflicts':FILES,'commands':[],'real_model_turns':0}
def run(argv):
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    r['commands'].append({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    assert p.returncode==0,(argv,p.returncode,p.stderr)
    return p.stdout.strip()
try:
    assert run(['git','rev-parse','HEAD'])==HEAD
    assert run(['git','rev-parse','REBASE_HEAD'])==REBASE_HEAD
    assert run(['git','diff','--name-only','--diff-filter=U']).splitlines()==FILES
    head_name=ROOT/run(['git','rev-parse','--git-path','rebase-merge/head-name'])
    assert head_name.read_text(encoding='utf-8').strip()=='refs/heads/exec/t078'
    for name in FILES:
        data=(ROOT/name).read_bytes()
        assert data==(HERE/'resolved'/name).read_bytes(),('Resolved candidate changed',name)
        assert not re.search(rb'(?m)^(?:<<<<<<<|=======|>>>>>>>)',data),name
        run(['node','--check',name])
    run(['git','diff','--check'])
    r['status']='PASS'
except Exception as error:
    r['error']=repr(error)
print(json.dumps(r,ensure_ascii=False,indent=2))
raise SystemExit(0 if r['status']=='PASS' else 1)
