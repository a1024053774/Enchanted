"""Stage-gated 09B runner. Without executor approval it performs no spawn."""
import argparse, json, os, re, shutil, signal, subprocess, sys, tempfile, time, uuid
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
NODE=shutil.which('node')
REGRESSION_REPORTS = ['review-followup-regressions-02', 'review-followup-mutant-cas-03',
                      'review-followup-mutant-lock-04', 'merge-main-4-t078-regressions-01']
PREFLIGHT_SOURCE = str(Path(__file__).resolve().relative_to(SOURCE))
CLASSIFIER_SOURCE = str(Path(__file__).resolve().with_name('run-review-followup-regressions.py').relative_to(SOURCE))

def validate_regression_readbacks(static, approval):
    paths = [str(BASE / name / 'result.json') for name in REGRESSION_REPORTS]
    assert static.get('regression_readbacks') == approval.get('regression_readbacks') == paths, 'four_bound_regression_readbacks_required'
    reports = [json.loads(Path(path).read_bytes()) for path in paths]
    full, cas, lock, own = reports
    assert full['status'] == 'INCOMPLETE' and full.get('error') == 'AssertionError()', 'legacy_failure_must_be_CAS_classifier_only'
    stages = full['stages']
    assert [row['name'] for row in stages] == ['coop', 'recovery', 'run', 'cas', 'cards', 'mutant-fence', 'mutant-cas'], 'unexpected_legacy_failure_boundary'
    for row in stages[:6]:
        assert row['status'] == 'PASS' and row['exit_code'] == (1 if row['name'] == 'mutant-fence' else 0), 'legacy_completed_stage_required'
    assert stages[6]['status'] == 'INCOMPLETE' and stages[6]['exit_code'] == 1 and 'verdict' not in stages[6], 'legacy_CAS_classification_failure_required'
    trace = full['traceback']
    frames = re.findall(r'File "([^"]+)", line (\d+), in verify_mutant', trace)
    classifier = CLASSIFIER_SOURCE
    assert len(frames) == 1 and frames[0][0] == str(SOURCE / classifier) and trace.rstrip().endswith('AssertionError'), 'legacy_CAS_classifier_frame_required'
    old_source = subprocess.check_output(['git', 'show', full['revision'] + ':' + classifier], cwd=SOURCE, text=True)
    predicate = "assert any(item['claim'] in labels and item['pass'] is False for item in assertions)"
    assert old_source.splitlines()[int(frames[0][1]) - 1].strip() == predicate and predicate in trace, 'legacy_CAS_classifier_assertion_required'
    assert all(label in old_source for label in ['CAS rejects a changed expected old value', 'CAS preserves the external writer reference']), 'legacy_CAS_classifier_labels_required'
    suites = [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1), ('cards', 15)]
    for suite, count in suites:
        child = json.loads((Path(paths[0]).parent / suite / 'run.json').read_bytes())
        assert child['revision'] == full['revision'] and child['status'] == 'PASS' and child['tests_run'] == count
        assert child['failures'] == child['errors'] == child['skipped'] == 0 and not child['unexecuted_methods'] and not child['collection_errors'], 'complete_original_suite_required'
    cases = {'cas': 'test_external_write_between_read_and_cas_is_preserved', 'lock': 'test_live_verify_excludes_verify_and_integrate'}
    legacy_child = json.loads((Path(paths[0]).parent / 'mutant-cas/run.json').read_bytes())
    assert legacy_child['selected_cases'] == [cases['cas']] and legacy_child['tests_run'] == 1 and legacy_child['failures'] == 1 and legacy_child['errors'] == legacy_child['skipped'] == 0
    assert any(row.get('classification') == 'business-red' for row in legacy_child['original_results']), 'legacy_CAS_must_be_business_red'
    for report, name, path in [(cas, 'cas', paths[1]), (lock, 'lock', paths[2])]:
        assert report['status'] == 'PASS' and report['scope'] == 'mutant-' + name + ' only' and report['business_revision'] == full['business_revision'], 'scoped_mutant_receipt_required'
        assert len(report['stages']) == 1
        row = report['stages'][0]; verdict = row['verdict']
        assert row['name'] == 'mutant-' + name and row['status'] == 'PASS' and row['exit_code'] == 1
        assert verdict['status'] == 'PASS' and verdict['expected_exit'] == verdict['actual_exit'] == 1 and verdict['errors'] == 0 and verdict['business_assertion_rejected_mutant'] is True
        child = json.loads((Path(path).parent / ('mutant-' + name) / 'run.json').read_bytes())
        assert child['revision'] == report['revision'] and child['selected_cases'] == [cases[name]] and child['tests_run'] == 1 and child['failures'] > 0 and child['errors'] == child['skipped'] == 0
        assert child['mutant_core'] == verdict['loaded_core'] and any(row.get('classification') == 'business-red' for row in child['original_results']), 'scoped_mutant_business_red_required'
    assert own['status'] == 'PASS' and [row['name'] for row in own['stages']] == ['pending', 'startup-domain', 'startup-entry', 'worker']
    assert all(row['status'] == 'PASS' and row['exit_code'] == 0 for row in own['stages']), 'T078_regression_required'
    # Only this Stage A readback preflight changed since the runtime regressions.
    # The new packet still freezes this file; all other closure members, the
    # complete product/tests and acceptance remain bound to every tested revision.
    protected = list(dict.fromkeys(['workbench', 'acceptance', 'scripts', *[p for p in static['source_paths'] if p != PREFLIGHT_SOURCE]]))
    harness_validation = None
    if static['scene'] == '09C' and static.get('harness_rehearsal'):
        import importlib.util
        path = BASE/'c3-revalidation.py';spec = importlib.util.spec_from_file_location('c3_revalidation',path)
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        exclusions, harness_validation = module.validate(static, approval)
        protected = [p for p in protected if p not in exclusions]
        protected += [':(exclude,literal)' + p for p in exclusions]
    tested_revisions = []
    for receipt in reports:
        tested = receipt.get('revision') or receipt.get('source_revision'); assert tested, 'tested_revision_required'
        subprocess.run(['git', 'merge-base', '--is-ancestor', tested, 'HEAD'], cwd=SOURCE, check=True)
        assert not subprocess.check_output(['git', 'diff', tested, '--', *protected], cwd=SOURCE), 'regression_source_changed'
        tested_revisions.append(tested)
    return {'status': 'PASS', 'readbacks': paths, 'tested_revisions': tested_revisions,
            'legacy_overall_status': full['status'], 'legacy_exception': 'CAS classifier assertion only; original result retained',
            'CAS_replacement': paths[1], 'lock_completion': paths[2], 'completed_original_methods': 51,
            'regression_scope_excludes': [PREFLIGHT_SOURCE], 'exclusion_reason': 'Stage A preflight is frozen in the new packet',
            'harness_validation': harness_validation}

