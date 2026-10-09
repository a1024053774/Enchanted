import runpy,sys,json,time,sqlite3
from pathlib import Path
out=Path(__file__).resolve().parent;label=sys.argv[1];sys.argv=[str(out/'coverage-matrix-03.py'),label]
c=runpy.run_path(str(out/'coverage-matrix-03.py'));root=c['root'];rpc=c['rpc'];uid=c['uid'];now=c['now'];save=c['save'];control=c['control'];ordinary=c['ordinary']
# Use the latest actual user message in the authoritative read model.
detail=control('thread',thread=ordinary)['value'];tail=next(m for m in reversed(detail['messages']) if m['role']=='user')
commands=[('edit-retry',dict(type='thread.message.edit-and-resend',commandId=uid(),threadId=ordinary,messageId=tail['id'],text='重试 Ω 外部哨兵',runtimeMode='approval-required',interactionMode='default',createdAt=now())),
 ('checkpoint-retry',dict(type='thread.checkpoint.revert',commandId=uid(),threadId=c['controller'],turnCount=0,scope='thread',createdAt=now()))]
checks=[]
for name,cmd in commands:
 rpc(name,cmd);time.sleep(.2)
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:records=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
 matched=[r for r in records if r['source_ref'].get('command_id')==cmd['commandId']]
 events=control('events');domain=[e for e in events if e.get('commandId')==cmd['commandId']]
 checks.append(dict(case=name,input=cmd,records=matched,events=domain,passed=len(matched)==1 and matched[0]['form']=='action' and matched[0]['content']==cmd))
save('retry-oracle',dict(status='PASS' if all(x['passed'] for x in checks) else 'INCOMPLETE',checks=checks,provider_enabled=False))
assert all(x['passed'] for x in checks),'Retry inputs missing from enum'
