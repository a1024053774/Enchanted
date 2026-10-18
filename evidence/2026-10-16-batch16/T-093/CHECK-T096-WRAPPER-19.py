"""Actual Bash wrapper argv; supplied Git/mount/exec, no runner or process probes."""
import json
from pathlib import Path
import subprocess
import sys

script=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).with_name('T096-REGRESSION-16.sh')
checks=[]
cases={'tracer':(1,['--check-close']),'three':(3,['--check-close']),
 'missing-argv':(1,['--fault','missing-argv']),'version-mismatch':(1,['--fault','version-mismatch']),
 'missing-session':(1,['--fault','missing-session']),'isolation':(3,['--fault','missing-argv']),
 'empty-reopen':(3,['--check-close','--check-empty-reopen'])}
repo='/fixture/repo';candidate='a'*40;cli='/fixture/claude-2.1.302';approval='controller approval reference'
shell='''git() { if [ "$3" = rev-parse ]; then printf '%s\\n' "$candidate"; fi; }
/usr/bin/python3() { return 0; }
exec() { printf '%s\\0' "$@"; }
candidate=$3
script=$1; shift
. "$script" "$@"
'''
for mode,(panes,extra) in cases.items():
 label='supplied-r19-'+mode
 args=[str(script),mode,repo,candidate,cli,approval,label]
 process=subprocess.run(['/bin/bash','-c',shell,'wrapper-contract',*args],capture_output=True,text=False,env={'PATH':'/usr/bin:/bin','LANG':'C'},timeout=5)
 actual=[value.decode() for value in process.stdout.split(b'\0') if value]
 expected=['python3',repo+'/evidence/2026-10-16-batch16/T-096/run_restart.py','--source',repo,
  '--output','/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/'+label,'--label',label,
  '--approval-ref',approval,'--claude',cli,'--claude-version','2.1.302','--panes',str(panes),
  '--expect','restore','--startup-wait-seconds','600',*extra]
 try:
  assert process.returncode==0,'wrapper_must_reach_supplied_exec'
  assert actual==expected,'T096_output_and_arguments_must_match_public_runner_contract'
  checks.append({'case':mode,'status':'PASS','runner_invoked':False})
 except AssertionError as error:checks.append({'case':mode,'status':'FAIL','business_failure':str(error),'exit':process.returncode,'stderr':process.stderr.decode()})
status='PASS' if all(row['status']=='PASS' for row in checks) else 'FAIL'
with Path(sys.argv[1]).open('x',encoding='utf-8') as file:json.dump({'status':status,'scope':__doc__,'checks':checks},file,indent=2);file.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
