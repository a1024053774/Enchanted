"""Controller-only P1 lifecycle. Launch pauses for explicit initial-readiness approval."""
import argparse,base64,json,os,signal,sqlite3,subprocess,sys,time,tarfile,shutil,traceback
from pathlib import Path
from command_evidence import CommandLog,command_json
from p1_endpoint import resolved_input
from p1_processes import identity_from_ps,cli_exit_verdict
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
parser=argparse.ArgumentParser();parser.add_argument('--materials',type=Path,required=True);parser.add_argument('--phase',choices=['launch','screen','key','continue','continue-esc','cleanup'],required=True)
parser.add_argument('--label');parser.add_argument('--source-materials',type=Path);parser.add_argument('--readiness-file',type=Path)
parser.add_argument('--actions-approval',type=Path)
parser.add_argument('--key',choices=['ArrowUp','ArrowDown','Enter']);parser.add_argument('--purpose',choices=['onboarding-theme','onboarding-notice','workspace-trust']);parser.add_argument('--screen-id');parser.add_argument('--approval-file',type=Path);parser.add_argument('--screen-file',type=Path)
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
scenario_name=json.loads((root/'scenario.json').read_bytes())['name']
api_script=SOURCE/'workbench/tests'/('t078_fake_inbox_tool.py' if scenario_name in ['slice1-inbox-red','slice1-inbox-green'] else 't078_fake_messages.py')
def save(): (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
def run(argv,child_env=env,allowed=(0,),timeout=15):
    p=log.run(argv,cwd=SOURCE,env=child_env,timeout=timeout)
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
    with sqlite3.connect((state/'state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:return [{'seq':r[0],'time':r[1],'launch':r[2],'type':r[3],'data':json.loads(r[4])} for r in db.execute('SELECT seq,time,launch,type,data FROM orchestration_events ORDER BY seq')]
def user_inputs():
    with sqlite3.connect((state/'state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:return [json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs')]
def probe_process(pid):
    p=run(['/bin/ps','-p',str(pid),'-o','pid=,lstart=,comm='],child_env={**env,'LC_ALL':'C','LANG':'C'},allowed=(0,1))
    return identity_from_ps(pid,p.returncode,p.stdout,p.stderr)
def same_cli():
    manifest=json.loads((materials/'launch/process-manifest.json').read_text(encoding='utf-8'))
    if any(manifest.get(k)!=approval['input'][k] for k in ['launch','session']) or probe_process(manifest['cli']['pid'])!=manifest['cli']:
        raise RuntimeError('continuation_cli_identity_changed')
    return manifest
def snapshot():
    value=call('pane_output','--launch',approval['input']['launch'],'--offset','0')
    if value['next_offset']!=value['total_bytes']:raise RuntimeError('screen_exceeds_review_limit')
    raw=base64.b64decode(value['data_base64'])
    with (out/'screen.bin').open('xb') as f:f.write(raw)
    with (out/'screen.json').open('x',encoding='utf-8') as f:
        json.dump({'observed_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                   'directory':str(root/'repo'),'screen_id':args.screen_id,'launch':approval['input']['launch'],'session':approval['input']['session'],'output':value},f,ensure_ascii=False,indent=2)
    return value
def raw_hook_receipts():
    records=[]
    for directory in sorted((root/'hooks').iterdir()):
        if (directory/'finished.json').exists():
            done=json.loads((directory/'finished.json').read_text(encoding='utf-8'))
            payload=json.loads((directory/'stdin.bin').read_bytes())
            records.append({'event':payload.get('hook_event_name'),'exit_code':done['exit_code'],'launch':done['launch'],'directory':str(directory)})
    return records
def verify_readiness():
    owner=json.loads((root/'api-owner.json').read_text())
    bound=resolved_input(approval['input'],json.loads((root/'api-ready.json').read_text()),owner['pid'])
    if json.loads((root/'runtime-input.json').read_text())!=bound:raise RuntimeError('resolved_api_manifest_changed')
    if json.loads((materials/'launch/runtime-manifest.json').read_text())['input']!=bound:raise RuntimeError('runtime_launch_manifest_changed')
    if not args.readiness_file:raise RuntimeError('Explicit startup-readiness file required')
    ready=json.loads(args.readiness_file.read_text(encoding='utf-8'))
    if ready.get('launch')!=approval['input']['launch'] or ready.get('session')!=approval['input']['session'] or ready.get('confirmed_by')!='executor' or ready.get('readiness')!='confirmed' or not ready.get('basis'):raise RuntimeError('Explicit startup-readiness approval required')
    result['readiness_file']=str(args.readiness_file.resolve());result['readiness_confirmation']=ready
    result['process_confirmation']=same_cli();save()
    return approval['input']['thread']
try:
    if api_script.name=='t078_fake_inbox_tool.py' and args.phase not in ['launch','screen','key']:
        raise RuntimeError('Slice1 submit/permission/readback uses its approved driver; cleanup needs a separate identity-bound script.')
    if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External volume missing')
    for name in ['input.json','role.md','nonce.txt','scenario.json',*(['nonce-2.txt'] if scenario_name=='esc-two' else [])]:
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
            api=subprocess.Popen(['/usr/bin/python3','-B',str(api_script),str(root)],env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        (root/'api-owner.json').write_text(json.dumps({'pid':api.pid,'argv':['/usr/bin/python3','-B',str(api_script),str(root)]}))
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
            if argv[-1]=='--help' and any(flag not in p.stdout for flag in ['--session-id','--model','--effort','--settings','--append-system-prompt','--permission-mode','--strict-mcp-config','--tools','--debug-file']):raise RuntimeError('Required CLI options missing')
        if sorted(p.name for p in (root/'repo').iterdir())!=['value.txt'] or (root/'repo/value.txt').read_text(encoding='utf-8')!='P1 isolated fixture\n':raise RuntimeError('fixture_repo_changed')
        run(['git','-C',root/'repo','init','-b','main'])
        run(['git','-C',root/'repo','add','value.txt']);run(['git','-C',root/'repo','commit','-m','P1 fixture'])
        call('daemon_start')
        card={'id':approval['input']['task'],'source':None,'goal':'Claude CLI protocol tracer bullet','non_goals':['worker delivery or integration'],
              'paths':{'allow':['.'],'deny':[]},'oracle_paths':['value.txt'],'completion_conditions':[{'argv':[sys.executable,'-c',"raise SystemExit('P1 does not deliver a worker candidate')"]}],
              'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
        (root/'card.json').write_text(json.dumps(card));task=approval['input']['task']
        call('card_save','--task',task,'--card',root/'card.json','--expected-version','0')
        call('create','--task',task,'--repo',root/'repo','--branch','refs/heads/main','--card-version','1','--project','t078-p1-project')
        scenario=json.loads((root/'scenario.json').read_bytes())
        if scenario['name']=='slice1-inbox-green':
            with sqlite3.connect(state/'state.sqlite3') as db:
                for entry in scenario['inbox_fixture']:db.execute('INSERT INTO inbox_records(id,data) VALUES (?,?)',(entry['id'],json.dumps(entry,ensure_ascii=False)))
                db.commit()
            result['seeded_inbox_inputs']={'origin':scenario['inbox_fixture_origin'],'entries':scenario['inbox_fixture']};save()
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
        result['scope']='Process startup only; no first-screen capture or readiness claim.'
        result['terminal_trace']=str(state/'traces'/approval['input']['launch']/'pty.raw')
        result['next']='No input has been sent. Run a separately approved screen phase after the CLI displays its screen; inspect and preserve those raw bytes before approving any key. Key, continue and cleanup phases require separate approval.'
    elif args.phase=='screen':
        result['process_confirmation']=same_cli();result['pty_output']=snapshot()
        result['scope']='Read-only screen; no readiness or trust inferred.'
    elif args.phase=='key':
        if not args.key or not args.purpose or not args.screen_id or not args.approval_file or not args.screen_file:raise RuntimeError('explicit_screen_key_materials_required')
        permitted=json.loads(args.approval_file.read_text(encoding='utf-8'))
        if any(permitted.get(k)!=approval['input'][k] for k in ['launch','session']) or permitted.get('directory')!=str(root/'repo') or permitted.get('key')!=args.key or permitted.get('purpose')!=args.purpose or permitted.get('screen_id')!=args.screen_id or not permitted.get('selected_label') or permitted.get('approved_by')!='executor' or not permitted.get('approval_ref') or not permitted.get('basis') or permitted.get('screen_file')!=str(args.screen_file.resolve()):
            raise RuntimeError('screen_approval_binding_mismatch')
        with (out/'reviewed-screen.bin').open('xb') as f:f.write(args.screen_file.read_bytes())
        result['approval']=permitted;result['process_confirmation']=same_cli();save()
        result['key_result']=call('pane_screen_key','--thread',approval['input']['thread'],'--key',args.key,'--purpose',args.purpose,'--screen-id',args.screen_id,'--screen-file',args.screen_file,'--selected-label',permitted['selected_label'],'--authorization-ref',permitted['approval_ref'])
        result['pty_output']=snapshot();result['events']=events()
        result['scope']='One explicitly approved screen key sent by authenticated executor; inspect again. No automatic Enter or continue.'
        # Screen transitions and trust completion are human observations.
    elif args.phase=='continue':
        if approval['input']['turn_limit']!=1:raise RuntimeError('Two-turn scenario requires the explicit esc/release driver, not single-round continue')
        thread=verify_readiness();call('pane_release','--thread',thread,'--reason','P1 explicit initial readiness approved by executor')
        result['dispatch']=call('pane_dispatch','--thread',thread,'--body-file',root/'nonce.txt')
        wait(lambda:(root/'api-request-1.json').exists())
        result['before_completion']=call('pane_status','--thread',thread)
        if result['before_completion']['state']!='busy' or not any(e['type']=='turn_start_signal' for e in events()):raise RuntimeError('CR/hook did not establish the registered active submission')
        (root/'api-release-1').write_text('release the one scripted response')
        wait(lambda:call('pane_status','--thread',thread)['state']=='idle')
        result['events']=events();result['after_completion']=call('pane_status','--thread',thread)
        wait(lambda:('P1_ACK '+(root/'nonce.txt').read_text()).encode('utf-8') in base64.b64decode(call('pane_output','--launch',approval['input']['launch'],'--offset','0')['data_base64']))
        if sum(e['type']=='pane_idle' for e in result['events'])!=1:raise RuntimeError('Unexpected completion count')
        wait(lambda:all(any(h['event']==event and h['exit_code']==0 and h['launch']==approval['input']['launch'] for h in raw_hook_receipts()) for event in ['UserPromptSubmit','Stop']))
        result['hook_receipts']=raw_hook_receipts()
        result['status']='PASS';result['scope']='One real Claude CLI using scripted SSE; no real model or multi-turn claim.'
    elif args.phase=='continue-esc':
        if approval['input']['turn_limit']!=2 or not args.actions_approval:raise RuntimeError('Explicit two-turn actions approval required')
        handling=json.loads((root/'scenario.json').read_text(encoding='utf-8')).get('draft_handling')
        from p1_simulated_actions import validate_actions
        consent=json.loads(args.actions_approval.read_text(encoding='utf-8'))
        validate_actions(approval,consent,handling)
        result['actions_approval']=consent;thread=verify_readiness()
        from electron_client import ElectronClient
        slot='t078-09-'+approval['input']['launch']
        built=run([node,SOURCE/'workbench/app/build.mjs','--slot',slot],timeout=90);build=Path(command_json(built)['out'])
        result['electron_build']=str(build);save()
        client=ElectronClient(SOURCE,build,state,approval['input']['task'],root/'electron-home',out/'electron',env,launch=approval['input']['launch'])
        try:
            client.call('inspect')
            call('pane_release','--thread',thread,'--reason','09A explicit initial readiness approved by executor')
            first=call('pane_dispatch','--thread',thread,'--body-file',root/'nonce.txt');result['first_dispatch']=first;save()
            wait(lambda:(root/'api-request-1.json').exists() and any(e['type']=='turn_start_signal' for e in events()))
            before=call('pane_status','--thread',thread);assert before['state']=='busy' and before['active']['dispatch']==first['dispatch']['id']
            prompt1=next(e['data']['prompt_id'] for e in events() if e['type']=='turn_start_signal');result['before_esc']=before;result['prompt1']=prompt1
            second=call('pane_dispatch','--thread',thread,'--body-file',root/'nonce-2.txt');result['second_dispatch']=second
            queued=call('pane_status','--thread',thread);assert queued['queued']==[second['dispatch']['id']] and not (root/'api-request-2.json').exists()
            assert not any(e['type']=='paste_intent' and e['data']['dispatch']==second['dispatch']['id'] for e in events());save()
            binding = {'launch':approval['input']['launch'], 'thread':thread, 'dispatch':first['dispatch']['id']}
            view = client.wait(lambda v:v.get('launch')==binding['launch'] and v.get('thread')==binding['thread'] and
                               v.get('active_dispatch')==binding['dispatch'] and v.get('state')=='busy' and
                               v.get('lifecycle')=='running' and v.get('input_enabled') is True)
            result['window_before_esc']=view
            prior=events();after_seq=max(e['seq'] for e in prior)
            window_id=next(e['data']['window_id'] for e in reversed(prior) if e['type']=='window_opened' and e['launch']==binding['launch'])
            result['key_attempt']=client.call('terminal-key',key='Escape',**binding,source='test-simulated-user',approval_ref=consent['actions'][0]['approval_ref']);save()
            from p1_window_receipts import confirmed_escape
            def receipt():return confirmed_escape(events(),user_inputs(),**binding,window=window_id,after_seq=after_seq)
            wait(lambda:receipt() is not None)
            result['escape_delivery']=receipt();save()
            wait(lambda:call('pane_status','--thread',thread)['active'] is None)
            wait(lambda:(root/'api-cancelled-1.json').exists())
            held=call('pane_status','--thread',thread);assert held['state']=='busy' and held['interrupted'] and held['queued']==[second['dispatch']['id']]
            assert not (root/'api-request-2.json').exists() and not any(e['type']=='turn_end_signal' for e in events())
            result['after_esc']=held;result['cancelled_request']=json.loads((root/'api-cancelled-1.json').read_bytes());save()
            client.call('capture',name='before-user-release')
            from p1_simulated_actions import prompt_frame,bound_held
            from p1_window_receipts import confirmed_control
            result['draft_handling']=handling
            result['automation']={'source':'test-simulated-user','approved_by':'executor','approval_ref':consent['approval_ref'],'actions':consent['actions']}
            nonce1=(root/'nonce.txt').read_text(encoding='utf-8')
            view=client.wait(lambda v:bound_held(v,binding) and nonce1 in prompt_frame(v)['text'])
            restored=client.call('capture',name='restored-draft')
            assert bound_held(restored,binding) and restored['window_id']==window_id and nonce1 in prompt_frame(restored)['text']
            result['restored_draft']=restored
            draft_status=call('pane_status','--thread',thread)
            assert draft_status['interruption']==held['interruption'] and draft_status['input_generation']==held['input_generation'] and draft_status['active'] is None
            if handling=='simulated-empty-declaration':
                before_output=call('pane_output','--launch',binding['launch'],'--offset','0')
                before_clear=max((e['seq'] for e in events()),default=after_seq)
                result['clear_attempt']=client.call('terminal-key',key='Control+C',**binding,window_id=window_id,interruption=held['interruption'],approval_ref=consent['actions'][1]['approval_ref'])
                def clear_receipt():return confirmed_control(events(),user_inputs(),launch=binding['launch'],thread=thread,window=window_id,after_seq=before_clear,data='\x03')
                wait(lambda:clear_receipt() is not None)
                result['clear_delivery']=clear_receipt();save()
                after_clear=call('pane_status','--thread',thread)
                assert after_clear['active'] is None and after_clear['interruption']==held['interruption'] and after_clear['input_generation']==held['input_generation']+1
                empty=client.wait(lambda v:bound_held(v,binding) and v.get('interruption')==held['interruption'] and
                                  v.get('input_generation')==after_clear['input_generation'] and v['offset']>before_output['total_bytes'] and prompt_frame(v)['empty'])
                with client.output_checkpoint(empty['offset']) as checkpoint:
                    captured=client.call('capture',name='cleared-draft')
                    assert bound_held(captured,binding) and captured['window_id']==window_id and captured['interruption']==held['interruption']
                    assert captured['input_generation']==after_clear['input_generation'] and captured['offset']==checkpoint['highwater'] and prompt_frame(captured)['empty']
                    raw=call('pane_output','--launch',binding['launch'],'--offset','0')
                    data=base64.b64decode(raw['data_base64']);assert len(data)>=checkpoint['highwater']
                    with (out/'cleared-draft-pty.bin').open('xb') as stream:stream.write(data[:checkpoint['highwater']])
                    result['empty_editor_observation']={'frame':prompt_frame(captured),'snapshot':captured,'pty_highwater':checkpoint['highwater'],'pty_file':'cleared-draft-pty.bin'}
            else:
                assert handling=='retain-draft-for-block'
                after_clear=draft_status
            fresh=call('pane_status','--thread',thread)
            assert fresh['interruption']==held['interruption'] and fresh['input_generation']==after_clear['input_generation'] and fresh['active'] is None
            result['declaration_click']=client.call('queue-release',source='test-simulated-user',approval_ref=consent['actions'][2]['approval_ref'],launch=binding['launch'],interruption=held['interruption'],input_generation=fresh['input_generation'])
            assert result['declaration_click']['clicked'] is True and result['declaration_click']['source']=='test-simulated-user';save()
            wait(lambda:any(e['type']=='user_queue_release' and e['launch']==binding['launch'] for e in events()))
            release_event=next(e for e in events() if e['type']=='user_queue_release' and e['launch']==binding['launch'])
            declarations=[r for r in user_inputs() if r.get('content',{}).get('action')=='queue-release']
            assert len(declarations)==1 and declarations[0]['text']=='用户声明输入框已空'
            assert declarations[0]['content']['declaration']==release_event['data']['declaration']
            assert release_event['data']['declaration']['interruption']==held['interruption']
            assert release_event['data']['declaration']['input_generation']==fresh['input_generation']
            result['user_release']=release_event;result['declaration']=declarations[0];save()
            client.call('capture',name='after-declaration')
            if handling=='retain-draft-for-block':
                wait(lambda:len([e for e in events() if e['type']=='injected_prompt_blocked'])==1 and len(raw_hook_receipts())==2)
                blocked=next(e for e in events() if e['type']=='injected_prompt_blocked')
                assert (root/'nonce.txt').read_text() in blocked['data']['prompt'] and (root/'nonce-2.txt').read_text() in blocked['data']['prompt']
                assert blocked['data']['dispatch']==second['dispatch']['id']
                ups2=[h for h in raw_hook_receipts() if h['event']=='UserPromptSubmit'][-1]
                output=json.loads((Path(ups2['directory'])/'stdout.bin').read_bytes())
                assert ups2['exit_code']==0 and output['decision']=='block'
                # Bounded observation after the actual blocking hook completed.
                for _ in range(40):
                    assert not (root/'api-request-2.json').exists() and not (root/'api-error.json').exists();time.sleep(.05)
                final=events()
                assert len([e for e in final if e['type']=='turn_start_signal'])==1
                assert not any(e['type']=='turn_end_signal' for e in final)
                assert len([e for e in final if e['type']=='turn_submitted'])==2
                assert not [r for r in user_inputs() if r.get('source_ref',{}).get('source_sequence',0)>declarations[0]['source_ref']['source_sequence']]
                result.update(status='PASS',events=final,blocked=blocked,hook_receipts=raw_hook_receipts(),after_block=call('pane_status','--thread',thread),
                              scope='09A-3 retained concatenation: real hook JSON block, one fake API request, two-second no-request observation; not general reliability')
                client.call('capture',name='blocked-concatenation');result['pty_output']=snapshot()
                save()
            else:
                manual=[r for r in user_inputs() if r['source_ref'].get('window_id')==window_id and
                        result['escape_delivery']['action']['source_ref']['source_sequence']<r['source_ref'].get('source_sequence',0)<declarations[0]['source_ref']['source_sequence']]
                assert manual,'No separately recorded draft handling before the empty declaration'
                assert result['clear_delivery']['action'] in manual
                result['simulated_draft_inputs']=manual;save()
                wait(lambda:(root/'api-request-2.json').exists() and len([e for e in events() if e['type']=='turn_start_signal'])==2)
                prompt2=[e['data']['prompt_id'] for e in events() if e['type']=='turn_start_signal'][-1];assert prompt2 and prompt2!=prompt1
                active2=call('pane_status','--thread',thread);assert active2['state']=='busy' and active2['active']['dispatch']==second['dispatch']['id']
                result['before_second_completion']=active2;result['prompt2']=prompt2;save()
                (root/'api-release-2').write_text('release second approved scripted response')
                wait(lambda:call('pane_status','--thread',thread)['state']=='idle')
                wait(lambda:len(raw_hook_receipts())==3 and all(h['exit_code']==0 for h in raw_hook_receipts()))
                final=events();assert len([e for e in final if e['type']=='pane_idle'])==1
                assert [e['data']['prompt_id'] for e in final if e['type']=='turn_end_signal']==[prompt2]
                assert len([e for e in final if e['type']=='user_queue_release'])==1
                assert len([e for e in final if e['type']=='turn_submitted' and e['data']['dispatch']==second['dispatch']['id']])==1
                result['events']=final;result['hook_receipts']=raw_hook_receipts();result['after_completion']=call('pane_status','--thread',thread)
                client.call('capture',name='second-completion');result['pty_output']=snapshot()
                assert ('P2_ACK '+(root/'nonce-2.txt').read_text()).encode() in base64.b64decode(result['pty_output']['data_base64'])
                result['status']='PASS';result['scope']='09A-3 executor-approved test-simulated-user clear/declaration, real CLI with two exact fake API requests; not a real-user or dual-controller claim'
        finally:client.close()
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
                if str(api_script) not in p.stdout or str(root) not in p.stdout:raise RuntimeError('API identity changed; no signal sent')
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
