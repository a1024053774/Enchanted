import json,os,sys,time,uuid,sqlite3,subprocess,datetime as dt,shutil,tempfile
from pathlib import Path
out=Path(__file__).resolve().parent;results=out/'native-11';results.mkdir()
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
    assert data['ok'],data
    if operation=='thread':
     assert data['result']['_tag']=='Some',data
     return data['result']['value']
    return data['result']
  time.sleep(.1)
 raise TimeoutError(operation)
def rpc(name,cmd):
 path=results/(name+'.input.json');path.write_text(json.dumps(cmd,ensure_ascii=False)+'\n')
 argv=['./a2a/scripts/bun','run',str(out/'native-rpc-02.mjs'),name,origin,str(path)]
 env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','SHELL','LC_ALL')};env.update(A2A_SYNARA_SLOT='t056-native-10',T056_EVIDENCE=str(results))
 r=subprocess.run(argv,cwd=fork,env=env,text=True,capture_output=True,timeout=45);save(name+'.command',dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
ask=json.loads((out/'native-10/ask.input.json').read_text());thread=ask['threadId']
isolation=json.loads((out/'native-10/isolation.json').read_text());home=Path(isolation['home'])
detail=control('thread',thread=thread)
question=next((m for m in reversed(detail['messages']) if m.get('asyncUserInput',{}).get('questions')),None)
assert question,detail
save('question-observation',dict(thread=thread,detail=detail,has_native_questions=True))
answer_id=uid();qid=question['id'];answers=['蓝色 Ω 用户哨兵']*len(question['asyncUserInput']['questions'])
rpc('answer',dict(type='thread.turn.start',commandId=uid(),threadId=thread,message=dict(messageId=answer_id,role='user',text='原生异步答复',attachments=[]),asyncUserInputResponse=dict(messageId=qid,answers=answers),runtimeMode='approval-required',interactionMode='default',createdAt=now()))
time.sleep(.5)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:inputs=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs WHERE message=?',(answer_id,))]
assert len(inputs)==1 and inputs[0]['form']=='answer' and inputs[0]['certainty']=='observed' and inputs[0]['target']['request']==qid,inputs
assert inputs[0]['reply_to']==qid and inputs[0]['content']==answers
save('answer-oracle',dict(status='PASS',thread=thread,native_question_id=qid,expected_answers=answers,inputs=inputs,home=str(home),real_turns_requested=2))
print('PASS native async answer',thread)

for _ in range(300):
 detail=control('thread',thread=thread)
 matched=[m for m in detail['messages'] if m['role']=='assistant' and answers[0] in m['text']]
 if matched and detail.get('session',{}).get('activeTurnId') is None:break
 time.sleep(.2)
else:raise TimeoutError('native answer acknowledgement')
save('native-ack',dict(status='PASS',thread=thread,detail=detail,expected_answer=answers[0]))
