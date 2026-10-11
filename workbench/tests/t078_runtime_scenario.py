"""Extend the input tracer bullet through the real pane runtime.

Known gap for the first red run: the window has no user-release control.
Other contract failures stop the checkpoint. Incoming issue/stop rows are
explicit persisted fixture inputs, not evidence of an authenticated sender.
Only the target byte receiver and its real hook CLI run; no Claude fixture.
"""
from contextlib import closing
import datetime
import json
import socket
import sqlite3
import time
import uuid


def run_runtime(*, home, state, attempt, window, call, query, check, result, output, credential):
    thread = attempt['thread_id']
    launch = json.loads(query('launch_records')[0]['data'])
    started = json.loads((home/'receiver-started.json').read_text())
    model_scope = '原生字节接收器及 Codex 形状的最小日志；不是 Codex 或 Claude 验收'
    result['runtime_scope'] = model_scope
    result['seeded_inbox_inputs'] = []

    def wait_for(predicate, description):
        deadline = time.monotonic()+10
        while not predicate():
            if time.monotonic() >= deadline:
                raise RuntimeError('Fixture deadline: '+description)
            time.sleep(0.025)

    def bytes_now():
        return (home/'received.bin').read_bytes()

    def rows(table):
        return [json.loads(row['data']) for row in query(table)]

    def verify(name, passed, expected, observed):
        check(name, passed, expected, observed)
        if not passed and name != 'window_user_release_available':
            raise AssertionError(name)

    def raw(input_value, identity):
        # Capability values are never written to command/evidence output.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(20)
            connection.connect(str(state/'control.sock'))
            connection.sendall((json.dumps({'id':str(uuid.uuid4()), 'identity':identity, 'input':input_value})+'\n').encode())
            buffer = b''
            while b'\n' not in buffer:
                chunk = connection.recv(65536)
                if not chunk:
                    raise RuntimeError('Daemon closed before a complete response')
                buffer += chunk
            return json.loads(buffer.split(b'\n', 1)[0])

    operator = json.loads(credential.read_text())
    # Only incoming data is seeded. The actual ack/delivery/stop operations
    # below go through authenticated production commands and never edit rows.
    def seed(kind, sender, ident):
        entry = {'schema':1,'id':ident,'kind':kind,'from':sender,'to':'triage' if kind=='issue' else 'executor',
                 'body':'T078 固定运行时输入 '+ident,'title':ident,'blocking':False,
                 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'reply_to':None,'refs':['thread:'+thread,'attempt:'+attempt['attempt_id']]}
        with closing(sqlite3.connect(state/'state.sqlite3')) as db:
            db.execute('INSERT INTO inbox_records(id,data) VALUES (?,?)',(ident,json.dumps(entry,ensure_ascii=False)))
            db.commit()
        result['seeded_inbox_inputs'].append({'entry':entry,'origin':'test fixture insertion, not a role credential'})

    hook_number = 0
    def stop(turn):
        nonlocal hook_number
        wait_for(lambda:(home/f'turn-{turn}.ready').exists(), 'receiver turn '+str(turn))
        hook_number += 1
        payload = {'session_id':started['native_session'],'hook_event_name':'Stop','turn_id':f'turn-{turn}'}
        temporary = home/f'hook-{hook_number}.pending'
        temporary.write_text(json.dumps(payload)+'\n')
        temporary.rename(home/f'hook-{hook_number}.json')
        wait_for(lambda:(home/f'hook-{hook_number}.exit').exists(),'hook completion')
        code = int((home/f'hook-{hook_number}.exit').read_text())
        if code != 0:
            raise RuntimeError({'hook_exit':code,'stdout':(home/f'hook-{hook_number}.stdout').read_text(),
                                'stderr':(home/f'hook-{hook_number}.stderr').read_text()})

    info = call('pane_process_info','--thread',thread)
    verify('native_receiver_foreground_identity', info['leader'] == started['pid'] and not info['failed'],
           '真实 ps 的前台领导进程必须是本次原生接收器', info)

    # The original input slice submitted two CRs. End only the second turn;
    # this releases the initial registered task prompt as turn 3.
    inputs_before = rows('user_inputs')
    before = bytes_now()
    stop(2)
    wait_for(lambda:(home/'turn-3.ready').exists(),'initial dispatch turn')
    after_initial = bytes_now()
    injected = after_initial[len(before):]
    verify('registered_injection_is_not_user_input', after_initial.startswith(before)
           and injected.startswith('\x1b[200~⟦主控 #1⟧\n仅收集输入字节，不运行任何模型或工具。\n'.encode())
           and injected.endswith(b'\x1b[201~\r') and rows('user_inputs') == inputs_before,
           '已登记任务提示以独立角色卡开头，使用 paste 和单独 CR；不新增用户输入',
           {'before_bytes':len(before),'after_bytes':len(after_initial)})

    seed('issue','worker:'+thread,'runtime-issue-1')
    queued = call('inbox_send','--to','worker:'+thread,'--kind','disposition','--reply-to','runtime-issue-1',
                  '--action','snooze','--body','RUNTIME_DISPOSITION_ONE')
    verify('runtime_wake_queues_while_busy', queued['delivery']['state']=='queued' and bytes_now()==after_initial,
           '忙时只有一条待送达记录，不写 PTY', queued)
    stop(3)
    wait_for(lambda:(home/'turn-4.ready').exists(),'wake turn')
    after_wake = bytes_now()
    marked = ('\x1b[200~⟦主控 #2⟧\n收件箱 disposition '+queued['entry']['id']+'\nRUNTIME_DISPOSITION_ONE\x1b[201~\r').encode()
    submissions = [row for row in rows('orchestration_events') if row.get('dispatch')==queued['delivery']['message']]
    verify('runtime_wake_reaches_pty', after_wake==after_initial+marked
           and rows('user_inputs')==inputs_before,
           'Stop 后将指定收件箱处置按固定正文送达 PTY；注入不算用户输入',
           {'entry':queued['entry'],'submission_events':submissions})

    window.call('terminal-key',key='Escape')
    wait_for(lambda:len(bytes_now())>=len(after_wake)+1,'window Esc')
    seed('issue','worker:'+thread,'runtime-issue-2')
    queued2 = call('inbox_send','--to','worker:'+thread,'--kind','disposition','--reply-to','runtime-issue-2',
                   '--action','snooze','--body','RUNTIME_DISPOSITION_AFTER_ESC')
    stop(4)
    held = call('pane_status','--thread',thread)
    verify('late_stop_keeps_queue_held', bytes_now()==after_wake+b'\x1b' and held['state']=='busy'
           and held['interrupted'] is True and queued2['delivery']['message'] in held['queued'],
           'Esc 后迟到 Stop 不放出排队消息',held)
    # This is a user-visible control contract, not a direct Panes call.
    release = window.call('queue-release')
    if release.get('clicked'):
        wait_for(lambda:(home/'turn-5.ready').exists(),'released wake turn')
    actions = [item for item in rows('user_inputs') if item['form']=='action'
               and item.get('content',{}).get('action')=='queue-release']
    verify('window_user_release_available', release.get('clicked') is True and len(actions)==1,
           '窗口提供显式放行，放行记一次用户 action，随后队首送达',
           {'control':release,'release_actions':actions})

    seed('stop','ideation','runtime-stop')
    before_interrupt = bytes_now()
    stopped = raw({'command':'stop','thread':thread,'stop_id':'runtime-stop','actor':'user'},operator)
    wait_for(lambda:len(bytes_now())>=len(before_interrupt)+1,'gate Esc')
    after_stop = call('pane_process_info','--thread',thread)
    acknowledged = raw({'command':'inbox_ack','id':'runtime-stop','role':'user'},operator)
    task_after = call('status','--task',launch['task'])['task']
    audit = [json.loads(row['details']) for row in query('events') if row['type']=='emergency_interrupt_requested']
    verify('runtime_stop_uses_credential_and_only_esc', stopped.get('ok') is True
           and bytes_now()==before_interrupt+b'\x1b' and after_stop['leader']==started['pid']
           and not after_stop['failed'] and not task_after['current_attempt']['reclaimed']
           and len(audit)==1 and audit[0]['actor']=='executor'
           and acknowledged.get('entry',{}).get('from')=='executor' and acknowledged['entry']['kind']=='ack',
           '执行主控仅向目标 PTY 写 Esc 后追加 ack；伪造角色无效，不回收、不关窗格',
           {'response':stopped,'ack':acknowledged,'process':after_stop,'audit':audit,'task_state':task_after['state']})

    # Large paste, followed immediately by close. The driver waits only for
    # the DOM paste handler, not the daemon; production close drains admitted IPC.
    phrase = '中文组合与关闭期间的大段粘贴\n'*1200
    before_close = bytes_now()
    window.call('capture',name='runtime-before-close')
    window.call('terminal-input',paste=phrase,submit=False)
    window.close()
    result['runtime_window_closed'] = True
    expected_close = ('\x1b[200~'+phrase.replace('\n','\r')+'\x1b[201~').encode()
    wait_for(lambda:len(bytes_now())>=len(before_close)+len(expected_close),'pending paste after close')
    inputs = [item for item in rows('user_inputs') if item['text']==phrase and item['form']=='message']
    verify('close_waits_for_large_paste', bytes_now()==before_close+expected_close and len(inputs)==1,
           '立即关窗口后仍完整写出已接收粘贴，且只记录一次',
           {'expected_bytes':len(expected_close),'actual_bytes':len(bytes_now())-len(before_close),'input_count':len(inputs)})
    (output/'runtime-observed.bin').write_bytes(bytes_now())
    return True  # The window is already closed; do not close its streams twice.
