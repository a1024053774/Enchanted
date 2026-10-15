"""A-06 I1 driver: register one dispatch, arm protocol, release once, stop at idle."""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
CORE = SOURCE / 'workbench/tests'
sys.path.insert(0, str(CORE))
from t078_09b_protocol_core import (ProtocolRefusal, normalize_anthropic_request,
                                    validate_request)


def uid():
    return str(uuid.uuid4())


def registration(prompt, binding, seq=1):
    dispatch = {
        'id': uid(), 'seq': seq, 'role': 'ideation',
        'text': f'⟦主控 #{seq}⟧\n{prompt}',
        'request_id': uid(), 'stop_id': uid(),
        'attempt': binding['attempt_id'], 'session': binding['session_id'],
        'fence': binding['fence'],
    }
    registry = {'dispatches': {dispatch['id']: dispatch}, 'message_budget': 6, 'ack_text': 'I1_ACK'}
    return dispatch, registry


def anthropic_body(dispatch):
    return {'model': 'claude-haiku-5-5', 'stream': True,
            'messages': [{'role': 'user', 'content': dispatch['text']}]}


def custom_request(dispatch):
    return {'path': '/v1/messages', 'dispatch_id': dispatch['id'], 'dispatch_seq': dispatch['seq'],
            'role': dispatch['role'], 'request_id': dispatch['request_id'], 'stop_id': dispatch['stop_id'],
            'attempt': dispatch['attempt'], 'session': dispatch['session'], 'fence': dispatch['fence'],
            'messages': [{'role': 'user', 'content': dispatch['text']}], 'stream': True,
            'model': 'claude-haiku-5-5'}


def spy(mutant=None):
    binding = {'attempt_id': uid(), 'session_id': uid(), 'fence': 1}
    dispatch, registry = registration('I1 A-06 ideation prompt; acknowledge once and stop.', binding)
    if mutant is None:
        normalized, anthropic = normalize_anthropic_request(anthropic_body(dispatch), registry, 'ideation')
        response = validate_request(normalized, registry)
        return {'status': 'PASS', 'mutant': None, 'decision': '200', 'stopped': False,
                'anthropic_normalization': anthropic, 'dispatch': dispatch,
                'response_events': len(response['sse']), 'messages_sent': 1, 'roots_used': 1}
    request = custom_request(dispatch)
    if mutant == 'text': request['messages'][0]['content'] += ' stale'
    if mutant == 'seq': request['dispatch_seq'] = 2
    if mutant == 'identity': request['attempt'] = ''
    if mutant == 'stop': request['stop_id'] = 'wrong-stop'
    if mutant == 'role': request['role'] = 'executor'
    if mutant == 'budget': request['messages'] = [request['messages'][0] for _ in range(7)]
    try:
        validate_request(request, registry)
    except ProtocolRefusal as error:
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409', 'stopped': True,
                'error': str(error), 'messages_sent': 0, 'roots_used': 0}
    return {'status': 'INCOMPLETE', 'mutant': mutant, 'decision': '200', 'stopped': False,
            'error': 'mutant accepted', 'messages_sent': 1, 'roots_used': 1}


