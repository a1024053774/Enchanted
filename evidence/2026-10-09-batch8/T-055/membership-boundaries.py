import importlib.util,json,sys,urllib.request,urllib.error,sqlite3
from pathlib import Path
b=Path(__file__).resolve().parent;out=Path(sys.argv[2]);sp=importlib.util.spec_from_file_location('a',b/'fixture-api.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);f=a.Fixture(sys.argv[1]);fixture=json.loads((out/'membership-fixture.json').read_text());results=[]
def request(method,path,body=None,origin=None):
 headers={'Content-Type':'application/json'}
 if origin:headers['Origin']=origin
 r=urllib.request.Request(f.origin+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method)
 try:
  with urllib.request.urlopen(r,timeout=30) as response:status=response.status;raw=response.read().decode();h=dict(response.headers)
 except urllib.error.HTTPError as e:status=e.code;raw=e.read().decode();h=dict(e.headers)
 item=dict(method=method,path=path,input=body,origin=origin,status=status,headers=h,raw=raw);results.append(item)
 return status,json.loads(raw) if raw else None,h
for path in ['/api/a2a','/api/a2a/membership','/api/a2a/issues']:
 status,_,headers=request('OPTIONS',path,origin='http://localhost:7788');assert status==204 and headers['access-control-allow-origin']=='http://localhost:7788'
 status,_,_=request('OPTIONS',path,origin='https://untrusted.invalid');assert status==403
tasks=request('GET','/api/a2a/membership')[1]['tasks'];task=next(t for t in tasks if t['taskId']==fixture['task']);worker=json.loads((out/'real-dispatch.json').read_text())['attempt']['thread_id']
status,result,_=request('POST','/api/a2a/membership',dict(command='save',task={**task,'members':[dict(threadId=worker,role='worker')]}));assert status==400 and result['error']=='thread_project_mismatch'
gate=next(t for t in tasks if t['taskId']=='t055')
status,result,_=request('POST','/api/a2a/membership',dict(command='save',task={**gate,'projectId':fixture['project'],'members':[]}));assert status==400 and result['error']=='gate_project_mismatch'
lock=sqlite3.connect(f.root/'userdata/a2a-gates/locks/t055.sqlite3');lock.execute('BEGIN IMMEDIATE')
try:
 status,result,_=request('POST','/api/a2a/membership',dict(command='save',task=gate));assert status==409 and result['error']=='operation_busy'
finally:lock.rollback();lock.close()
after=request('GET','/api/a2a/membership')[1]['tasks'];assert next(t for t in after if t['taskId']=='t055')==gate
with (out/'membership-boundaries.json').open('x') as file:json.dump(results,file,ensure_ascii=False,indent=2);file.write('\n')
print('Membership CORS, cross-project, gate binding, shared operation lock PASS')
