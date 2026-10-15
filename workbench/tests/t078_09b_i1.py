"""Offline I1 Messages protocol fixture and independent oracle; no processes."""
import argparse, json, uuid
from pathlib import Path
from t078_09b_protocol_core import validate_request
class Refusal(ValueError): pass
def uid(): return str(uuid.uuid4())
def run(mutant=None):
    binding={'task':'t078-09b-runtime-I1','attempt':uid(),'session':uid(),'fence':1,'thread':uid(),'workspace':'/private/tmp/t078-I1','role':'ideation','launch':uid()}
    dispatch={'seq':1,'id':uid(),'text':'⟦门禁 #1⟧\nI1 registered ideation prompt','role':'ideation','launch':binding['launch']}
    request={'path':'/v1/messages','request_id':uid(),'registered_request_id':None,'dispatch_seq':dispatch['seq'],'dispatch_id':dispatch['id'],'stop_id':uid(),'role':'ideation','attempt':binding['attempt'],'session':binding['session'],'fence':binding['fence'],'messages':[{'role':'user','content':dispatch['text']}],'stream':True,'model':'claude-haiku-5-5'};request['registered_request_id']=request['request_id']
    if mutant=='text':request['messages'][0]['content']+=' stale'
    if mutant=='seq':request['dispatch_seq']=2
    if mutant=='request':request['request_id']=uid(); request['registered_request_id']='other'
    if mutant=='role':request['role']='executor'
    if mutant=='budget':request['messages']=[{'role':'user','content':dispatch['text']} for _ in range(7)]
    dispatch['request_id']=request['registered_request_id'];dispatch.update(attempt=binding['attempt'],session=binding['session'],fence=1)
    protocol=validate_request(request,{'dispatches':{dispatch['id']:dispatch},'message_budget':6,'ack_text':'I1_ACK'});sse=protocol['sse']
    return {'status':'PASS','request':request,'registered_dispatch':dispatch,'binding':binding,'response_sse':sse,'messages_used':1,'roots_used':1,'model_turns':0}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['text','seq','request','role','budget']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=True)
    try:r=run(a.mutant);result={'status':'PASS','mutant':a.mutant,'oracle':r,'scope':'offline I1 /v1/messages protocol only; no socket/API/CLI/daemon/target/model'}
    except Refusal as e:result={'status':'INCOMPLETE' if a.mutant is None else 'PASS','mutant':a.mutant,'error':str(e),'scope':'offline I1 protocol oracle; no processes'}
    (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'mutant':a.mutant,'error':result.get('error')}));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
