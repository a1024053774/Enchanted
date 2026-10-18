"""Actual system Bash and wrapper, supplied exec boundary only; no delegated process runs."""
import json
from pathlib import Path
import subprocess
import sys

script=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).resolve().parents[2]/'evidence/2026-10-16-batch16/T-093/T093-OS-16.sh'
output=Path(sys.argv[1]);assert not output.exists()
repo='/fixture/repo';candidate='f'*40;result='/private/tmp/supplied-result.json'
inputs=['/private/tmp/supplied-one.json','/private/tmp/supplied-two.json']
base=['/usr/bin/python3','-I','-S','-B']
cases={
 'compile':base+[repo+'/evidence/2026-10-16-batch16/T-093/compile-profiles-16.py','--source',repo,'--candidate',candidate,'--output',result],
 'none':base+[repo+'/workbench/tests/run_t093_login_chain.py','--source-revision',candidate,'--output',result,'--mutation','none'],
 'primary':base+[repo+'/workbench/tests/run_t093_login_chain.py','--source-revision',candidate,'--output',result,'--rehearsal','primary'],
 'green':base+[repo+'/workbench/tests/run_t093_login_chain.py','--source-revision',candidate,'--output',result,'--rehearsal','green'],
 'verify-six':base+[repo+'/workbench/tests/check_t093_chain_results.py','--candidate',candidate,'--output',result,*inputs],
 'verify-counts':base+[repo+'/workbench/tests/check_t093_chain_results.py','--candidate',candidate,'--counts-only','--output',result,*inputs],
 'verify-rehearsal':base+[repo+'/workbench/tests/check_t093_chain_results.py','--candidate',candidate,'--rehearsal','--output',result,*inputs],
}
checks=[]
for mode,expected in cases.items():
 args=[str(script),mode,repo,candidate,result]+(inputs if mode.startswith('verify-') else [])
 shell='exec() { printf "%s\\0" "$@"; }; script=$1; shift; . "$script" "$@"'
 process=subprocess.run(['/bin/bash','-c',shell,'wrapper-test',*args],capture_output=True,env={'PATH':'/usr/bin:/bin','LANG':'C'},timeout=5)
 actual=[value.decode() for value in process.stdout.split(b'\0') if value]
 try:
  assert process.returncode==0,'wrapper_must_delegate_without_shell_failure'
  assert actual==expected,'wrapper_must_preserve_selected_mode_and_all_arguments'
  checks.append({'mode':mode,'status':'PASS','delegated_program_invoked':False})
 except AssertionError as error:checks.append({'mode':mode,'status':'FAIL','business_failure':str(error),'exit_code':process.returncode,'stderr':process.stderr.decode()})
status='PASS' if all(row['status']=='PASS' for row in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'actual /bin/bash script with exec supplied as an argv-capturing function; no Python/OS/profile/CLI invocation','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
