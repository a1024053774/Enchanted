"""Real loopback HTTP red/green protocol checks; no vendor CLI/model."""
import argparse,json,subprocess,sys,tempfile,time,urllib.error,urllib.request,uuid
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2];API=SOURCE/'workbench/tests/t078_09b_fake_api.py'
def start(root,protocol):
 p=subprocess.Popen([sys.executable,'-B',str(API),'--root',str(root),'--role','ideation','--port','0']+(['--protocol'] if protocol else []),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True);ready=root/'api-ready.json';end=time.monotonic()+5
 while not ready.exists() and time.monotonic()<end:time.sleep(.02)
 if not ready.exists():raise RuntimeError('api_not_ready')
 return p,json.loads(ready.read_bytes())
def request(url,body):
 req=urllib.request.Request(url+'/v1/messages',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=3) as r:return r.status,r.read().decode()
 except urllib.error.HTTPError as e:return e.code,e.read().decode()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);checks=[]
 with tempfile.TemporaryDirectory(dir='/private/tmp') as td:
  root=Path(td);red,rr=start(root/'red',False);status,_=request(rr['api_url'],{});red.terminate();red.wait(5);checks.append({'name':'current-stage-A-409-red','status':'PASS' if status==409 else 'INCOMPLETE','http':status})
  for mutant in [None,'text','seq','identity','role','budget']:
   rroot=root/('green-'+str(mutant));p,ready=start(rroot,True);did=str(uuid.uuid4());reg={'dispatches':{did:{'seq':1,'id':did,'role':'ideation','text':'⟦门禁 #1⟧\nI1','request_id':'req','attempt':'att','session':'ses','fence':1}},'message_budget':6};(rroot/'protocol-registry.json').write_text(json.dumps(reg));body={'dispatch_id':did,'dispatch_seq':1,'role':'ideation','request_id':'req','attempt':'att','session':'ses','fence':1,'messages':[{'role':'user','content':'⟦门禁 #1⟧\nI1'}]}
   if mutant=='text':body['messages'][0]['content']+=' stale'
   if mutant=='seq':body['dispatch_seq']=2
   if mutant=='identity':body['attempt']='other'
   if mutant=='role':body['role']='executor'
   if mutant=='budget':reg['message_budget']=0;(rroot/'protocol-registry.json').write_text(json.dumps(reg))
   code,_=request(ready['api_url'],body);p.terminate();p.wait(5);checks.append({'name':'protocol-green' if mutant is None else 'protocol-'+mutant+'-red','status':'PASS' if ((code==200)==(mutant is None)) else 'INCOMPLETE','http':code})
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'scope':'real loopback fake API HTTP only; no Claude/daemon/target/model'};(a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
