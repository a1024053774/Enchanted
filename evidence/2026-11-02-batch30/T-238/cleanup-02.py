import os,signal,subprocess,time,pathlib
out=pathlib.Path('evidence/2026-11-02-batch30/T-238'); needles=('/private/tmp/a2a-t238b/','/private/tmp/a2a-build-t238-20261102/')
def find():
 s=subprocess.run(['ps','-axo','pid,ppid,stat,command'],capture_output=True,text=True).stdout
 return [x for x in s.splitlines()[1:] if any(n in x for n in needles) and int(x.split()[0]) not in (os.getpid(),os.getppid())]
rows=find();(out/'cleanup-before-02.txt').write_text('\n'.join(rows)+'\n')
for x in rows:
 try:os.kill(int(x.split()[0]),signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(3)
rows=find();(out/'cleanup-after-02.txt').write_text('\n'.join(rows)+'\n');print('\n'.join(rows) or 'no matching processes')
