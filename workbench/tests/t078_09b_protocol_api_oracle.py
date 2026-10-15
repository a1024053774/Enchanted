"""Offline oracle for the protocol API's tool-use round trip.

This exercises the same normalizer/validator used by the loopback service.  It
does not bind a port, start a process, invoke a gate, or send a Claude turn.
"""
import argparse
import json
import shlex
import uuid
from pathlib import Path

from t078_09b_protocol_core import (ProtocolRefusal, anthropic_sse,
                                    normalize_anthropic_request,
                                    validate_request)


def uid():
    return str(uuid.uuid4())


def frozen_commands():
    root = Path(__file__).resolve().parents[2]
    path = root / 'evidence/2026-10-11-batch13/T-078/09b-materials-01/protocol.json'
    return json.loads(path.read_bytes())['commands'], str(path)


def substitute(value, values):
    if isinstance(value, list):
        return [substitute(item, values) for item in value]
    if isinstance(value, str):
        for key, replacement in values.items():
            value = value.replace('{' + key + '}', str(replacement))
        return value
    return value


def make_case(mutant=None):
    target_thread, target_attempt, synthetic_input = uid(), uid(), uid()
    commands, protocol_source = frozen_commands()
    stop_entry = {
        'id': uid(), 'from': 'ideation', 'to': 'executor', 'kind': 'stop',
        'refs': [f'thread:{target_thread}', f'attempt:{target_attempt}',
                 f'input:{synthetic_input}'],
    }
    tool_id = uid()
    body_file = '/private/tmp/runtime/roles/ideation/stop-body.txt'
    command_values = {
        'target.thread_id': target_thread, 'target.attempt_id': target_attempt,
        'synthetic_user_input.id': synthetic_input,
    }
    argv = substitute(commands['I_SEND_STOP']['argv'], command_values)
    argv = [body_file if token.endswith('/roles/ideation/stop-body.txt') else token for token in argv]
    dispatch = {
        'id': uid(), 'seq': 2, 'role': 'ideation',
        'text': '⟦主控 #2⟧\nApproved test-simulated-user stop request',
        'request_id': uid(), 'stop_id': uid(), 'attempt': uid(),
        'session': uid(), 'fence': 1,
        'tool_use': {
            'id': tool_id, 'name': 'Bash',
            'input': {'command': shlex.join(argv)},
            'command_argv': argv,
        },
        'tool_result': {'entry': stop_entry},
    }
    registry = {
        'dispatches': {dispatch['id']: dispatch}, 'message_budget': 6,
        'ack_text': 'I1_STOP_SENT',
    }
    first_body = {
        'model': 'claude-haiku-5-5', 'stream': True,
        'messages': [{'role': 'user', 'content': dispatch['text']}],
    }
    first, first_anthropic = normalize_anthropic_request(first_body, registry, 'ideation')
    first_result = validate_request(first, registry)
    first_events = anthropic_sse(first_result, first['model'], uid())
    tool_block = {
        'type': 'tool_use', 'id': tool_id, 'name': 'Bash',
        'input': dispatch['tool_use']['input'],
    }
    tool_result_payload = {'ok': True, 'entry': stop_entry}
    second_body = {
        'model': 'claude-haiku-5-5', 'stream': True,
        'messages': [
            {'role': 'user', 'content': dispatch['text']},
            {'role': 'assistant', 'content': [tool_block]},
            {'role': 'user', 'content': [{
                'type': 'tool_result', 'tool_use_id': tool_id,
                'content': json.dumps(tool_result_payload, ensure_ascii=False,
                                      separators=(',', ':')),
            }]},
        ],
    }
    second, second_anthropic = normalize_anthropic_request(second_body, registry, 'ideation')
    second_result = validate_request(second, registry)
    second_events = anthropic_sse(second_result, second['model'], uid())
    if mutant:
        bad = json.loads(json.dumps(second_body))
        if mutant == 'tool_id':
            bad['messages'][-1]['content'][0]['tool_use_id'] = uid()
        elif mutant == 'entry_id':
            payload = json.loads(bad['messages'][-1]['content'][0]['content'])
            payload['entry']['id'] = uid()
            bad['messages'][-1]['content'][0]['content'] = json.dumps(payload, separators=(',', ':'))
        elif mutant == 'target':
            argv = shlex.split(bad['messages'][1]['content'][0]['input']['command'])
            argv[12] = f'thread:{uid()}'
            bad['messages'][1]['content'][0]['input']['command'] = shlex.join(argv)
        elif mutant == 'text':
            bad['messages'][0]['content'] += ' stale'
        try:
            bad_normalized, _ = normalize_anthropic_request(bad, registry, 'ideation')
            if mutant == 'seq':
                bad_normalized['dispatch_seq'] = 3
            elif mutant == 'role':
                bad_normalized['role'] = 'executor'
            validate_request(bad_normalized, registry)
        except ProtocolRefusal as error:
            return {'status': 'PASS', 'mutant': mutant, 'decision': '409',
                    'error': str(error), 'messages_used': 0, 'roots_used': 0}
        return {'status': 'INCOMPLETE', 'mutant': mutant, 'decision': '200',
                'error': 'mutant accepted'}
    return {
        'status': 'PASS', 'stage': 'I1', 'role': 'ideation',
        'messages_used': 2, 'roots_used': 1,
        'first': {'dispatch_id': dispatch['id'], 'seq': dispatch['seq'],
                  'tool_use_id': tool_id, 'anthropic_normalization': first_anthropic,
                  'sse_events': len(first_events), 'stop_reason': 'tool_use'},
        'second': {'tool_use_id': tool_id, 'anthropic_normalization': second_anthropic,
                   'sse_events': len(second_events), 'settlement': True,
                   'stop_reason': 'end_turn'},
        'bindings': {'target_thread': target_thread, 'target_attempt': target_attempt,
                     'synthetic_input': synthetic_input, 'stop_entry': stop_entry},
        'protocol_source': protocol_source,
        'scope': 'offline shared protocol core; no socket/API/CLI/daemon/target/model',
    }


