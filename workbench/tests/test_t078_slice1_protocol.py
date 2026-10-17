"""Fixed tool protocol counterexamples; no socket, CLI, daemon, UI or model."""
import argparse
import copy
import json
from pathlib import Path
import t078_slice1_protocol as protocol


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mutant-budget', action='store_true')
    args = p.parse_args(); args.output.mkdir()
    if args.mutant_budget:
        source = Path(protocol.__file__).read_text(encoding='utf-8')
        assert source.count('not 1 <= number <= limit') == 1
        source = source.replace('not 1 <= number <= limit', 'number < 1')
        scope = {}; exec(compile(source, 'known-bad-budget', 'exec'), scope)
        validate = scope['validate_request']
    else:
        validate = protocol.validate_request
    scenario = {'name':'slice1-inbox-red','nonce': 'S1_UNSEEN_ALPHA', 'ack': 'FIXTURE_ACK', 'tool_use_id': 'toolu_unique_7',
                'bash_command': '/fixture/node /fixture/inbox list --role executor'}
    root = {'model': 'claude-haiku-5-5', 'stream': True,
            'tools': [{'name': 'Bash', 'input_schema': {'properties': {'command': {'type': 'string'}}}}],
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': '⟦主控 #1⟧\nS1_UNSEEN_ALPHA'}]}]}
    tool = {'type': 'tool_use', 'id': 'toolu_unique_7', 'name': 'Bash',
            'input': {'command': '/fixture/node /fixture/inbox list --role executor'}}
    result = {'type': 'tool_result', 'tool_use_id': 'toolu_unique_7', 'content': 'NATIVE_SENTINEL_7', 'is_error': True}
    second = {**root, 'messages': root['messages'] + [{'role': 'assistant', 'content': [tool]},
                                                     {'role': 'user', 'content': [result]}]}
    checks = []

    def check(name, body, number, accepted):
        try:
            observed = validate(body, number, scenario); ok = True
        except ValueError as error:
            observed = str(error); ok = False
        checks.append({'name': name, 'status': 'PASS' if ok == accepted else 'INCOMPLETE',
                       'expected_accepted': accepted, 'observed': observed})

    check('registered-root-and-advertised-Bash', root, 1, True)
    check('correlated-native-result', second, 2, True)
    check('third-Messages-is-rejected', second, 3, False)
    bad = copy.deepcopy(root); bad['messages'][0]['content'][0]['text'] += ' stale'
    check('concatenated-root-is-rejected', bad, 1, False)
    bad = copy.deepcopy(root); bad['tools'] = []
    check('no-advertised-Bash-is-rejected', bad, 1, False)
    bad = copy.deepcopy(second); bad['messages'][-1]['content'][0]['tool_use_id'] = 'foreign'
    check('foreign-result-is-rejected', bad, 2, False)
    bad = copy.deepcopy(second); bad['messages'][-2]['content'][0]['input']['command'] += ' --extra'
    check('changed-command-is-rejected', bad, 2, False)
    bad = copy.deepcopy(second); bad['messages'][-1]['content'][0]['content'] = ''
    check('empty-tool-result-is-rejected', bad, 2, False)
    bad = copy.deepcopy(second); bad['messages'][-1]['content'].append(copy.deepcopy(result))
    check('duplicate-tool-result-is-rejected', bad, 2, False)
    bad = copy.deepcopy(second); bad['model'] = 'foreign-model'
    check('wrong-model-is-rejected', bad, 2, False)
    packets = list(protocol.response_events(1, scenario, 'msg_fixture'))
    command = json.loads(next(v['delta']['partial_json'] for k, v in packets if k == 'content_block_delta'))
    checks.append({'name': 'response-uses-frozen-command', 'status': 'PASS' if command == tool['input'] else 'INCOMPLETE'})
    altered = {**scenario, 'nonce': 'S1_UNSEEN_BETA'}
    a = list(protocol.response_events(2, scenario, 'msg_a'))
    b = list(protocol.response_events(2, altered, 'msg_b'))
    aa = next(v['delta']['text'] for k, v in a if k == 'content_block_delta')
    bb = next(v['delta']['text'] for k, v in b if k == 'content_block_delta')
    checks.append({'name': 'new-nonce-changes-ack', 'status': 'PASS' if aa != bb and 'BETA' in bb and 'ALPHA' not in bb else 'INCOMPLETE'})
    record = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'INCOMPLETE',
              'checks': checks, 'mutant_budget': args.mutant_budget,
              'scope': 'Synthetic API body/SSE contract only; no native tool or transport claim', 'real_model_turns': 0}
    with (args.output / 'results.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'checks': len(checks)}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
