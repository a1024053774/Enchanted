import json,os,signal,subprocess,time,sys,datetime
from pathlib import Path
out=Path(__file__).resolve().parent
records=[]
for name in sys.argv[2:]:
 launch_path=out/name; data=json.loads(launch_path.read_text());pid=data['pid']
 ps=subprocess.run(['ps','-p',str(pid),'-o','lstart=,command='],capture_output=True,text=True,env={**os.environ,'LC_ALL':'C'})
 record=dict(launch=name,pid=pid,ps_before=ps.stdout)
 if ps.returncode==0:
  assert 'server-fixture-02.ts' in ps.stdout,record
  stamp=datetime.datetime.strptime(ps.stdout.strip()[:24],'%a %b %d %H:%M:%S %Y').timestamp()
  assert abs(stamp-launch_path.stat().st_mtime)<10,(stamp,launch_path.stat().st_mtime,record)
  os.kill(pid,signal.SIGTERM)
  for _ in range(100):
   try:os.kill(pid,0)
   except ProcessLookupError:break
   time.sleep(.1)
  else:raise RuntimeError('own server did not exit')
  record['terminated']=True
 else:record['already_exited']=True
 records.append(record)
with (out/sys.argv[1]).open('x',encoding='utf-8') as f:json.dump(records,f,ensure_ascii=False,indent=2);f.write('\n')
print('PASS own fixture processes',len(records))
