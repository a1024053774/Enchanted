import json,os,signal,subprocess,time,sqlite3,re
from pathlib import Path
out=Path(__file__).resolve().parent
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-desktop/desktop-home/dev')
records={}
for name in ['state.sqlite3','membership.sqlite3']:
 c=sqlite3.connect(f'file:{base}/a2a-gates/{name}?mode=ro',uri=True);c.row_factory=sqlite3.Row
 tables=[r[0] for r in c.execute("select name from sqlite_master where type='table'")]
 records[name]={t:[dict(r) for r in c.execute('select * from "'+t+'"')] for t in tables}
 c.close()
(out/'fixture-gate-membership.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ps=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True)
groups=[json.loads((out/f).read_text())['pgid'] for f in ['vite-start.json','electron-start.json','electron-02-start.json']]
owned=[line for line in ps.splitlines()[1:] if len(line.split(None,3))==4 and int(line.split(None,3)[2]) in groups]
(out/'owned-processes-before-stop.txt').write_text('\n'.join(owned)+'\n')
ports=[]
for f in ['electron.log','electron-02.log']:
 ports+=re.findall(r'  port: (\d+),',(out/f).read_text())
ports+=['7771','5811']
actions=[]
for group in groups:
 try: os.killpg(group,signal.SIGTERM); actions.append({'group':group,'signal':'SIGTERM'})
 except ProcessLookupError: actions.append({'group':group,'already_exited':True})
time.sleep(3)
ps2=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True)
remaining=[line for line in ps2.splitlines()[1:] if len(line.split(None,3))==4 and int(line.split(None,3)[2]) in groups]
for group in groups:
 if any(int(line.split(None,3)[2])==group for line in remaining):
  os.killpg(group,signal.SIGKILL);actions.append({'group':group,'signal':'SIGKILL'})
time.sleep(1)
checks=[]
for port in sorted(set(ports)):
 r=subprocess.run(['lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN'],capture_output=True,text=True)
 checks.append({'port':port,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
ps3=subprocess.check_output(['ps','-axo','pid,ppid,pgid,command'],text=True)
remaining=[line for line in ps3.splitlines()[1:] if len(line.split(None,3))==4 and int(line.split(None,3)[2]) in groups]
(out/'cleanup.json').write_text(json.dumps({'actions':actions,'remaining':remaining,'listeners':checks},indent=2)+'\n')
print(json.dumps({'remaining':remaining,'listeners':checks},indent=2))
