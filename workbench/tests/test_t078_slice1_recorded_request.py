"""Replay the captured native request against the fake-API validator only."""
import argparse
import copy
import json
from pathlib import Path
import t078_slice1_protocol as protocol


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--api-jsonl', type=Path, required=True)
    p.add_argument('--scenario', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mutant-command', action='store_true')
    args = p.parse_args(); args.output.mkdir()
    raw = args.api_jsonl.read_bytes()
    (args.output / 'api.jsonl').write_bytes(raw)
    (args.output / 'scenario.json').write_bytes(args.scenario.read_bytes())
    scenario = json.loads(args.scenario.read_bytes())
    requests = [json.loads(s)['body'] for s in raw.splitlines() if json.loads(s)['path'] == '/v1/messages']
    validate = protocol.validate_request
    if args.mutant_command:
        source = Path(protocol.__file__).read_text(encoding='utf-8')
        marker = "tool.get('input') != {'command': scenario['bash_command']}"
        assert source.count(marker) == 1
        scope = {}; exec(compile(source.replace(marker, 'False'), 'known-bad-command', 'exec'), scope)
        validate = scope['validate_request']
    checks = []

    def check(name, body, number, accepted):
        try:
            observed = validate(body, number, scenario); ok = True
        except ValueError as error:
            observed = str(error); ok = False
        checks.append({'name': name, 'status': 'PASS' if ok == accepted else 'INCOMPLETE',
                       'expected_accepted': accepted, 'observed': observed})

    check('actual-api1-root', requests[0], 1, True)
    check('actual-api2-with-system-tail', requests[1], 2, True)
    check('actual-third-request-budget-rejected', requests[2], 3, False)
    body = requests[1]
    ri = next(i for i, m in enumerate(body['messages']) if m['role'] == 'user'
              and any(p.get('type') == 'tool_result' for p in m['content']))
    ti = next(i for i, m in enumerate(body['messages']) if m['role'] == 'assistant'
              and any(p.get('type') == 'tool_use' for p in m['content']))
    bad = copy.deepcopy(body); bad['messages'][ri]['content'][0]['tool_use_id'] = 'foreign'
    check('wrong-result-id-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'][ti]['content'][0]['input']['command'] += ' --extra'
    check('changed-command-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'][ri]['content'].append(copy.deepcopy(bad['messages'][ri]['content'][0]))
    check('duplicate-result-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'].append({'role': 'user', 'content': [{'type': 'text', 'text': 'UNAPPROVED_NEW_ROOT'}]})
    check('late-user-message-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'][ti], bad['messages'][ri] = bad['messages'][ri], bad['messages'][ti]
    check('result-before-tool-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'][ri]['content'][0]['content'] = ''
    check('empty-result-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'][ri]['role'] = 'system'
    check('tool-result-must-be-user-content', bad, 2, False)
    bad = copy.deepcopy(body); bad['model'] = 'foreign-model'
    check('wrong-model-rejected', bad, 2, False)
    bad = copy.deepcopy(body); bad['messages'].append({'role': 'assistant', 'content': [{'type': 'text', 'text': 'UNAPPROVED_ASSISTANT_TAIL'}]})
    check('late-assistant-message-rejected', bad, 2, False)
    result = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'INCOMPLETE',
              'argv': __import__('sys').argv, 'checks': checks, 'mutant_command': args.mutant_command,
              'scope': 'Unmodified actual API bodies; validator only, no server/CLI/model/old-root mutation'}
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks)}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
