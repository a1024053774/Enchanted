"""Create/dispatch/attach/reclaim only via the production CLI HTTP transport; readback is read-only."""
import json,os,subprocess,sys,tempfile,uuid,urllib.request,sqlite3,time
from pathlib import Path
here=Path(__file__).resolve().parent
label,phase=sys.argv[1:]
run=here/label
fork=Path('/Users/luckye/Documents/Code/synara')
native=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t044/home/dev')
endpoint='http://127.0.0.1:5817'
env={**os.environ,'A2A_SYNARA_SLOT':'t044','A2A_GATE_BEARER':'t044-isolated-owner-placeholder',
 'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0'}
for key in ['GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_CONFIG_COUNT']:env.pop(key,None)
if phase=='create':run.mkdir()
trace=run/('create.jsonl' if phase=='create' else 'reclaim.jsonl')
assert not trace.exists()
def record(value):
 with trace.open('a',encoding='utf-8') as out:out.write(json.dumps(value,ensure_ascii=False)+'\n')
def command(argv,cwd):
 result=subprocess.run(argv,cwd=cwd,env=env,text=True,capture_output=True,timeout=60)
 record({'argv':argv,'cwd':str(cwd),'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 assert result.returncode==0,(argv,result.stdout,result.stderr)
 return result.stdout.strip()
def gate(body):
 argv=['./a2a/scripts/bun','packages/a2a-gates/src/cli.ts',endpoint,json.dumps(body,ensure_ascii=False)]
 return json.loads(command(argv,fork))
def memberships():
 result=json.load(urllib.request.urlopen(endpoint+'/api/a2a/membership',timeout=30));record({'method':'GET','path':'/api/a2a/membership','result':result});return result['tasks']
def shell(thread):
 result=json.loads(command(['./a2a/scripts/bun',str(here/'read-native.mjs'),endpoint,thread],fork))
 raw=result['exit']['value']['thread']
 value={'thread':thread,'project':raw['projectId'],'title':raw['title'],'model':raw['modelSelection'],
  'runtimeMode':raw['runtimeMode'],'envMode':raw['envMode'],'archivedAt':raw['archivedAt'],'session':raw['session'],
  'messages':[{'role':m['role'],'text':m['text'],'dispatch_origin':m.get('dispatchOrigin')} for m in raw['messages']]}
 record({'read_only_native_projection':value});return value
if phase=='create':
 root=Path(tempfile.mkdtemp(prefix='window-cli-',dir='/Volumes/WD-Elements/dev-cache/synara/instances/t044/fixtures'));repo=root/'repo';repo.mkdir()
 def git(*args):return command(['git','-C',str(repo),*args],repo)
 git('init');git('config','user.name','T-044 final window');git('config','user.email','t044@example.invalid');git('config','commit.gpgsign','false')
 (repo/'input.txt').write_text('Independent task window sentinel\n',encoding='utf-8');git('add','input.txt');git('-c','core.hooksPath=/dev/null','commit','-m','Independent fixture');base=git('rev-parse','HEAD')
 task='r2-'+uuid.uuid4().hex[:12];title='门禁任务 · '+label
 instructions=root/'instructions.txt';instructions.write_text('执行任务窗口夹具。供应商关闭，不调用模型。标记 '+task+'\n',encoding='utf-8')
 review=root/'review.txt';review.write_text('审查角色 '+task+'：核对任务归属与结束历史；不提交交付，不调用模型。\n',encoding='utf-8')
 oracle=root/'oracle.py';oracle.write_text('raise SystemExit(0)\n',encoding='utf-8')
 def call(cmd,**args):return gate({'command':cmd,'task':task,**args})
 created=call('create',project=task+'-project',title=title,repo=str(repo),base=base,oracle=str(oracle),instructions=str(instructions))
 group=next(m for m in memberships() if m['taskId']==task);assert group['title']==title and group['projectId']==created['task']['project_id'] and group['members']==[]
 dispatched=call('dispatch',runtimeMode='approval-required')
 model={'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'high','fastMode':False}}
 attached=call('attach',role='reviewer',modelSelection=model,runtimeMode='approval-required',instructions=str(review))
 worker=dispatched['attempt']['thread_id'];reviewer=attached['attachment']['thread_id']
 group=next(m for m in memberships() if m['taskId']==task);assert group['members']==[{'threadId':worker,'role':'worker'},{'threadId':reviewer,'role':'reviewer'}]
 for thread,role,text in [(worker,'worker',instructions.read_text()),(reviewer,'reviewer',review.read_text())]:
  row=shell(thread);assert row['project']==created['task']['project_id'];assert row['session']['status']=='error',row
  assert any(m['role']=='user' and m['dispatch_origin']=='agent' and text in m['text'] for m in row['messages'])
  if role=='reviewer':assert row['model']['model']==model['model'] and row['model']['options']==model['options'] and row['envMode']=='local'
 fixture={'root':str(root),'repo':str(repo),'task':task,'title':title,'base':base,'created':created,'dispatched':dispatched,'attached':attached,'review_input':model,'fork':command(['git','rev-parse','HEAD'],fork)}
 (run/'fixture.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
 fixture=json.loads((run/'fixture.json').read_text());task=fixture['task']
 def call(cmd,**args):return gate({'command':cmd,'task':task,**args})
 before=call('status')['task'];reviewer=fixture['attached']['attachment']['thread_id'];worker=fixture['dispatched']['attempt']['thread_id']
 ordinary=call('reclaim',thread=reviewer);assert call('status')['task']==before
 call('reclaim',attempt=fixture['dispatched']['attempt']['attempt_id'])
 group=next(m for m in memberships() if m['taskId']==task);assert len(group['members'])==2 and all(m.get('endedAt') for m in group['members'])
 events=call('events')['events'];assert len([e for e in events if e['type']=='attached'])==1
 assert len([e for e in events if e['type']=='attachment_reclaimed'])==1 and len([e for e in events if e['type']=='reclaimed'])==1
 for thread in [worker,reviewer]:
  row=shell(thread);assert row['archivedAt'] and row['session']['status']=='stopped',row
 assert not any(e['type'] in ['submitted','verification_started','integrated'] for e in events)
 (run/'ended-membership.json').write_text(json.dumps(group,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS CLI HTTP '+phase)
