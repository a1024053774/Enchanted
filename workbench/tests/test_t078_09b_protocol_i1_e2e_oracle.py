"""Offline end-to-end I1 oracle using Claude's real queued inbox receipt shape."""
import argparse, json, shlex, uuid
from pathlib import Path
from t078_09b_protocol_core import ProtocolRefusal, normalize_anthropic_request, validate_request


def uid(): return str(uuid.uuid4())


def run(mutant=None):
    thread, attempt, request_id = uid(), uid(), uid()
    command_argv=['node','/workbench/bin/inbox','send','--from','executor','--to','executor','--kind','stop',
                  '--ref',f'thread:{thread}','--ref',f'attempt:{attempt}']
    tool_id=uid(); dispatch={'id':uid(),'seq':2,'role':'ideation','text':'⟦主控 #2⟧\nI1 queued stop','request_id':uid(),'stop_id':uid(),
        'attempt':attempt,'session':uid(),'fence':1,'tool_use':{'id':tool_id,'name':'Bash','input':{'command':shlex.join(command_argv)}},
        'tool_result':{'request_root':'/private/tmp/requests'}}
    registry={'dispatches':{dispatch['id']:dispatch},'message_budget':6,'ack_text':'I1_STOP_QUEUED'}
    first={'model':'claude-haiku-5-5','stream':True,'messages':[{'role':'user','content':dispatch['text']}]}
    normalized,_=normalize_anthropic_request(first,registry,'ideation');first_result=validate_request(normalized,registry)
    queued={'ok':True,'queued':True,'delivered':False,'request_id':request_id,'path':f'/private/tmp/requests/{request_id}.json'}
    if mutant=='missing-queue': queued={'ok':True,'entry':{'id':uid(),'from':'ideation','to':'executor','kind':'stop'}}
    if mutant=='wrong-request': queued['request_id']=uid()
    if mutant=='wrong-target': queued['path']='/private/tmp/foreign/request.json'
    second={'model':'claude-haiku-5-5','stream':True,'messages':[{'role':'user','content':dispatch['text']},
        {'role':'assistant','content':[{'type':'tool_use','id':tool_id,'name':'Bash','input':dispatch['tool_use']['input']}]},
        {'role':'user','content':[{'type':'tool_result','tool_use_id':tool_id,'content':json.dumps(queued)}]}]}
    try:
        normalized2,_=normalize_anthropic_request(second,registry,'ideation');second_result=validate_request(normalized2,registry)
        if mutant:
            return {'status':'INCOMPLETE','mutant':mutant,'decision':'200','error':'mutant accepted'}
    except ProtocolRefusal as error:
        return {'status':'PASS' if mutant else 'INCOMPLETE','mutant':mutant,'decision':'409','error':str(error)}
    stop={'id':uid(),'from':'ideation','to':'executor','kind':'stop','refs':[f'thread:{thread}',f'attempt:{attempt}',f'request:{request_id}']}
    return {'status':'PASS','stage':'I1','roots_used':1,'messages_used':2,'queued_receipt':queued,'stop_entry':stop,
            'relay':{'request_id':request_id,'from':'ideation','wake':'executor','delivered':True},
            'first_settlement':bool(first_result.get('tool_use')),'second_settlement':bool(second_result.get('settlement')),
            'scope':'offline shared core + queued relay oracle; no process/API/CLI'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['missing-queue','wrong-request','wrong-target']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);r=run(a.mutant);(a.output/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'mutant':a.mutant,'messages':r.get('messages_used',0)}));return 0
if __name__=='__main__':raise SystemExit(main())
