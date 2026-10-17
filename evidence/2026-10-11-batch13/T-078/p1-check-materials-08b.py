"""Validate P1-08b frozen materials; do not start services or vendor CLIs."""
import argparse,ast,json,subprocess,tarfile
from pathlib import Path
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078';M=BASE/'p1-materials-08b'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
r={'status':'INCOMPLETE','scope':'Static material checks only','commands':[],'real_cli_starts':0,'api_starts':0,'real_vendor_model_turns':0}
def run(argv):
    c=subprocess.run(argv,cwd=SOURCE,capture_output=True,text=True,encoding='utf-8')
    r['commands'].append({'argv':argv,'exit_code':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
    assert c.returncode==0,argv
try:
    a=json.loads((M/'approval.json').read_text(encoding='utf-8'));root=Path(a['input']['root']);env=a['launch']['env'];argv=a['launch']['argv']
    assert root.is_dir() and sorted(f.name for f in (root/'repo').iterdir())==['value.txt']
    assert (root/'repo/value.txt').read_bytes()==b'P1 isolated fixture\n'
    assert env['HOME']==str(root/'home') and env['CLAUDE_CONFIG_DIR']==str(root/'claude')
    assert env['ANTHROPIC_AUTH_TOKEN']=='a2a-fixture-key-not-a-secret' and 'ANTHROPIC_API_KEY' not in env
    assert env['CLAUDE_CODE_DISABLE_TERMINAL_TITLE']=='1' and 'IS_DEMO' not in env
    assert env['A2A_HOOK_TRACE_DIR']==str(root/'hooks')
    assert argv[argv.index('--debug-file')+1]==str(root/'claude-debug.log')
    assert json.loads((root/'claude/settings.json').read_bytes())=={'theme':'dark'}
    assert (root/'claude/settings.json').read_bytes()==(M/'isolated-settings.json').read_bytes()
    assert set(a['launch']['settings'])=={'hooks'}
    for groups in a['launch']['settings']['hooks'].values():assert groups[0]['hooks'][0]['timeout']==3
    assert a['launch']['turn_limit']==1 and '--bare' not in argv and '-p' not in argv
    assert not (root/'claude/.claude.json').exists() and not (root/'home/.claude.json').exists()
    assert not (M/'readiness.json').exists() and not list((M/'approvals').glob('*.json'))
    for n in ['input.json','role.md','nonce.txt']:assert (root/n).read_bytes()==(M/n).read_bytes()
    names=json.loads((M/'source-files.json').read_text(encoding='utf-8'))
    with tarfile.open(M/'sources.tar.gz') as arc:
        for n in names:
            data=(SOURCE/n).read_bytes();assert data==arc.extractfile(n).read(),n
            if n.endswith('.py'):ast.parse(data,filename=n)
    r.update(root=str(root),launch=a['input']['launch'],session=a['input']['session'],code_revision=a['input']['code_revision'],frozen_files=len(names))
    for n in ['src/claudeLaunch.ts','src/gates/cli.ts','src/hookTrace.ts','src/panes.ts','src/daemon.ts']:
        run([a['launch']['node_executable'],'--check',str(SOURCE/'workbench'/n)])
    run(['bash','-n',str(BASE/'outside-sandbox.sh')]);run(['git','diff','--check','--','workbench'])
    oversized=[str(f) for f in BASE.rglob('*') if f.is_file() and f.stat().st_size>5*1024*1024]
    assert not oversized,oversized
    run(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'])
    r['status']='PASS'
except Exception as error:
    import traceback
    r.update(error=repr(error),traceback=traceback.format_exc())
with args.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
