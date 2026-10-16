"""A-06 I1 driver: register one dispatch, arm protocol, release once, stop at idle."""
import argparse
import json
import os
import shlex
import sqlite3
import subprocess
import sys
import time
import uuid
import tempfile
import traceback
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
CORE = SOURCE / 'workbench/tests'
sys.path.insert(0, str(CORE))
from t078_09b_protocol_core import (ProtocolRefusal, normalize_anthropic_request,
                                    validate_request)


def uid():
    return str(uuid.uuid4())


def registration(prompt, binding, seq=1, role='ideation'):
    dispatch = {
        'id': uid(), 'seq': seq, 'role': role,
        'text': f'⟦主控 #{seq}⟧\n{prompt}',
        'request_id': uid(), 'stop_id': uid(),
        'attempt': binding['attempt_id'], 'session': binding['session_id'],
        'fence': binding['fence'],
    }
    registry = {'dispatches': {dispatch['id']: dispatch}, 'message_budget': 6, 'ack_text': 'I1_ACK'}
    return dispatch, registry


def protocol_i1_tool(binding, root, synthetic_input_id):
    """Build I_SEND_STOP from the frozen command with live IDs substituted."""
    protocol_path = SOURCE / 'evidence/2026-10-11-batch13/T-078/09b-materials-01/protocol.json'
    commands = json.loads(protocol_path.read_bytes())['commands']
    values = {
        '{target.thread_id}': binding['thread_id'],
        '{target.attempt_id}': binding['attempt_id'],
        '{synthetic_user_input.id}': synthetic_input_id,
    }
    argv = []
    for token in commands['I_SEND_STOP']['argv']:
        for placeholder, value in values.items():
            token = token.replace(placeholder, str(value))
        if token.endswith('/roles/ideation/stop-body.txt'):
            token = str(root / 'roles' / 'ideation' / 'stop-body.txt')
        argv.append(token)
    return {'name': 'Bash', 'id': uid(), 'input': {'command': shlex.join(argv)}, 'command_argv': argv}, str(protocol_path)


def anthropic_body(dispatch):
    return {'model': 'claude-haiku-5-5', 'stream': True,
            'messages': [{'role': 'user', 'content': dispatch['text']}]}


def custom_request(dispatch):
    return {'path': '/v1/messages', 'dispatch_id': dispatch['id'], 'dispatch_seq': dispatch['seq'],
            'role': dispatch['role'], 'request_id': dispatch['request_id'], 'stop_id': dispatch['stop_id'],
            'attempt': dispatch['attempt'], 'session': dispatch['session'], 'fence': dispatch['fence'],
            'messages': [{'role': 'user', 'content': dispatch['text']}], 'stream': True,
            'model': 'claude-haiku-5-5'}

def canonical_prompt(text):
    return text.rstrip('\r\n')


def resolve_approved_p1(approval):
    p1_value = approval.get('p1_materials')
    if not isinstance(p1_value, str) or not p1_value:
        raise RuntimeError('approved_p1_materials_required')
    p1 = Path(p1_value).resolve()
    if not p1.is_dir():
        raise FileNotFoundError(f'approved_p1_materials_missing: {p1}')
    input_file = p1 / 'input.json'
    if not input_file.is_file():
        raise FileNotFoundError(f'approved_p1_input_missing: {input_file}')
    p1_input = json.loads(input_file.read_bytes())
    if p1_input.get('launch') != approval.get('launch') or p1_input.get('session') != approval.get('session'):
        raise RuntimeError('approved_p1_launch_session_mismatch')
    return p1, p1_input


def stage_role(stage):
    return 'ideation' if stage.startswith('I') else 'executor'

def stage_budget(stage):
    return 6 if stage_role(stage)=='ideation' else 11

