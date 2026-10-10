"""Real Synara provider processes; expected outcomes come from decision 02.

Replay: python3 real-provider-33.py UNIQUE_LABEL claudeAgent|codex good|checked-prompts
Claude's model API is scripted localhost I/O, never an independent model oracle.
The bad implementation changes only the server-side selected-tool decision.
"""
import datetime as dt
import fcntl
import http.server
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label, provider, variant = sys.argv[1:]
assert provider in ('claudeAgent', 'codex') and variant in ('good', 'checked-prompts')
assert label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label)
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-' + label)
root.mkdir(mode=0o700)
results = out / (label + '-real'); results.mkdir()
for name in ('os-home', 'codex-empty', 'claude-empty'):
    (root/name).mkdir(mode=0o700)
spec = importlib.util.spec_from_file_location('api', out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py')
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
fixture = None
process = None; auth_home = None; native_home = None; fake = None
def uid(): return str(uuid.uuid4())
def now(): return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
def save(name, value):
    with (results/(name+'.json')).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
def gate(command, **args):
    request = dict(command=command, **args); result = fixture.http('/api/a2a', request)
    save('gate-'+uid(), dict(request=request, result=result))
    assert result.get('ok'), result
    return result
def native(thread): return fixture.control('thread', thread=thread)['value']
def events(thread): return fixture.control('runtime-events',thread=thread)

# The response sequence is an independently specified checked write, then an
# unchecked write. It is not derived from the implementation or its choices.
fake_requests = []
scripted_tools = [
    ('mcp__synara__a2a_raise', dict(title='T064 actual CLI checked write '+label, body='Controlled API tool input; no real Claude model behavior claim')),
    ('mcp__synara__a2a_submit', dict(task='t064-real', attempt='not-an-attempt', session='not-a-session', fence=1, spec_rev=1, commit='0'*40)),
]
class FakeMessages(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        body=json.dumps({'data':[], 'has_more':False}).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        request=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
        # Record request bodies, not credential-bearing HTTP headers.
        fake_requests.append(dict(path=self.path, body=request, created_at=now()))
        completed={block.get('tool_use_id') for message in request.get('messages',[]) for block in (message.get('content',[]) if isinstance(message.get('content'),list) else []) if block.get('type')=='tool_result'}
        index=len({x for x in completed if str(x).startswith('t064-script-')})
        if index < len(scripted_tools):
            name,args=scripted_tools[index]
            content=[dict(type='tool_use',id='t064-script-'+str(index),name=name,input=args)]
            reason='tool_use'
        else:
            content=[dict(type='text',text='T064_LOCAL_API_FINISHED')]; reason='end_turn'
        message=dict(id='msg_t064_'+uid(),type='message',role='assistant',model=request.get('model','claude-sonnet-5'),content=content,stop_reason=reason,stop_sequence=None,usage=dict(input_tokens=100,output_tokens=25))
        self.send_response(200)
        if request.get('stream'):
            self.send_header('Content-Type','text/event-stream'); self.end_headers()
            stream=[('message_start',dict(type='message_start',message={**message,'content':[],'stop_reason':None}))]
            for i,block in enumerate(content):
                stream.append(('content_block_start',dict(type='content_block_start',index=i,content_block={**block, **({'input':{}} if block['type']=='tool_use' else {'text':''})})))
                delta=dict(type='input_json_delta',partial_json=json.dumps(block['input'])) if block['type']=='tool_use' else dict(type='text_delta',text=block['text'])
                stream.append(('content_block_delta',dict(type='content_block_delta',index=i,delta=delta)))
                stream.append(('content_block_stop',dict(type='content_block_stop',index=i)))
            stream += [('message_delta',dict(type='message_delta',delta=dict(stop_reason=reason,stop_sequence=None),usage=dict(output_tokens=25))),('message_stop',dict(type='message_stop'))]
            try:
                for event,data in stream:
                    self.wfile.write(('event: '+event+'\ndata: '+json.dumps(data)+'\n\n').encode()); self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError): pass
        else:
            self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps(message).encode())

