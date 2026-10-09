import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

out=Path(__file__).resolve().parent; label=sys.argv[1]
launch=json.loads((out/('server-'+label+'-launch.json')).read_text(encoding='utf-8'))
root=Path(launch['root']); fork=Path('/Users/luckye/Documents/Code/synara')
oracle=json.loads((out/label/'transport-oracle.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('t058_presets_api',out.parents[1]/'2026-10-09-batch8/T-055/fixture-api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api); f=api.Fixture(root)
results=out/(label+'-presets15');results.mkdir()
def save(name,value):
 with (results/(name+'.json')).open('x',encoding='utf-8') as s:json.dump(value,s,ensure_ascii=False,indent=2);s.write('\n')
def listed(token):
 result=f.http('/mcp',dict(jsonrpc='2.0',id=str(uuid.uuid4()),method='tools/list',params={}),token)
 return sorted(t['name'] for t in result['result']['tools'])
old=(root/'private-executor.token').read_text(encoding='utf-8'); thread=oracle['threads']['executor']
expected_old=['a2a_attach','a2a_claim','a2a_create','a2a_dispatch','a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_integrate','a2a_issues','a2a_reclaim','a2a_revise','a2a_revoke','a2a_run','a2a_status','a2a_verify']
expected_new=['a2a_disposition','a2a_events','a2a_inbox_ack','a2a_inbox_list','a2a_inbox_send','a2a_issues','a2a_status','a2a_stop']
env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']};env['A2A_SYNARA_SLOT']='s11-t058-'+label
def bind(preset):
 # A setup-only change through the actual preset store, not an exposed tool.
 code='import { A2AMembership } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/membership.ts"; const store=new A2AMembership('+json.dumps(str(root/'userdata/a2a-gates'))+'); store.bindPreset('+json.dumps(thread)+','+json.dumps(preset)+'); store.close();'
 argv=['./a2a/scripts/bun','-e',code]; p=subprocess.run(argv,cwd=fork,env=env,capture_output=True,text=True)
 save('binding-'+preset,dict(argv=argv,cwd=str(fork),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0
try:
 bind('ideation')
 observed_old=listed(old);assert observed_old==expected_old
 path=root/'private-fresh15.token';issued=f.control('token',thread=thread,path=str(path));fresh=path.read_text(encoding='utf-8')
 observed_new=listed(fresh);assert observed_new==expected_new
 save('frozen-and-fresh',dict(candidate=launch['source_revision'],old_expected=expected_old,old_observed=observed_old,new_expected=expected_new,new_observed=observed_new,new_capabilities=issued['capabilities']))
finally:bind('executor')
ordinary=str(uuid.uuid4());now=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
f.control('command',command=dict(type='thread.create',commandId=str(uuid.uuid4()),threadId=ordinary,projectId='t058-control',title='普通会话能力哨兵',modelSelection=dict(provider='codex',model='gpt-6.1-sol'),runtimeMode='full-access',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now))
path=root/'private-ordinary15.token';normal=f.control('token',thread=ordinary,path=str(path))
expected=['automation:write','browser:control','device:control','diagnostics:read','thread:read','thread:write']
assert normal['capabilities']==expected,normal
save('ordinary',dict(expected_from_parent_and_decision01=expected,observed=normal['capabilities'],thread=ordinary,new_model_turns=0))
print('PASS real signed credentials stay frozen, new credential sees changed preset, ordinary Synara capabilities unchanged')
