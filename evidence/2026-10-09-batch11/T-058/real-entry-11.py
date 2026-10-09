import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
launch = json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root = Path(launch['root']).resolve()
results = out/label; results.mkdir()
assert launch['tracked_status'] == '', 'Real turns require the frozen clean candidate'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()==launch['source_revision']
api_path = out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py'
spec = importlib.util.spec_from_file_location('t058_fixture_api',api_path)
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
fixture = api.Fixture(root)
auth_home = None

def save(name, value):
    with (results/(name+'.json')).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2); f.write('\n')
def uid(): return str(uuid.uuid4())
def native(thread): return fixture.control('thread',thread=thread)['value']
def gate(command, **args):
    request = dict(command=command, **args); result = fixture.http('/api/a2a',request)
    save('gate-'+str(len(list(results.iterdir()))),dict(request=request,result=result)); return result
def mcp(token, name, **args):
    request=dict(jsonrpc='2.0',id=uid(),method='tools/call',params=dict(name=name,arguments=args))
    result=fixture.http('/mcp',request,token)
    save('mcp-'+str(len(list(results.iterdir()))),dict(request=request,result=result,authenticated=True))
    assert 'result' in result,result
    return json.loads(result['result']['content'][0]['text'])
def wait_thread(thread, label, predicate, seconds=80):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        view=native(thread)
        if predicate(view): save(label,view); return view
        if view.get('hasPendingApprovals') or view.get('hasPendingUserInput'):
            save(label+'-pending',view); raise RuntimeError('Unexpected permission/input wait; no approval was sent')
        time.sleep(.3)
    save(label+'-timeout',native(thread)); raise TimeoutError(label)

