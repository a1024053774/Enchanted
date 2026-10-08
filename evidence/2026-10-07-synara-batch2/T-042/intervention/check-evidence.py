import json
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda n:json.loads((p/(n+'.json')).read_text())
body=lambda n:load(n)['body']
thread=lambda n:load(n)['messages'][-1]['exit']['value']['thread']
a=body('dispatch')['attempt'];pos=thread('native-managed-complete');neg=thread('native-unmanaged-complete')
before=body('events-before')['events'];after=body('events-managed-complete')['events'];final=body('events-negative-complete')['events']
assert not [e for e in before if e['type']=='human_intervention']
assert after[:-1]==before and final==after
h=[e for e in final if e['type']=='human_intervention'];assert len(h)==1
e=h[0];d=e['details'];message=[m for m in pos['messages'] if m.get('dispatchOrigin')=='user'];assert len(message)==1
assert message[0]['text']=='人工介入复验 T042-人-81：请只回复 OK，不要调用工具或修改文件，不要提交或交付。'
assert d['text']==message[0]['text'] and d['message_id']==message[0]['id'] and d['thread_id']==pos['id']==a['thread_id']
assert d['dispatch_origin']==message[0]['dispatchOrigin']=='user'
assert e['task']==d['task_id']==a['task_id'] and e['attempt']==d['attempt_id']==a['attempt_id']
for k in ['session_id','fence','spec_rev']:assert d[k]==a[k]
assert body('status-managed-complete')['task']==body('dispatch')['task']==body('status-after-negative')['task']
assert body('unmanaged-binding-before')['task'] is None and body('unmanaged-binding-after')['task'] is None
assert all(m['threadId']!=neg['id'] for t in body('membership-before-negative')['tasks'] for m in t['members'])
assert [m['text'] for m in neg['messages'] if m.get('dispatchOrigin')=='user']==['普通会话反例 T042-非-29：请只回复 OK，不要调用工具或修改文件。']
for t in [pos,neg]:
 assert t['session']['status']=='ready' and t['session']['activeTurnId'] is None
 assert not t['pendingInteractions'] and len(t['checkpoints'])==1
 assert t['modelSelection']['model']=='gpt-6.1-sol' and t['modelSelection']['options']['fastMode'] is True
 assert t['runtimeMode']=='full-access'
 assert [m['text'] for m in t['messages'] if m['role']=='assistant']==['OK']
assert '人工介入 ·  1' in (p/'03-managed-expanded.txt').read_text()
print(json.dumps({'status':'PASS','human_intervention':d,'gate_event_count_before':len(before),'after_managed':len(after),'after_unmanaged':len(final),'business_state':'claimed unchanged','completed_model_turns':2,'negative_thread':neg['id'],'negative_message':neg['messages'][0]['id']},ensure_ascii=False,indent=2))
