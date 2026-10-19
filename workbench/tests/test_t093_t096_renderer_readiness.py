"""Replay the real runner predicate with saved views; no CLI/helper/GUI/model.

Failure list: driver snapshot is mistaken for DOM readiness; one pending pane
is skipped; DOM identity/input differs; failed panes lose identity; saved empty
reopen becomes nonempty; stale cached frame hides a later complete rendering.
"""
import ast
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

repo = Path(__file__).resolve().parents[2]
evidence = repo / 'evidence/2026-10-16-batch16/T-093'
source = Path(sys.argv[2]) if len(sys.argv) > 2 else repo / 'evidence/2026-10-16-batch16/T-096/run_restart.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'inspect_window')
current = None
class Observer:
    def call(self, command):
        assert command == 'inspect-all'
        return current
namespace = {'observer': Observer(), 'args': SimpleNamespace(panes=3)}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
inspect = namespace['inspect_window']
inputs = json.loads((evidence / 'renderer-readiness-inputs-22.json').read_text(encoding='utf-8'))['inputs']
checks = []
def check(name, view, expected, count=None):
    global current
    current = copy.deepcopy(view)
    result = inspect(count)
    passed = (result is not None) == expected
    checks.append({'case': name, 'status': 'PASS' if passed else 'FAIL',
                   'expected_ready': expected, 'observed_ready': result is not None})
    return result

for sample in inputs:
    check(sample['case'], sample['view'], sample['expected_ready'])

complete = next(s['view'] for s in inputs if s['case'] == 't093-r21-empty-reopen-01-later-inspect-2')
for field in ['launch', 'task', 'role', 'preset', 'thread', 'pane_key', 'input_enabled']:
    changed = copy.deepcopy(complete)
    changed['panes'][1][field] = False if field == 'input_enabled' else 'unrecognized-dom-' + field
    check('different_DOM_' + field, changed, False)
for index in range(3):
    pending = copy.deepcopy(complete)
    pending['panes'][index].pop('launch')
    check('pending_DOM_' + str(index), pending, False)
check('saved_empty_reopen', {'panes': [], 'pane_keys': [], 'text': '当前任务没有打开的窗格。'}, True, 0)
check('empty_with_leftover_key', {'panes': [], 'pane_keys': ['stale-key'], 'text': '当前任务没有打开的窗格。'}, False, 0)
check('empty_without_message', {'panes': [], 'pane_keys': [], 'text': ''}, False, 0)
check('wrong_pane_count', {**complete, 'panes': complete['panes'][:2]}, False)

# Replay the real bounded wait with a supplied clock. A persistent placeholder
# must time out; a later fully rendered frame may proceed. No delay is raised.
wait_node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'wait')
class Clock:
    value = 0
    def monotonic(self): return self.value
    def sleep(self, seconds): self.value += seconds
clock = Clock(); namespace['time'] = clock
exec(compile(ast.Module(body=[wait_node], type_ignores=[]), str(source), 'exec'), namespace)
pending = next(s['view'] for s in inputs if s['case'] == 't093-r21-empty-reopen-01')
current = pending
try:
    namespace['wait'](inspect, 'complete renderer snapshots', timeout=4)
except TimeoutError:
    checks.append({'case': 'persistent_placeholder_times_out', 'status': 'PASS'})
else:
    checks.append({'case': 'persistent_placeholder_times_out', 'status': 'FAIL'})
clock.value = 0
frames = iter([pending, complete])
def next_frame():
    global current
    current = next(frames)
    return inspect()
try:
    result = namespace['wait'](next_frame, 'complete renderer snapshots', timeout=4)
    assert result is complete
    checks.append({'case': 'later_DOM_commit_unblocks_wait', 'status': 'PASS'})
except (AssertionError, StopIteration):
    checks.append({'case': 'later_DOM_commit_unblocks_wait', 'status': 'FAIL'})

# The business oracle below is independent of the readiness predicate. Awaiting
# a DOM identity must not make a writable or invisible failed pane acceptable.
predicates = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'check' and len(node.args) >= 2:
        if isinstance(node.args[0], ast.Constant) and node.args[0].value == 'fault_visible_readonly':
            predicates['fault_visible_readonly'] = compile(ast.Expression(node.args[1]), str(source), 'eval')
assert 'fault_visible_readonly' in predicates
fault = next(s['view']['panes'][0] for s in inputs if s['case'] == 't093-r18b-isolation-01')
for name, view, expected in [('visible_failed_pane', fault, True),
    ('failed_pane_must_be_readonly', {**fault, 'input_enabled': True}, False),
    ('placeholder_is_not_unrestored_message', {**fault, 'text': '窗格 读取中 尚未启动窗格'}, False)]:
    actual = bool(eval(predicates['fault_visible_readonly'], {'view': view}))
    checks.append({'case': name, 'status': 'PASS' if actual == expected else 'FAIL'})

status = 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL'
report = {'status': status, 'source': str(source), 'scope': 'actual inspect_window/wait and unchanged failed-pane assertion; saved read-only observations and supplied clock; no real runtime',
          'checks': checks, 'real_CLI_helper_model_calls': 0}
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(report, output, ensure_ascii=False, indent=2); output.write('\n')
print(json.dumps({'status': status, 'cases': len(checks), 'failed': [c['case'] for c in checks if c['status'] == 'FAIL']}))
raise SystemExit(0 if status == 'PASS' else 2)