def validate_stage_a_inputs(materials, approval, *, protocol=False):
    assert NODE and materials.resolve().parent==BASE and (materials/'static-check.json').exists()
    static=json.loads((materials/'static-check.json').read_bytes());assert static['status']=='PASS' and static['launch_status']=='NO_GO'
    static_root_value=static.get('root')
    assert isinstance(static_root_value,str) and static_root_value, 'executable_material_static_root_required'
    static_root=Path(static_root_value)
    assert static_root.is_dir() and (static_root/'repo/value.txt').is_file() and (static_root/'oracle/contract-09b.json').is_file(), 'executable_material_static_root_required'
    if protocol:
        assert static.get('protocol') is True and static.get('protocol_tag') == 'rev2-raw-c-profile-v1', 'executable_material_protocol_required'
    validate_material_lineage(materials, static)
    assert approval.get('approved_by')=='executor' and approval.get('stage')=='A' and approval.get('approval_ref')
    assert approval.get('source_revision')==static['revision'] and approval.get('allow_role_cli_spawn') is False
    assert static['scene'] in ['09B','09C']
    static['regression_validation'] = validate_regression_readbacks(static, approval)
    return static

def validate_material_lineage(materials, static, changed_paths=None):
    current_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()
    subprocess.run(['git','merge-base','--is-ancestor',static['revision'],current_revision],cwd=SOURCE,check=True)
    if changed_paths is None:
        changed_paths=subprocess.check_output(['git','diff','--name-only',static['revision'],current_revision],cwd=SOURCE,text=True).splitlines()
        dirty=subprocess.check_output(['git','status','--porcelain','--','workbench','scripts',str(BASE/'run-09b.py')],cwd=SOURCE,text=True).strip()
        assert not dirty,'runner/product worktree changed after material source; no spawn'
        assert not subprocess.check_output(['git','diff',static['revision'],'--',*static['source_paths']],cwd=SOURCE),'frozen source closure changed; no spawn'
    ticket_prefix=str(BASE.relative_to(SOURCE))+'/';blocked=[p for p in changed_paths if p in static['source_paths'] or p.startswith('workbench/') or p.startswith('scripts/') or p in [str(BASE.relative_to(SOURCE)/'run-09b.py'),str(BASE.relative_to(SOURCE)/'prepare-09b-executable.py')]]
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
    out=a.output.resolve();out.mkdir(parents=False,exist_ok=False);record={'status':'INCOMPLETE','stage':a.stage,'spawned':False,'real_vendor_model_turns':0,'commands':[],'scope':'Stage-gated 09B/09C; no role CLI in A; role launch uses the separate Stage B runner'}
    def save(): (out/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        approval=json.loads(a.approval.read_bytes());static=validate_stage_a_inputs(a.materials,approval,protocol=a.protocol)
        record['regression_validation']=static['regression_validation'];save()
        if a.stage!='A': raise RuntimeError('Stage B/C require a separate approved continuation; no spawn from this runner.')
        scene=static['scene']; prefix='09b' if scene=='09B' else '09c'
        task='t078-'+prefix+'-runtime-'+uuid.uuid4().hex[:8]
        card={'id':task,'source':None,'goal':scene+' deterministic target stage A','non_goals':['real model','candidate submission'],'paths':{'allow':['value.txt'],'deny':[]},'oracle_paths':['oracle/contract-09b.json'],'completion_conditions':[{'argv':[sys.executable,'-I','-B','-c','raise SystemExit(\'no candidate\')']}],'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        preflight_file=out/'card-preflight.json';preflight_file.write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        validate_card_preflight(preflight_file);record['card_preflight']='taskCards.validateTaskCard via real Node gate module; no root/API/daemon/target';save()
        root=Path(tempfile.mkdtemp(prefix='t078-2-'+prefix+'-run-',dir='/private/tmp')).resolve();record['root']=str(root);record['scene']=scene
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
        sys.path.insert(0,str(SOURCE/'workbench/tests'))
        from p1_reuse import process_command
        original_processes={}
        for label,pid in [('daemon',daemon['pid']),('target_shell',info['shell_pid']),('target_leader',info['leader'])]+[(item['role']+'_api',item['pid']) for item in api_pids]:
            first=process_command(pid);assert first is not None and process_command(pid)==first,'stage_a_process_identity_changed'
            original_processes[label]=first
        for item in api_pids:item['lstart']=original_processes[item['role']+'_api']['started']
        record['original_processes']=original_processes
        record['runtime_binding']={'task':task,'attempt':attempt,'process':info,'api':api_pids,'daemon':daemon,'target_claim':'runtime dispatch receipt'}
        (out/'readiness.json').write_text(json.dumps({'status':'READY_FOR_APPROVAL','stage':'A','source_revision':static['revision'],'root':str(root),'task':task,'scene':scene,'materials':str(a.materials.resolve()),'roles_started':[],'target_binding':attempt,'target_process':info,'original_processes':original_processes,'api_processes':api_pids,'daemon':daemon,'cleanup_plan':'Authenticated daemon_stop; verify target/API argv+PID/lstart; stop owned APIs once; archive and delete root only after byte readback; slots separate'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');record['status']='READY_FOR_APPROVAL';record['next']='Stop here; main approval required before stage B role launches';save()
    except Exception as error:
        record.update(error=repr(error),traceback=__import__('traceback').format_exc());save();return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