def gate(root, command, *args):
    env = {**os.environ, 'A2A_OPERATOR_CREDENTIAL': str(root / 'operator.json'),
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    result = subprocess.run([
        '/opt/homebrew/bin/node', str(SOURCE / 'workbench/src/gates/cli.ts'),
        '--state', str(root / 'state'), command, *map(str, args),
    ], cwd=SOURCE, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError({'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return json.loads(result.stdout.strip().splitlines()[-1])


def execute(materials, stage_a, approval, output):
    approval_data = json.loads(approval.read_bytes())
    if approval_data.get('approved_by') != 'executor' or approval_data.get('phase') != 'I1':
        raise RuntimeError('i1_approval_required')
    readiness = json.loads((stage_a / 'readiness.json').read_bytes())
    p1 = materials / '09b-a06-b1-ideation-p1-01'
    p1_input = json.loads((p1 / 'input.json').read_bytes())
    root = Path(readiness['root']).resolve(); thread = p1_input['thread']
    prompt = (materials / 'i1-prompt.txt').read_text(encoding='utf-8')
    api_root = root / 'roles' / 'ideation'
    api_ready = json.loads((api_root / 'api-ready.json').read_bytes())
    if api_ready.get('protocol') != 'a06-registered-anthropic-v1':
        raise RuntimeError('protocol_api_revision_unbound')
    queued = gate(root, 'pane_dispatch', '--thread', thread, '--body-file', materials / 'i1-prompt.txt')
    dispatch = queued['dispatch']
    binding = readiness['target_binding']
    assert dispatch['seq'] >= 1 and dispatch['text'] == f"⟦主控 #{dispatch['seq']}⟧\n{prompt}"
    registry_dispatch = {**dispatch, 'role': 'ideation',
                         'attempt': binding['attempt_id'], 'session': p1_input['session'], 'fence': binding['fence']}
    registry = {'dispatches': {dispatch['id']: registry_dispatch}, 'message_budget': 6, 'ack_text': 'I1_ACK'}
    (api_root / 'protocol-registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    released = gate(root, 'pane_release', '--thread', thread, '--reason', 'I1 approval: release one registered dispatch')
    deadline = time.monotonic() + 45
    response = None
    events = []
    stop_events = []
    while time.monotonic() < deadline:
        response_file = api_root / 'responses.ndjson'
        if response_file.exists():
            for line in response_file.read_text(encoding='utf-8').splitlines():
                row = json.loads(line)
                if row.get('dispatch_id') == dispatch['id']:
                    response = row; break
        events = gate(root, 'orchestration_events').get('events', [])
        stop_events = [event for event in events if event.get('launch') == p1_input['launch'] and event.get('type') == 'turn_end_signal']
        if response and stop_events: break
        time.sleep(.1)
    if response is None: raise RuntimeError('i1_response_deadline')
    if len(stop_events) != 1 or not stop_events[0].get('data',{}).get('prompt_id'):
        raise RuntimeError('i1_stop_id_unobserved')
    registry_dispatch['request_id']=response['request_id']; registry_dispatch['stop_id']=stop_events[0]['data']['prompt_id']
    registry['dispatches'][dispatch['id']]=registry_dispatch
    (api_root / 'protocol-registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    status = gate(root, 'pane_status', '--thread', thread)
    if status.get('state') != 'idle': raise RuntimeError('i1_not_idle')
    result = {'status': 'PASS', 'dispatch': dispatch, 'registered': registry_dispatch,
              'response': response, 'stop_event': stop_events[0], 'release': released, 'messages_sent': 1,
              'roots_used': 1, 'stop_condition': 'one response, one turn idle, no retry'}
    output.mkdir(parents=False, exist_ok=False)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['spy', 'execute'], required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--materials', type=Path)
    parser.add_argument('--stage-a', type=Path); parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    if args.mode == 'spy':
        args.output.mkdir(parents=False, exist_ok=False)
        rows = [spy(None)] + [spy(name) for name in ['text', 'seq', 'identity', 'stop', 'role', 'budget']]
        result = {'status': 'PASS' if all(row['status'] == 'PASS' for row in rows) else 'INCOMPLETE',
                  'mode': 'spy', 'checks': rows, 'real_process_starts': 0, 'model_turns': 0,
                  'scope': 'I1 protocol normalization/409 oracle; no socket/API/CLI/daemon/target'}
        (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False)); return 0 if result['status'] == 'PASS' else 1
    if not (args.materials and args.stage_a and args.approval): raise SystemExit('execute requires materials, stage-a and approval')
    try:
        result = execute(args.materials.resolve(), args.stage_a.resolve(), args.approval.resolve(), args.output.resolve())
    except Exception as error:
        result = {'status': 'INCOMPLETE', 'error': repr(error), 'real_process_starts': 0,
                  'scope': 'I1 execute path; no retry'}
        args.output.mkdir(parents=False, exist_ok=False)
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False)); return 1
    print(json.dumps(result, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
