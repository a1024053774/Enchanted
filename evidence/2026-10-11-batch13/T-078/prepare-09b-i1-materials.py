"""Generate I1 material and approval draft from real Stage-A and B1 P1 inputs."""
import argparse,json,shutil
from pathlib import Path

def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage-a',type=Path,required=True);p.add_argument('--p1',type=Path,required=True);p.add_argument('--prompt-file',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 stage=a.stage_a.resolve();p1=a.p1.resolve();out=a.output.resolve();assert not out.exists()
 ready=json.loads((stage/'readiness.json').read_bytes());inp=json.loads((p1/'input.json').read_bytes());manifest=json.loads((p1/'approval.json').read_bytes())
 assert ready['status']=='READY_FOR_APPROVAL' and ready['stage']=='A' and ready['roles_started']==[]
 assert manifest['input']==inp and inp['root']==ready['root'] and inp['launch']==manifest['launch']['id'] and inp['session']==manifest['launch']['session']
 api=next(x for x in ready['api_processes'] if x['role']==inp['preset']);assert api['ready'].get('protocol')
 prompt=a.prompt_file.resolve();assert prompt.is_file();out.mkdir(parents=False);shutil.copyfile(prompt,out/'i1-prompt.txt');shutil.copyfile(stage/'readiness.json',out/'stage-a-readiness.json');shutil.copyfile(p1/'input.json',out/'b1-input.json');shutil.copyfile(p1/'approval.json',out/'b1-approval.json')
 write(out/'static-check.json',{'status':'PASS','launch_status':'NO_GO','root':inp['root'],'task':inp['task'],'role':inp['preset'],'launch':inp['launch'],'session':inp['session'],'api_pid':api['pid'],'api_port':api['ready']['port'],'api_protocol_tag':api['ready']['protocol'],'messages_expected':1,'roots_expected':1,'messages_budget':6 if inp['preset']=='ideation' else 11,'real_process_starts':0})
 approval={'approved_by':None,'approval_ref':None,'stage':'I1','role':inp['preset'],'phase':'I1','source_revision':ready['source_revision'],'launch':inp['launch'],'session':inp['session'],'thread':inp['thread'],'target_binding':ready['target_binding'],'p1_materials':str(p1),'readiness_reference':str((stage/'readiness.json').resolve()),'api_root':str(Path(ready['root'])/'roles'/inp['preset']),'api_protocol_tag':api['ready']['protocol'],'dispatch_text_file':str((out/'i1-prompt.txt').resolve()),'messages_expected':1,'roots_expected':1,'messages_budget':6 if inp['preset']=='ideation' else 11,'real_vendor_model_turns':0,'actions':['pane_dispatch exact material text','record dispatch id/seq','record request_id','record Stop prompt_id','pane_release once','verify one SSE and idle'],'stop_condition':'one Messages, one Stop/idle, no retry'}
 write(out/'approval-template.json',approval);(out/'I1-COMMAND.txt').write_text(f"python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_09b_i1_driver.py --mode execute --materials {out} --stage-a {stage} --approval {out/'approval.json'} --output {out/'execute-01'}\n",encoding='utf-8');write(out/'generation.json',{'status':'PASS','launch_status':'NO_GO','real_process_starts':0,'stage_a':str(stage),'p1':str(p1),'api_protocol_tag':api['ready']['protocol']});print(json.dumps({'status':'PASS','output':str(out),'launch':'NO_GO'},ensure_ascii=False))
if __name__=='__main__':main()
