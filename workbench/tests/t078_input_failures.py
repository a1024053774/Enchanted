"""Input failure contracts through the production window, daemon and PTY.

Known red contracts: composition must hold injection; request_id reuse must not write another input; legacy mouse
bytes >= 128 must reach PTY unchanged and be recorded as user actions. Other
failures stop. Only isolated fixture data receives the recorder fault injection.
"""
import base64
from contextlib import closing
import json
import socket
import sqlite3
import time
import uuid


def run_input_failures(*,home,state,attempt,window,call,query,check,result,output,credential):
    launch=json.loads(query('launch_records')[0]['data'])
    operator=json.loads(credential.read_text())
    result['input_failure_scope']='真实 Electron/daemon/PTY；组合输入事件为合成事件；无供应商 CLI、Claude 夹具或模型'

    def wait_for(predicate,description,timeout=5):
        deadline=time.monotonic()+timeout
        while not predicate():
            if time.monotonic()>=deadline:raise RuntimeError('Fixture deadline: '+description)
            time.sleep(.025)

    def received():return (home/'received.bin').read_bytes()

    def raw(command,identity):
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(15);connection.connect(str(state/'control.sock'))
            connection.sendall((json.dumps({'id':str(uuid.uuid4()),'input':command,'identity':identity})+'\n').encode())
            data=b''
            while b'\n' not in data:
                part=connection.recv(65536)
                if not part:raise RuntimeError('Incomplete daemon response')
                data+=part
            return json.loads(data.split(b'\n',1)[0])

    def new_window():
        opened=raw({'command':'window_open','task':launch['task'],'launch':launch['id']},operator)
        if not opened.get('ok'):raise RuntimeError('Window credential setup rejected')
        return opened['identity']  # Never serialize a capability into evidence.

    def verify(name,passed,expected,observed):
        check(name,passed,expected,observed)
        if not passed and name not in ['composition_holds_injection','request_id_reuse_is_not_written','binary_mouse_bytes_and_action']:
            raise AssertionError(name)

    # Independent fixed text. This extends P1's public DOM composition sequence
    # through the real backend; it does not claim to drive the system IME.
    phrase='组合输入：中文乙'
    before=received();window.call('terminal-compose-start')
    started=json.loads((home/'receiver-started.json').read_text())
    wait_for(lambda:(home/'turn-2.ready').exists(),'second user submit')
    pending=home/'hook-1.pending'
    pending.write_text(json.dumps({'session_id':started['native_session'],'hook_event_name':'Stop','turn_id':'turn-2'})+'\n')
    pending.rename(home/'hook-1.json')
    wait_for(lambda:(home/'hook-1.exit').exists(),'Stop during composition')
    if (home/'hook-1.exit').read_text().strip()!='0':raise RuntimeError('Fixture Stop was rejected')
    held=call('pane_status','--thread',attempt['thread_id'])
    verify('composition_holds_injection',received()==before and len(held['queued'])==1 and not held['writing'],
           '组合输入开始但尚未提交时，即使收到上一回合 Stop，也不能注入初始排队提示',held)
    # Let an already-observed wrong injection finish before the next assertion;
    # this read-only wait does not change or forgive the failed contract above.
    wait_for(lambda:not call('pane_status','--thread',attempt['thread_id'])['writing'],'in-flight write completion')
    before=received();window.call('terminal-compose',text=phrase,started=True)
    wait_for(lambda:len(received())>=len(before)+len(phrase.encode()),'composition bytes')
    inputs=[json.loads(row['data']) for row in query('user_inputs')]
    matching=[item for item in inputs if item['form']=='message' and item['text']==phrase]
    verify('composition_reaches_backend_once',received()==before+phrase.encode() and len(matching)==1
           and matching[0]['target']['attempt']==attempt['attempt_id'],
           '中文合成组合事件只提交一次准确文本，绑定活动 attempt',{'inputs':matching,'received_suffix':received()[len(before):].hex()})

    extra=new_window();before=received()
    first=raw({'command':'window_input','sequence':1,'request_id':'same-window-request','data':'FIRST_ONLY'},extra)
    if not first.get('ok'):raise RuntimeError('First input unexpectedly rejected')
    wait_for(lambda:len(received())>=len(before)+10,'first request bytes')
    second=raw({'command':'window_input','sequence':2,'request_id':'same-window-request','data':'MUST_NOT_WRITE'},extra)
    # The response is after the production write operation. Wait for a read-only
    # status roundtrip as well; no repeated input or retry occurs here.
    call('pane_status','--thread',attempt['thread_id'])
    verify('request_id_reuse_is_not_written',second.get('ok') is False and received()==before+b'FIRST_ONLY',
           '同一窗口 request_id 重用且正文不同，第二次必须拒绝并且不写字节',
           {'first':first,'second':second,'received_suffix':received()[len(before):].hex()})
    closed=raw({'command':'window_close'},extra)
    if not closed.get('ok'):raise RuntimeError('Close rejected')
    before=received()
    stale=raw({'command':'window_input','sequence':3,'request_id':'after-close','data':'FORBIDDEN'},extra)
    verify('closed_window_credential_is_rejected',stale.get('error')=='invalid_window_identity' and received()==before,
           '已关闭窗口的凭据不能再写 PTY',stale)

    (home/'mouse-mode.request').write_text('fixture: enable DECSET 1000\n')
    wait_for(lambda:(home/'mouse-mode.ready').exists(),'mouse mode output')
    trace=state/'traces'/launch['id']/'pty.raw'
    wait_for(lambda:b'\x1b[?1000h' in trace.read_bytes(),'daemon mouse mode trace')
    highwater=trace.stat().st_size
    window.wait(lambda view:view['offset']>=highwater)
    before=received();mouse=window.call('terminal-mouse-binary')
    expected=b'\x1b[M\x20\xa3\x27\x1b[M\x23\xa3\x27'
    deadline=time.monotonic()+3
    while len(received())<len(before)+len(expected) and time.monotonic()<deadline:
        time.sleep(.025)
    binary=[json.loads(row['data']) for row in query('user_inputs')]
    binary=[item for item in binary if item.get('content',{}).get('action')=='terminal-binary']
    recorded=b''.join(base64.b64decode(item['content']['data_base64'],validate=True) for item in binary)
    verify('binary_mouse_bytes_and_action',received()==before+expected and recorded==expected
           and len(binary)==2 and all(item['form']=='action' and item['target']['attempt']==attempt['attempt_id'] for item in binary),
           '第 131 列第 7 行左键按下／抬起的 12 字节完整写入；两个二进制用户 action，不按 UTF-8 扩展 0xa3',
           {'mouse':mouse,'expected_hex':expected.hex(),'received_suffix':received()[len(before):].hex(),'records':binary})
    window.call('capture',name='input-failures-before-close');window.close();result['runtime_window_closed']=True

    # Database fault injected only into this freshly-created fixture. The
    # production recorder must fail before writing any corresponding PTY byte.
    fault_window=new_window();before=received();inputs_before=query('user_inputs')
    with closing(sqlite3.connect(state/'state.sqlite3')) as db:
        db.execute("CREATE TRIGGER t078_fixture_recorder_failure BEFORE INSERT ON user_inputs BEGIN SELECT RAISE(ABORT,'T078 injected recorder failure'); END")
        db.commit()
    failed=raw({'command':'window_input','sequence':1,'request_id':'record-fault','data':'DO_NOT_SEND'},fault_window)
    observer=call('status','--task',launch['task']).get('user_input_observer')
    verify('recorder_failure_prevents_pty_write',failed.get('ok') is False and received()==before
           and query('user_inputs')==inputs_before and observer and observer['state']=='failed',
           '输入登记故障必须拒绝、标记记录器失败，且不写 PTY 或伪造输入',{'response':failed,'observer':observer})
    with closing(sqlite3.connect(state/'state.sqlite3')) as db:
        db.execute('DROP TRIGGER t078_fixture_recorder_failure');db.commit()

    # Explicit cold restart scenario, not a recovery retry. The old capabilities
    # remain only in this Python process; the old owned credential file is removed
    # after shutdown, so startup must issue a different credential at that path.
    call('daemon_stop');wait_for(lambda:not (state/'daemon.pid').exists(),'owned daemon shutdown',10)
    old_bytes=received();credential.unlink();call('daemon_start')
    new_operator=json.loads(credential.read_text())
    historical=call('pane_status','--thread',attempt['thread_id'])
    old_window=raw({'command':'window_input','sequence':2,'request_id':'post-restart','data':'FORBIDDEN'},fault_window)
    old_operator=raw({'command':'pane_dispatch','thread':attempt['thread_id'],'body':'FORBIDDEN'},operator)
    current_dispatch=raw({'command':'pane_dispatch','thread':attempt['thread_id'],'body':'FORBIDDEN'},new_operator)
    verify('restart_is_unknown_without_replay_or_old_credentials',historical['state']=='unknown'
           and historical.get('historical') is True and historical['queued']==[]
           and old_window.get('error')=='invalid_window_identity'
           and old_operator.get('error')=='invalid_operator_identity'
           and current_dispatch.get('error')=='unknown_pane' and received()==old_bytes,
           '冷启动把历史窗格标 unknown；旧凭据被拒，当前管理凭据也不能重放历史 PTY',
           {'pane':historical,'old_window':old_window,'old_operator':old_operator,'current_dispatch':current_dispatch})
    (output/'input-failures-observed.bin').write_bytes(received())
