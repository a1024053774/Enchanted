import base64,json,os,socket,subprocess,time,uuid,pathlib,re
F=pathlib.Path('/private/tmp/a2a-t238b');S=F/'source-state';C=F/'source-operator.json';O=pathlib.Path('evidence/2026-11-02-batch30/T-238');op=json.loads(C.read_text())
def req(command,identity=None,**kw):
 with socket.socket(socket.AF_UNIX) as s:
  s.settimeout(10);s.connect(str(S/'control.sock'));s.sendall((json.dumps(dict(id=str(uuid.uuid4()),input=dict(command=command,**kw),identity=identity))+'\n').encode());b=b''
  while b'\n' not in b:b+=s.recv(65536)
  return json.loads(b.split(b'\n')[0])
r=subprocess.run(['node','workbench/src/gates/cli.ts','--state',str(S),'shell_start','--project','proj','--cwd',str(F/'project')],env=dict(os.environ,A2A_OPERATOR_CREDENTIAL=str(C)),capture_output=True,text=True,timeout=40);print(r.stdout,r.stderr,flush=True);l=json.loads(r.stdout)['launch']['id'];w=req('window_open',op,launch=l,project='proj');time.sleep(5);print(req('window_input',w['identity'],sequence=1,request_id=str(uuid.uuid4()),data='zsh -f /private/tmp/a2a-t238b/probe.zsh\r'),flush=True);time.sleep(12);r=req('pane_output',launch=l,offset=0);(O/'source-screen-02.txt').write_text(base64.b64decode(r['data_base64']).decode('utf8','replace'));print('launch',l)
