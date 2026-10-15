"""Stage-gated 09B runner. Without executor approval it performs no spawn."""
import argparse, json, os, shutil, signal, subprocess, sys, tempfile, time, uuid
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
NODE=shutil.which('node')

def validate_stage_a_inputs(materials, approval, *, protocol=False):
    assert NODE and materials.resolve().parent==BASE and (materials/'static-check.json').exists()
    static=json.loads((materials/'static-check.json').read_bytes());assert static['status']=='PASS' and static['launch_status']=='NO_GO'
    static_root_value=static.get('root')
    assert isinstance(static_root_value,str) and static_root_value, 'executable_material_static_root_required'
    static_root=Path(static_root_value)
    assert static_root.is_dir() and (static_root/'repo/value.txt').is_file() and (static_root/'oracle/contract-09b.json').is_file(), 'executable_material_static_root_required'
    if protocol:
        assert static.get('protocol') is True and static.get('protocol_tag') == 'a07-registered-anthropic-v1', 'executable_material_protocol_required'
    validate_material_lineage(materials, static)
    assert approval.get('approved_by')=='executor' and approval.get('stage')=='A' and approval.get('approval_ref')
    assert approval.get('source_revision')==static['revision'] and approval.get('allow_role_cli_spawn') is False
    return static

def validate_material_lineage(materials, static, changed_paths=None):
    current_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    subprocess.run(['git','merge-base','--is-ancestor',static['revision'],current_revision],cwd=SOURCE,check=True)
    if changed_paths is None:
        changed_paths=subprocess.check_output(['git','diff','--name-only',static['revision'],current_revision],cwd=SOURCE,text=True).splitlines()
        dirty=subprocess.check_output(['git','status','--porcelain','--','workbench','scripts',str(BASE/'run-09b.py')],cwd=SOURCE,text=True).strip()
        assert not dirty,'runner/product worktree changed after material source; no spawn'
    ticket_prefix=str(BASE.relative_to(SOURCE))+'/';blocked=[p for p in changed_paths if p.startswith('workbench/') or p.startswith('scripts/') or p in [str(BASE.relative_to(SOURCE)/'run-09b.py'),str(BASE.relative_to(SOURCE)/'prepare-09b-executable.py')]]
    assert not blocked and all(p.startswith(ticket_prefix) for p in changed_paths),{'blocked_changes':blocked,'changes':changed_paths}

def validate_attempt(attempt):
    required=['attempt_id','session_id','fence','thread_id','workspace']
    assert isinstance(attempt,dict) and all(attempt.get(k) not in [None,''] for k in required)
    assert Path(attempt['workspace']).is_dir()
    return True

