import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys
import time
import uuid
import urllib.request
from pathlib import Path

out = Path(__file__).resolve().parent
label = sys.argv[1] if len(sys.argv) > 1 else 'red-matrix-02'
assert label.replace('-', '').replace('_', '').isalnum(), label
root = Path(json.loads((out / ('server-' + label + '-launch.json')).read_text())['root'])
fork = Path('/Users/luckye/Documents/Code/synara')
origin = json.loads((root / 'ready.json').read_text())['origin']
results = out / label
results.mkdir()


def save(name, value):
    with (results / (name + '.json')).open('x', encoding='utf-8') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write('\n')


def control(operation, **args):
    name = str(uuid.uuid4())
    (root / 'control' / f'{name}.request.json').write_text(
        json.dumps(dict(operation=operation, **args)), encoding='utf-8')
    path = root / 'control' / f'{name}.result.json'
    for _ in range(450):
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            if not data.get('pending'):
                assert data['ok'], data
                return data['result']
        time.sleep(.1)
    raise TimeoutError(operation)


def gate(command, **args):
    req = urllib.request.Request(origin + '/api/a2a',
        data=json.dumps(dict(command=command, **args)).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.load(response)
    save('gate-' + command + str(len(list(results.iterdir()))), data)
    assert data['ok'], data
    return data


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def uid():
    return str(uuid.uuid4())


env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
env.update(A2A_SYNARA_SLOT='t056-' + label, T056_EVIDENCE=str(results))


def rpc(label, command, tag='orchestration.dispatchCommand'):
    path = results / (label + '.input.json')
    path.write_text(json.dumps(command, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    argv = ['./a2a/scripts/bun', 'run', str(out / 'native-rpc-02.mjs'), label, origin, str(path)]
    run = subprocess.run(argv, cwd=fork, env={**env, 'A2A_RPC_TAG': tag},
        text=True, capture_output=True, timeout=45)
    save(label + '.command', dict(argv=argv, cwd=str(fork), rpc_tag=tag,
        exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr))
    assert run.returncode == 0, (label, run.stdout, run.stderr)


def message(label, thread, extra=None):
    command = dict(type='thread.turn.start', commandId=uid(), threadId=thread,
        message=dict(messageId=uid(), role='user', text=label + ' 用户哨兵 Ω', attachments=[]),
        runtimeMode='approval-required', interactionMode='default', createdAt=now())
    if extra:
        command.update(extra)
    rpc(label, command)
    return command['message']['messageId']


repo = root / 'repo'
repo.mkdir()
genv = {**env, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, env=genv).strip()


git('init')
git('config', 'user.name', 'T056 isolated red')
git('config', 'user.email', 'fixture@example.invalid')
git('config', 'commit.gpgsign', 'false')
(repo / 'fixture.txt').write_text('Independent original\n', encoding='utf-8')
git('add', 'fixture.txt')
git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'Independent original')
(root / 'oracle.py').write_text(
    'from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="Independent original\\n"\n',
    encoding='utf-8')
(root / 'instructions.txt').write_text(
    'T056 隔离记录器探针；provider 全部禁用；不调用模型、不修改文件。', encoding='utf-8')
created = gate('create', task='t056', project='t056-project', repo=str(repo),
    base=git('rev-parse', 'HEAD'), oracle=str(root / 'oracle.py'), instructions=str(root / 'instructions.txt'))
dispatched = gate('dispatch', task='t056', runtimeMode='approval-required')
worker = dispatched['attempt']['thread_id']
reviewer = gate('attach', task='t056', role='reviewer',
    modelSelection=dict(provider='codex', model='gpt-6.1-sol'), runtimeMode='approval-required',
    instructions=str(root / 'instructions.txt'))['attachment']['thread_id']
controller = gate('attach', task='t056', role='controller',
    modelSelection=dict(provider='codex', model='gpt-6.1-sol'), runtimeMode='approval-required',
    instructions=str(root / 'instructions.txt'))['attachment']['thread_id']
ordinary = uid()
control('command', command=dict(type='thread.create', commandId=uid(), threadId=ordinary,
    projectId='t056-project', title='普通非受管 thread', modelSelection=dict(provider='codex', model='gpt-6.1-sol'),
    runtimeMode='approval-required', interactionMode='default', envMode='local', branch=None,
    worktreePath=None, createdAt=now()))
cases = []
for label, thread in [('managed-message', worker), ('attached-message', reviewer),
                      ('ordinary-message', ordinary), ('controller-message', controller)]:
    message_id = message(label, thread)
    cases.append(dict(label=label, thread=thread, message=message_id, form='message'))
question = uid()
control('command', command=dict(type='thread.message.assistant.delta', commandId=uid(), threadId=ordinary,
    messageId=question, delta='请选择颜色', createdAt=now()))
control('command', command=dict(type='thread.message.assistant.complete', commandId=uid(), threadId=ordinary,
    messageId=question, asyncQuestions=[dict(title='颜色', options=['蓝', '红'])], createdAt=now()))
message_id = message('async-answer', ordinary,
    dict(asyncUserInputResponse=dict(messageId=question, answers=['蓝'])))
cases.append(dict(label='async-answer', thread=ordinary, message=message_id, form='answer', request=question))
for label, kind, extra, form in [
    ('structured-answer', 'thread.user-input.respond', dict(answers={'q1': '手写 Ω 答复'}), 'answer'),
    ('approval', 'thread.approval.respond', dict(decision='accept'), 'approval'),
    ('denial', 'thread.approval.respond', dict(decision='decline'), 'denial'),
    ('ui-stop', 'thread.session.stop', {}, 'action'),
    ('ui-interrupt', 'thread.turn.interrupt', {}, 'action'),
]:
    command = dict(type=kind, commandId=uid(), threadId=ordinary, createdAt=now(), **extra)
    if kind.endswith('respond'):
        command['requestId'] = uid()
    rpc(label, command)
    cases.append(dict(label=label, thread=ordinary, command=command['commandId'],
        form=form, request=command.get('requestId')))
time.sleep(.6)
events = control('events')
save('domain-events', events)
state = root / 'userdata/a2a-gates/state.sqlite3'
assert state.is_file(), state
with sqlite3.connect(state) as db:
    inputs = [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
    gate_events = [dict(seq=row[0], type=row[1], details=json.loads(row[2]))
        for row in db.execute('SELECT seq,type,details FROM events ORDER BY seq')]
save('user-inputs', inputs)
save('gate-events', gate_events)
for case in cases:
    if case.get('message'):
        matches = [value for value in inputs if value['target'].get('message') == case['message']]
        domain = [event for event in events if event.get('payload', {}).get('messageId') == case['message']]
    else:
        domain = [event for event in events if event.get('commandId') == case['command']]
        if case.get('request'):
            matches = [value for value in inputs if value['target'].get('request') == case['request']]
        else:
            event_ids = {event['eventId'] for event in domain}
            matches = [value for value in inputs if value.get('source_ref', {}).get('event_id') in event_ids]
    case.update(expected_form=case['form'], observed_count=len(matches),
        contract_pass=len(matches) == 1 and matches[0]['form'] == case['form'],
        authoritative_events=[dict(eventId=e['eventId'], sequence=e['sequence'], type=e['type']) for e in domain])
summary = dict(status='INCOMPLETE',
    fork=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip(),
    root=str(root), provider_enabled=False, model_turns=0, cases=cases,
    limitations=[
        '真实服务、WS/HTTP、门禁、SQLite 与事件流；provider 全部禁用。异步问题由真实 internal command 建立，不是原生 Codex provider 事件；本次红态不证明原生提问或执行结果。',
        '结构化回答和审批的 RPC 正常接受并有域事件；request 是隔离哨兵，不主张真实 provider 请求的送达。',
    ])
save('summary', summary)
print(json.dumps(cases, ensure_ascii=False, indent=2))
assert all(case['contract_pass'] for case in cases), 'T056 coverage contract missing on parent revision'