try:
    repo=root/'repo'; repo.mkdir()
    env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']}
    env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
    def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True,env=env).strip()
    git('init','-q'); git('config','user.name','T058 real boundary'); git('config','user.email','fixture@example.invalid')
    (repo/'fixture.txt').write_text('T058 external boundary Ω\n',encoding='utf-8')
    git('add','fixture.txt'); git('-c','core.hooksPath=/dev/null','commit','-qm','Independent original')
    initial=git('rev-parse','HEAD')
    (root/'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="T058 external boundary Ω\\n"\n',encoding='utf-8')
    (root/'controller.txt').write_text('这是隔离验收。不要调用任何工具，不修改文件。第一条消息只回复 READY。以后收到收件箱唤醒消息，只逐字回复该消息全文，不调用工具。',encoding='utf-8')
    (root/'worker.txt').write_text('这是隔离的中断验收。不要修改文件，不调用 MCP，不 submit。调用 shell 工具执行 sleep 180。若工具返回 session id，使用 write_stdin 等待该 session，每次等待不超过 30 秒，直到命令结束再回复 WAIT_FINISHED。不要提前结束 turn。',encoding='utf-8')
    created=gate('create',task='t058-real',project='t058-real-project',repo=str(repo),base=initial,oracle=str(root/'oracle.py'),instructions=str(root/'controller.txt'))
    assert created['ok'],created
    # The sender is a controlled native session. Only the two receiver turns
    # and one worker turn use the real Codex runtime.
    ideation=gate('attach',task='t058-real',role='controller',preset='ideation',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',instructions=str(root/'controller.txt'))
    assert ideation['ok'],ideation
    sender=ideation['attachment']['thread_id']; time.sleep(.4)
    fixture.control('controlled-session',thread=sender,active=True,turn=uid(),workspace=str(repo))
    token_path=root/'private-ideation.token'
    sender_caps=fixture.control('token',thread=sender,path=str(token_path)); token=token_path.read_text(encoding='utf-8')
    binary=str(Path(shutil.which('codex')).resolve())
    version=subprocess.check_output([binary,'-c','check_for_update_on_startup=false','--version'],text=True).strip()
    assert version=='codex-cli 0.162.0',version
    auth_home=Path(tempfile.mkdtemp(prefix='a2a-t058-auth-',dir='/tmp')).resolve(); auth_home.chmod(0o700)
    shutil.copyfile('/Users/luckye/.codex/auth.json',auth_home/'auth.json'); (auth_home/'auth.json').chmod(0o600)
    config='check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n[projects.'+json.dumps(str(root))+']\ntrust_level = "trusted"\n'
    (auth_home/'config.toml').write_text(config,encoding='utf-8'); (auth_home/'rules').mkdir()
    rules='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
    (auth_home/'rules/default.rules').write_text(rules,encoding='utf-8')
    launcher=root/'codex-fixed'
    launcher.write_text('#!/bin/sh\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n',encoding='utf-8'); launcher.chmod(0o700)
    save('isolation',dict(home=str(auth_home),copied=['auth.json'],config=config,rules=rules,hooks=[],binary=binary,version=version,launcher_argv=[binary,'-c','service_tier="fast"','-c','check_for_update_on_startup=false'],requested_tier='fast',actual_supplier_tier='unverified'))
    settings=fixture.control('settings',patch={'providers':{'codex':{'enabled':True,'homePath':str(auth_home),'binaryPath':str(launcher)}}})
    assert settings['providers']['codex']['enabled'] is True
    selection=dict(provider='codex',model='gpt-6.1-sol',options=dict(reasoningEffort='xhigh',fastMode=True))
    executor=gate('attach',task='t058-real',role='controller',preset='executor',modelSelection=selection,runtimeMode='full-access',instructions=str(root/'controller.txt'))
    assert executor['ok'],executor
    receiver=executor['attachment']['thread_id']
    prepared=wait_thread(receiver,'receiver-ready',lambda t: (t.get('latestTurn') or {}).get('state')=='completed')
    assert any(m['role']=='assistant' and m['text']=='READY' for m in prepared['messages']),prepared
    first_turn=prepared['latestTurn']['turnId']
    sent=mcp(token,'a2a_inbox_send',to='executor',kind='assign',body='真实唤醒哨兵 Ω\n不可丢失的第二行',refs=['ticket:T-058'])
    assert sent['ok'],sent
    entry_id=sent['entry']['id']; message_id=sent['delivery']['message']
    expected='收件箱 '+entry_id+'：真实唤醒哨兵 Ω'
    awakened=wait_thread(receiver,'receiver-awakened',lambda t: (t.get('latestTurn') or {}).get('state')=='completed' and t['latestTurn']['turnId']!=first_turn)
    message=next(m for m in awakened['messages'] if m['id']==message_id)
    assert message['text']==expected and message['dispatchOrigin']=='agent',message
    assert any(m['role']=='assistant' and m['text']==expected and m.get('turnId')==awakened['latestTurn']['turnId'] for m in awakened['messages']),awakened
    assert sum(m['id']==message_id for m in awakened['messages'])==1
    reclaimed=gate('reclaim',task='t058-real',thread=receiver); assert reclaimed['ok'],reclaimed
    worker=gate('attach',task='t058-real',role='worker',preset='worker',modelSelection=selection,runtimeMode='full-access',instructions=str(root/'worker.txt'))
    assert worker['ok'],worker
    target=worker['attachment']['thread_id']
    running=wait_thread(target,'worker-running',lambda t: (t.get('latestTurn') or {}).get('state')=='running')
    stop=mcp(token,'a2a_inbox_send',to='executor',kind='stop',body='URGENT 停止隔离 worker',refs=['thread:'+target])
    assert not stop['ok'] and stop['delivery']['state']=='undelivered',stop
    stop_id=stop['entry']['id']; created_at=dt.datetime.fromisoformat(stop['entry']['created_at'].replace('Z','+00:00'))
    early=mcp(token,'a2a_stop',thread=target,stop_id=stop_id); assert early['error']=='stop_too_early',early
    forbidden=mcp(token,'a2a_stop',thread=sender,stop_id=stop_id); assert forbidden['error']=='worker_target_required',forbidden
    deadline=time.monotonic()+125
    while (dt.datetime.now(dt.timezone.utc)-created_at).total_seconds()<=120.1:
        assert time.monotonic()<deadline
        view=native(target)
        assert (view.get('latestTurn') or {}).get('state')=='running',view
        time.sleep(5)
    before=gate('status',task='t058-real')['task']
    result=mcp(token,'a2a_stop',thread=target,stop_id=stop_id)
    assert result['ok'] and result['interruptRequested'],result
    interrupted=wait_thread(target,'worker-interrupted',lambda t: (t.get('latestTurn') or {}).get('state')=='interrupted',seconds=45)
    assert interrupted['archivedAt'] is None
    assert gate('status',task='t058-real')['task']==before
    with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
        inputs=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
        assert not any(v['target'].get('message')==message_id for v in inputs)
        interrupt_events=[json.loads(r[0]) for r in db.execute("SELECT details FROM events WHERE type='emergency_interrupt_requested'")]
        assert len(interrupt_events)==1 and interrupt_events[0]['stop_id']==stop_id
    assert git('rev-parse','HEAD')==initial and git('status','--porcelain')==''
    cleanup=gate('reclaim',task='t058-real',thread=target); assert cleanup['ok'],cleanup
    save('real-oracle',dict(status='PASS',candidate=launch['source_revision'],controlled_sender=True,sender_capabilities=sender_caps,provider_turns=3,
        first_turn=first_turn,new_wake_turn=awakened['latestTurn']['turnId'],worker_turn=running['latestTurn']['turnId'],sent=sent,native_message=message,stop=stop,interrupt=result,interrupted_state=interrupted['latestTurn']['state'],gate_task_unchanged=True,worker_cleanup=cleanup,receiver_cleanup=reclaimed,manual_approvals=0))
    print('PASS real Codex new wake turn and actual interrupt; three provider turns, no manual approval',flush=True)
finally:
    if auth_home is not None:
        # This is the home created by this driver. Raw auth is never evidence.
        assert auth_home.parent == Path('/tmp').resolve() and auth_home.name.startswith('a2a-t058-auth-')
        shutil.rmtree(auth_home)
        save('auth-cleanup',dict(home=str(auth_home),exists=auth_home.exists(),copied_auth_removed=True))
