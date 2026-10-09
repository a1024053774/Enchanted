import importlib.util
import json
from pathlib import Path
import sys
import time

out = Path(__file__).resolve().parent
old = out.parents[1]/'2026-10-09-batch8/T-055'
spec = importlib.util.spec_from_file_location('fixture_api', old/'fixture-api.py')
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
f = api.Fixture(sys.argv[1])
label = sys.argv[2]
thread = json.loads((out/'native-initial-command-01.json').read_text())['thread']
expected = [
    '问题 1：oracle 漏了空页\n分页夹具没有覆盖最后一页为空的情况。\n用户答复：补上，并在 RESULTS 里写明。\n\n问题 3：README 的构建命令已过期\n用户答复：不用管，T-050 会重写。\n\n问题 4：长正文哨兵\n'+'😀'*599+'…\n用户答复：问题 99：原样\n用户答复：保留分隔文字。\n\n（另：你上报的问题 5 已被关闭，理由：已登记为后续工作。如不同意，请重新上报并补充证据。）',
    '问题 2：未答哨兵\n这题未答，不参加发送。\n用户答复：逐个发送的第一题。',
    '问题 5：重复问题\n已经登记为后续工作。\n用户答复：逐个发送的第二题。',
]
until = time.monotonic()+55
while True:
    raw = f.control('thread', thread=thread)
    value = raw.get('value', raw)
    if value['latestTurn']['state'] == 'completed' and not value['hasPendingApprovals'] and not value['hasPendingUserInput']: break
    if time.monotonic() > until: raise TimeoutError('native reply completion')
    time.sleep(.5)
messages = [{k:m.get(k) for k in ['id','role','text','dispatchOrigin','turnId','createdAt']} for m in value['messages']]
user = [message for message in messages if message['role']=='user' and message['dispatchOrigin']=='user']
answers = f.gate('issues',task='t057')
events = f.gate('events',task='t057')
failure = None
try:
    assert [m['text'] for m in user] == expected, 'native user messages differ from requirement-written oracle'
    assert len(user)==3
    assert len(answers['user_inputs'])==5
    assert all(input['form']=='answer' and input['reply_to'] and input['bundle_id'] for input in answers['user_inputs'])
    actual_ids = {m['id'] for m in user}
    assert len(actual_ids)==3 and all(actual_ids)
    assert {input['target']['message'] for input in answers['user_inputs']} == actual_ids
    assert len({input['bundle_id'] for input in answers['user_inputs'][:3]})==1
    assert len({input['bundle_id'] for input in answers['user_inputs'][3:]})==2
    assert [input['question']['number'] for input in answers['user_inputs']] == [1,3,4,2,5]
    assert not any(input['form']=='message' for input in answers['user_inputs'])
    assert len([e for e in events['events'] if e['type']=='human_intervention'])==5
    assert len([e for e in events['events'] if e['type']=='issue_closure_notified'])==1
    assert len([m for m in messages if m['role']=='assistant'])==4
    assert all(v['state']=='已送达' for v in answers['issues'])
    assert answers['human_input_observer']['state']=='healthy'
except AssertionError as error: failure=str(error)
with (out/(label+'.json')).open('x',encoding='utf-8') as file:
    json.dump({'thread':thread,'expected':expected,'native_user_messages':user,'native_messages':messages,
               'latestTurn':value['latestTurn'],'pendingApprovals':value['hasPendingApprovals'],'failure':failure,
               'issues':answers,'events':events,'model_turn_count':len([m for m in messages if m['role']=='assistant'])},file,ensure_ascii=False,indent=2)
print(json.dumps({'label':label,'failure':failure,'native_user_messages':len(user),'answer_inputs':len(answers['user_inputs']),
                  'model_turns':len([m for m in messages if m['role']=='assistant'])},ensure_ascii=False))
if failure: raise SystemExit(1)
