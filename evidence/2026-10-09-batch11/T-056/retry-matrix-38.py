import runpy,sys,json,time,sqlite3
from pathlib import Path
out=Path(__file__).resolve().parent;label=sys.argv[1];sys.argv=[str(out/'coverage-matrix-03.py'),label]
c=runpy.run_path(str(out/'coverage-matrix-03.py'));root=c['root'];rpc=c['rpc'];uid=c['uid'];now=c['now'];save=c['save'];control=c['control'];ordinary=c['ordinary']
# Use the latest actual user message in the authoritative read model.
# Use managed native tail and actual engine session state; no provider call.
ordinary=c['worker'];detail=control('thread',thread=ordinary)['value'];tail=next(m for m in reversed(detail['messages']) if m['role']=='user')
control('command',command=dict(type='thread.session.set',commandId=uid(),threadId=ordinary,session=dict(threadId=ordinary,status='running',providerName='codex',runtimeMode='approval-required',activeTurnId=uid(),lastError=None,updatedAt=now()),createdAt=now()))
# Checkpoint target has no in-flight turn and no prior checkpoint activity.
checkpoint=uid()
control('command',command=dict(type='thread.create',commandId=uid(),threadId=checkpoint,projectId='t056-project',title='checkpoint retry external sentinel',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='approval-required',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now()))
commands=[('edit-retry',dict(type='thread.message.edit-and-resend',commandId=uid(),threadId=ordinary,messageId=tail['id'],text='重试 Ω 外部哨兵',runtimeMode='approval-required',interactionMode='default',createdAt=now())),
 ('checkpoint-retry',dict(type='thread.checkpoint.revert',commandId=uid(),threadId=checkpoint,turnCount=0,scope='thread',createdAt=now()))]
checks=[]
for name,cmd in commands:
 rpc(name,cmd);rpc(name+'-duplicate',cmd);time.sleep(.2)
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:records=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
 matched=[r for r in records if r['source_ref'].get('command_id')==cmd['commandId']]
 events=control('events');domain=[e for e in events if e.get('commandId')==cmd['commandId']]
 checks.append(dict(case=name,input=cmd,records=matched,events=domain,passed=len(matched)==1 and matched[0]['form']=='action' and matched[0]['content']==cmd and matched[0]['target']['thread']==cmd['threadId'] and matched[0]['target']['project']=='t056-project' and matched[0]['target']['message']==cmd.get('messageId') and matched[0]['certainty']=='observed'))
save('retry-oracle',dict(status='PASS' if all(x['passed'] for x in checks) else 'INCOMPLETE',checks=checks,provider_enabled=False))
assert all(x['passed'] for x in checks),'Retry inputs missing from enum'

with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:gate_events=[dict(seq=row[0],time=row[1],task=row[2],attempt=row[3],type=row[4],details=json.loads(row[5])) for row in db.execute('SELECT seq,time,task,attempt,type,details FROM events ORDER BY seq')]
managed=checks[0]['records'][0];derived=[e for e in gate_events if e['type']=='human_intervention' and e['details'].get('input_id')==managed['id']]
assert len(derived)==1 and derived[0]['details']['message_id']==commands[0][1]['messageId']
save('retry-gate-events',gate_events)
