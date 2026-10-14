"""Prepare a fresh P1 instance and source snapshot without starting services."""
import argparse,json,shlex,shutil,subprocess,tarfile,tempfile,uuid
from pathlib import Path

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--extra-source',type=Path,nargs='*',default=[])
args=parser.parse_args()
if not args.label.startswith('p1-materials-'):parser.error('A new p1-materials-NN label is required')
suffix=args.label[len('p1-materials-'):]
if not (suffix in ['slice1-red','09a2','09a3','09a3-block','09a3r','09a3r-block','09a3r2','09a3r2-block'] or suffix.isdigit() or (suffix[-1:] in ['b','c','d','e'] and suffix[:-1].isdigit())):parser.error('A supported fresh material label is required')
tool_slice=suffix=='slice1-red'
two_turn=suffix in ['09','09a2','09a3','09a3-block','09a3r','09a3r-block','09a3r2','09a3r2-block']
out=BASE/args.label;out.mkdir()
root=Path(tempfile.mkdtemp(prefix='t078-2-p1-'+suffix+'-',dir='/tmp')).resolve()
record={'status':'INCOMPLETE','argv':__import__('sys').argv,'root':str(root),'real_cli_starts':0,'api_starts':0}
try:
    for name in ['state','repo','home','claude','tmp','shell','requests','manager-home','hooks']:(root/name).mkdir()
    (root/'repo/value.txt').write_text('P1 isolated fixture\n',encoding='utf-8')
    with (root/'claude/settings.json').open('x',encoding='utf-8') as f:json.dump({'theme':'dark'},f,indent=2)
    (root/'role.md').write_text('构思主控 P1 隔离协议探针。只回复收到的 nonce；不调用工具，不修改文件，不新增任务。\n',encoding='utf-8')
    (root/'nonce.txt').write_text('P1_NONCE_'+uuid.uuid4().hex,encoding='utf-8')
    manifest={'schema':1,'root':str(root),'state':str(root/'state'),'task':'t078-p1-'+suffix,'preset':'ideation',
              'launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),
              'executable':'/Users/luckye/.local/share/claude/versions/2.1.296','role_file':str(root/'role.md'),
              'code_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip(),
              'source_snapshot':str(out/'sources.tar.gz'),'api_url':'http://127.0.0.1:0','turn_limit':2 if two_turn else 1}
    requests=[{'nonce':(root/'nonce.txt').read_text(),'mode':'cancel' if two_turn else 'echo','ack':'P1_ACK'}]
    if two_turn:
        (root/'nonce-2.txt').write_text('P2_NONCE_'+uuid.uuid4().hex,encoding='utf-8')
        requests.append({'nonce':(root/'nonce-2.txt').read_text(),'mode':'echo','ack':'P2_ACK'})
    scenario={'schema':1,'name':'esc-two' if two_turn else 'single','requests':requests}
    if tool_slice:
        command=shlex.join([str(Path(shutil.which('node')).resolve()),str(SOURCE/'workbench/bin/inbox'),'list','--role','executor'])
        scenario={'schema':1,'name':'slice1-inbox-red','nonce':requests[0]['nonce'],
                  'ack':'SLICE1_TOOL_RESULT_RECORDED','bash_command':command,
                  'tool_use_id':'toolu_t078_'+uuid.uuid4().hex,'root_submit_budget':1,'messages_request_budget':2}
        (root/'role.md').write_text('构思主控单角色收件箱工具切片。收到 nonce 后只调用一次已批准的 Bash 库收件箱 list；工具返回后只确认并结束，让真实 Stop 转交。不得修改文件、新增请求或 agent、重试、打印环境或访问用户配置。工具的真实返回由测试记录，不自称业务通过。\n',encoding='utf-8')
    if suffix in ['09a3','09a3-block','09a3r','09a3r-block']:scenario['draft_handling']='retain-draft-for-block' if suffix.endswith('-block') else 'manual-empty-declaration'
    if suffix in ['09a3r2','09a3r2-block']:scenario['draft_handling']='retain-draft-for-block' if suffix.endswith('-block') else 'simulated-empty-declaration'
    with (root/'scenario.json').open('x',encoding='utf-8') as f:json.dump(scenario,f,indent=2)
    with (root/'input.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
    subprocess.run(['node',SOURCE/'workbench/tests/prepare_t078_p1.ts',root/'input.json',root/'approval.json'],cwd=SOURCE,check=True)
    for name in ['approval.json','input.json','nonce.txt','role.md','scenario.json',*(['nonce-2.txt'] if two_turn else [])]:shutil.copyfile(root/name,out/name)
    shutil.copyfile(root/'claude/settings.json',out/'isolated-settings.json')
    with (out/'readiness-template.json').open('x',encoding='utf-8') as f:
        json.dump({'launch':manifest['launch'],'session':manifest['session'],'confirmed_by':None,'readiness':'unconfirmed','basis':None},f,indent=2)
    with (out/'screen-key-approval-template.json').open('x',encoding='utf-8') as f:
        json.dump({'launch':manifest['launch'],'session':manifest['session'],'directory':str(root/'repo'),
                   'approved_by':None,'approval_ref':None,'basis':None,'screen_id':None,'purpose':None,'key':None,
                   'selected_label':None,'screen_file':None,
                   'selected_label_semantics':'Target item after this key; Enter confirms the target recorded by prior navigation',
                   'notice_reference':str(BASE/'p1-materials-09a3r2/security-notice-text.txt'),
                   'trust_sequence':['ArrowDown','Enter'],'trust_target':'Yes, I trust this folder',
                   'template_origin':'generator; approval fields deliberately empty'},f,ensure_ascii=False,indent=2)
    control={'environment':{'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(root/'manager-home'),'TMPDIR':str(root/'tmp'),
                           'A2A_OPERATOR_CREDENTIAL':str(root/'operator.json'),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
                           'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':'/dev/null','GIT_CONFIG_KEY_1':'commit.gpgsign',
                           'GIT_CONFIG_VALUE_1':'false','GIT_AUTHOR_NAME':'T078 P1 fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
                           'GIT_COMMITTER_NAME':'T078 P1 fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'},
             'api_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_messages.py'),str(root)],
             'driver_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(out),'--phase','launch'],
             'continue_driver_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(out),'--phase','continue-esc' if two_turn else 'continue','--readiness-file',str(out/'readiness.json'),
                                     *(['--actions-approval',str(out/'actions-approval.json')] if two_turn else [])],
             'readiness':{'template':str(out/'readiness-template.json'),'approved_file':str(out/'readiness.json'),'confirmation_required':'executor observes this new instance and explicitly approves its first nonce'},
             'endpoint_resolution':{'bind_host':'127.0.0.1','bind_port':0,'ready_file':str(root/'api-ready.json'),'runtime_input':str(root/'runtime-input.json'),
                                    'runtime_manifest':str(out/'launch/runtime-manifest.json'),'changes_allowed':['api_url','launch.env.ANTHROPIC_BASE_URL']},
             'isolated_settings':{'path':str(root/'claude/settings.json'),'content':{'theme':'dark'},'approval_file':str(out/'isolated-settings.json')},
             'launch_input_budget':0,'real_vendor_model_budget':0,'messages_request_budget':manifest['turn_limit'],'start_runs':0}
    if tool_slice:
        control.update(api_argv=['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_inbox_tool.py'),str(root)],
                       continue_driver_argv=['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/run_t078_slice1.py'),
                         '--materials',str(out),'--phase','submit','--readiness-file',str(out/'readiness.json'),
                         '--approval-file',str(out/'submit-approval.json')],
                       root_submit_budget=1,messages_request_budget=2,tool_call_budget=1)
        with (out/'submit-approval-template.json').open('x',encoding='utf-8') as f:
            json.dump({'launch':manifest['launch'],'session':manifest['session'],'thread':manifest['thread'],
                       'approved_by':None,'approval_ref':None,'basis':None,'nonce':scenario['nonce'],
                       'bash_command':scenario['bash_command'],'source':'test-simulated-user',
                       'root_submit_budget':1,'messages_request_budget':2,'tool_call_budget':1},f,ensure_ascii=False,indent=2)
        with (out/'permission-approval-template.json').open('x',encoding='utf-8') as f:
            json.dump({'launch':manifest['launch'],'session':manifest['session'],'thread':manifest['thread'],
                       'approved_by':None,'approval_ref':None,'basis':None,'source':'test-simulated-user',
                       'bash_command':scenario['bash_command'],'key':'Enter','selected_label':'Yes',
                       'screen_file':None,'selected_line':None,'dispatch':None,'permission_seq':None},f,ensure_ascii=False,indent=2)
    with (out/'control-plane.json').open('x',encoding='utf-8') as f:json.dump(control,f,ensure_ascii=False,indent=2)
    names=['test_t078_empty_declaration_entry.ts','test_t078_window_binding.mjs','test_t078_window_receipts.py','p1_window_receipts.py','p1_simulated_actions.py','test_t078_simulated_draft.py','cleanup_t078_electron_slot.py','test_t078_claude_signals.ts','test_t078_claude_epochs.ts','test_t078_controller_window.ts','test_t078_two_turn_profile.ts','test_t078_fake_two_requests.py','electron_client.py','electron_driver.mjs','t078_runtime_scenario.py','test_t078_p1_port_guard.ts','test_t078_p1_endpoint.py','test_t078_role_prompt.ts','test_t078_p1_bootstrap.ts','test_t078_p1_auth.ts','test_t078_p1_bearer.py','test_t078_p1_cleanup.py','test_t078_profile08.ts','test_t078_hook_trace.py','test_t078_screen_key.ts','test_t078_theme_confirmation.ts','test_t078_notice_key.ts','test_t078_trust_selection.ts','p1_processes.py','p1_endpoint.py','prepare_t078_p1.ts',
           'regenerate_t078_p1.py','run_t078_p1.py','t078_fake_messages.py','command_evidence.py','archive_t078_evidence.py']
    extra=[]
    if tool_slice:
        names+=['t078_slice1_protocol.py','t078_fake_inbox_tool.py','run_t078_slice1.py',
                'test_t078_slice1_protocol.py','test_t078_slice1_permission_key.mjs']
        extra.append(SOURCE/'workbench/bin/inbox')
    for p in args.extra_source:
        resolved=p.resolve();resolved.relative_to(SOURCE);extra.append(resolved)
    files=sorted([*SOURCE.joinpath('workbench/src').rglob('*.ts'),*[p for p in SOURCE.joinpath('workbench/app').rglob('*') if p.is_file()],*[SOURCE/'workbench/tests'/n for n in names],
                  SOURCE/'workbench/README.md',SOURCE/'workbench/package.json',SOURCE/'workbench/package-lock.json',BASE/'outside-sandbox.sh',*extra])
    with tarfile.open(out/'sources.tar.gz','x:gz') as arc:
        for p in files:arc.add(p,arcname=str(p.relative_to(SOURCE)))
    with (out/'source-files.json').open('x',encoding='utf-8') as f:json.dump([str(p.relative_to(SOURCE)) for p in files],f,indent=2)
    (out/'candidate.diff').write_bytes(subprocess.check_output(['git','diff','--','workbench'],cwd=SOURCE))
    record.update(status='PASS',scope='Static material generation only',launch=manifest['launch'],session=manifest['session'])
except Exception as error:record['error']=repr(error)
with (out/'generation.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(record,ensure_ascii=False));raise SystemExit(0 if record['status']=='PASS' else 1)
