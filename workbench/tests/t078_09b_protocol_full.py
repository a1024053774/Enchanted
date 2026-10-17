"""Offline full I1-I4/E1-E6 protocol oracle; no processes."""
import argparse,json,uuid
from pathlib import Path
class Refusal(ValueError):pass
def run(mutant=None):
 seq=0;roles={'ideation':{'roots':0,'messages':0,'limit':6},'executor':{'roots':0,'messages':0,'limit':11}};rows=[]
 for stage in ['I1','I2','I3','I4','E1','E2','E3','E4','E5','E6']:
  role='ideation' if stage.startswith('I') else 'executor';seq+=1;dispatch={'seq':seq,'id':str(uuid.uuid4()),'role':role,'text':f'⟦门禁 #{seq}⟧\n{stage} registered prompt','attempt':str(uuid.uuid4()),'session':str(uuid.uuid4()),'fence':1,'request_id':str(uuid.uuid4()),'stop_id':str(uuid.uuid4())};req={'dispatch_seq':dispatch['seq'],'dispatch_id':dispatch['id'],'role':role,'attempt':dispatch['attempt'],'session':dispatch['session'],'fence':1,'request_id':dispatch['request_id'],'stop_id':dispatch['stop_id'],'messages':[{'role':'user','content':dispatch['text']}]}
  if mutant=='seq' and stage=='E1':req['dispatch_seq']=1
  if mutant=='text' and stage=='I2':req['messages'][0]['content']+=' stale'
  if mutant=='identity' and stage=='E2':req['attempt']=''
  if mutant=='role' and stage=='E3':req['role']='ideation'
  if req['dispatch_seq']!=dispatch['seq']:raise Refusal('global_dispatch_seq_mismatch')
  if req['messages'][-1]['content']!=dispatch['text']:raise Refusal('registered_text_mismatch')
  if req['role']!=role or not req['attempt']:raise Refusal('identity_or_role_mismatch')
  roles[role]['roots']+=1;roles[role]['messages']+=1
  if roles[role]['messages']>roles[role]['limit']:raise Refusal('messages_budget_exhausted')
  rows.append({'stage':stage,'seq':seq,'request':req,'sse':[{'type':'message_start'},{'type':'content_block_delta','text':stage+'_ACK'},{'type':'message_stop'}]})
 return {'stages':rows,'budgets':roles,'dispatch_seq':seq}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['seq','text','identity','role']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=True)
 try:r=run(a.mutant);out={'status':'PASS','mutant':a.mutant,'oracle':r,'scope':'offline full I1-I4/E1-E6 registered dispatch/SSE; no processes'}
 except Refusal as e:out={'status':'PASS' if a.mutant else 'INCOMPLETE','mutant':a.mutant,'error':str(e),'scope':'offline protocol oracle; no processes'}
 (a.output/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':out['status'],'mutant':a.mutant,'error':out.get('error')}));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
