import json
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
base=Path('/Users/luckye/Library/Application Support/a2a-orchestrator')
runs=[('merge',base/'worktrees/a2a/T-257-1-a3-verify-1/evidence/2026-11-08-batch34/T-257/worker/t257-20261108T130249-ee4fa75ad61d482ab3748509c9e24f98.json',True),('base',base/'verification/46ec2429-ac82-48d0-9016-9e90aa43c946-red-base-1/evidence/2026-11-08-batch34/T-257/worker/t257-20261108T130301-943e72e8c5a74b92b25b0299c1b48a33.json',False),('candidate',base/'verification/46ec2429-ac82-48d0-9016-9e90aa43c946-red-candidate-1/evidence/2026-11-08-batch34/T-257/worker/t257-20261108T130330-e631b17fcbbd4769aa227a18f7c65fb7.json',True)]
result=[]
date=lambda s:datetime.fromisoformat(s.replace('Z','+00:00'))
for label,path,fixed in runs:
 d=json.loads(path.read_text()); rows=d['timeline']; hooks=d['hook_timeline']; obs=d['observed']
 starts=[r for r in rows if r['type']=='turn_start_signal']
 turn,session=starts[0]['turn'],starts[0]['session']
 assert starts[1]['turn']==turn and starts[1]['session']==session
 receipt=obs['receipt_submitted']
 released=next(h for h in hooks if h['hook']=='Stop' and h['kind']=='hook_release')
 assert date(receipt['time'])<date(released['time'])<date(starts[1]['time'])
 native_starts=[r for r in rows if r.get('native_type')=='task_started' and r['seq']<=starts[1]['seq']]
 assert len(native_starts)==1 and native_starts[0]['turn']==turn
 second=next(r for r in rows if r['type']=='turn_end_signal' and r['turn']==turn and r['seq']>starts[1]['seq'])
 complete=next(r for r in rows if r.get('native_type')=='task_complete' and r['turn']==turn and r['seq']>second['seq'])
 for k in ('reclaim_initial_working','reclaim_continuation_working'):
  assert obs[k]['ok'] is False and obs[k]['error']=='worker_working'
 follow=obs['queued_during_continuation']['queued']; assert len(follow)==1
 delivered=[r for r in rows if r['type']=='turn_submitted' and r.get('dispatch')==follow[0]]
 proc=[r for r in rows if r['type']=='relay_processed']; assert len(proc)==4 and all(r['key'] and r['result']['ok'] for r in proc) and len({r['key'] for r in proc})==4
 final=obs['final_pane_before_reclaim']; reclaimed=obs['reclaim_after_native_complete']
 markers=[r for r in d['api']['phases'] if r['phase']=='queued-marker']
 if fixed:
  assert final['state']=='idle' and not final['active'] and not final['queued'] and not final['interrupted'] and not final['failed'] and not final['writing']
  assert reclaimed['ok'] is True and len(delivered)==1 and delivered[0]['seq']>second['seq']
  assert len(markers)==1 and markers[0]['marker'].startswith('T257-queued-') and len(markers[0]['marker'])>12
  assert starts[-1]['turn']!=turn and any(r.get('native_type')=='task_complete' and r['turn']==starts[-1]['turn'] and r['seq']>starts[-1]['seq'] for r in rows)
  assert any(r['type']=='pane_idle' and r.get('stop_turn')==turn and r['seq']>second['seq'] for r in rows)
 else:
  assert final['state']=='busy' and follow[0] in final['queued'] and reclaimed['error']=='worker_working' and not delivered and not markers
 assert d['source_worktree_status']=='' and d['api']['error'] is None and d['cleanup']['processes_stopped'] is True and d['cleanup']['core']['exit']==0
 result.append(dict(run=label,path=str(path),source=d['source_head'],same_turn=turn,receipt_seq=receipt['seq'],receipt_time=receipt['time'],first_stop_release=released['time'],second_ups=starts[1]['seq'],second_stop=second['seq'],native_complete=complete['seq'],final_state=final['state'],queued_deliveries=len(delivered),reclaim=reclaimed,status='PASS: independent evidence readback',scope='审查已有本候选门禁实测，不是 reviewer 新跑 CLI'))
with (ROOT/'reviewer-checks/gate-evidence-readback.json').open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
for row in result: print(json.dumps(row,ensure_ascii=False))