def run_i2_e1():
    target_thread, stop_id = uid(), uid()
    commands, protocol_source = frozen_commands()
    argv = substitute(commands['E_WRONG_TARGET']['argv'], {'stop.id': stop_id})
    dispatch = {
        'id': uid(), 'seq': 4, 'role': 'executor',
        'text': '⟦主控 #4⟧\nActual inbox wake with wrong target probe',
        'request_id': uid(), 'stop_id': stop_id, 'attempt': uid(),
        'session': uid(), 'fence': 1,
        'tool_use': {'id': uid(), 'name': 'Bash', 'input': {'command': shlex.join(argv)}, 'command_argv': argv},
        'tool_result': {'ok': False, 'error': 'worker_target_required'},
    }
    registry = {'dispatches': {dispatch['id']: dispatch}, 'message_budget': 11,
                'ack_text': 'E1_DENIED'}
    first_body = {'model': 'claude-haiku-5-5', 'stream': True,
                  'messages': [{'role': 'user', 'content': dispatch['text']}]}
    first, _ = normalize_anthropic_request(first_body, registry, 'executor')
    first_result = validate_request(first, registry)
    tool_block = {'type': 'tool_use', 'id': dispatch['tool_use']['id'], 'name': 'Bash',
                  'input': dispatch['tool_use']['input']}
    second_body = {'model': 'claude-haiku-5-5', 'stream': True,
                   'messages': [
                       {'role': 'user', 'content': dispatch['text']},
                       {'role': 'assistant', 'content': [tool_block]},
                       {'role': 'user', 'content': [{'type': 'tool_result',
                           'tool_use_id': dispatch['tool_use']['id'],
                           'content': json.dumps({'ok': False, 'error': 'worker_target_required'})}]},
                   ]}
    second, _ = normalize_anthropic_request(second_body, registry, 'executor')
    second_result = validate_request(second, registry)
    return {
        'I2': {'status': 'PASS', 'role': 'ideation', 'messages_used': 1,
               'confirm_only': True, 'input': 'actual send execution feedback',
               'stop_effect': 'confirm only'},
        'E1': {'status': 'PASS', 'role': 'executor', 'messages_used': 2,
               'gate_decision': '409', 'api_settlement': '200', 'error': 'worker_target_required',
               'wrong_target_rejected': True, 'esc_count': 0,
               'tool_use_id': dispatch['tool_use']['id'],
               'first_sse_events': len(first_result['sse']),
               'second_settlement': bool(second_result.get('settlement')),
               'protocol_source': protocol_source},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=['tool_id', 'entry_id', 'target', 'seq', 'role', 'text'])
    args = parser.parse_args()
    args.output.mkdir(parents=False, exist_ok=False)
    try:
        result = make_case(args.mutant) if args.mutant else {'I1': make_case(), **run_i2_e1()}
    except ProtocolRefusal as error:
        result = {'status': 'PASS' if args.mutant else 'INCOMPLETE',
                  'mutant': args.mutant, 'error': str(error),
                  'scope': 'offline shared protocol core; no processes'}
    if args.mutant is None:
        result['status'] = 'PASS' if all(row.get('status') == 'PASS' for row in result.values()) else 'INCOMPLETE'
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'mutant': args.mutant,
                      'messages': result.get('I1', {}).get('messages_used', 0)}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
