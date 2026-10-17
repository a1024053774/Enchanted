"""Check the real adapter's fixture budget without running the original suites.

The controlled quality path needs its declared 30-second positive-case budget.
Failure cases: positives retain the old short budget; negative deadlines expand;
caller fields change; budget translation has no evidence. No daemon/PTY/ps starts.
"""
import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FILE = 'workbench/tests/daemon_acceptance_adapter.py'
REVISION = 'f20a74ada49564499691cd14cf019f8cec448db1'


def adapter_type(source):
    original = ast.parse((ROOT / 'acceptance/test_run_e2e.py').read_text(encoding='utf-8'))
    base = next(node for node in original.body if isinstance(node, ast.ClassDef) and node.name == 'RunCLI')
    method = next(node for node in base.body if isinstance(node, ast.FunctionDef) and node.name == 'run_args')
    legacy = ast.ClassDef(name='Legacy', bases=[], keywords=[], body=[method], decorator_list=[])
    adapter = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'DaemonRun')
    adapter.bases = [ast.Name(id='Legacy', ctx=ast.Load())]
    scope = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[legacy, adapter], type_ignores=[])), FILE, 'exec'), scope)
    return scope['DaemonRun']


def exercise(source):
    cls = adapter_type(source)
    checks = []
    positive = ['test_run_entry_point_completes_registered_task',
                'test_transient_tool_activity_keeps_same_thread_owner',
                'test_matching_reclaim_guard_is_idempotent_after_automatic_success']
    for name, seconds, expected in [(name, 8, 30) for name in positive] + [
        ('test_done_without_submit_hits_deadline_and_cannot_accept_committed_candidate', 2, 2),
        ('test_oracle_failure_is_not_success_and_reclaims_only_owned_thread', 8, 8),
        ('test_concurrent_duplicate_run_has_one_prompt_and_one_attempt', 30, 30),
        (positive[0], 5, 5)]:
        fixture = cls(); fixture.task = 'independent-task'; fixture._testMethodName = name
        records = []; fixture.lifecycle = lambda event, **data: records.append({'event': event, **data})
        args = fixture.run_args(seconds=seconds, name='independent-name')
        actual = args[args.index('--wait-seconds') + 1]
        assert actual == str(expected), ('Full quality positive keeps its declared budget' if name in positive and seconds == 8
                                        else 'Negative or explicit nondefault budget must stay unchanged')
        assert args[:4] == ('--task', 'independent-task', '--runtime-mode', 'approval-required')
        if seconds != expected:
            assert records == [{'event': 'quality_run_wait_budget', 'requested_seconds': 8,
                                'configured_seconds': 30, 'reason': 'controlled reviewer and executor stages'}]
        else:
            assert records == []
        checks.append({'test': name, 'requested': seconds, 'expected': expected})
    return checks


report = {'status': 'INCOMPLETE', 'argv': sys.argv, 'scope': __doc__}
try:
    bad = subprocess.check_output(['git', 'show', REVISION + ':' + FILE], cwd=ROOT, text=True)
    try:
        exercise(bad)
    except AssertionError as error:
        report['known_bad'] = {'revision': REVISION, 'rejected': str(error) == 'Full quality positive keeps its declared budget', 'error': str(error)}
    assert report.get('known_bad', {}).get('rejected')
    source = (ROOT / FILE).read_text(encoding='utf-8')
    report['checks'] = exercise(source)
    marker = 'if seconds == 8 and self._testMethodName in quality_positives:'
    assert source.count(marker) == 1
    try:
        exercise(source.replace(marker, 'if True:', 1))
    except AssertionError as error:
        report['negative_budget_mutant'] = {'rejected': str(error) == 'Negative or explicit nondefault budget must stay unchanged', 'error': str(error)}
    assert report.get('negative_budget_mutant', {}).get('rejected')
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(report, output, ensure_ascii=False, indent=2); output.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
