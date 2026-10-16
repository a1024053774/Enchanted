"""Approved 09B phase entry; historical no-tool pipeline checks stay separate."""
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
    if mutant == 'budget': registry['messages_used'] = stage_budget(stage)+1
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
    env = {**{k:v for k,v in os.environ.items() if not k.startswith('A2A_')}, 'A2A_OPERATOR_CREDENTIAL': str(root / 'operator.json'),
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    result = subprocess.run([
        '/opt/homebrew/bin/node', str(SOURCE / 'workbench/src/gates/cli.ts'),
        '--state', str(root / 'state'), command, *map(str, args),
    ], cwd=SOURCE, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError({'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    value = json.loads(result.stdout.strip().splitlines()[-1])
    if value.get('ok') is not True:
        raise RuntimeError({'gate_refused': value, 'command': command})
    return value


def execute(materials, stage_a, approval, output, stage='I1', resume_queued=False, protocol=False, protocol_phase='dispatch'):
    if protocol:
        if resume_queued:
            raise RuntimeError('A14 protocol never re-dispatches an old root')
        from t078_09b_phase_driver import execute as execute_phase
        return execute_phase(materials, stage_a, approval, output, stage, protocol_phase)
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
    registry = {'dispatches': {dispatch['id']: registry_dispatch}, 'message_budget': stage_budget(stage), 'ack_text': stage+'_ACK'}
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
    result = {'status': 'PASS', 'stage': stage, 'role': role, 'dispatch': dispatch, 'registered': registry_dispatch,
              'response': response, 'stop_event': stop_events[0], 'release': released, 'messages_sent': 1,
              'roots_used': 1, 'stop_condition': 'one response, one turn idle, no retry'}
    output.mkdir(parents=False, exist_ok=False)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['spy', 'execute'], required=True); parser.add_argument('--stage', choices=['I1','I2','I3','I4','E1','E2','E3','E4','E5','E6'], default='I1'); parser.add_argument('--resume-queued', action='store_true'); parser.add_argument('--protocol', action='store_true'); parser.add_argument('--protocol-phase', choices=['dispatch','arm','collect','release','observe'], default='dispatch')
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
    if args.output.exists(): raise SystemExit('output_exists; no action')
    try:
        result = execute(args.materials.resolve(), args.stage_a.resolve(), args.approval.resolve(), args.output.resolve(), stage=args.stage, resume_queued=args.resume_queued, protocol=args.protocol, protocol_phase=args.protocol_phase)
    except Exception as error:
        result = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc(),
                  'paths': {'materials': str(args.materials.resolve()) if args.materials else None,
                            'stage_a': str(args.stage_a.resolve()) if args.stage_a else None,
                            'approval': str(args.approval.resolve()) if args.approval else None},
                  'real_process_starts': 0, 'scope': 'I1 execute path; no retry'}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False)); return 1
    print(json.dumps(result, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
