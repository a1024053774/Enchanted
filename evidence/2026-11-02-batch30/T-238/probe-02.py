import base64,json,os,re,socket,subprocess,time,uuid
from pathlib import Path
F=Path('/private/tmp/a2a-t238b'); S=F/'state'; OUT=Path('evidence/2026-11-02-batch30/T-238')
conn=json.loads((F/'state-credentials/desktop-connection.json').read_text()); cred=conn['credential']; op=json.loads(Path(cred).read_text()); seq={}
def req(command,identity=None,**kw):
 with socket.socket(socket.AF_UNIX) as s:
  s.settimeout(15);s.connect(str(S/'control.sock'));s.sendall((json.dumps(dict(id=str(uuid.uuid4()),input=dict(command=command,**kw),identity=identity))+'\n').encode()); b=b''
  while b'\n' not in b:b+=s.recv(65536)
  return json.loads(b.split(b'\n')[0])
def output(l):
 r=req('pane_output',launch=l,offset=0);return base64.b64decode(r['data_base64']).decode('utf8','replace')
def send(i,d):
 key=json.dumps(i,sort_keys=True);seq[key]=seq.get(key,0)+1;r=req('window_input',i,sequence=seq[key],request_id=str(uuid.uuid4()),data=d);assert r['ok'],r
def start():
 e=dict(os.environ,A2A_OPERATOR_CREDENTIAL=cred);r=subprocess.run(['node','workbench/src/gates/cli.ts','--state',str(S),'shell_start','--project','proj','--cwd',str(F/'project')],capture_output=True,text=True,env=e,timeout=20);assert r.returncode==0,r.stderr
 l=json.loads(r.stdout)['launch']['id'];r=req('window_open',op,launch=l,project='proj');assert r['ok'],r;return l,r['identity']
ls=[]
for name in ['codex','agy','files']:
 l,i=start();ls.append((name,l,i))
time.sleep(5)
for name,l,i in ls:
 if name=='codex':send(i,'codex\r')
 if name=='agy':send(i,'agy --dangerously-skip-permissions\r')
 if name=='files':send(i,'zsh -f /private/tmp/a2a-t238b/probe.zsh\r')
time.sleep(8)
for name,l,i in ls[:2]:send(i,'请回复：测试正常。不要操作文件。\r')
time.sleep(20)
for name,l,i in ls:(OUT/('screen-02-'+name+'.txt')).write_text(output(l))
ps=subprocess.run(['ps','-axo','pid,ppid,stat,etime,command'],capture_output=True,text=True).stdout;(OUT/'ps-02.txt').write_text(ps)
print(json.dumps({'launches':[(n,l) for n,l,i in ls]},ensure_ascii=False))
