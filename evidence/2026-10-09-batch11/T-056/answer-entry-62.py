import json,runpy,sqlite3,subprocess,sys,time
from pathlib import Path
out=Path(__file__).resolve().parent;label=sys.argv[1];sys.argv=[str(out/'coverage-matrix-03.py'),label]
c=runpy.run_path(str(out/'coverage-matrix-03.py'));control=c['control'];save=c['save'];worker=c['worker'];uid=c['uid'];now=c['now']
request=uid();activity=dict(id=uid(),tone='info',kind='user-input.requested',summary='受控 provider 请求 Ω',payload=dict(requestId=request,questions=[dict(id='colour',header='颜色',question='选择隔离哨兵颜色',options=[dict(label='紫色',description='外部哨兵')])]),turnId=None,createdAt=now())
control('command',command=dict(type='thread.activity.append',commandId=uid(),threadId=worker,activity=activity,createdAt=now()))
pending=control('pending',thread=worker);save('pending-before-answer',pending)
matched=[r for r in pending if r['requestId']==request and r['threadId']==worker]
assert len(matched)==1 and matched[0]['status']=='pending',matched
command=dict(type='thread.user-input.respond',commandId=uid(),threadId=worker,requestId=request,answers={'colour':'紫色 Ω 真实入口'},createdAt=now())
c['rpc']('managed-structured-answer',command);c['rpc']('managed-structured-answer-duplicate',command);time.sleep(.3)
with sqlite3.connect(c['root']/'userdata/a2a-gates/state.sqlite3') as db:
 inputs=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
 events=[dict(seq=r[0],time=r[1],task=r[2],attempt=r[3],type=r[4],details=json.loads(r[5])) for r in db.execute('SELECT seq,time,task,attempt,type,details FROM events ORDER BY seq')]
records=[v for v in inputs if v['source_ref'].get('command_id')==command['commandId']]
assert len(records)==1 and records[0]['form']=='answer' and records[0]['target']['request']==request and records[0]['target']['message'] is None
interventions=[e for e in events if e['type']=='human_intervention' and e['details'].get('input_id')==records[0]['id']]
assert len(interventions)==1 and interventions[0]['details']['message_id'] is None
fixture=dict(task='t056',attempt=records[0]['target']['attempt'],request=request,event=interventions[0],events=events,command=command,input=records[0],pending_before=matched,controlled_provider_state=True,new_model_turns=0)
save('structured-answer-fixture',fixture)
argv=['./a2a/scripts/bun','run',str(out/'answer-projection-62.mjs'),str(c['fork']/'apps/web/src/a2a/humanIntervention.ts'),str(c['results']/'structured-answer-fixture.json')]
r=subprocess.run(argv,cwd=c['fork'],env=c['env'],capture_output=True,text=True)
save('projection-command',dict(argv=argv,cwd=str(c['fork']),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
save('answer-oracle',dict(status='PASS' if r.returncode==0 else 'INCOMPLETE',source_revision=c['summary']['fork'],request=request,input=records[0],intervention=interventions[0],projection_exit=r.returncode,signal='real managed WS receipt and persisted derived event handed to actual web parser'))
assert r.returncode==0,'Managed structured answer failed actual display parser'
print('PASS managed answer receipt, derivation and display; broad-answer mutants detectable')
