"""Generate a phase approval/material packet from real Stage-A and B1 inputs."""
import argparse,json,shutil
from pathlib import Path

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage-a',type=Path,required=True);p.add_argument('--p1',type=Path,required=True);p.add_argument('--stage',choices=['I1','I2','I3','I4','E1','E2','E3','E4','E5','E6'],required=True);p.add_argument('--prompt-file',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    stage=a.stage_a.resolve();p1=a.p1.resolve();out=a.output.resolve();assert not out.exists()
    ready=json.loads((stage/'readiness.json').read_bytes());inp=json.loads((p1/'input.json').read_bytes());manifest=json.loads((p1/'approval.json').read_bytes());role='ideation' if a.stage.startswith('I') else 'executor';budget=6 if role=='ideation' else 11
    assert ready['status']=='READY_FOR_APPROVAL' and ready['roles_started']==[] and manifest['input']==inp and inp['root']==ready['root'] and inp['preset']==role
    api=next(x for x in ready['api_processes'] if x['role']==role);assert api['ready'].get('protocol')
    prompt=a.prompt_file.resolve();assert prompt.is_file();out.mkdir(parents=False)
    for source,name in [(stage/'readiness.json','stage-a-readiness.json'),(p1/'input.json','b1-input.json'),(p1/'approval.json','b1-approval.json'),(prompt,'phase-prompt.txt')]:shutil.copyfile(source,out/name)
    write(out/'static-check.json',{'status':'PASS','launch_status':'NO_GO','stage':a.stage,'role':role,'root':inp['root'],'task':inp['task'],'launch':inp['launch'],'session':inp['session'],'api_pid':api['pid'],'api_port':api['ready']['port'],'api_protocol_tag':api['ready']['protocol'],'messages_expected':1,'roots_expected':1,'messages_budget':budget,'real_vendor_model_turns':0,'real_process_starts':0})
    approval={'approved_by':None,'approval_ref':None,'stage':a.stage,'phase':a.stage,'role':role,'source_revision':ready['source_revision'],'launch':inp['launch'],'session':inp['session'],'thread':inp['thread'],'target_binding':ready['target_binding'],'p1_materials':str(p1),'readiness_reference':str((stage/'readiness.json').resolve()),'api_root':str(Path(ready['root'])/'roles'/role),'api_protocol_tag':api['ready']['protocol'],'dispatch_text_file':str((out/'phase-prompt.txt').resolve()),'messages_expected':1,'roots_expected':1,'messages_budget':budget,'real_vendor_model_turns':0,'actions':['pane_dispatch exact phase text','record dispatch id/seq','record request_id','record Stop prompt_id','pane_release once','verify one SSE and idle'],'stop_condition':f'one {a.stage} Messages, one Stop/idle, no retry'}
    write(out/'approval-template.json',approval)
    (out/'PHASE-COMMAND.txt').write_text(f"python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_09b_i1_driver.py --mode execute --stage {a.stage} --materials {out} --stage-a {stage} --approval {out/'approval.json'} --output {out/'execute-01'}\n",encoding='utf-8')
    write(out/'generation.json',{'status':'PASS','stage':a.stage,'role':role,'launch_status':'NO_GO','real_process_starts':0})
    print(json.dumps({'status':'PASS','stage':a.stage,'output':str(out),'launch':'NO_GO'},ensure_ascii=False))
if __name__=='__main__':main()