def spy(mutant=None, stage='I1'):
    binding = {'attempt_id': uid(), 'session_id': uid(), 'fence': 1}
    role=stage_role(stage); dispatch, registry = registration(f'{stage} registered prompt; acknowledge once and stop.', binding, role=role); registry['message_budget']=stage_budget(stage)
    if mutant is None:
        normalized, anthropic = normalize_anthropic_request(anthropic_body(dispatch), registry, role)
        response = validate_request(normalized, registry)
        return {'status': 'PASS', 'mutant': None, 'decision': '200', 'stopped': False,
                'anthropic_normalization': anthropic, 'dispatch': dispatch,
                'response_events': len(response['sse']), 'messages_sent': 1, 'roots_used': 1, 'stage': stage, 'role': role}
    request = custom_request(dispatch)
    if mutant == 'text': request['messages'][0]['content'] += ' stale'
    if mutant == 'seq': request['dispatch_seq'] = 2
    if mutant == 'identity': request['attempt'] = ''
    if mutant == 'stop': request['stop_id'] = 'wrong-stop'
    if mutant == 'role': request['role'] = 'executor'
    if mutant == 'budget': request['messages'] = [request['messages'][0] for _ in range(stage_budget(stage)+1)]
    try:
        validate_request(request, registry)
    except ProtocolRefusal as error:
        return {'status': 'PASS', 'mutant': mutant, 'decision': '409', 'stopped': True,
                'error': str(error), 'messages_sent': 0, 'roots_used': 0}
    return {'status': 'INCOMPLETE', 'mutant': mutant, 'decision': '200', 'stopped': False,
            'error': 'mutant accepted', 'messages_sent': 1, 'roots_used': 1}


def approved_path_spy():
    with tempfile.TemporaryDirectory(dir='/tmp') as td:
        root = Path(td); good = root / 'good'; bad = root / 'bad'; good.mkdir(); bad.mkdir()
        launch, session = uid(), uid()
        (good / 'input.json').write_text(json.dumps({'launch': launch, 'session': session}) + '\n')
        valid = {'p1_materials': str(good), 'launch': launch, 'session': session}
        resolve_approved_p1(valid)
        rejected = []
        for candidate in [str(bad), str(root / 'missing')]:
            try:
                resolve_approved_p1({'p1_materials': candidate, 'launch': launch, 'session': session})
            except (RuntimeError, FileNotFoundError):
                rejected.append(candidate)
        wrong = {'p1_materials': str(good), 'launch': uid(), 'session': session}
        try:
            resolve_approved_p1(wrong)
        except RuntimeError:
            rejected.append('launch-session-mismatch')
        return {'status': 'PASS' if len(rejected) == 3 else 'INCOMPLETE', 'name': 'approved-p1-path-red-green',
                'green': 'approved path and matching launch/session accepted', 'red': rejected,
                'real_process_starts': 0}

def prompt_and_queue_spy():
    prompt='I1 prompt with approved trailing newline\n'; normalized=canonical_prompt(prompt)
    event={'id':'dispatch-real','seq':2,'text':f'⟦主控 #2⟧\n{normalized}'}
    green=event['text']==f'⟦主控 #2⟧\n{canonical_prompt(prompt)}'
    red=event['text']==f'⟦主控 #2⟧\n{canonical_prompt(prompt).replace("approved","MUTATED")}'
    return {'status':'PASS' if green and not red else 'INCOMPLETE','name':'queued-dispatch-normalization-red-green','green':green,'red_mutation_rejected':not red,'real_process_starts':0}


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


