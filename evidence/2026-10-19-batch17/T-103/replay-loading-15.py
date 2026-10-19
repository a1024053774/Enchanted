#!/usr/bin/env python3
"""Replay saved observations against the real wait predicates; no live app."""
import argparse
import ast
import copy
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
run = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-20261019T062714Z')
rows = json.loads((run / 'green-state-expected.json').read_text(encoding='utf-8'))


def observations(label):
    records = [json.loads(line) for line in (run / label / 'driver.ndjson').read_text(encoding='utf-8').splitlines()]
    return [entry['response']['value'] for entry in records
            if isinstance(entry.get('response', {}).get('value'), dict) and 'panes' in entry['response']['value']]


loading = observations('green-explicit-task')[0]
assert loading['busy'] == 'true' and len(loading['panes']) == 1 and 'task' not in loading['panes'][0]
ready = next(value for value in observations('green-no-task')
             if len(value['panes']) == 1 and value['panes'][0].get('task') == rows[2]['task_id']
             and rows[2]['trace'] in value['panes'][0]['terminal'])


def predicates(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    result = {}
    for name, marker in [('explicit', 'rows[2]'), ('switch', "row['task_id']")]:
        matches = [node for node in ast.walk(tree) if isinstance(node, ast.Lambda) and marker in ast.unparse(node)]
        assert len(matches) == 1, (name, len(matches))
        result[name] = eval(compile(ast.Expression(matches[0]), str(path), 'eval'), {'rows': rows, 'row': rows[2]})
    return result


source = root / 'workbench/tests/run_t103_picker.py'
known_bad = run / 'source-snapshot/workbench/tests/run_t103_picker.py'
report = {'status': 'INCOMPLETE', 'scope': 'Saved observation replay only; explicit-task live readiness remains unproved',
          'argv': sys.argv, 'run': str(run), 'source': str(source), 'known_bad': str(known_bad), 'checks': []}
for name, predicate in predicates(known_bad).items():
    try:
        predicate(loading)
    except KeyError as error:
        assert error.args == ('task',)
        report['checks'].append({'predicate': name, 'case': 'frozen faulty code on real loading observation', 'error': repr(error)})
    else:
        raise AssertionError('Frozen faulty predicate did not reproduce KeyError')

wrong_task = copy.deepcopy(ready)
wrong_task['panes'][0]['task'] = rows[0]['task_id']
wrong_trace = copy.deepcopy(ready)
wrong_trace['panes'][0]['terminal'] = rows[0]['trace']
missing_task_with_trace = copy.deepcopy(ready)
del missing_task_with_trace['panes'][0]['task']
cases = [('actual loading', loading, False), ('actual matching task and trace', ready, True),
         ('wrong task with expected trace', wrong_task, False), ('expected task with wrong trace', wrong_trace, False),
         ('missing task with expected trace', missing_task_with_trace, False),
         ('no panes', {'panes': []}, False), ('two panes', {'panes': ready['panes'] * 2}, False)]
for name, predicate in predicates(source).items():
    for label, value, expected in cases:
        actual = predicate(value)
        assert actual is expected, (name, label, actual, expected)
        report['checks'].append({'predicate': name, 'case': label, 'expected': expected, 'actual': actual})
report['status'] = 'PASS'
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
