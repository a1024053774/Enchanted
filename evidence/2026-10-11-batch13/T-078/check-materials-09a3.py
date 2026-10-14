"""Static 09A-3 checks. No vendor CLI, sockets, API, UI or build starts."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import tarfile

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078');BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--generation',choices=['09a3r2'],required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
r={'status':'INCOMPLETE','scope':'静态材料和源码字节核对；不作产品验收','starts':0,'real_model_turns':0,'fixtures':[],'commands':[]}
def run(argv):
    result=subprocess.run(argv,cwd=SOURCE,capture_output=True,text=True,encoding='utf-8')
    r['commands'].append({'argv':argv,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr});assert result.returncode==0,argv
try:
    seen=set()
    for suffix,handling,actions in [(args.generation,'simulated-empty-declaration',[{'action':'Escape'},{'action':'clear-restored-draft','key':'Control+C'},{'action':'declare-empty-release','truth':'empty'}]),
                                  (args.generation+'-block','retain-draft-for-block',[{'action':'Escape'},{'action':'retain-restored-draft'},{'action':'declare-empty-release','truth':'intentionally-false'}])]:
        m=BASE/('p1-materials-'+suffix);a=json.loads((m/'approval.json').read_bytes());root=Path(a['input']['root'])
        assert root.is_dir() and root.as_posix().startswith('/private/tmp/t078-2-p1-09a3')
        assert sorted(x.name for x in (root/'repo').iterdir())==['value.txt']
        assert (root/'repo/value.txt').read_bytes()==b'P1 isolated fixture\n'
        for n in ['input.json','nonce.txt','nonce-2.txt','role.md','scenario.json']:assert (root/n).read_bytes()==(m/n).read_bytes(),n
        assert not (root/'state/state.sqlite3').exists() and not (root/'api-ready.json').exists()
        assert not (m/'launch').exists() and not (m/'readiness.json').exists() and not (m/'actions-approval.json').exists()
        assert not list((m/'approvals').iterdir())
        assert a['input']['turn_limit']==2
        env=a['launch']['env'];argv=a['launch']['argv']
        assert env['HOME']==str(root/'home') and env['CLAUDE_CONFIG_DIR']==str(root/'claude')
        assert env['ANTHROPIC_AUTH_TOKEN']=='a2a-fixture-key-not-a-secret' and 'ANTHROPIC_API_KEY' not in env
        assert env['ANTHROPIC_BASE_URL']=='http://127.0.0.1:0' and env['A2A_HOOK_TRACE_DIR']==str(root/'hooks')
        assert not (root/'home/.claude.json').exists() and not (root/'claude/.claude.json').exists()
        assert json.loads((root/'claude/settings.json').read_bytes())=={'theme':'dark'}
        assert (root/'claude/settings.json').read_bytes()==(m/'isolated-settings.json').read_bytes()
        assert argv[0]=='/Users/luckye/.local/share/claude/versions/2.1.296' and '--bare' not in argv and '-p' not in argv
        assert set(a['launch']['settings'])=={'hooks'}
        assert set(a['launch']['settings']['hooks'])=={'UserPromptSubmit','Stop','PermissionRequest'}
        for hooks in a['launch']['settings']['hooks'].values():assert hooks[0]['hooks'][0]['timeout']==3
        scenario=json.loads((m/'scenario.json').read_bytes());assert scenario['name']=='esc-two' and scenario['draft_handling']==handling
        assert [x['mode'] for x in scenario['requests']]==['cancel','echo']
        assert scenario['requests'][0]['nonce']!=scenario['requests'][1]['nonce']
        consent=json.loads((m/'actions-approval-template.json').read_bytes())
        assert consent['source']=='test-simulated-user' and consent['approved_by'] is None
        assert [{k:v for k,v in step.items() if k not in ['approved_by','approval_ref','basis']} for step in consent['actions']]==actions
        assert all(step['approved_by'] is None and step['approval_ref'] is None and step['basis'] is None for step in consent['actions'])
        assert Path(consent['key_basis'])==BASE/'KEY-BASIS-09A3R2.md'
        assert a['input']['code_revision']==json.loads((BASE/'source-freeze-09a3r2.json').read_bytes())['revision']
        template=json.loads((m/'screen-key-approval-template.json').read_bytes());assert template['approved_by'] is None
        assert template['trust_sequence']==['ArrowDown','Enter'] and template['trust_target']=='Yes, I trust this folder'
        assert (m/'security-notice-text.txt').read_bytes()==(BASE/'p1-materials-09a2/security-notice-text.txt').read_bytes()
        for key in ['root','launch','session','thread','task']:
            identity=(key,a['input'][key]);assert identity not in seen;seen.add(identity)
        names=json.loads((m/'source-files.json').read_bytes())
        with tarfile.open(m/'sources.tar.gz') as archive:
            for n in names:
                data=(SOURCE/n).read_bytes();assert data==archive.extractfile(n).read(),n
                if n.endswith('.py'):ast.parse(data,filename=n)
        driver=json.loads((m/'scenario-driver.json').read_bytes());assert driver['starts']==0 and driver['real_model_budget']==0
        assert driver['expected_messages_requests']==(1 if suffix.endswith('-block') else 2)
        assert driver['automation_source']=='test-simulated-user' and driver['control_c_attempt_budget']==(0 if suffix.endswith('-block') else 1)
        r['fixtures'].append({'materials':str(m),'root':str(root),'launch':a['input']['launch'],'session':a['input']['session'],
                              'code_revision':a['input']['code_revision'],'frozen_files':len(names)})
    for n in ['src/panes.ts','src/daemon.ts','src/gates/cli.ts','app/main.ts','app/preload.ts','tests/electron_driver.mjs']:
        run(['node','--check',str(SOURCE/'workbench'/n)])
    run(['node','--input-type=module','-e',"import {readFileSync} from 'node:fs';import {transformWithOxc} from './workbench/node_modules/vite/dist/node/index.js';const p='workbench/app/renderer.tsx';await transformWithOxc(readFileSync(p,'utf8'),p);console.log('PASS TSX in memory');"])
    run(['bash','-n',str(BASE/'outside-09a3.sh')]);run(['git','diff','--check'])
    run(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'])
    oversized=[str(f) for f in BASE.rglob('*') if f.is_file() and f.stat().st_size>5*1024*1024];assert not oversized,oversized
    r['status']='PASS'
except Exception as error:
    import traceback
    r.update(error=repr(error),traceback=traceback.format_exc())
with args.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
