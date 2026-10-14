"""Worker credential → actual inbox client → request files → real Stop → gate.

No operator is substituted for the worker. Seeded incoming inbox data is marked
as a fixture input. No Claude CLI, Claude fixture or real Codex turn runs.
"""
from contextlib import closing
import datetime
import json
from pathlib import Path
import shutil
import sqlite3
import time


def receipts_for_launch(query,launch):
    # Journal keys are opaque and owned by a launch. Resolve both current and
    # historical receipts through their persisted request binding, not a prefix.
    request_ids={row['key']:row['request_id'] for row in query('relay_requests')
                 if row['launch']==launch and row['request_id'] is not None}
    return {request_ids[row['key']]:json.loads(row['data']) for row in query('relay_results')
            if row['key'] in request_ids}


def run_worker_inbox(*,source,repo,home,state,attempt,window,call,query,check,result,output):
    launch=json.loads(query('launch_records')[0]['data']);thread=attempt['thread_id'];address='worker:'+thread
    expected_failures={'worker_client_queues_inbox_commands','worker_issue_records_real_sender','worker_assign_spoof_denied',
        'worker_list_uses_real_scope','worker_ack_is_owned_and_idempotent','worker_ready_is_role_denied',
        'worker_foreign_ack_is_denied','worker_stop_receipts_are_delivered_once','revoked_worker_inbox_is_rejected'}
    def verify(name,passed,expected,observed):
        check(name,passed,expected,observed)
        if not passed and name not in expected_failures:raise AssertionError(name)
    def wait_for(predicate,description):
        end=time.monotonic()+10
        while not predicate():
            if time.monotonic()>=end:raise RuntimeError('Fixture deadline: '+description)
            time.sleep(.025)
    def rows(table):return [json.loads(row['data']) for row in query(table)]
    def stop(n,turn):
        wait_for(lambda:(home/f'turn-{turn}.ready').exists(),'native turn')
        session=json.loads((home/'receiver-started.json').read_text())['native_session']
        pending=home/f'hook-{n}.pending'
        pending.write_text(json.dumps({'session_id':session,'hook_event_name':'Stop','turn_id':f'turn-{turn}'})+'\n')
        pending.rename(home/f'hook-{n}.json')
        wait_for(lambda:(home/f'hook-{n}.exit').exists(),'Stop return')
        if (home/f'hook-{n}.exit').read_text().strip()!='0':raise RuntimeError('Stop fixture rejected; inspect hook stdout/stderr')

    # This endpoint constructs records only. Absent executable paths must never
    # be invoked. The live worker is the only process/pane created by the host.
    plans=[call('controller_prepare','--task',launch['task'],'--preset',preset)['prepared'] for preset in ['ideation','executor']]
    started=[row for row in query('orchestration_events') if row['type']=='pane_started']
    verify('controller_prepare_is_static',len(started)==1 and all(row['attempt'] is None and row['execution_state']=='prepared'
        and row['cli_version']=='unknown' and row['validation']=='待真实 Claude 复核' for row in plans)
        and all(call('pane_status','--thread',row['thread'])['lifecycle']=='not_started' for row in plans),
        '两条静态主控启动计划入库；实际只启动一个 worker 接收器；Claude 不启动',plans)
    # A valid ready ticket lets the permission mutant expose an actual forbidden
    # read, rather than fail later because the requested fixture data is absent.
    tickets=repo/'.project-map/tickets';tickets.mkdir(parents=True)
    (tickets/'W-READY.md').write_text('---\nid: W-READY\ntitle: Worker must not list this ready ticket\ntype: build\nstatus: open\nclaimed_by:\nblocked_by: []\nready: yes\nready_by: executor\nready_rev: 1\n---\n',encoding='utf-8')
    result['ready_fixture']=str(tickets/'W-READY.md')
    incoming=[{'id':'seed-issue','schema':1,'kind':'issue','from':address,'to':'triage','title':'固定问题',
               'body':'固定问题','blocking':False,'reply_to':None,'refs':[],
               'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}]
    for ident,target in [('owned-message',address),('visible-message',address),('foreign-message','worker:other-thread')]:
        incoming.append({'id':ident,'schema':1,'kind':'disposition','from':'executor','to':target,'action':'snooze',
                         'body':'固定入站处置 '+ident,'reply_to':'seed-issue','refs':[],
                         'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with closing(sqlite3.connect(state/'state.sqlite3')) as db:
        for entry in incoming:db.execute('INSERT INTO inbox_records(id,data) VALUES (?,?)',(entry['id'],json.dumps(entry,ensure_ascii=False)))
        db.commit()
    result['seeded_inbox_inputs']={'origin':'test fixture input; not an authenticated controller send','entries':incoming}
    body='WORKER_ISSUE 中文 𐐀\n';body_file=home/'worker-body.txt';body_file.write_text(body,encoding='utf-8')
    commands=[
        {'name':'issue','args':['send','--kind','issue','--to','triage','--from','ideation','--title','WORKER_REAL_CLIENT','--body-file',str(body_file)]},
        {'name':'assign','args':['send','--kind','assign','--to','executor','--from','ideation','--body-file',str(body_file)]},
        {'name':'list','args':['list','--role','ideation']},
        {'name':'ack-one','args':['ack','--id','owned-message','--role','user']},
        {'name':'ack-two','args':['ack','--id','owned-message','--role','user']},
        {'name':'ready','args':['ready','--project','t078-fixture']},
        {'name':'ack-foreign','args':['ack','--id','foreign-message','--role','user']},
    ]
    (home/'worker-client-plan-1.json').write_text(json.dumps({'client':str(source/'workbench/bin/inbox'),'commands':commands}),encoding='utf-8')
    shutil.copyfile(source/'workbench/tests/t078_worker_inbox_client.mjs',home/'worker-client.mjs')
    inputs_before=rows('user_inputs');(home/'client-1.request').write_text('Run the real worker inbox client once\n')
    wait_for(lambda:(home/'client-1.exit').exists(),'worker client completion')
    if (home/'client-1.exit').read_text().strip()!='0':raise RuntimeError('Worker client harness failed; not product red evidence')
    client=json.loads((home/'worker-client-result-1.json').read_text());result['worker_client']=client
    queued={item['name']:item['response'].get('request_id') for item in client['commands'] if item['response'].get('queued') is True}
    bindings=[]
    for item in client['commands']:
        if item['response'].get('queued') is True:
            packet=json.loads(Path(item['response']['path']).read_text())
            bindings.append(packet['task']==launch['task'] and packet['attempt']==attempt['attempt_id']
                            and packet['session']==attempt['session_id'] and packet['fence']==attempt['fence'])
    verify('worker_client_queues_inbox_commands',len(queued)==7 and all(bindings)
           and client['identity']['launch']==launch['id'] and not client['identity']['operator_credential_present'],
           '七个真实 worker 客户端调用均由会话身份写请求文件，不借 operator、不提前声称送达',client)
    stop(1,2);wait_for(lambda:(home/'turn-3.ready').exists(),'initial prompt after Stop')
    receipts=receipts_for_launch(query,launch['id'])
    def reply(name):return receipts.get(queued.get(name,''),{})
    all_inbox=rows('inbox_records');issue=[entry for entry in all_inbox if entry.get('title')=='WORKER_REAL_CLIENT']
    verify('worker_issue_records_real_sender',len(issue)==1 and issue[0]['from']==address and issue[0]['body']==body
           and reply('issue').get('entry',{}).get('id')==issue[0]['id'] and rows('user_inputs')==inputs_before,
           '实际 worker 身份写 issue；from=ideation 不生效；正文原样，客户端调用不算用户输入',reply('issue'))
    verify('worker_assign_spoof_denied',reply('assign').get('error')=='invalid_direction' and not any(x['kind']=='assign' for x in all_inbox),
           '越权 assign 在真实角色门禁拒绝，而非客户端一律禁止命令',reply('assign'))
    listed=reply('list').get('entries',[])
    verify('worker_list_uses_real_scope',reply('list').get('ok') is True and any(x['entry']['id']=='visible-message' for x in listed)
           and all(x['entry']['to']==address for x in listed),
           '忽略伪造 role=ideation；至少看到未确认的本人条目，不泄露他人条目',reply('list'))
    acks=[x for x in all_inbox if x['kind']=='ack' and x['reply_to']=='owned-message']
    verify('worker_ack_is_owned_and_idempotent',len(acks)==1 and acks[0]['from']==address
           and reply('ack-one').get('entry',{}).get('id')==reply('ack-two').get('entry',{}).get('id')==acks[0]['id'],
           '本人条目两次 ack 只有一条记录；role=user 不改变来源',{'first':reply('ack-one'),'second':reply('ack-two')})
    verify('worker_ready_is_role_denied',reply('ready').get('error')=='controller_required',
           'ready 已转交后台，按真实 worker 角色拒绝',reply('ready'))
    verify('worker_foreign_ack_is_denied',reply('ack-foreign').get('error')=='recipient_required'
           and not any(x['kind']=='ack' and x['reply_to']=='foreign-message' for x in all_inbox),
           '不能确认另一 worker 的条目',reply('ack-foreign'))
    stop(2,3)
    gate_dispatches=[row for row in query('dispatch_records') if json.loads(row['data'])['source']=='gate']
    if gate_dispatches:wait_for(lambda:(home/'turn-4.ready').exists(),'receipt turn')
    before=(home/'received.bin').read_bytes();stop(3,3)
    call('pane_status','--thread',thread)
    after=(home/'received.bin').read_bytes()
    gate_after=[row for row in query('dispatch_records') if json.loads(row['data'])['source']=='gate']
    verify('worker_stop_receipts_are_delivered_once',len(queued)==7 and len(gate_dispatches)==1 and len(gate_after)==1
           and all(ident.encode() in before for ident in queued.values()) and after==before,
           'Stop 转交真实请求并把七份回执写回 worker；重复旧 Stop 不重发',
           {'relay_result_count':len(receipts),'gate_dispatch_count':len(gate_after),'byte_count':len(after)})
    # Start one explicitly simulated input turn, then revoke its attempt while
    # the owned foreground process remains alive. This checks revocation at
    # transfer time, rather than just whether a capability string is present.
    next_turn=1+max(int(path.stem.split('-')[1]) for path in home.glob('turn-*.ready'))
    window.call('terminal-input',paste='REVOKE_PROBE',submit=True)
    wait_for(lambda:(home/f'turn-{next_turn}.ready').exists(),'turn before revocation')
    call('revoke','--task',launch['task'],'--reason','T078 isolated credential revocation probe')
    stale_commands=[{'name':'stale-issue','args':['send','--kind','issue','--to','triage','--title','MUST_NOT_APPEND_AFTER_REVOKE','--body-file',str(body_file)]}]
    (home/'worker-client-plan-2.json').write_text(json.dumps({'client':str(source/'workbench/bin/inbox'),'commands':stale_commands}),encoding='utf-8')
    (home/'client-2.request').write_text('Run revoked worker client once\n')
    wait_for(lambda:(home/'client-2.exit').exists(),'revoked worker client')
    if (home/'client-2.exit').read_text().strip()!='0':raise RuntimeError('Revocation client harness failed')
    stale_client=json.loads((home/'worker-client-result-2.json').read_text());result['revoked_worker_client']=stale_client
    stop(4,next_turn)
    stale_id=stale_client['commands'][0]['response'].get('request_id')
    stale_results=receipts_for_launch(query,launch['id'])
    stale_reply=stale_results.get(str(stale_id),{})
    verify('revoked_worker_inbox_is_rejected',stale_reply.get('error')=='stale_attempt'
           and not any(item.get('title')=='MUST_NOT_APPEND_AFTER_REVOKE' for item in rows('inbox_records')),
           '原 worker 凭据仍存在时，已撤销 attempt 的新请求必须在后台拒绝，不追加 inbox',stale_reply)
    (output/'worker-inbox-observed.bin').write_bytes((home/'received.bin').read_bytes())
