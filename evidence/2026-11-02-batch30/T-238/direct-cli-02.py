import os,pty,subprocess,time,select,pathlib
out=pathlib.Path('evidence/2026-11-02-batch30/T-238');procs=[]
for name,args in [('codex',['codex','--no-daemon','-c','check_for_update_on_startup=false']),('agy',['agy','--dangerously-skip-permissions'])]:
 m,s=pty.openpty();p=subprocess.Popen(args,cwd='/private/tmp/a2a-t238b/project',stdin=s,stdout=s,stderr=s,start_new_session=True);os.close(s);procs.append((name,p,m,bytearray()))
t0=time.monotonic();sent=False
while time.monotonic()-t0<35:
 for name,p,m,b in procs:
  if select.select([m],[],[],0)[0]:
   try:b.extend(os.read(m,65536))
   except OSError:pass
 if not sent and time.monotonic()-t0>12:
  for name,p,m,b in procs:os.write(m,'请回复：测试正常。不要操作文件。\r'.encode())
  sent=True
 time.sleep(.05)
for name,p,m,b in procs:
 (out/('direct-cli-'+name+'-02.txt')).write_bytes(b)
 os.write(m,b'\x03');p.terminate()
 try:p.wait(timeout=2)
 except subprocess.TimeoutExpired:p.kill();p.wait()
 os.close(m)
