from pathlib import Path
import importlib.util,json,os,subprocess,sys,time,signal
SOURCE=Path('/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1/workbench/tests/test_t265_review_cli_e2e.py')
spec=importlib.util.spec_from_file_location('t265_native_driver',SOURCE); d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
out=Path(__file__).resolve().parent/'process-wait-probe-01-events.jsonl'
masters=[];original_openpty=d.pty.openpty;original_close=d.os.close

def event(kind,**data):
 with out.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(at=time.time(),kind=kind,**data),ensure_ascii=False)+'\n')
def opened():
 result=original_openpty();masters.append(result[0]);return result

def observe(child,phase):
 try: group=os.getpgid(child.pid)
 except ProcessLookupError:group='ESRCH'
 status=subprocess.run(['/bin/ps','-p',str(child.pid),'-o','pid=,ppid=,pgid=,stat=,comm='],capture_output=True,text=True)
 event('observation',phase=phase,pid=child.pid,pgid=group,poll=child.poll(),wait_lock_locked=child._waitpid_lock.locked(),ps_exit=status.returncode,ps=status.stdout)

def traced_stop(child,diagnostic):
 assert child is not None and child.pid>0 and child.pid==diagnostic['pid']
 observe(child,'before-stop')
 assert os.getpgid(child.pid)==child.pid==diagnostic['pgid'] and child.pid!=os.getpgrp()
 os.killpg(child.pid,signal.SIGTERM);event('term-sent',pid=child.pid)
 try:
  code=child.wait(timeout=3);event('wait-returned',phase='before-master-close',exit_code=code)
 except subprocess.TimeoutExpired:
  observe(child,'after-three-seconds')
  original_close(masters[-1]);masters.remove(masters[-1]);event('owned-master-closed')
  try:
   code=child.wait(timeout=3);event('wait-returned',phase='after-master-close',exit_code=code)
  except subprocess.TimeoutExpired:
   observe(child,'after-master-close-timeout');raise
 # End after this parent-only diagnostic; never run the candidate here.
 raise RuntimeError('diagnostic complete; owned wait result is in events, not a business verdict')

d.pty.openpty=opened;d.stop_owned=traced_stop
# Intentionally preserves the original driver's outcome even if closing the
# master makes its final close report EBADF. This is a narrow diagnostic, not PASS.
sys.argv=[str(SOURCE),'--codex','/Users/luckye/.local/bin/codex','--node','/opt/homebrew/Cellar/node/26.5.0/bin/node','--summary',str(out.parent/'process-wait-probe-01.json')]
raise SystemExit(d.main())
