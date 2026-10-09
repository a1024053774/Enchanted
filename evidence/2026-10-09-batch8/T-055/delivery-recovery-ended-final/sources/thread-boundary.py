"""External, controlled native-thread service; no provider or product state writes."""
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import traceback
import uuid

control = Path(os.environ['A2A_TEST_THREAD_CONTROL'])
method, payload = sys.argv[1], json.loads(sys.argv[2])
started = time.time()
# Synchronize the old run's live observation without holding the fixture lock.
if method == 'read':
    observed = json.loads((control / 'store.json').read_text(encoding='utf-8'))
    thread = observed['threads'].get(payload['thread'])
    if (observed['scenario'] == 'hold-observe' and thread and thread.get('prompted') and
            thread.get('name') == 'check-run' and thread.get('reads', 0) >= 1 and
            not (control / 'release-observe').exists()):
        try:
            (control / 'observe-once').mkdir()
        except FileExistsError:
            pass
        else:
            (control / (uuid.uuid4().hex + '.observe-entry.json')).write_text(
                json.dumps({'argv': sys.argv, 'pid': os.getpid(), 'thread_id': payload['thread']}), encoding='utf-8')
            deadline = time.monotonic() + 60
            while not (control / 'release-observe').exists():
                if time.monotonic() >= deadline:
                    (control / 'fixture-error').write_text('Observation barrier expired', encoding='utf-8')
                    break
                time.sleep(0.02)
reply, exit_code = None, 0
with (control / 'lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    store = json.loads((control / 'store.json').read_text(encoding='utf-8'))
    try:
        if method == 'ensure':
            reply = {'ok': True}
        elif method == 'create':
            attempt = payload['attempt']
            store['next'] += 1
            store['threads'][attempt['thread_id']] = dict(
                thread_id=attempt['thread_id'], workspace=attempt['workspace'], provider='codex',
                turn=None, running=False, stopped=False, archived=False,
                blocked=store['scenario'] == 'startup-blocked', reads=0,
                name=payload['task']['task_id'], envMode='worktree', baseRef=attempt['base_commit'])
            reply = {'ok': True}
        elif method == 'start':
            p = store['threads'][payload['thread']]
            if p['blocked']:
                raise RuntimeError('Start called while awaiting approval')
            prompt = payload['prompt']
            run_name = store.get('requested_name', 'check-run')
            p.update(prompted=True, name=run_name, turn='native-turn:' + p['thread_id'])
            if store['scenario'] == 'post-prompt-blocked':
                p['blocked'] = True
            store['prompts'].append({'thread_id': p['thread_id'], 'name': p['name'], 'text': prompt})
            reply = {'ok': True}
        elif method == 'read':
            p = store['threads'].get(payload['thread']) or store.get('archived', {}).get(payload['thread'])
            if not p:
                raise LookupError(payload['thread'])
            if p.get('prompted'):
                p['reads'] += 1
                if p['reads'] > 1 and store['scenario'] == 'leader-changed':
                    p['turn'] = 'replaced-turn:' + p['thread_id']
                elif p['reads'] > 1 and store['scenario'] == 'identity-changed':
                    p['workspace'] = '/unknown/replaced-worktree'
            reply = dict(p)
            if store['scenario'] == 'helper-joins' and p.get('prompted'):
                reply['active_tools'] = ['transient-shell-command']
        elif method == 'submit-begin':
            p = store['threads'][payload['thread']]
            p['running'] = True
            reply = dict(p)
        elif method == 'submit-end':
            p = store['threads'][payload['thread']]
            p['running'] = False
            reply = dict(p)
        elif method == 'stop':
            p = store['threads'][payload['thread']]
            p['stopped'] = True
            reply = dict(p)
        elif method == 'archive':
            p = store['threads'].pop(payload['thread'])
            p['archived'] = True
            store.setdefault('archived', {})[payload['thread']] = p
            store['closes'].append(payload['thread'])
            reply = dict(p)
        else:
            raise RuntimeError('Unsupported thread service request: ' + method)
    except Exception:
        exit_code = 97
        reply = {'fixture_error': traceback.format_exc()}
        (control / 'fixture-error').write_text(reply['fixture_error'], encoding='utf-8')
    temporary = control / (uuid.uuid4().hex + '.store.tmp')
    temporary.write_text(json.dumps(store), encoding='utf-8')
    temporary.replace(control / 'store.json')
    with (control / 'boundary.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps(dict(layer='isolated-native-thread-service', pid=os.getpid(),
            argv=sys.argv, cwd=os.getcwd(), started_epoch=started, finished_epoch=time.time(),
            method=method, request=payload, result=reply, exit_code=exit_code,
            threads_after=store['threads'], prompts_after=len(store['prompts']), closes_after=store['closes']))+'\n')
print(json.dumps(reply))
sys.exit(exit_code)
