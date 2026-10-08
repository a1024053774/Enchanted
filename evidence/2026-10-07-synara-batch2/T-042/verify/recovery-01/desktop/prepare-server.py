import json,subprocess,sys,datetime
from pathlib import Path
from owned_api import connection,request
out=Path(__file__).resolve().parent
repo=Path('/Users/luckye/Documents/Code/synara')
env=json.loads((out/'isolation.json').read_text())['env']
def run(label,argv,extra=None):
 r=subprocess.run(argv,cwd=repo,env=dict(env,**(extra or {})),capture_output=True,text=True)
 with (out/(label+'-command.json')).open('x',encoding='utf-8') as f:json.dump({'argv':argv,'cwd':str(repo),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,ensure_ascii=False,indent=2)
 assert r.returncode==0,(label,r.stderr)
run('prepare-fixture',[sys.executable,str(out/'prepare-fixture.py')])
f=json.loads((out/'fixture.json').read_text())
result=request('gate-create',{'command':'create','task':f['task'],'project':f['project'],'repo':f['repo'],'base':f['base'],'oracle':f['oracle'],'instructions':f['instructions']})
assert result['ok'] is True,result
endpoint,token,pid=connection()
for role in ['worker','reviewer']:
 body={'type':'thread.create','commandId':f[role]+'-create','threadId':f[role],'projectId':f['project'],'title':role+' · 合并复验','modelSelection':{'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'xhigh','fastMode':True}},'runtimeMode':'approval-required','interactionMode':'default','envMode':'local','branch':None,'worktreePath':None,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')}
 path=out/(role+'-input.json');path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 run('native-'+role,['./a2a/scripts/bun','run','node',str(out/'native-rpc.mjs'),'native-'+role,endpoint,str(path)],{'A2A_GATE_BEARER':token})
run('membership',[sys.executable,str(out/'http-scenario.py'),'membership',endpoint])
foreign=f['project']+'-foreign'
folder=Path(f['root'])/'foreign-project';folder.mkdir()
body={'type':'project.create','commandId':foreign+'-create','projectId':foreign,'title':'跨项目反例','workspaceRoot':str(folder),'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')}
path=out/'foreign-project-input.json';path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
run('foreign-project',['./a2a/scripts/bun','run','node',str(out/'native-rpc.mjs'),'foreign-project',endpoint,str(path)],{'A2A_GATE_BEARER':token})
body=json.loads((out/'reviewer-input.json').read_text());body.update(commandId=foreign+'-thread-create',threadId=foreign+'-thread',projectId=foreign)
path=out/'foreign-thread-input.json';path.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
run('foreign-thread',['./a2a/scripts/bun','run','node',str(out/'native-rpc.mjs'),'foreign-thread',endpoint,str(path)],{'A2A_GATE_BEARER':token})
for label,task,error in [('cross-project-member',{'taskId':f['task']+'-wrong-member','projectId':f['project'],'title':'跨项目成员反例','revision':0,'members':[{'threadId':foreign+'-thread','role':'reviewer'}]},'thread_project_mismatch'),('cross-project-gate',{'taskId':f['task'],'projectId':foreign,'title':'门禁项目反例','revision':1,'members':[]},'gate_project_mismatch')]:
 result=request(label,{'command':'save','task':task},path='/api/a2a/membership');assert result['ok'] is False and result['error']==error,result
 assert json.loads((out/(label+'.json')).read_text())['status']==400
import urllib.request,urllib.error,urllib.parse
checks=[]
for path in ['/api/a2a','/api/a2a/membership']:
 for origin,expected in [('http://localhost:7771',204),('https://untrusted.invalid',403)]:
  req=urllib.request.Request(endpoint+path+'?token='+urllib.parse.quote(token),method='OPTIONS',headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'Content-Type'})
  try:
   with urllib.request.urlopen(req,timeout=30) as response:status,headers,raw=response.status,dict(response.headers),response.read().decode()
  except urllib.error.HTTPError as error:status,headers,raw=error.code,dict(error.headers),error.read().decode()
  checks.append({'path':path,'origin':origin,'expected_status':expected,'status':status,'headers':headers,'body':raw})
  (out/'preflight.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  assert status==expected
  if expected==204:
   headers={k.lower():v for k,v in headers.items()};assert headers['access-control-allow-origin']==origin and headers['access-control-allow-credentials']=='true' and 'Content-Type' in headers['access-control-allow-headers']
result=request('gate-events-before',{'command':'events','task':f['task']})
assert result['ok'] is True
observer=request('observer-before',path='/api/a2a')
assert observer['human_input_observer']['state']=='healthy',observer
print('PASS membership HTTP; actual observer healthy')
