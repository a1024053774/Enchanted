"""Controller-only P1 lifecycle. Launch pauses for explicit initial-readiness approval."""
import argparse,base64,json,os,signal,sqlite3,subprocess,sys,time,tarfile,shutil,traceback
from pathlib import Path
from command_evidence import CommandLog,command_json
from p1_endpoint import resolved_input
from p1_processes import identity_from_ps,cli_exit_verdict
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
parser=argparse.ArgumentParser();parser.add_argument('--materials',type=Path,required=True);parser.add_argument('--phase',choices=['launch','continue','cleanup'],required=True)
parser.add_argument('--label');parser.add_argument('--source-materials',type=Path);parser.add_argument('--readiness-file',type=Path)
args=parser.parse_args();materials=args.materials.resolve();approval=json.loads((materials/'approval.json').read_text());root=Path(approval['input']['root']);state=root/'state'
label=args.label or args.phase
if Path(label).name!=label or label in ['.','..']:parser.error('A single new output-directory name is required')
source_materials=args.source_materials.resolve() if args.source_materials else materials
out=materials/label;out.mkdir();log=CommandLog(out)
node=approval['launch']['node_executable']
env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(root/'manager-home'),'TMPDIR':str(root/'tmp'),'A2A_OPERATOR_CREDENTIAL':str(root/'operator.json'),
     'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':os.devnull,'GIT_CONFIG_KEY_1':'commit.gpgsign','GIT_CONFIG_VALUE_1':'false',
     'GIT_AUTHOR_NAME':'T078 P1 fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'T078 P1 fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
cli=[node,SOURCE/'workbench/src/gates/cli.ts','--state',state]
result={'status':'INCOMPLETE','phase':args.phase,'label':label,'source_materials':str(source_materials),
        'real_vendor_model_turns':0,'authentication':'isolated fake API','input':approval['input']}
