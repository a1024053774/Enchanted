"""Test-driver regression only; not evidence of native sandbox behavior.
Failure modes: reviewer copy has no task-shaped cwd; reviewer is routed to another
task; worker/monitor routing stops working when reviewer routing is repaired.
--revision extracts the driver from a known-bad revision without editing the checkout.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import review_task  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('--summary', required=True, type=Path)
parser.add_argument('--revision')
args = parser.parse_args()
assert not args.summary.exists(), 'Preserve existing evidence'
driver = 'workbench/tests/test_t140_extra_dirs_e2e.py'
text = (subprocess.check_output(['git', 'show', args.revision + ':' + driver], text=True) if args.revision
        else Path(driver).read_text(encoding='utf-8'))
tree = ast.parse(text)
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
plan = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == 'plan')
namespace = dict(json=json, re=re, x=Path('/fixture/X'), tasks={'T-C': ('Claude Code', True), 'T-D': ('Codex', True)},
                 review_task=review_task, probe=lambda *args: 'probe', quote=lambda value: "'" + value.replace("'", "'\\''") + "'")
exec(compile(ast.Module(body=[plan], type_ignores=[]), driver, 'exec'), namespace)
report = dict(status='INCOMPLETE', argv=sys.argv, scope='scripted model plan routing only; no product/native proof', checks=[])
try:
    for task in ('T-C', 'T-D'):
        # A real reviewer copy is keyed by UUID; the task comes from the card in the review prompt (T-203).
        prompt = '审查这一次交付\n' + json.dumps({'id': task, 'goal': 'T-140'}, indent=2, ensure_ascii=False)
        key, commands, final = namespace['plan']('/fixture/state/review-copies/88b94f3e-fb70-4c79-a69e-aa157142db29', prompt)
        assert key == 'review-' + task
        assert f'check_{task}.py' in commands[1] and commands[-1][:2] == ('enchanted', 'review_submit') and commands[-1][2]['verdict'] == '可合并'
        report['checks'].append('reviewer_' + task)
    key, commands, final = namespace['plan']('/fixture/worktrees/demo/T-C-a1', "显式交付：\n'node' 'submit' 'FULL_COMMIT_SHA'\n")
    assert key == 'T-C' and 'git add result-T-C.json' in commands
    report['checks'].append('worker')
    assert namespace['plan']('/fixture/state/monitors/uuid', 'T140_MONITOR_D')[0] == 'monitor-D'
    report['checks'].append('monitor')
    report['status'] = 'PASS'
except BaseException as error:
    report['error'] = f'{type(error).__name__}: {error}'
    raise
finally:
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