def validate_card_preflight(card_file, *, env=None):
    """Run the production task-card validator before any runtime process spawn."""
    task_card_module=(SOURCE/'workbench/src/gates/taskCards.ts').resolve().as_uri()
    card_validator=f"import {{readFileSync}} from 'node:fs'; import {{validateTaskCard}} from '{task_card_module}'; const c=JSON.parse(readFileSync(process.argv[1],'utf8')); validateTaskCard(c,c.id);"
    result=subprocess.run([NODE,'--input-type=module','-e',card_validator,str(card_file)],cwd=SOURCE,env=env,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError({'card_preflight_exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('--materials',type=Path,required=True);p.add_argument('--stage',choices=['A','B','C'],required=True);p.add_argument('--approval',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--protocol',action='store_true');a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=False,exist_ok=False);record={'status':'INCOMPLETE','stage':a.stage,'spawned':False,'real_vendor_model_turns':0,'commands':[],'scope':'Stage-gated 09B; no role CLI in A, B/C not implemented'}
    def save(): (out/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        approval=json.loads(a.approval.read_bytes());static=validate_stage_a_inputs(a.materials,approval,protocol=a.protocol)
        if a.stage!='A': raise RuntimeError('Stage B/C require a separate approved continuation; no spawn from this runner.')
        task='t078-09b-runtime-'+uuid.uuid4().hex[:8]
        card={'id':task,'source':None,'goal':'09B deterministic target stage A','non_goals':['real model','candidate submission'],'paths':{'allow':['value.txt'],'deny':[]},'oracle_paths':['oracle/contract-09b.json'],'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c','raise SystemExit(\'no candidate\')']}],'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        preflight_file=out/'card-preflight.json';preflight_file.write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        validate_card_preflight(preflight_file);record['card_preflight']='taskCards.validateTaskCard via real Node gate module; no root/API/daemon/target';save()
        root=Path(tempfile.mkdtemp(prefix='t078-2-09b-run-',dir='/private/tmp')).resolve();record['root']=str(root)
        for d in ['state','repo','oracle','target','target/home','target/bin','roles/ideation','roles/executor']: (root/d).mkdir(parents=True,exist_ok=True)
        static_root=Path(static['root']);shutil.copyfile(static_root/'repo/value.txt',root/'repo/value.txt');shutil.copyfile(static_root/'oracle/contract-09b.json',root/'oracle/contract-09b.json')
        (root/'target/role.md').write_text('Deterministic 09B target; no model.\n',encoding='utf-8')
        (root/'repo/oracle/contract-09b.json').parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'oracle/contract-09b.json',root/'repo/oracle/contract-09b.json')
        def run(argv,expected=0,timeout=60,env=None):
            item={'argv':list(map(str,argv)),'timeout':timeout};record['commands'].append(item);save();q=subprocess.run(list(map(str,argv)),cwd=SOURCE,env=env or base_env,capture_output=True,text=True,timeout=timeout);item.update({'exit_code':q.returncode,'stdout':q.stdout,'stderr':q.stderr});save();assert q.returncode==expected,(argv,q.stdout,q.stderr);return json.loads(q.stdout.strip().splitlines()[-1]) if q.stdout.strip().startswith('{') else q.stdout
        base_env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CLAUDE_','ANTHROPIC_','CODEX_','GIT_'))};base_env.update(PATH=os.environ.get('PATH','/usr/bin:/bin'),A2A_OPERATOR_CREDENTIAL=str(root/'operator.json'),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
        run(['git','-C',root/'repo','init','-b','main']);run(['git','-C',root/'repo','add','value.txt','oracle/contract-09b.json']);run(['git','-C',root/'repo','commit','-m','09B target baseline'],env={**base_env,'GIT_AUTHOR_NAME':'T078 09B','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'T078 09B','GIT_COMMITTER_EMAIL':'fixture@example.invalid'})
        card_file=root/'card.json';shutil.copyfile(preflight_file,card_file);project='t078-09b-runtime-project'
        receiver=root/'target/bin/codex-receiver';run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',SOURCE/'workbench/tests/t078_native_receiver.c','-o',receiver])
        config={'codex_bin':str(receiver),'codex_home':str(root/'target/home'),'role_card':str(root/'target/role.md'),'role_card_revision':'T078-09B-deterministic','code_revision':static['revision'],'source_snapshot':str(a.materials/'sources.tar.gz'),'hook_authorization':'09B Stage A target only; no role CLI','turn_limit':10,'turn_authorization':'deterministic receiver; model 0'}
        config_file=root/'target/launch-config.json';config_file.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        api_pids=[]
        for role in ['ideation','executor']:
            api_root=root/'roles'/role;log=out/(role+'-api.log');err=out/(role+'-api.err');fout=log.open('w');ferr=err.open('w');argv=[sys.executable,'-B',str(SOURCE/'workbench/tests/t078_09b_fake_api.py'),'--root',api_root,'--role',role,'--port','0']+(['--protocol'] if a.protocol else []);proc=subprocess.Popen(argv,cwd=SOURCE,env=base_env,stdout=fout,stderr=ferr,start_new_session=True);fout.close();ferr.close();api_pids.append({'role':role,'pid':proc.pid,'argv':list(map(str,argv))});record['spawned']=True;save()
        for item in api_pids:
            ready=Path(root/'roles'/item['role']/'api-ready.json');deadline=time.monotonic()+10
            while not ready.exists():
                if time.monotonic()>deadline:raise RuntimeError('fake API readiness deadline')
                time.sleep(.05)
            item['ready']=json.loads(ready.read_bytes())
        daemon=run([NODE,SOURCE/'workbench/src/gates/cli.ts','--state',root/'state','daemon_start','--launch-config',config_file],env=base_env,timeout=30);record['daemon']=daemon;save()
        run(['git', '-C',root/'repo','status','--porcelain=v1'])
        run([NODE,SOURCE/'workbench/src/gates/cli.ts','--state',root/'state','card_save','--task',task,'--card',card_file,'--expected-version','0'],env=base_env);run([NODE,SOURCE/'workbench/src/gates/cli.ts','--state',root/'state','create','--task',task,'--repo',root/'repo','--branch','refs/heads/main','--card-version','1','--project',project],env=base_env)
        dispatch=run([NODE,SOURCE/'workbench/src/gates/cli.ts','--state',root/'state','dispatch','--task',task,'--runtime-mode','workspace-write'],env=base_env,timeout=120);assert dispatch.get('attempt');attempt=dispatch['attempt'];validate_attempt(attempt);record['task']=task;record['project']=project;record['attempt']=attempt;record['dispatch_claim']='dispatch path returned a live non-null attempt; no operator-authored attempt fields'
        info=run([NODE,SOURCE/'workbench/src/gates/cli.ts','--state',root/'state','pane_process_info','--thread',attempt['thread_id']],env=base_env);assert info.get('shell_pid') and info.get('leader');record['target_process']=info
        record['runtime_binding']={'task':task,'attempt':attempt,'process':info,'api':api_pids,'daemon':daemon,'target_claim':'runtime dispatch receipt'}
        (out/'readiness.json').write_text(json.dumps({'status':'READY_FOR_APPROVAL','stage':'A','source_revision':static['revision'],'root':str(root),'task':task,'roles_started':[],'target_binding':attempt,'target_process':info,'api_processes':api_pids,'daemon':daemon,'cleanup_plan':'Authenticated daemon_stop; verify target/API argv+PID/lstart; stop owned APIs once; archive and delete root only after byte readback; slots separate'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');record['status']='READY_FOR_APPROVAL';record['next']='Stop here; main approval required before stage B role launches';save()
    except Exception as error:
        record.update(error=repr(error),traceback=__import__('traceback').format_exc());save();return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
