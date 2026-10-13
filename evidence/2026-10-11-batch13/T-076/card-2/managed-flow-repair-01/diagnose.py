"""Read saved turn boundaries and W07 red evidence; no live backend calls."""
import argparse
import ast
import difflib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent; card = here.parent; root = card.parents[3]
out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
source = card / 'outside-legacy-green-03'
w07 = json.loads((source / 'w07-red/run.json').read_text(encoding='utf-8'))
base = w07['artifacts'][0]['base_commit']
refs = [row for row in w07['commands'] if row.get('label') == 'git' and row['argv'][-2:] == ['rev-parse', 'refs/heads/main']]
assert (w07['tests_run'], w07['failures'], w07['errors']) == (1, 1, 0)
assert 'W07-MANUAL-SOURCE' in w07['failure_text'][0]['traceback'] and refs[-1]['stdout'].strip() != base
case_dir = source / 'provenance-and-frozen-green/managed_frozen_candidate_integrates_original'
case = json.loads((case_dir / 'case.json').read_text(encoding='utf-8'))
tables = json.loads((case_dir / 'database-readback.json').read_text(encoding='utf-8'))['tables']
events = [{**row, 'data': json.loads(row['data'])} for row in tables['orchestration_events']]
idles = [row for row in events if row['type'] == 'pane_idle']
stops = [row for row in events if row['type'] == 'stop_not_matched']
rejected = [row for row in events if row['type'] == 'relay_rejected' and row['data']['result']['error'] == 'relay_requires_current_stop']
task = json.loads(tables['tasks'][0]['data'])
assert case['outcome'] == 'harness_error' and not case['cleanup_failures']
assert [row['data']['stop']['turn_id'] for row in idles] == ['fixture-turn-1', 'fixture-turn-2']
assert len(stops) == 1 and stops[0]['data']['turn_id'] == 'fixture-turn-2'
assert len([row for row in events if row['type'] == 'turn_submitted']) == 2
assert [row['key'] for row in tables['relay_requests']] == ['id:dirty']
assert {row['data']['key'] for row in rejected} == {'id:00-short', 'id:01-base', 'id:delivery', 'id:zz-duplicate'}
assert task['state'] == 'claimed' and task['candidate_commit'] is None and task['current_attempt']['turn_id'] is None
assert not any('pane_dispatch' in row['argv'] for row in case['commands'])
selected = [row for row in events if row['type'] in ('turn_submitted', 'pane_idle', 'stop_not_matched') or row in rejected]
path = root / 'workbench/tests/test_quality_legacy_e2e.py'
before = (here / 'test_quality_legacy_e2e.py.before').read_text(encoding='utf-8')
after = path.read_text(encoding='utf-8'); ast.parse(after)
with (out / 'fixture-fix.diff').open('x', encoding='utf-8') as stream:
    stream.writelines(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                       fromfile='before/test_quality_legacy_e2e.py', tofile='after/test_quality_legacy_e2e.py'))
record = {'status': 'PASS', 'product_status': 'INCOMPLETE', 'real_codex_turns': 0,
          'scope': 'saved evidence classification and static boundary plan, not a new E2E pass',
          'source': str(source), 'w07': {'assertion': 'W07-MANUAL-SOURCE', 'base': base, 'changed_ref': refs[-1]['stdout'].strip()},
          'classification': 'fixture sent new requests while idle and reused an ended Stop without starting a worker turn',
          'task': {'state': task['state'], 'candidate_commit': task['candidate_commit'], 'delivery_turn': task['current_attempt']['turn_id']},
          'observed_events': selected, 'old_durable_requests': [row['key'] for row in tables['relay_requests']],
          'expected_after_fix': ['worker T1 dirty request', 'receipt T2 -> idle', 'executor input -> worker T3',
              'same-turn short/base/C/duplicate batch', 'receipt T4 -> idle', 'executor input -> worker T5',
              'unauthorized C2 rejection', 'receipt T6 -> idle', 'reviewer own T1 -> result/reclaimed', 'scored C integration -> worker reclaimed'],
          'synthetic_input_count': 7, 'configured_limit': 10, 'remaining': 'new full entry execution by controller'}
with (out / 'run.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({key: record[key] for key in ('status', 'product_status', 'classification')}))
