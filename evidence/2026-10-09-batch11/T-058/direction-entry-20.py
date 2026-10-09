import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

out=Path(__file__).resolve().parent;label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'));root=Path(launch['root']);fork=Path('/Users/luckye/Documents/Code/synara')
spec=importlib.util.spec_from_file_location('direction_api',out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);f=api.Fixture(root)
results=out/label;results.mkdir()
def save(name,value):
 with (results/(name+'.json')).open('x',encoding='utf-8') as s:json.dump(value,s,ensure_ascii=False,indent=2);s.write('\n')
repo=root/'repo';repo.mkdir();env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']};env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',A2A_SYNARA_SLOT='s11-t058-'+label,A2A_GATE_BEARER='fixture-local-owner')
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],env=env,text=True).strip()
git('init','-q');git('config','user.name','T058 direction oracle');git('config','user.email','fixture@example.invalid');(repo/'sentinel.txt').write_text('Direction baseline\n',encoding='utf-8');git('add','sentinel.txt');git('-c','core.hooksPath=/dev/null','commit','-qm','Baseline')
(root/'instructions.txt').write_text('Controlled provider state; no model.\n',encoding='utf-8');(root/'oracle.py').write_text('raise SystemExit(0)\n',encoding='utf-8')
assert f.gate('create',task='direction',project='direction-project',repo=str(repo),base=git('rev-parse','HEAD'),oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'))['ok']
tokens={};threads={}
for role in ['executor','ideation','worker']:
 result=f.gate('attach',task='direction',role='controller' if role!='worker' else 'worker',preset=role,modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',instructions=str(root/'instructions.txt'));assert result['ok'];threads[role]=result['attachment']['thread_id']
 f.control('controlled-session',thread=threads[role],active=True,turn=str(uuid.uuid4()),workspace=str(repo))
 path=root/('private-'+role+'.token');f.control('token',thread=threads[role],path=str(path));tokens[role]=path.read_text(encoding='utf-8')
issue=f.gate('inbox_send',**{'from':'worker:'+threads['worker']},to='triage',kind='issue',title='direction parent',body='issue')
assignment=f.gate('inbox_send',**{'from':'ideation'},to='executor',kind='assign',body='valid parent')
cases=[
 ('assign','executor','executor',{}),('revise','executor','executor',{}),('cancel','ideation','ideation',{}),
 ('report','ideation','ideation',{}),('needs-decision','executor','executor',{}),('stop','executor','executor',{}),
 ('issue','ideation','triage',{'title':'bad sender'}),('answer','executor','executor',{}),
 ('disposition','worker','triage',{'reply_to':issue['entry']['id'],'action':'needs-user'}),
 ('ack','ideation','ideation',{'reply_to':assignment['entry']['id']}),
]
def rows():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
  return dict(records=list(db.execute('SELECT id,data FROM inbox_records ORDER BY rowid')),deliveries=list(db.execute('SELECT entry,data FROM inbox_deliveries ORDER BY seq')))
for kind,actor,to,extra in cases:
 request=dict(kind=kind,to=to,body='illegal direction '+kind,refs=[],**extra)
 for transport in ['mcp','http','cli']:
  before=rows()
  sender=actor if actor!='worker' else 'worker:'+threads['worker']
  if transport=='mcp':
   rpc=dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/call',params=dict(name='a2a_inbox_send',arguments=request))
   response=f.http('/mcp',rpc,tokens[actor]);result=json.loads(response['result']['content'][0]['text'])
  elif transport=='http':
   rpc=dict(command='inbox_send',**{'from':sender},**request);result=f.http('/api/a2a',rpc)
  else:
   rpc=dict(command='inbox_send',**{'from':sender},**request)
   argv=['./a2a/scripts/bun','run','packages/a2a-gates/src/cli.ts',f.origin,json.dumps(rpc)]
   p=subprocess.run(argv,cwd=fork,env=env,capture_output=True,text=True);result=json.loads(p.stdout)
   save('cli-command-'+kind,dict(argv=argv,cwd=str(fork),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
  after=rows();save(transport+'-'+kind,dict(request=rpc,result=result,before=before,after=after))
  assert not result.get('ok') and 'entry' not in result,(kind,transport,result)
  assert before==after,(kind,transport,'illegal direction appended')
save('direction-oracle',dict(status='PASS',candidate=launch['source_revision'],kinds=[x[0] for x in cases],transports=['mcp','http','cli'],new_model_turns=0,no_append_for_invalid_direction=True))
print('PASS illegal direction for all ten kinds rejected before append through MCP/HTTP/CLI')
