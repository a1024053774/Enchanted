"""Independent sentinel, correlation and budget contracts for the green fake API."""
import argparse
import copy
import json
from pathlib import Path
import t078_slice1_protocol as protocol

p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
p.add_argument('--mutant-budget', action='store_true'); args = p.parse_args(); args.output.mkdir()
validate = protocol.validate_request
if args.mutant_budget:
    source = Path(protocol.__file__).read_text(encoding='utf-8')
    assert source.count('not 1 <= number <= limit') == 1
    source = source.replace('not 1 <= number <= limit', 'number < 1')
    scope = {}; exec(compile(source, 'known-bad-budget', 'exec'), scope); validate = scope['validate_request']
scenario = {'name': 'slice1-inbox-green', 'nonce': 'UNSEEN_GREEN_23', 'ack': 'ACK', 'final_ack': 'FINAL',
            'tool_use_id': 'toolu_23', 'bash_command': '/fixture/node /fixture/inbox list --role executor',
            'inbox_fixture': [{'id': 'IDEATION_23', 'to': 'ideation'}, {'id': 'FOREIGN_47', 'to': 'executor'}]}
tool = {'type': 'tool_use', 'id': 'toolu_23', 'name': 'Bash', 'input': {'command': scenario['bash_command']}}
queued = {'ok': True, 'queued': True, 'delivered': False, 'request_id': 'actual_request_31'}
result = {'type': 'tool_result', 'tool_use_id': 'toolu_23', 'content': json.dumps(queued)}
second = {'model': 'claude-haiku-5-5', 'stream': True, 'messages': [
    {'role': 'assistant', 'content': [tool]}, {'role': 'user', 'content': [result]},
    {'role': 'system', 'content': 'native metadata'}]}
receipt = {'request_id': 'actual_request_31', 'replayed': False,
           'result': {'ok': True, 'entries': [{'entry': {'id': 'IDEATION_23'}}]}}
def third(value):
    return {**copy.deepcopy(second), 'messages': copy.deepcopy(second['messages']) + [
        {'role': 'assistant', 'content': [{'type': 'text', 'text': 'ACK UNSEEN_GREEN_23'}]},
        {'role': 'user', 'content': [{'type': 'text', 'text': '⟦门禁 #2⟧\nExecution receipts\n' + json.dumps([value])}]}]}
checks = []
def check(name, body, number, expected):
    try: observed = validate(body, number, scenario); accepted = True
    except ValueError as error: observed = str(error); accepted = False
    checks.append({'name': name, 'status': 'PASS' if accepted == expected else 'INCOMPLETE',
                   'expected_accepted': expected, 'observed': observed})
check('actual-queued-result-with-system-tail', second, 2, True)
check('registered-feedback-correlates-and-scopes-sentinel', third(receipt), 3, True)
check('fourth-Messages-is-rejected', second, 4, False)
for name, changed in [('always-empty-result', []), ('foreign-role-result', [{'entry': {'id': 'FOREIGN_47'}}]),
                       ('both-role-results', [{'entry': {'id': 'IDEATION_23'}}, {'entry': {'id': 'FOREIGN_47'}}])]:
    value = copy.deepcopy(receipt); value['result']['entries'] = changed; check(name, third(value), 3, False)
value = copy.deepcopy(receipt); value['request_id'] = 'foreign_request'; check('foreign-request-correlation', third(value), 3, False)
value = copy.deepcopy(receipt); value['replayed'] = True; check('replay-is-not-new-execution', third(value), 3, False)
bad = third(receipt); bad['messages'][0]['content'][0]['input']['command'] += ' --extra'
check('changed-tool-command-in-feedback-history', bad, 3, False)
bad = third(receipt); bad['messages'][0]['content'].append(copy.deepcopy(tool))
check('second-tool-call-is-rejected', bad, 3, False)
bad = copy.deepcopy(second); bad['messages'][1]['content'][0]['is_error'] = True
check('queued-error-is-rejected', bad, 2, False)
record = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'INCOMPLETE',
          'checks': checks, 'mutant_budget': args.mutant_budget, 'real_model_turns': 0,
          'scope': 'Synthetic protocol only; no native CLI, Stop or role authenticity proof'}
(args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'checks': len(checks)})); raise SystemExit(0 if record['status'] == 'PASS' else 1)