try:
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
    tracked=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=fork,text=True)
    assert tracked=='', tracked
    env={k:v for k,v in os.environ.items() if k in ('PATH','SHELL','LANG','LC_ALL')}
    env.update(HOME=str(root/'os-home'),CODEX_HOME=str(root/'codex-empty'),CLAUDE_CONFIG_DIR=str(root/'claude-empty'),
        A2A_SYNARA_SLOT='s11-t064-'+label,T058_ROOT=str(root),T058_FORK=str(fork),T058_SOURCE_REVISION=revision,T064_VARIANT=variant)
    auth_home=Path(tempfile.mkdtemp(prefix='a2a-t064-'+provider+'-',dir='/tmp')).resolve(); auth_home.chmod(0o700)
    if provider=='claudeAgent':
        fake=http.server.ThreadingHTTPServer(('127.0.0.1',0),FakeMessages)
        threading.Thread(target=fake.serve_forever,daemon=True).start()
        env.update(ANTHROPIC_BASE_URL='http://127.0.0.1:'+str(fake.server_port),ANTHROPIC_API_KEY='t064-local-fake-key',
            CLAUDE_CONFIG_DIR=str(auth_home),DISABLE_AUTOUPDATER='1',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
        binary='/Users/luckye/.local/bin/claude'
        version=subprocess.check_output([binary,'--version'],env=env,text=True).strip()
        # An explicit provider home removes ambient auth environment by design.
        # This owned launcher supplies only the fake endpoint/key/config to the
        # installed CLI after that legitimate isolation boundary.
        launcher=root/'claude-local-api'
        launcher.write_text('#!/bin/sh\nexport ANTHROPIC_BASE_URL="'+env['ANTHROPIC_BASE_URL']+'"\nexport ANTHROPIC_API_KEY="t064-local-fake-key"\nexport CLAUDE_CONFIG_DIR="'+str(auth_home)+'"\nexport DISABLE_AUTOUPDATER=1\nexport CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1\nexec '+binary+' "$@"\n',encoding='utf-8'); launcher.chmod(0o700)
        save('isolation',dict(home=str(auth_home),copied=[],binary=binary,version=version,launcher=str(launcher),launcher_text=launcher.read_text(),base_url=env['ANTHROPIC_BASE_URL'],model_api='scripted localhost',real_cli=True,real_synara_adapter=True,user_claude_credentials_read=False,scripted_tools=scripted_tools))
    else:
        native_home=Path(tempfile.mkdtemp(prefix='a2a-t064-native-',dir='/tmp')).resolve(); native_home.chmod(0o700)
        env['T064_NATIVE_HOME']=str(native_home)
        # Only this auth file is copied; config and rules are fixture-only.
        shutil.copyfile('/Users/luckye/.codex/auth.json',auth_home/'auth.json'); (auth_home/'auth.json').chmod(0o600)
        config='check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n[projects.'+json.dumps(str(root))+']\ntrust_level = "trusted"\n'
        (auth_home/'config.toml').write_text(config,encoding='utf-8'); (auth_home/'rules').mkdir()
        rules='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
        (auth_home/'rules/default.rules').write_text(rules,encoding='utf-8')
        binary=str(Path(shutil.which('codex')).resolve())
        version=subprocess.check_output([binary,'-c','check_for_update_on_startup=false','--version'],text=True).strip()
        assert version=='codex-cli 0.162.0',version
        launcher=root/'codex-fixed'
        launcher.write_text('#!/bin/sh\nprintf \'%s\\n\' "$CODEX_HOME" >> "'+str(root/'codex-observed-homes.txt')+'"\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n',encoding='utf-8'); launcher.chmod(0o700)
        save('isolation',dict(home=str(auth_home),native_synara_home=str(native_home),expected_actual_codex_home=str(native_home/'codex-home-overlay'),copied=['auth.json'],config=config,rules=rules,hooks=[],binary=binary,version=version,launcher_argv=[binary,'-c','service_tier="fast"','-c','check_for_update_on_startup=false'],requested_tier='fast',actual_supplier_tier='unverified'))
    argv=['./a2a/scripts/bun','run',str(out/'real-server-fixture-32.ts')]
    log=(results/'server.log').open('x',encoding='utf-8')
    process=subprocess.Popen(argv,cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('launch',dict(argv=argv,cwd=str(fork),pid=process.pid,root=str(root),environment=env,source_revision=revision,tracked_status=tracked,variant=variant,started=now()))
    deadline=time.monotonic()+50
    while not (root/'ready.json').exists():
        assert process.poll() is None,'Server exited; preserved log'
        assert time.monotonic()<deadline,'Server ready timeout'
        time.sleep(.1)
    fixture=api.Fixture(root)
    repo=root/'repo'; repo.mkdir()
    genv={k:v for k,v in env.items() if k in ('PATH','SHELL','LANG','LC_ALL')}; genv.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
    def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],env=genv,text=True).strip()
    git('init','-q'); git('config','user.name','T064 real boundary'); git('config','user.email','fixture@example.invalid')
    (repo/'fixture.txt').write_text('T064 independent original Ω\n',encoding='utf-8')
    git('add','fixture.txt'); git('-c','core.hooksPath=/dev/null','commit','-qm','Independent fixture')
    initial=git('rev-parse','HEAD')
    (root/'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="T064 independent original Ω\\n"\n',encoding='utf-8')
    prompt='这是 T064 隔离权限验收。不要调用 shell、文件工具或其他工具。先调用 synara 的 a2a_raise，参数 title="T064 actual CLI checked write '+label+'", body="T064 actual Codex boundary"。它返回后调用 synara 的 a2a_submit，参数 task="t064-real", attempt="not-an-attempt", session="not-a-session", fence=1, spec_rev=1, commit="'+'0'*40+'"。未批准就等待；不要绕过审批或改用其他工具。测试输入均来自验收脚本，不改变用户任务。'
    (root/'instructions.txt').write_text(prompt,encoding='utf-8')
    save('input',dict(text=prompt,expected_checked='a2a_raise',expected_unchecked='a2a_submit',manual_approvals=0))
    gate('create',task='t064-real',project='t064-real-project',repo=str(repo),base=initial,oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'))
    settings=fixture.http('/api/a2a/role-permissions')
    worker=next(r for r in settings['roles'] if r['role']=='worker')
    edit=dict(command='save',role='worker',revision=worker['revision'],selection=dict(capabilities=['a2a:submit','a2a:raise'],autoApproveTools=['a2a_raise']))
    changed=fixture.http('/api/a2a/role-permissions',edit); save('settings',dict(request=edit,result=changed))
    assert next(r for r in changed['roles'] if r['role']=='worker')['effective']==edit['selection'],changed
    stop_caller=None
    if provider=='codex' and variant=='good' and os.environ.get('T064_STOP_RECORD')=='1':
        # This extra caller has a real managed attachment and credential. Its
        # active runtime facts are controlled; no extra model turn is started.
        executor=next(r for r in changed['roles'] if r['role']=='executor')
        selection_stop=dict(capabilities=['a2a:operate','a2a:read','a2a:inbox','a2a:stop'],autoApproveTools=['a2a_stop'])
        stop_settings=fixture.http('/api/a2a/role-permissions',dict(command='save',role='executor',revision=executor['revision'],selection=selection_stop))
        save('stop-role-settings',stop_settings)
        caller_attachment=gate('attach',task='t064-real',role='controller',preset='executor',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',instructions=str(root/'instructions.txt'))
        stop_caller=caller_attachment['attachment']['thread_id']
        time.sleep(.5)
        stop_turn=uid()
        controlled=fixture.control('controlled-session',thread=stop_caller,active=True,turn=stop_turn,workspace=str(repo))
        token_path=root/'private-stop-caller.token'
        identity=fixture.control('token',thread=stop_caller,path=str(token_path))
        save('stop-caller',dict(attachment=caller_attachment,controlled_native_facts=True,controlled=controlled,credential=identity,thread=stop_caller,turn=stop_turn))
        stop_token=token_path.read_text(encoding='utf-8')
    patch={'providers':{provider:{'enabled':True,'homePath':str(auth_home),'binaryPath':str(launcher)}}}
    configured=fixture.control('settings',patch=patch); save('provider-settings',configured)
    selection=dict(provider=provider,model='gpt-6.1-sol' if provider=='codex' else 'claude-sonnet-5',options=dict(reasoningEffort='xhigh',fastMode=True) if provider=='codex' else dict(thinking=False))
    if provider=='codex':
        # Reserve before dispatch. Failed starts still consume a reservation,
        # so retries cannot silently exceed decision 02's four-turn ceiling.
        with (out/'codex-turn-budget-42.jsonl').open('a+',encoding='utf-8') as budget:
            fcntl.flock(budget.fileno(),fcntl.LOCK_EX); budget.seek(0)
            previous=[json.loads(line) for line in budget if line.strip()]
            assert len(previous)<4,'Codex real-turn budget exhausted'
            budget.write(json.dumps(dict(label=label,variant=variant,reservation=len(previous)+1,limit=4,created_at=now()))+'\n'); budget.flush()
    attached=gate('attach',task='t064-real',role='worker',preset='worker',modelSelection=selection,runtimeMode='approval-required' if provider=='codex' else 'full-access',instructions=str(root/'instructions.txt'))
    thread=attached['attachment']['thread_id']; save('thread-id',dict(thread=thread,provider=provider,model_turn_budget=4 if provider=='codex' else 0))
    if stop_caller:
        stop_request=dict(command='inbox_send',to='executor',kind='stop',body='T064 stop-address evidence: stop owned pending worker',refs=['thread:'+thread])
        stop_entry=fixture.http('/api/a2a',stop_request)
        save('stop-entry',dict(request=stop_request,result=stop_entry))
        assert stop_entry['entry']['from']=='user',stop_entry
    save('journal-location',dict(path=str(root/'userdata/state.sqlite'),read_via='Actual SQL owner, runtime-events control operation'))
    deadline=time.monotonic()+(140 if provider=='codex' else 45)
    observed=None
    while time.monotonic()<deadline:
        view=native(thread)
        requests=[e for e in events(thread) if e['type']=='request.opened']
        if requests:
            observed=requests; break
        turn=view.get('latestTurn') or {}
        if turn.get('state') in ('completed','error','interrupted') or (view.get('session') or {}).get('status')=='error':
            break
        time.sleep(.3)
    raw=events(thread); save('runtime-events',raw); save('thread-observed',native(thread)); save('orchestration-events',fixture.control('events'))
    if provider=='codex':
        observed_homes=(root/'codex-observed-homes.txt').read_text(encoding='utf-8').splitlines()
        expected_home=native_home/'codex-home-overlay'
        assert str(expected_home) in observed_homes,observed_homes
        assert all(not p or Path(p).resolve().is_relative_to(native_home) for p in observed_homes),observed_homes
        save('actual-native-home',dict(status='PASS',observed_cli_CODEX_HOME=observed_homes,actual_config=(expected_home/'config.toml').read_text(encoding='utf-8'),actual_home_in_tmp=True,auth_links_to_owned_source=(expected_home/'auth.json').resolve()==auth_home/'auth.json',auth_bytes_read=False))
    if provider=='claudeAgent': save('fake-messages-api',fake_requests)
    with sqlite3.connect('file:'+str(root/'userdata/a2a-gates/state.sqlite3')+'?mode=ro',uri=True) as db:
        rows={table:[dict(zip([c[0] for c in cursor.description],row)) for row in cursor] for table in ('issue_records','events') for cursor in [db.execute('SELECT * FROM '+table)]}
    save('gateway-core-records',rows)
    pending=[e for e in raw if e['type']=='request.opened']
    if not pending:
        save('oracle',dict(status='INCOMPLETE',reason='Real process emitted no permission request; minimal protocol leg stops here',provider=provider,variant=variant,manual_approvals=0))
        raise RuntimeError('Real CLI permission flow missing; do not replace with a fake callback')
    expected='a2a_raise' if variant=='checked-prompts' else 'a2a_submit'
    assert len(pending)==1,pending
    if provider=='claudeAgent':
        assert pending[0]['raw']['method']=='canUseTool/request'
        assert pending[0]['payload']['args']['toolName']=='mcp__synara__'+expected,pending[0]
    else:
        assert pending[0]['raw']['method']=='mcpServer/elicitation/request'
        args=pending[0]['payload']['args']
        assert args['serverName']=='synara' and args['_meta']['codex_approval_kind']=='mcp_tool_call',args
        # Exact native protocol field, not keywords used to infer meaning.
        assert args['message']=='Allow the synara MCP server to run tool "'+expected+'"?',args
        if variant=='good':
            assert args['_meta']['tool_params']==scripted_tools[1][1],args
    raised=[r for r in rows['issue_records'] if json.loads(r['data'])['title']=='T064 actual CLI checked write '+label]
    if variant=='good':
        assert len(raised)==1,raised
        assert json.loads(raised[0]['data'])['thread_id']==thread,raised
        save('oracle',dict(status='PASS',provider=provider,variant=variant,thread=thread,checked_executed=True,checked_pending_approvals=0,unchecked_pending_approval=True,issue=raised[0],request=pending[0],manual_approvals=0,actual_supplier_tier='unverified' if provider=='codex' else 'not-applicable'))
        print('PASS real '+provider+' checked tool executes and unchecked tool waits',flush=True)
    else:
        assert not raised,raised
        save('oracle',dict(status='NO_GO',provider=provider,variant=variant,thread=thread,known_bad_rejected=True,violation='Checked tool prompts rather than executes',actual_request=pending[0],manual_approvals=0))
        print('NO_GO known-bad '+provider+' checked tool incorrectly prompts',flush=True)
    if stop_caller:
        created=dt.datetime.fromisoformat(stop_entry['entry']['created_at'].replace('Z','+00:00'))
        stop_id=stop_entry['entry']['id']
        while (dt.datetime.now(dt.timezone.utc)-created).total_seconds()<=120.1:
            assert native(thread)['latestTurn']['state']=='running'
            time.sleep(2)
        request=dict(jsonrpc='2.0',id=uid(),method='tools/call',params=dict(name='a2a_stop',arguments=dict(thread=thread,stop_id=stop_id)))
        result=fixture.http('/mcp',request,stop_token)
        save('stop-mcp',dict(request=request,result=result,credential_thread=stop_caller,credential_role='executor',credential_turn=stop_turn,authenticated=True))
        stopped=json.loads(result['result']['content'][0]['text']); assert stopped.get('ok'),stopped
        deadline=time.monotonic()+25
        while native(thread)['latestTurn']['state']=='running':
            assert time.monotonic()<deadline,'Stop failed to reach native provider'
            time.sleep(.3)
        with sqlite3.connect('file:'+str(root/'userdata/a2a-gates/state.sqlite3')+'?mode=ro',uri=True) as db:
            interrupts=[dict(seq=r[0],time=r[1],task=r[2],attempt=r[3],type=r[4],details=json.loads(r[5])) for r in db.execute("SELECT seq,time,task,attempt,type,details FROM events WHERE type='emergency_interrupt_requested'")]
        assert len(interrupts)==1 and interrupts[0]['details']['actor']=='ideation' and interrupts[0]['details']['thread']==thread,interrupts
        save('stop-address-record',dict(status='PASS',caller_role='executor',caller_thread=stop_caller,caller_turn=stop_turn,caller_credential=identity,core_record=interrupts[0],core_actor_address='ideation',core_details_thread_is='target thread; caller thread is bound by gateway credential, not separately copied into this core event',target_thread=thread,target_state=native(thread)['latestTurn']['state'],controlled_caller_native_facts=True,real_target_cli=True,elapsed_seconds=(dt.datetime.now(dt.timezone.utc)-created).total_seconds(),manual_approvals=0))
    # The unchecked request remains pending and receives no approval. End the
    # owned turn through the real native interruption path before reclaiming.
    # Export request settlement as well as its opening, including CLI output.
    before_cleanup=native(thread)
    if (before_cleanup.get('latestTurn') or {}).get('state')=='running':
        interruption=fixture.control('command',command=dict(type='thread.turn.interrupt',commandId='t064-cleanup-interrupt:'+uid(),threadId=thread,turnId=before_cleanup['latestTurn']['turnId'],createdAt=now()))
        save('cleanup-interrupt',interruption)
        deadline=time.monotonic()+45
        while (native(thread).get('latestTurn') or {}).get('state')=='running':
            assert time.monotonic()<deadline,'Real CLI did not settle after owned interruption'
            time.sleep(.3)
    save('runtime-events-after-denial',events(thread)); save('thread-after-denial',native(thread))
    if provider=='claudeAgent': save('fake-messages-api-after-denial',fake_requests)
    gate('reclaim',task='t064-real',thread=thread)
    assert git('rev-parse','HEAD')==initial and git('status','--porcelain')==''
finally:
    if fake is not None:
        fake.shutdown(); fake.server_close()
        if not (results/'fake-messages-api.json').exists(): save('fake-messages-api',fake_requests)
    if process is not None:
        if process.poll() is None:
            os.kill(process.pid,signal.SIGTERM)
            try: process.wait(timeout=25)
            except subprocess.TimeoutExpired:
                save('cleanup-failed',dict(pid=process.pid,reason='Owned server did not stop')); raise
        save('server-stop',dict(pid=process.pid,exit=process.returncode,stopped=True,created_at=now()))
        log.close()
    if auth_home is not None:
        assert auth_home.parent==Path('/tmp').resolve() and auth_home.name.startswith('a2a-t064-')
        shutil.rmtree(auth_home)
        save('auth-cleanup',dict(home=str(auth_home),exists=auth_home.exists(),copied_auth_removed=provider=='codex',user_claude_credentials_read=False))
    if native_home is not None:
        assert native_home.parent==Path('/tmp').resolve() and native_home.name.startswith('a2a-t064-native-')
        shutil.rmtree(native_home)
        save('native-home-cleanup',dict(home=str(native_home),exists=native_home.exists(),entire_native_overlay_removed=True))
