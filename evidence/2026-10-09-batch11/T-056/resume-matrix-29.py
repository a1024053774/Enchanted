import runpy,sys,json,time,sqlite3,subprocess,os
from pathlib import Path
out=Path(__file__).resolve().parent;label=sys.argv[1]
sys.argv=[str(out/'coverage-matrix-03.py'),label]
c=runpy.run_path(str(out/'coverage-matrix-03.py'));root=c['root'];results=c['results'];save=c['save'];rpc=c['rpc'];worker=c['worker'];ordinary=c['ordinary'];uid=c['uid'];now=c['now']
def inputs():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:return [json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
def interventions():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:return [json.loads(r[0]) for r in db.execute("SELECT details FROM events WHERE type='human_intervention' ORDER BY seq")]
# Seed a controlled failed delivery through the real repository, tied to a real intent event.
events=c['control']('events')
intent=next(e for e in reversed(events) if e['type']=='thread.turn-start-requested' and e['payload']['threadId']==ordinary)
seeded=c['control']('seed-delivery',sequence=intent['sequence'],thread=ordinary)
assert seeded
save('delivery-seed',dict(controlled_state=True,intent_event=intent,result=seeded,model_turns=0))
rpc('blockers',dict(threadId=ordinary),tag='orchestration.listProviderDeliveryBlockers')
frames=json.loads((results/'blockers.json').read_text())['messages'];exit=next(x for x in frames if x['_tag']=='Exit');blockers=exit['exit']['value']
assert blockers, 'fixture needs an actual delivery blocker'
blocker=blockers[0];req=dict(eventSequence=blocker['eventSequence'],threadId=ordinary,expectedState=blocker['state'],outcome='abandon',note='T056 收件请求 Ω')
checks=[]
for index in range(2):
 name='unblock-'+str(index+1);path=results/(name+'.input.json');path.write_text(json.dumps(req,ensure_ascii=False)+'\n')
 argv=['./a2a/scripts/bun','run',str(out/'native-rpc-02.mjs'),name,c['origin'],str(path)]
 before=inputs();r=subprocess.run(argv,cwd=c['fork'],env={**c['env'],'A2A_RPC_TAG':'orchestration.reconcileProviderDelivery'},capture_output=True,text=True)
 save(name+'.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
 after=inputs();new=[v for v in after if v['id'] not in {x['id'] for x in before}]
 checks.append(dict(case=name,expected_inputs=1,observed_inputs=len(new),business_exit=r.returncode,records=new,
  passed=len(new)==1 and new[0]['form']=='action' and new[0]['target']['thread']==ordinary and new[0]['target'].get('eventSequence')==req['eventSequence'] and new[0]['target']['project']=='t056-project' and new[0]['certainty']=='observed' and new[0]['source_ref']['rpc']=='orchestration.reconcileProviderDelivery'))
# Constructor evaluation proves that the actual automatic call sites carry origin.
path=results/'branch-calls.json';argv=['./a2a/scripts/bun','run',str(out/'branch-calls-28.mjs'),worker,str(path)]
r=subprocess.run(argv,cwd=c['fork'],env=c['env'],capture_output=True,text=True);save('branch-construction.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
for index,source in enumerate(json.loads(path.read_text())):
 before=interventions();command=source['command'];rpc('branch-derived-'+str(index+1),command);time.sleep(.15)
 matches=[v for v in inputs() if v['source_ref'].get('command_id')==command['commandId']]
 checks.append(dict(case='workspace-derived-'+str(index+1),source=source,records=matches,
  passed=command.get('origin')=='ui-derived' and len(matches)==1 and matches[0]['channel']=='ui-derived' and interventions()==before))
rpc('quit-project',dict(threadIds=[ordinary],continuationPrompt='继续 Ω'),tag='orchestration.prepareQuitResume')
quit=[v for v in inputs() if v['source_ref'].get('rpc')=='orchestration.prepareQuitResume']
checks.append(dict(case='ordinary-quit-project',records=quit,passed=len(quit)==1 and quit[0]['target']['project']=='t056-project' and quit[0]['channel']=='ui-derived'))
save('resume-oracle',dict(status='PASS' if all(x['passed'] for x in checks) else 'INCOMPLETE',checks=checks,baseline=c['summary']['fork'],provider_enabled=False,model_turns=0))
print([(x['case'],x['passed']) for x in checks]);assert all(x['passed'] for x in checks),'Decision 02 additions missing'
