"""Prepare a fresh P1 instance and source snapshot without starting services."""
import argparse,json,shutil,subprocess,tarfile,tempfile,uuid
from pathlib import Path

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--extra-source',type=Path,nargs='*',default=[])
args=parser.parse_args()
if not args.label.startswith('p1-materials-') or not args.label[len('p1-materials-'):].isdigit():parser.error('A new p1-materials-NN label is required')
suffix=args.label[len('p1-materials-'):]
out=BASE/args.label;out.mkdir()
root=Path(tempfile.mkdtemp(prefix='t078-2-p1-'+suffix+'-',dir='/tmp')).resolve()
record={'status':'INCOMPLETE','argv':__import__('sys').argv,'root':str(root),'real_cli_starts':0,'api_starts':0}
try:
    for name in ['state','repo','home','claude','tmp','shell','requests','manager-home']:(root/name).mkdir()
    with (root/'claude/settings.json').open('x',encoding='utf-8') as f:json.dump({'theme':'dark'},f,indent=2)
    (root/'role.md').write_text('构思主控 P1 隔离协议探针。只回复收到的 nonce；不调用工具，不修改文件，不新增任务。\n',encoding='utf-8')
    (root/'nonce.txt').write_text('P1_NONCE_'+uuid.uuid4().hex,encoding='utf-8')
    manifest={'schema':1,'root':str(root),'state':str(root/'state'),'task':'t078-p1-'+suffix,'preset':'ideation',
              'launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),
              'executable':'/Users/luckye/.local/share/claude/versions/2.1.296','role_file':str(root/'role.md'),
              'code_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip(),
              'source_snapshot':str(out/'sources.tar.gz'),'api_url':'http://127.0.0.1:0'}
    with (root/'input.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
    subprocess.run(['node',SOURCE/'workbench/tests/prepare_t078_p1.ts',root/'input.json',root/'approval.json'],cwd=SOURCE,check=True)
    for name in ['approval.json','input.json','nonce.txt','role.md']:shutil.copyfile(root/name,out/name)
    shutil.copyfile(root/'claude/settings.json',out/'isolated-settings.json')
    with (out/'readiness-template.json').open('x',encoding='utf-8') as f:
        json.dump({'launch':manifest['launch'],'session':manifest['session'],'confirmed_by':None,'readiness':'unconfirmed','basis':None},f,indent=2)
    control={'environment':{'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(root/'manager-home'),'TMPDIR':str(root/'tmp'),
                           'A2A_OPERATOR_CREDENTIAL':str(root/'operator.json'),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
                           'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':'/dev/null','GIT_CONFIG_KEY_1':'commit.gpgsign',
                           'GIT_CONFIG_VALUE_1':'false','GIT_AUTHOR_NAME':'T078 P1 fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
                           'GIT_COMMITTER_NAME':'T078 P1 fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'},
             'api_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/t078_fake_messages.py'),str(root)],
             'driver_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(out),'--phase','launch'],
             'continue_driver_argv':['/usr/bin/python3','-B',str(SOURCE/'workbench/tests/run_t078_p1.py'),'--materials',str(out),'--phase','continue','--readiness-file',str(out/'readiness.json')],
             'readiness':{'template':str(out/'readiness-template.json'),'approved_file':str(out/'readiness.json'),'confirmation_required':'executor observes this new instance and explicitly approves its first nonce'},
             'endpoint_resolution':{'bind_host':'127.0.0.1','bind_port':0,'ready_file':str(root/'api-ready.json'),'runtime_input':str(root/'runtime-input.json'),
                                    'runtime_manifest':str(out/'launch/runtime-manifest.json'),'changes_allowed':['api_url','launch.env.ANTHROPIC_BASE_URL']},
             'isolated_settings':{'path':str(root/'claude/settings.json'),'content':{'theme':'dark'},'approval_file':str(out/'isolated-settings.json')},
             'launch_input_budget':0,'real_vendor_model_budget':0,'messages_request_budget':1,'start_runs':0}
    with (out/'control-plane.json').open('x',encoding='utf-8') as f:json.dump(control,f,ensure_ascii=False,indent=2)
    names=['test_t078_claude_signals.ts','test_t078_p1_port_guard.ts','test_t078_p1_endpoint.py','test_t078_role_prompt.ts','test_t078_p1_bootstrap.ts','test_t078_p1_auth.ts','test_t078_p1_bearer.py','test_t078_p1_cleanup.py','p1_processes.py','p1_endpoint.py','prepare_t078_p1.ts',
           'regenerate_t078_p1.py','run_t078_p1.py','t078_fake_messages.py','command_evidence.py','archive_t078_evidence.py']
    extra=[]
    for p in args.extra_source:
        resolved=p.resolve();resolved.relative_to(SOURCE);extra.append(resolved)
    files=sorted([*SOURCE.joinpath('workbench/src').rglob('*.ts'),*[SOURCE/'workbench/tests'/n for n in names],
                  SOURCE/'workbench/README.md',SOURCE/'workbench/package.json',SOURCE/'workbench/package-lock.json',BASE/'outside-sandbox.sh',*extra])
    with tarfile.open(out/'sources.tar.gz','x:gz') as arc:
        for p in files:arc.add(p,arcname=str(p.relative_to(SOURCE)))
    with (out/'source-files.json').open('x',encoding='utf-8') as f:json.dump([str(p.relative_to(SOURCE)) for p in files],f,indent=2)
    (out/'candidate.diff').write_bytes(subprocess.check_output(['git','diff','--','workbench'],cwd=SOURCE))
    record.update(status='PASS',scope='Static material generation only',launch=manifest['launch'],session=manifest['session'])
except Exception as error:record['error']=repr(error)
with (out/'generation.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(record,ensure_ascii=False));raise SystemExit(0 if record['status']=='PASS' else 1)
