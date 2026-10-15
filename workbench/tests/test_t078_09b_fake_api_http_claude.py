"""Loopback HTTP test using a captured Claude 2.1.296 request body."""
import argparse, copy, json, subprocess, sys, tempfile, time, urllib.error, urllib.request, uuid
from pathlib import Path
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078'); API=SOURCE/'workbench/tests/t078_09b_fake_api.py'; FIXTURE=SOURCE/'evidence/2026-10-11-batch13/T-078/slice1-green-3-readback/api.jsonl'
def start(root,api):
 p=subprocess.Popen([sys.executable,'-B',str(api),'--root',str(root),'--role','ideation','--port','0','--protocol'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True);ready=root/'api-ready.json';deadline=time.monotonic()+5
 while not ready.exists() and time.monotonic()<deadline:time.sleep(.02)
 if not ready.exists():raise RuntimeError('api_not_ready')
 return p,json.loads(ready.read_bytes())
def post(url,body):
 req=urllib.request.Request(url+'/v1/messages',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=5) as r:return r.status,r.read().decode()
 except urllib.error.HTTPError as e:return e.code,e.read().decode()
def prompt_block(body):
 for message in reversed(body.get('messages',[])):
  if message.get('role')!='user' or not isinstance(message.get('content'),list): continue
  for item in reversed(message['content']):
   if item.get('type')=='text' and item.get('text','').startswith('⟦主控 #'):return item['text']
 raise AssertionError('captured dispatch prompt missing')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--api',type=Path,default=API);ap.add_argument('--expect',choices=['red','green'],default='green');a=ap.parse_args();a.output.mkdir(parents=False,exist_ok=False);raw=json.loads(FIXTURE.read_text(encoding='utf-8').splitlines()[0]);captured=raw['body'];text=prompt_block(captured);did=str(uuid.uuid4());dispatch={'id':did,'seq':2,'role':'ideation','text':text,'request_id':'req-claude','stop_id':'stop-claude','attempt':'attempt-claude','session':'session-claude','fence':1};checks=[]
 with tempfile.TemporaryDirectory(dir='/private/tmp') as td:
  root=Path(td);p,ready=start(root,a.api);(root/'protocol-registry.json').write_text(json.dumps({'dispatches':{did:dispatch},'message_budget':6,'ack_text':'I1_ACK'}))
  status,body=post(ready['api_url'],captured);captured_ok=(status==200 and 'message_start' in body and 'message_stop' in body) if a.expect=='green' else (status==409 and "ROLE" in body)
  checks.append({'name':'captured-claude-request-'+a.expect,'status':'PASS' if captured_ok else 'INCOMPLETE','http':status,'response':body[:500],'body_bytes':len(json.dumps(captured).encode())})
  custom={'dispatch_id':did,'dispatch_seq':2,'role':'ideation','request_id':'req-claude','stop_id':'stop-claude','attempt':'attempt-claude','session':'session-claude','fence':1,'messages':[{'role':'user','content':text}],'stream':True,'model':'claude-haiku-5-5'}
  for name,mutate in [('text',lambda x:x['messages'][0].update(content=text+' stale')),('seq',lambda x:x.update(dispatch_seq=3)),('identity',lambda x:x.update(attempt='other')),('role',lambda x:x.update(role='executor')),('budget',lambda x:x.update(messages=[x['messages'][0]]*7))]:
   bad=copy.deepcopy(custom);mutate(bad);code,_=post(ready['api_url'],bad);checks.append({'name':'protocol-'+name+'-red','status':'PASS' if code==409 else 'INCOMPLETE','http':code})
  p.terminate();p.wait(5)
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'captured_source':str(FIXTURE),'captured_prompt_bytes':len(json.dumps(captured,ensure_ascii=False).encode()),'scope':'real loopback fake API with captured Claude 2.1.296 body; no vendor CLI/model'};(a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
