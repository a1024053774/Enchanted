"""Offline I1 Messages protocol fixture and independent oracle; no processes."""
import argparse, json, uuid
from pathlib import Path
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
    if request['role']!=dispatch['role']:raise Refusal('role_mismatch')
    if request['dispatch_seq']!=dispatch['seq']:raise Refusal('global_dispatch_seq_mismatch')
    if request['dispatch_id']!=dispatch['id']:raise Refusal('dispatch_id_mismatch')
    if request['request_id']!=request['registered_request_id']:raise Refusal('request_id_mismatch')
    if request['messages'][-1]['content']!=dispatch['text']:raise Refusal('registered_text_mismatch')
    if request['attempt']!=binding['attempt'] or request['session']!=binding['session'] or request['fence']!=binding['fence']:raise Refusal('target_binding_mismatch')
    if len(request['messages'])>6:raise Refusal('message_budget_exhausted')
    sse=[{'type':'message_start','message':{'id':uid(),'role':'assistant'}},{'type':'content_block_delta','delta':{'type':'text_delta','text':'I1_ACK'}},{'type':'message_delta','usage':{'output_tokens':1}},{'type':'message_stop'}]
    return {'status':'PASS','request':request,'registered_dispatch':dispatch,'binding':binding,'response_sse':sse,'messages_used':1,'roots_used':1,'model_turns':0}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['text','seq','request','role','budget']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=True)
    try:r=run(a.mutant);result={'status':'PASS','mutant':a.mutant,'oracle':r,'scope':'offline I1 /v1/messages protocol only; no socket/API/CLI/daemon/target/model'}
    except Refusal as e:result={'status':'INCOMPLETE' if a.mutant is None else 'PASS','mutant':a.mutant,'error':str(e),'scope':'offline I1 protocol oracle; no processes'}
    (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'mutant':a.mutant,'error':result.get('error')}));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
