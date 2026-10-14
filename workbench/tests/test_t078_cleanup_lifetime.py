"""Replay the actual blocked cleanup ps records through the runner's wait loop."""
import argparse,copy,json,sys,textwrap
from pathlib import Path
from p1_processes import identity_from_ps,cli_exit_verdict
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
source=Path(__file__).resolve().parents[2];base=source/'evidence/2026-10-11-batch13/T-078';failed=base/'p1-materials-09a3r2-block'
manifest=json.loads((failed/'launch/process-manifest.json').read_bytes());pid=manifest['cli']['pid']
commands=[json.loads(line) for line in (failed/'cleanup/commands.jsonl').read_text(encoding='utf-8').splitlines()]
probes=[v for v in commands if v['phase']=='finished' and v['argv'][:3]==['/bin/ps','-p',str(pid)]]
observed=[identity_from_ps(pid,v['exit'],v['stdout'],v['stderr']) for v in probes]
assert observed[-1]['started']==manifest['cli']['started'] and observed[-1]['command']!=manifest['cli']['command']
runner=(source/'workbench/tests/run_t078_p1.py').read_text(encoding='utf-8')
start=runner.index('        deadline=time.monotonic()+15',runner.index('        attempted=False'))
end=runner.index("        if (root/'api-owner.json').exists():",start)
segment=textwrap.dedent(runner[start:end]);checks=[]
changed=cli_exit_verdict(True,manifest,{pid:observed[-1]})
checks.append({'name':'same_lifetime_command_change_waits_for_exit','pass':changed['status']=='BLOCKED' and changed['reason']=='recorded_cli_still_alive','observed':changed})
class Clock:
    value=0
    def monotonic(self):self.value+=.01;return self.value
    def sleep(self,_):pass
values=iter([*observed,None]);reads=[];result={}
def probe(asked):
    assert asked==pid;v=next(values);reads.append(v);return v
error=None
try:exec(compile(segment,'<actual cleanup lifetime loop>','exec'),{'time':Clock(),'manifest':manifest,'attempted':True,'probe_process':probe,'cli_exit_verdict':cli_exit_verdict,'result':result,'save':lambda:None})
except Exception as failure:error=repr(failure)
checks.append({'name':'runner_observes_absence_after_transient_comm','pass':error is None and len(reads)==len(observed)+1 and result.get('cli_exit_verdict',{}).get('reason')=='recorded_cli_exited','observed':result,'error':error,
               'last_absence':'Synthetic final ps absence supplied by the requirement; not an original cleanup log'})
for name,current,reason in [('pid_reused',{**observed[-1],'started':'later'},'cli_process_identity_changed'),
                             ('still_alive',manifest['cli'],'recorded_cli_still_alive'),('absent',None,'recorded_cli_exited')]:
    value=cli_exit_verdict(True,manifest,{pid:current});checks.append({'name':name,'pass':value['reason']==reason,'observed':value})
r={'status':'PASS' if all(v['pass'] for v in checks) else 'INCOMPLETE','scope':'Saved real ps rows + actual wait loop; one synthetic absence; no process/signal/API/UI starts','checks':checks,'original_probes':probes,'argv':sys.argv,'real_model_turns':0}
(args.output/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');(args.output/'wait-loop.py').write_text(segment,encoding='utf-8');(args.output/'p1_processes.py').write_bytes((source/'workbench/tests/p1_processes.py').read_bytes())
print(json.dumps({'status':r['status'],'failed':[v['name'] for v in checks if not v['pass']]}));raise SystemExit(0 if r['status']=='PASS' else 1)
