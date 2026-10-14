"""Check P1-06 materials and exact auth delta without starting a vendor CLI."""
import argparse
import ast
import json
import subprocess
import tarfile
from pathlib import Path

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
MATERIALS=BASE/'p1-materials-06'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=BASE/'p1-preparation-check-06.json')
args=parser.parse_args()
record={'status':'INCOMPLETE','scope':'Static checks only','commands':[],
        'real_cli_starts':0,'api_starts':0,'real_vendor_model_turns':0}
def command(argv):
    p=subprocess.run(argv,cwd=SOURCE,capture_output=True,text=True,encoding='utf-8')
    record['commands'].append({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:raise RuntimeError({'failed_command':argv,'exit_code':p.returncode})
    return p.stdout
try:
    old=json.loads((BASE/'p1-materials-05/approval.json').read_text(encoding='utf-8'))
    new=json.loads((MATERIALS/'approval.json').read_text(encoding='utf-8'))
    pairs=[(old['input'][k],new['input'][k]) for k in ['root','task','launch','session','thread','source_snapshot']]
    def rebind(v):
        if isinstance(v,str):
            for before,after in pairs:v=v.replace(before,after)
            return v
        if isinstance(v,list):return [rebind(i) for i in v]
        if isinstance(v,dict):return {k:rebind(i) for k,i in v.items()}
        return v
    for k in ['argv','shell_argv','settings','role_text','node_executable','node_version']:
        assert new['launch'][k]==rebind(old['launch'][k]),k
    expected=rebind(old['launch']['env'])
    assert expected.pop('ANTHROPIC_API_KEY')=='a2a-fixture-key-not-a-secret'
    expected['ANTHROPIC_AUTH_TOKEN']='a2a-fixture-key-not-a-secret'
    assert new['launch']['env']==expected
    record['exact_auth_delta']={'removed':'ANTHROPIC_API_KEY','added':'ANTHROPIC_AUTH_TOKEN','argv_hooks_role_unchanged':True}
    root=Path(new['input']['root']);assert root.is_dir()
    assert new['input']['api_url']=='http://127.0.0.1:0'
    for n in ['input.json','role.md','nonce.txt']:assert (root/n).read_bytes()==(MATERIALS/n).read_bytes(),n
    settings=(root/'claude/settings.json').read_bytes()
    assert json.loads(settings)=={'theme':'dark'} and settings==(MATERIALS/'isolated-settings.json').read_bytes()
    for p in ['claude','home']:assert not (root/p/'.claude.json').exists()
    ready=json.loads((MATERIALS/'readiness-template.json').read_text(encoding='utf-8'))
    assert ready=={'launch':new['input']['launch'],'session':new['input']['session'],'confirmed_by':None,'readiness':'unconfirmed','basis':None}
    assert not (MATERIALS/'readiness.json').exists()
    files=json.loads((MATERIALS/'source-files.json').read_text(encoding='utf-8'))
    with tarfile.open(MATERIALS/'sources.tar.gz') as archive:
        for n in files:
            data=(SOURCE/n).read_bytes();assert data==archive.extractfile(n).read(),n
            if n.endswith('.py'):ast.parse(data,filename=n)
    record['frozen_files']=len(files)
    node=new['launch']['node_executable']
    for n in ['workbench/src/claudeLaunch.ts','workbench/tests/test_t078_p1_auth.ts','workbench/tests/test_t078_p1_bootstrap.ts']:
        command([node,'--check',str(SOURCE/n)])
    command(['bash','-n',str(BASE/'outside-sandbox.sh')])
    command(['git','diff','--check'])
    for n in ['workbench/README.md','evidence/2026-10-11-batch13/T-078/P1-APPROVAL-06.md','evidence/2026-10-11-batch13/T-078/RESULTS.md']:
        data=(SOURCE/n).read_bytes();data.decode('utf-8');assert not data.startswith(b'\xef\xbb\xbf') and b'\r' not in data,n
    assert not command(['find',str(BASE),'-type','f','-size','+5M']).strip()
    command(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'])
    record.update(status='PASS',root=str(root),readiness_not_preapproved=True)
except Exception as error:
    import traceback
    record.update(error=repr(error),traceback=traceback.format_exc())
with args.output.open('x',encoding='utf-8') as output:json.dump(record,output,ensure_ascii=False,indent=2)
print(json.dumps(record,ensure_ascii=False));raise SystemExit(0 if record['status']=='PASS' else 1)
