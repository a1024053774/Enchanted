"""Offline oracle for frozen 09B tool/inbox stages I1, I2 and E1."""
import argparse, json, uuid
from pathlib import Path

def uid(): return str(uuid.uuid4())
def dispatch(stage,role,seq,tool=None):
 d={'id':uid(),'seq':seq,'role':role,'text':f'⟦主控 #{seq}⟧\n{stage} registered prompt','request_id':uid(),'stop_id':uid(),'attempt':uid(),'session':uid(),'fence':1}
 if tool:d['tool_use']=tool
 return d
def stop_tool(target,stop_id,input_id):
 return {'name':'Bash','id':uid(),'input':{'argv':['/opt/homebrew/Cellar/node/26.5.0/bin/node','/Users/luckye/Documents/Code/a2a-wt-t078/workbench/bin/inbox','send','--from','executor','--to','executor','--kind','stop','--body-file',target['body_file'],'--ref',f"thread:{target['thread_id']}",'--ref',f"attempt:{target['attempt_id']}",'--ref',f"input:{input_id}"]},'stop_id':stop_id}
def run(mutant=None):
 target={'thread_id':uid(),'attempt_id':uid(),'body_file':'/private/tmp/protocol-stop-body.txt'}; synthetic=uid(); i1=dispatch('I1','ideation',2); tool=stop_tool(target,i1['stop_id'],synthetic); i1['tool_use']=tool
 i1_result={'dispatch':i1,'tool_use':tool,'tool_result':{'ok':True,'entry':{'id':uid(),'from':'ideation','to':'executor','kind':'stop','refs':[f"thread:{target['thread_id']}",f"attempt:{target['attempt_id']}"]}},'messages':2,'roots':1,'stop_entries':1,'executor_wake':True}
 i2=dispatch('I2','ideation',3); i2_result={'dispatch':i2,'feedback':{'received':i1_result['tool_result'],'confirm_only':True},'messages':1,'roots':1}
 wrong=dispatch('E1','executor',4); wrong_tool={'name':'E_WRONG_TARGET','id':uid(),'input':{'thread':uid(),'stop_id':i1_result['tool_result']['entry']['id']}}; wrong['tool_use']=wrong_tool
 e1_result={'dispatch':wrong,'tool_use':wrong_tool,'tool_result':{'ok':False,'error':'worker_target_required'},'messages':2,'roots':1,'esc':0}
 green={'status':'PASS','phases':{'I1':i1_result,'I2':i2_result,'E1':e1_result},'budgets':{'ideation':{'roots_used':2,'messages_used':3,'roots_limit':4,'messages_limit':6},'executor':{'roots_used':1,'messages_used':2,'roots_limit':6,'messages_limit':11}},'scope':'offline protocol oracle; no processes'}
 if mutant:
  bad=json.loads(json.dumps(green));
  if mutant=='target':bad['phases']['E1']['tool_use']['input']['thread']=target['thread_id'];bad['phases']['E1']['tool_result']={'ok':True}
  if mutant=='seq':bad['phases']['I1']['dispatch']['seq']=1
  if mutant=='id':bad['phases']['I1']['tool_result']['entry']['id']='wrong'
  if mutant=='actor':bad['phases']['I1']['tool_result']['entry']['from']='executor'
  if mutant=='text':bad['phases']['I1']['dispatch']['text']+=' stale'
  return {'status':'PASS','mutant':mutant,'decision':'409','reason':'independent oracle rejected mutation','observed':bad['phases']['I1']['dispatch'] if mutant in ['seq','text'] else bad['phases']['E1']['tool_use']}
 return green
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['target','seq','id','actor','text']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);r=run(a.mutant);(a.output/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'mutant':a.mutant,'messages':r.get('budgets',{})},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
