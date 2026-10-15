"""Offline I2-I4/E1-E6 registry matrix; no socket, API, CLI, daemon or target."""
import argparse
import json
import uuid
from pathlib import Path
from t078_09b_protocol_core import ProtocolRefusal, normalize_anthropic_request, validate_request

STAGES = [('I2', 'ideation', 'text'), ('I3', 'ideation', 'seq'), ('I4', 'ideation', 'identity'),
          ('E1', 'executor', 'stop'), ('E2', 'executor', 'role'), ('E3', 'executor', 'budget'),
          ('E4', 'executor', 'text'), ('E5', 'executor', 'seq'), ('E6', 'executor', 'identity')]


def uid(): return str(uuid.uuid4())


def build(stage, role, seq):
    dispatch = {'id': uid(), 'seq': seq, 'role': role, 'text': f'⟦主控 #{seq}⟧\n{stage} registered prompt',
                'request_id': uid(), 'stop_id': uid(), 'attempt': uid(), 'session': uid(), 'fence': 1}
    registry = {'dispatches': {dispatch['id']: dispatch}, 'message_budget': 6 if role == 'ideation' else 11,
               'ack_text': stage + '_ACK'}
    return dispatch, registry


def custom(dispatch):
    return {'dispatch_id': dispatch['id'], 'dispatch_seq': dispatch['seq'], 'role': dispatch['role'],
            'request_id': dispatch['request_id'], 'stop_id': dispatch['stop_id'], 'attempt': dispatch['attempt'],
            'session': dispatch['session'], 'fence': dispatch['fence'],
            'messages': [{'role': 'user', 'content': dispatch['text']}], 'stream': True,
            'model': 'claude-haiku-5-5'}


def run_stage(stage, role, mutant, seq):
    dispatch, registry = build(stage, role, seq)
    body = {'model': 'claude-haiku-5-5', 'stream': True,
            'messages': [{'role': 'user', 'content': dispatch['text']}]}
    normalized, anthropic = normalize_anthropic_request(body, registry, role)
    green = validate_request(normalized, registry)
    bad = custom(dispatch)
    if mutant == 'text': bad['messages'][0]['content'] += ' stale'
    if mutant == 'seq': bad['dispatch_seq'] += 1
    if mutant == 'identity': bad['attempt'] = ''
    if mutant == 'stop': bad['stop_id'] = 'wrong-stop'
    if mutant == 'role': bad['role'] = 'ideation' if role == 'executor' else 'executor'
    if mutant == 'budget': bad['messages'] = [bad['messages'][0] for _ in range(registry['message_budget'] + 1)]
    try:
        validate_request(bad, registry)
    except ProtocolRefusal as error:
        red = {'status': 'PASS', 'stage': stage, 'role': role, 'decision': '409', 'error': str(error),
               'registered_seq': seq, 'messages_used': 0, 'roots_used': 0}
    else:
        red = {'status': 'INCOMPLETE', 'stage': stage, 'role': role, 'decision': '200',
               'error': 'mutant accepted', 'messages_used': 1, 'roots_used': 1}
    return {'green': {'status': 'PASS', 'stage': stage, 'role': role, 'decision': '200',
                      'anthropic_normalization': anthropic, 'sse_events': len(green['sse']),
                      'registered_seq': seq, 'registered_request_id': dispatch['request_id'],
                      'registered_stop_id': dispatch['stop_id'], 'messages_used': 1, 'roots_used': 1},
            'red': red}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    args.output.mkdir(parents=False, exist_ok=False); rows=[]
    for seq, (stage, role, mutant) in enumerate(STAGES, start=2):
        result = run_stage(stage, role, mutant, seq); stage_dir = args.output / stage.lower(); stage_dir.mkdir()
        (stage_dir / 'green.json').write_text(json.dumps(result['green'], ensure_ascii=False, indent=2) + '\n')
        (stage_dir / 'red.json').write_text(json.dumps(result['red'], ensure_ascii=False, indent=2) + '\n')
        rows.append({'stage': stage, 'role': role, 'mutant': mutant, **result})
    summary = {'status': 'PASS' if all(row['green']['status'] == 'PASS' and row['red']['status'] == 'PASS' for row in rows) else 'INCOMPLETE',
               'stages': rows, 'budgets': {'ideation': {'roots': 4, 'messages': 6}, 'executor': {'roots': 6, 'messages': 11}},
               'scope': 'offline registered SSE matrix I2-I4/E1-E6; no processes'}
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': summary['status'], 'stages': len(rows), 'roles': {'ideation': 3, 'executor': 6}, 'process_starts': 0}, ensure_ascii=False))
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