def save(): (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
def run(argv,child_env=env,allowed=(0,)):
    p=log.run(argv,cwd=SOURCE,env=child_env,timeout=15)
    if p.returncode not in allowed:raise RuntimeError({'unexpected_exit':p.evidence})
    return p
def call(command,*argv):
    p=run([*cli,command,*argv]);v=command_json(p)
    if p.returncode or not v.get('ok'):raise RuntimeError({'gate_refused':v,'command':command})
    return v
def wait(predicate,seconds=30):
    deadline=time.monotonic()+seconds
    while not predicate():
        if (root/'api-error.json').exists():raise RuntimeError('Fake API protocol/budget error; retain original')
        if time.monotonic()>deadline:raise RuntimeError('Observed-state deadline; no retry')
        time.sleep(.05)
def events():
    with sqlite3.connect((state/'state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:return [{'type':r[0],'data':json.loads(r[1])} for r in db.execute('SELECT type,data FROM orchestration_events ORDER BY seq')]
def probe_process(pid):
    p=run(['/bin/ps','-p',str(pid),'-o','pid=,lstart=,comm='],allowed=(0,1))
    return identity_from_ps(pid,p.returncode,p.stdout,p.stderr)
try:
    if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External volume missing')
    for name in ['input.json','role.md','nonce.txt']:
        if (root/name).read_bytes()!=(materials/name).read_bytes():raise RuntimeError('Approved input changed: '+name)
    frozen=json.loads((source_materials/'source-files.json').read_text())
    with tarfile.open(source_materials/'sources.tar.gz') as archive:
        for name in frozen:
            if (SOURCE/name).read_bytes()!=archive.extractfile(name).read():raise RuntimeError('Approved source changed: '+name)
    if args.phase=='launch':
        isolated_settings=(root/'claude/settings.json').read_bytes()
        if isolated_settings!=(materials/'isolated-settings.json').read_bytes() or json.loads(isolated_settings)!={'theme':'dark'}:
            raise RuntimeError('approved_isolated_settings_changed')
        with (root/'api.stdout').open('xb') as stdout,(root/'api.stderr').open('xb') as stderr:
            api=subprocess.Popen(['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_messages.py'),str(root)],env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        (root/'api-owner.json').write_text(json.dumps({'pid':api.pid,'argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_messages.py'),str(root)]}))
        wait(lambda:(root/'api-ready.json').exists() or api.poll() is not None)
        if api.poll() is not None:raise RuntimeError('Local API exited before readiness; retain logs, no restart')
        bound=resolved_input(approval['input'],json.loads((root/'api-ready.json').read_text()),api.pid)
        with (root/'runtime-input.json').open('x',encoding='utf-8') as f:json.dump(bound,f,ensure_ascii=False,indent=2)
        run([node,SOURCE/'workbench/tests/prepare_t078_p1.ts',root/'runtime-input.json',out/'runtime-manifest.json'])
        runtime=json.loads((out/'runtime-manifest.json').read_text())
        if runtime['launch']['argv']!=approval['launch']['argv'] or runtime['launch']['settings']!=approval['launch']['settings']:
            raise RuntimeError('approved_cli_argv_changed')
        expected={**approval['launch']['env'],'ANTHROPIC_BASE_URL':bound['api_url']}
        if runtime['launch']['env']!=expected:raise RuntimeError('approved_cli_environment_changed')
        result['runtime_manifest']=str(out/'runtime-manifest.json');result['api_url']=bound['api_url'];save()
        for argv in runtime['preflight_argv']:
            p=run(argv,runtime['launch']['env'])
            if p.returncode or (argv[-1]=='--version' and p.stdout.strip()!=runtime['launch']['cli_version_expected']):raise RuntimeError('Fixed CLI preflight mismatch')
            if argv[-1]=='--help' and any(flag not in p.stdout for flag in ['--session-id','--model','--effort','--settings','--append-system-prompt','--permission-mode','--strict-mcp-config','--tools']):raise RuntimeError('Required CLI options missing')
        run(['git','-C',root/'repo','init','-b','main'])
        (root/'repo/value.txt').write_text('P1 isolated fixture\n');run(['git','-C',root/'repo','add','value.txt']);run(['git','-C',root/'repo','commit','-m','P1 fixture'])
        call('daemon_start')
        card={'id':approval['input']['task'],'source':None,'goal':'Claude CLI protocol tracer bullet','non_goals':['worker delivery or integration'],
              'paths':{'allow':['.'],'deny':[]},'completion_conditions':[{'argv':[sys.executable,'-c',"raise SystemExit('P1 does not deliver a worker candidate')"]}],
              'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        (root/'card.json').write_text(json.dumps(card));task=approval['input']['task']
        call('card_save','--task',task,'--card',root/'card.json','--expected-version','0')
        call('create','--task',task,'--repo',root/'repo','--branch','refs/heads/main','--card-version','1','--project','t078-p1-project')
        result['started']=call('controller_start','--task',task,'--manifest',root/'runtime-input.json')
        owner_info=None
        def capture_owner():
            global owner_info
            owner_info=call('pane_process_info','--thread',approval['input']['thread'])
            if owner_info.get('failed'):raise RuntimeError('controller_process_identity_failed')
            return owner_info.get('leader') is not None
        wait(capture_owner,15)
        identity=probe_process(owner_info['leader'])
        if not identity:raise RuntimeError('controller_exited_before_identity_capture')
        with (out/'process-manifest.json').open('x',encoding='utf-8') as f:
            json.dump({'launch':approval['input']['launch'],'session':approval['input']['session'],
                       'shell_pid':owner_info['shell_pid'],'cli':identity},f,ensure_ascii=False,indent=2)
        result['process_manifest']=str(out/'process-manifest.json');save()
        result['next']='No input has been sent. Inspect and preserve the raw terminal output. Stop at any API-key approval or directory-trust prompt; do not press keys or select defaults. Continue and cleanup require separate approval.'
        result['pty_output']=call('pane_output','--launch',approval['input']['launch'],'--offset','0')
    elif args.phase=='continue':
        owner=json.loads((root/'api-owner.json').read_text())
        bound=resolved_input(approval['input'],json.loads((root/'api-ready.json').read_text()),owner['pid'])
        if json.loads((root/'runtime-input.json').read_text())!=bound:raise RuntimeError('resolved_api_manifest_changed')
        runtime=json.loads((materials/'launch/runtime-manifest.json').read_text())
        if runtime['input']!=bound:raise RuntimeError('runtime_launch_manifest_changed')
        if not args.readiness_file:raise RuntimeError('Explicit startup-readiness file required')
        ready=json.loads(args.readiness_file.read_text(encoding='utf-8'))
        if ready.get('launch')!=approval['input']['launch'] or ready.get('session')!=approval['input']['session'] or ready.get('confirmed_by')!='executor' or ready.get('readiness')!='confirmed' or not ready.get('basis'):
            raise RuntimeError('Explicit startup-readiness approval required; never use task input as a trust answer')
        result['readiness_file']=str(args.readiness_file.resolve());result['readiness_confirmation']=ready;save()
        process_manifest=json.loads((materials/'launch/process-manifest.json').read_text(encoding='utf-8'))
        if any(process_manifest.get(key)!=approval['input'][key] for key in ['launch','session']) or probe_process(process_manifest['cli']['pid'])!=process_manifest['cli']:
            raise RuntimeError('continuation_cli_identity_changed')
        result['process_confirmation']=process_manifest;save()
        thread=approval['input']['thread'];call('pane_release','--thread',thread,'--reason','P1 explicit initial readiness approved by executor')
        result['dispatch']=call('pane_dispatch','--thread',thread,'--body-file',root/'nonce.txt')
        wait(lambda:(root/'api-request.json').exists())
        result['before_completion']=call('pane_status','--thread',thread)
        if result['before_completion']['state']!='busy' or not any(e['type']=='turn_start_signal' for e in events()):raise RuntimeError('CR/hook did not establish the registered active submission')
        (root/'api-release').write_text('release the one scripted response')
        wait(lambda:call('pane_status','--thread',thread)['state']=='idle')
        result['events']=events();result['after_completion']=call('pane_status','--thread',thread)
        wait(lambda:('P1_ACK '+(root/'nonce.txt').read_text()).encode('utf-8') in base64.b64decode(call('pane_output','--launch',approval['input']['launch'],'--offset','0')['data_base64']))
        if sum(e['type']=='pane_idle' for e in result['events'])!=1:raise RuntimeError('Unexpected completion count')
        result['status']='PASS';result['scope']='One real Claude CLI using scripted SSE; no real model or multi-turn claim.'
    else:
        attempted=False
        if (state/'state.sqlite3').exists():
            with sqlite3.connect((state/'state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                if db.execute("SELECT 1 FROM sqlite_master WHERE name='launch_records'").fetchone():
                    attempted=db.execute('SELECT 1 FROM launch_records WHERE id=?',(approval['input']['launch'],)).fetchone() is not None
        process_file=materials/'launch/process-manifest.json'
        manifest=json.loads(process_file.read_text()) if process_file.exists() else None
        attempted=attempted or manifest is not None
        if manifest and any(manifest.get(key)!=approval['input'][key] for key in ['launch','session']):
            raise RuntimeError('cleanup_process_manifest_identity_mismatch')
        if (state/'daemon.pid').exists():call('daemon_stop');wait(lambda:not (state/'daemon.pid').exists(),15)
        deadline=time.monotonic()+15
        while True:
            observed={manifest['cli']['pid']:probe_process(manifest['cli']['pid'])} if manifest and manifest.get('cli') else {}
            verdict=cli_exit_verdict(attempted,manifest,observed)
            result['cli_exit_verdict']=verdict;save()
            if verdict['status']=='PASS':break
            if verdict['reason']!='recorded_cli_still_alive' or time.monotonic()>=deadline:
                result['status']='BLOCKED';raise RuntimeError(verdict['reason'])
            time.sleep(.05)
        if (root/'api-owner.json').exists():
            owner=json.loads((root/'api-owner.json').read_text());p=run(['/bin/ps','-p',str(owner['pid']),'-o','command='],allowed=(0,1))
            if p.returncode==0:
                if str(SOURCE/'workbench/tests/t078_fake_messages.py') not in p.stdout or str(root) not in p.stdout:raise RuntimeError('API identity changed; no signal sent')
                os.kill(owner['pid'],signal.SIGTERM)
                wait(lambda:run(['/bin/ps','-p',str(owner['pid']),'-o','command='],allowed=(0,1)).returncode==1,10)
        if (root/'operator.json').exists():(root/'operator.json').unlink()
        with tarfile.open(out/'fixture.tar.gz','x:gz') as archive:archive.add(root,arcname=root.name)
        if (root/'api-error.json').exists():
            result['error']='API reported a protocol/budget failure; original root retained after stopping owned processes.'
        else:
            shutil.rmtree(root);result['status']='PASS';result['cleanup']='Only this recorded fixture and owned processes removed.'
except Exception as error:
    result['error']=repr(error)
    result['error_filename']=getattr(error,'filename',None)
    result['traceback']=traceback.format_exc()
    if args.phase=='cleanup':result['status']='BLOCKED'
finally:save()
print(json.dumps({'status':result['status'],'phase':args.phase,'output':str(out),'error':result.get('error')}))
raise SystemExit(0 if not result.get('error') else 1)