def protocol_i1_readback(root, api_root, launch, thread, binding, dispatch, released, output,
                         protocol_source, action_path):
    """Wait for exactly tool_use/tool_result, then read inbox/relay state."""
    deadline = time.monotonic() + 45
    request_rows = []
    response_rows = []
    stop_events = []
    permission_events = []
    stop_entries = []
    while time.monotonic() < deadline:
        request_file = api_root / 'requests.ndjson'
        response_file = api_root / 'responses.ndjson'
        if request_file.exists():
            request_rows = [json.loads(line) for line in request_file.read_text(encoding='utf-8').splitlines() if line]
            request_rows = [row for row in request_rows if row.get('dispatch_id') == dispatch['id']]
        if response_file.exists():
            response_rows = [json.loads(line) for line in response_file.read_text(encoding='utf-8').splitlines() if line]
            response_rows = [row for row in response_rows if row.get('dispatch_id') == dispatch['id']]
        events = gate(root, 'orchestration_events').get('events', [])
        stop_events = [event for event in events if event.get('launch') == launch and event.get('type') == 'turn_end_signal']
        permission_events = [event for event in events if event.get('launch') == launch and event.get('type') == 'permission_wait']
        if len(request_rows) == 2 and [row.get('message_kind') for row in request_rows] == ['tool_use', 'tool_result'] and len(response_rows) == 2 and len(stop_events) >= 2 and len(permission_events) == 1:
            state = root / 'state' / 'state.sqlite3'
            if state.exists():
                with sqlite3.connect(f'file:{state}?mode=ro', uri=True) as db:
                    rows = db.execute('SELECT data FROM inbox_records ORDER BY rowid').fetchall()
                records = [json.loads(row[0]) for row in rows]
                required_refs = {f"thread:{binding['thread_id']}", f"attempt:{binding['attempt_id']}"}
                stop_entries = [record for record in records
                                if record.get('kind') == 'stop'
                                and record.get('from') == 'ideation'
                                and record.get('to') == 'executor'
                                and required_refs.issubset(set(record.get('refs', [])))]
            if stop_entries:
                break
        time.sleep(.1)
    if len(request_rows) != 2 or [row.get('message_kind') for row in request_rows] != ['tool_use', 'tool_result']:
        raise RuntimeError('protocol_i1_messages_mismatch')
    if len(response_rows) != 2 or len(permission_events) != 1:
        raise RuntimeError('protocol_i1_permission_or_response_mismatch')
    if not stop_entries:
        raise RuntimeError('protocol_i1_stop_entry_missing')
    status = gate(root, 'pane_status', '--thread', thread)
    if status.get('state') != 'idle':
        raise RuntimeError('i1_not_idle')
    result = {'status': 'PASS', 'stage': 'I1', 'role': 'ideation', 'dispatch': dispatch,
              'release': released, 'requests': request_rows, 'responses': response_rows,
              'permission_events': permission_events, 'stop_events': stop_events,
              'stop_entry': stop_entries[-1], 'messages_sent': 2, 'roots_used': 1,
              'protocol_source': protocol_source, 'test_simulated_user_action': str(action_path),
              'oracle': {'inbox_records': True, 'relay_events': True, 'target_binding': True},
              'stop_condition': 'tool_use + tool_result, actual Stop/relay wake, idle; no retry'}
    # The protocol command deliberately records dispatch and permission
    # evidence below execute-01/dispatch-01. Create only missing parents; a
    # pre-existing output directory remains a hard refusal.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def protocol_i1_wait_permission(root, api_root, launch, thread, binding, dispatch, released,
                                output, protocol_source, action_path):
    """Stop after the first tool_use and preserve the exact permission screen."""
    deadline = time.monotonic() + 45
    request_rows = []
    response_rows = []
    permission_events = []
    while time.monotonic() < deadline:
        request_file = api_root / 'requests.ndjson'
        response_file = api_root / 'responses.ndjson'
        if request_file.exists():
            request_rows = [json.loads(line) for line in request_file.read_text(encoding='utf-8').splitlines() if line]
            request_rows = [row for row in request_rows if row.get('dispatch_id') == dispatch['id']]
        if response_file.exists():
            response_rows = [json.loads(line) for line in response_file.read_text(encoding='utf-8').splitlines() if line]
            response_rows = [row for row in response_rows if row.get('dispatch_id') == dispatch['id']]
        events = gate(root, 'orchestration_events').get('events', [])
        permission_events = [event for event in events if event.get('launch') == launch and event.get('type') == 'permission_wait']
        if len(request_rows) == 1 and request_rows[0].get('message_kind') == 'tool_use' and len(response_rows) == 1 and len(permission_events) == 1:
            screen = gate(root, 'pane_output', '--launch', launch, '--offset', '0')
            raw = __import__('base64').b64decode(screen['data_base64'])
            output.mkdir(parents=True, exist_ok=False)
            (output / 'permission-screen.bin').write_bytes(raw)
            (output / 'permission-screen.json').write_text(json.dumps({'launch': launch, 'session': dispatch.get('session'),
                'dispatch': dispatch['id'], 'permission_event': permission_events[0], 'output': screen}, ensure_ascii=False, indent=2) + '\n')
            result = {'status': 'READY_FOR_PERMISSION', 'stage': 'I1', 'role': 'ideation',
                      'dispatch': dispatch, 'release': released, 'requests': request_rows,
                      'responses': response_rows, 'permission_event': permission_events[0],
                      'permission_screen': str((output / 'permission-screen.bin').resolve()),
                      'test_simulated_user_action': str(action_path), 'messages_sent': 1,
                      'roots_used': 1, 'protocol_source': protocol_source,
                      'stop_condition': 'pause before permission Enter; no tool_result, Stop or executor wake yet'}
            (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            return result
        time.sleep(.1)
    raise RuntimeError('protocol_i1_permission_wait_deadline')


def execute(materials, stage_a, approval, output, stage='I1', resume_queued=False, protocol=False, protocol_phase='full'):
    approval_data = json.loads(approval.read_bytes())
    role=stage_role(stage)
    if approval_data.get('approved_by') != 'executor' or approval_data.get('phase') != stage or approval_data.get('role') != role:
        raise RuntimeError('i1_approval_required')
    readiness = json.loads((stage_a / 'readiness.json').read_bytes())
    p1, p1_input = resolve_approved_p1(approval_data)
    if p1_input.get('root') != str(Path(readiness['root']).resolve()):
        raise RuntimeError('approved_p1_root_mismatch')
    if p1_input.get('preset') != role:
        raise RuntimeError('approved_p1_role_mismatch')
    root = Path(readiness['root']).resolve(); thread = p1_input['thread']
    prompt = (materials / 'i1-prompt.txt').read_text(encoding='utf-8')
    normalized_prompt = canonical_prompt(prompt)
    api_root = root / 'roles' / role
    api_ready = json.loads((api_root / 'api-ready.json').read_bytes())
    if api_ready.get('protocol') != 'a07-registered-anthropic-v1':
        raise RuntimeError('protocol_api_revision_unbound')
    if resume_queued:
        status = gate(root, 'pane_status', '--thread', thread)
        queued_ids = status.get('queued', [])
        if len(queued_ids) != 1: raise RuntimeError('queued_dispatch_required')
        events = gate(root, 'orchestration_events').get('events', [])
        matches = [e for e in events if e.get('type') == 'dispatch_queued' and e.get('launch') == p1_input['launch'] and e.get('data',{}).get('id') == queued_ids[0]]
        if len(matches) != 1: raise RuntimeError('queued_dispatch_record_required')
        data = matches[0]['data']; dispatch = {'id':data['id'],'seq':data['seq'],'source':data.get('source'),'text':data['text'],'registered_at':data.get('registered_at')}
        queued = {'dispatch':dispatch,'resumed_queued':True}
    else:
        queued = gate(root, 'pane_dispatch', '--thread', thread, '--body-file', materials / 'i1-prompt.txt')
        dispatch = queued['dispatch']
    binding = readiness['target_binding']
    assert dispatch['seq'] >= 1 and dispatch['text'] == f"⟦主控 #{dispatch['seq']}⟧\n{normalized_prompt}"
    registry_dispatch = {**dispatch, 'role': role,
                         'attempt': binding['attempt_id'], 'session': p1_input['session'], 'fence': binding['fence']}
    protocol_source = None
    if protocol and stage == 'I1':
        synthetic_input_id = uid()
        action = {'id': synthetic_input_id, 'source': 'test-simulated-user',
                  'action': 'window-stop-request', 'approval_ref': approval_data.get('approval_ref'),
                  'launch': p1_input['launch'], 'thread': thread}
        action_path = root / 'roles' / role / f'window-stop-action-{dispatch["id"]}.json'
        action_path.write_text(json.dumps(action, ensure_ascii=False, indent=2) + '\n')
        body_path = root / 'roles' / role / 'stop-body.txt'
        body_path.write_text(json.dumps({'action_id': synthetic_input_id, 'source': 'test-simulated-user',
                                         'approved_by': approval_data.get('approved_by')}, ensure_ascii=False) + '\n')
        tool, protocol_source = protocol_i1_tool(binding, root, synthetic_input_id)
        registry_dispatch['tool_use'] = tool
        registry_dispatch['tool_result'] = {'request_root': str(api_root / 'requests')}
        registry_dispatch['protocol_source'] = protocol_source
    registry = {'dispatches': {dispatch['id']: registry_dispatch}, 'message_budget': stage_budget(stage), 'ack_text': stage+'_ACK'}
    (api_root / 'protocol-registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    released = gate(root, 'pane_release', '--thread', thread, '--reason', 'I1 approval: release one registered dispatch')
    if protocol and stage == 'I1':
        if protocol_phase == 'dispatch':
            return protocol_i1_wait_permission(root, api_root, p1_input['launch'], thread, binding, dispatch, released,
                                               output, protocol_source, action_path)
        return protocol_i1_readback(root, api_root, p1_input['launch'], thread, binding, dispatch, released,
                                    output, protocol_source, action_path)
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
    result = {'status': 'PASS', 'stage': stage, 'role': role, 'dispatch': dispatch, 'registered': registry_dispatch,
              'response': response, 'stop_event': stop_events[0], 'release': released, 'messages_sent': 1,
              'roots_used': 1, 'stop_condition': 'one response, one turn idle, no retry'}
    if protocol and stage == 'I1':
        result.update({'messages_expected': 2, 'permission_screens_expected': 1,
                       'test_simulated_user_action': str(root / 'roles' / role / f'window-stop-action-{dispatch["id"]}.json'),
                       'protocol_source': protocol_source,
                       'stop_condition': 'tool_use + tool_result, actual Stop/relay wake, idle; no retry'})
    output.mkdir(parents=False, exist_ok=False)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['spy', 'execute'], required=True); parser.add_argument('--stage', choices=['I1','I2','I3','I4','E1','E2','E3','E4','E5','E6'], default='I1'); parser.add_argument('--resume-queued', action='store_true'); parser.add_argument('--protocol', action='store_true'); parser.add_argument('--protocol-phase', choices=['dispatch','full'], default='full')
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--materials', type=Path)
    parser.add_argument('--stage-a', type=Path); parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    if args.mode == 'spy':
        args.output.mkdir(parents=False, exist_ok=False)
        rows = [spy(None,args.stage)] + [spy(name,args.stage) for name in ['text', 'seq', 'identity', 'stop', 'role', 'budget']]
        rows.extend([approved_path_spy(), prompt_and_queue_spy()])
        result = {'status': 'PASS' if all(row['status'] == 'PASS' for row in rows) else 'INCOMPLETE',
                  'mode': 'spy', 'checks': rows, 'real_process_starts': 0, 'model_turns': 0,
                  'scope': 'I1 protocol normalization/409 oracle; no socket/API/CLI/daemon/target'}
        (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False)); return 0 if result['status'] == 'PASS' else 1
    if not (args.materials and args.stage_a and args.approval): raise SystemExit('execute requires materials, stage-a and approval')
    try:
        result = execute(args.materials.resolve(), args.stage_a.resolve(), args.approval.resolve(), args.output.resolve(), stage=args.stage, resume_queued=args.resume_queued, protocol=args.protocol, protocol_phase=args.protocol_phase)
    except Exception as error:
        result = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc(),
                  'paths': {'materials': str(args.materials.resolve()) if args.materials else None,
                            'stage_a': str(args.stage_a.resolve()) if args.stage_a else None,
                            'approval': str(args.approval.resolve()) if args.approval else None},
                  'real_process_starts': 0, 'scope': 'I1 execute path; no retry'}
        args.output.mkdir(parents=False, exist_ok=False)
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False)); return 1
    print(json.dumps(result, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
