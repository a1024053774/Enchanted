"""Controller-start argument gate reaches construction without spawning."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent));from p1_reuse import controller_start_args
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);checks=[]
 checks.append({'name':'valid-task-builds-controller-start-args','status':'PASS' if controller_start_args('t078-task',Path('/tmp/runtime-input.json'))==['controller_start','--task','t078-task','--manifest','/tmp/runtime-input.json'] else 'INCOMPLETE','spawned':False})
 try:controller_start_args('',Path('/tmp/runtime-input.json'));checks.append({'name':'missing-task-rejected','status':'INCOMPLETE'})
 except ValueError as e:checks.append({'name':'missing-task-rejected','status':'PASS','error':repr(e)})
 source=Path(__file__).resolve().parent/'p1_reuse.py';text=source.read_text();mutant=text.replace("if not isinstance(task, str) or not task: raise ValueError('controller_task_required')","if False: raise ValueError('controller_task_required')",1);scope={};exec(compile(mutant,str(source),'exec'),scope)
 try:scope['controller_start_args']('',Path('/tmp/runtime-input.json'));checks.append({'name':'task-check-mutant-red','status':'PASS','mutant_accepts':True})
 except Exception:checks.append({'name':'task-check-mutant-red','status':'INCOMPLETE','mutant_accepts':False})
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'argument construction only; no CLI/controller/daemon/API/pane start'};(a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
