import json,os,sys,time,uuid,sqlite3,subprocess,datetime as dt,shutil,tempfile
from pathlib import Path
out=Path(__file__).resolve().parent;results=out/'native-10';results.mkdir()
launch=json.loads((out/'server-boundaries-restart-09-launch.json').read_text());root=Path(launch['root']);origin=json.loads((root/'ready.json').read_text())['origin'];fork=Path('/Users/luckye/Documents/Code/synara')
def save(name,v): (results/(name+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def uid():return str(uuid.uuid4())
def now():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def control(operation,**args):
 token=uid();(root/'control'/f'{token}.request.json').write_text(json.dumps(dict(operation=operation,**args)))
 path=root/'control'/f'{token}.result.json'
 for _ in range(900):
  if path.exists():
   data=json.loads(path.read_text())
   if not data.get('pending'):
    assert data['ok'],data;return data['result']
  time.sleep(.1)
 raise TimeoutError(operation)
def rpc(name,cmd):
 path=results/(name+'.input.json');path.write_text(json.dumps(cmd,ensure_ascii=False)+'\n')
 argv=['./a2a/scripts/bun','run',str(out/'native-rpc-02.mjs'),name,origin,str(path)]
 env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','SHELL','LC_ALL')};env.update(A2A_SYNARA_SLOT='t056-native-10',T056_EVIDENCE=str(results))
 r=subprocess.run(argv,cwd=fork,env=env,text=True,capture_output=True,timeout=45);save(name+'.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
binary=str(Path(shutil.which('codex')).resolve());version=subprocess.check_output([binary,'--version'],text=True).strip();assert version=='codex-cli 0.162.0',version
home=Path(tempfile.mkdtemp(prefix='a2a-t056-native-',dir='/tmp')).resolve();home.chmod(0o700)
shutil.copyfile('/Users/luckye/.codex/auth.json',home/'auth.json');(home/'auth.json').chmod(0o600)
config='check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n[projects.'+json.dumps(str(root))+']\ntrust_level = "trusted"\n';(home/'config.toml').write_text(config);(home/'rules').mkdir();rules='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n';(home/'rules/default.rules').write_text(rules)
launcher=root/'codex-fixed-t056';launcher.write_text('#!/bin/sh\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n');launcher.chmod(0o700)
save('isolation',dict(home=str(home),launcher=launcher.read_text(),version=version,config=config,rules=rules,hooks=[],copied=['auth.json'],provider_requested='codex',model='gpt-6.1-sol',reasoning='xhigh',requested_tier='fast',limits='Requested Fast is not proof of actual supplier tier.'))
control('settings',patch={'providers':{'codex':{'enabled':True,'homePath':str(home),'binaryPath':str(launcher)}}})
thread=uid();control('command',command=dict(type='thread.create',commandId=uid(),threadId=thread,projectId='t056-project',title='T056 原生异步问题',modelSelection=dict(provider='codex',model='gpt-6.1-sol',options={'reasoningEffort':'xhigh','fastMode':True}),runtimeMode='approval-required',interactionMode='default',envMode='local',branch=None,worktreePath=None,createdAt=now()))
prompt='这是 T-056 用户输入记录的隔离验收。不要修改任何文件，不要运行命令，不要调用 MCP 工具，不要 submit。请使用 request_user_input_async 工具问我一题：标题“颜色 Ω”，选项“蓝色”和“红色”。输出该异步问题后停止本回合并等待用户回答。收到回答后，只回复“收到：”加用户回答，不调用任何工具。'
rpc('ask',dict(type='thread.turn.start',commandId=uid(),threadId=thread,message=dict(messageId=uid(),role='user',text=prompt,attachments=[]),runtimeMode='approval-required',interactionMode='default',createdAt=now()))
question=None
for _ in range(600):
 detail=control('thread',thread=thread)
 messages=detail.get('messages',[])
 question=next((m for m in reversed(messages) if m.get('asyncUserInput',{}).get('questions')),None)
 if question:break
 if any(m.get('role')=='assistant' and not m.get('streaming',False) for m in messages):
  # Give final question metadata ingestion a bounded chance to settle.
  time.sleep(.5);detail=control('thread',thread=thread);question=next((m for m in reversed(detail.get('messages',[])) if m.get('asyncUserInput',{}).get('questions')),None)
  if question:break
 time.sleep(.2)
save('question-observation',dict(thread=thread,detail=detail,has_native_questions=bool(question)))
if not question:
 save('result',dict(status='INCOMPLETE',reason='Native provider did not produce async question metadata in this turn. No synthetic provider event substitutes for it.',thread=thread,home=str(home)))
 print('INCOMPLETE native async question',thread);raise SystemExit(1)
answer_id=uid();qid=question['id'];answers=['蓝色 Ω 用户哨兵']*len(question['asyncUserInput']['questions'])
rpc('answer',dict(type='thread.turn.start',commandId=uid(),threadId=thread,message=dict(messageId=answer_id,role='user',text='原生异步答复',attachments=[]),asyncUserInputResponse=dict(messageId=qid,answers=answers),runtimeMode='approval-required',interactionMode='default',createdAt=now()))
time.sleep(.5)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:inputs=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs WHERE message=?',(answer_id,))]
assert len(inputs)==1 and inputs[0]['form']=='answer' and inputs[0]['certainty']=='observed' and inputs[0]['target']['request']==qid,inputs
assert inputs[0]['reply_to']==qid and inputs[0]['content']==answers
save('answer-oracle',dict(status='PASS',thread=thread,native_question_id=qid,expected_answers=answers,inputs=inputs,home=str(home),real_turns_requested=2))
print('PASS native async answer',thread)
