"""Real cli.ts signal hook-trace binding red/green probe; no daemon/vendor CLI."""
import argparse, json, os, subprocess, tempfile, uuid
from pathlib import Path

SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')

def run_case(root, launch, preset, env_launch, trace_preset):
    state=root/'state'; trace=root/'roles'/trace_preset/'hooks'; trace.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k not in ['A2A_LAUNCH','A2A_PRESET','A2A_HOOK_TRACE_DIR','A2A_STATE','A2A_CAPABILITY']}
    env.update(PATH='/opt/homebrew/bin:/usr/bin:/bin',A2A_STATE=str(state),A2A_LAUNCH=env_launch,A2A_PRESET=preset,
               A2A_CAPABILITY='PRIVATE_NEVER_LOG',A2A_HOOK_TRACE_DIR=str(trace))
    payload=b'{bad-hook-input\n'
    p=subprocess.run(['node',str(SOURCE/'workbench/src/gates/cli.ts'),'--state',str(state),'signal','--launch',launch],
                     input=payload,capture_output=True,env=env,timeout=10)
    trace_members=[]
    if trace.is_dir():
        for child in trace.iterdir():
            trace_members.append(child.name)
            if child.is_dir(): trace_members.extend(child.name+'/'+item.name for item in child.iterdir())
    return {'exit_code':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace'),
            'trace_dir':str(trace),'trace_members':sorted(trace_members),
            'binding_error':b'invalid_hook_trace_binding' in p.stderr}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['red','green'],required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=False,exist_ok=False)
    root=Path(tempfile.mkdtemp(prefix='t078-2-hook-binding-',dir='/tmp')).resolve();(root/'state').mkdir();(root/'roles/ideation/hooks').mkdir(parents=True);(root/'roles/executor/hooks').mkdir(parents=True)
    launch=str(uuid.uuid4());valid=run_case(root,launch,'ideation',launch,'ideation')
    cases={'valid':valid}
    if a.phase=='green':
        cases['wrong-preset']=run_case(root,launch,'executor',launch,'ideation')
        cases['wrong-launch']=run_case(root,launch,'ideation',str(uuid.uuid4()),'ideation')
    if a.phase=='red':
        ok=valid['binding_error'] and not valid['trace_members']
    else:
        ok=(not valid['binding_error'] and any(item.endswith('/finished.json') for item in valid['trace_members']) and
            cases['wrong-preset']['binding_error'] and cases['wrong-launch']['binding_error'])
    result={'status':'PASS' if ok else 'INCOMPLETE','phase':a.phase,'cases':cases,'root':str(root),'real_process_starts':0,'scope':'real cli.ts signal entry; hook trace binding only; no daemon/API/vendor CLI'}
    (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
