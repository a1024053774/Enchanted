"""已知坏行为必须触发对应的业务断言；Python 3.9，无模型或真实 PTY。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--summary', required=True, type=Path)
a = p.parse_args()
assert not a.summary.exists()
source = Path(__file__).resolve().parents[1]
root = Path(tempfile.mkdtemp(prefix='t112-mutants-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', cases=[], fixture=str(root), model_calls=0)
for dependency in ('effect', 'fast-check', 'pure-rand', 'node-pty'):
    shutil.copytree(source / 'node_modules' / dependency, root / 'node_modules' / dependency,
                    ignore=shutil.ignore_patterns('win32-*', 'linux-*'))
mutations = [
    ('claude_effort_filtered', 'contracts/modelOptions.ts', 'effort: Schema.optional(TrimmedNonEmptyString)',
     'effort: Schema.optional(Schema.Literals(["low", "medium", "high", "xhigh", "max"]))', 'future-effort-sentinel'),
    ('saved_beats_override', 'store.ts', '...factoryExecution, ...saved, ...executionOverrides(overrides)',
     '...factoryExecution, ...executionOverrides(overrides), ...saved', 'Expected values to be strictly deep-equal'),
    ('reviewer_inherits_worker', 'panes.ts', 'this.store.executionSelection(role, overrides)',
     "this.store.executionSelection('worker', overrides)", 'strictly equal'),
    ('old_executor_restriction', 'panes.ts', 'check(task.card.executor.cli === "Codex", "worker_executor_mismatch");',
     'check(task.card.executor.cli === "Codex" && model === "gpt-6.1-sol" && effort === "xhigh", "worker_executor_mismatch");', 'worker_executor_mismatch'),
    ('startup_failure_masked', 'panes.ts', '; a2a_cli_status=$?; if (( a2a_cli_status != 0 )); then exit $a2a_cli_status; fi; exec /bin/zsh -f -i',
     '; : \\"if (( a2a_cli_status != 0 )); then exit\\"; exec /bin/zsh -f -i', 'Recorded shell must propagate native startup failure'),
]
for name, file, old, new, signal in mutations:
    tree = root / name
    shutil.copytree(source / 'src', tree / 'src')
    path = tree / 'src' / file
    text = path.read_text(); assert text.count(old) == 1, (name, text.count(old))
    path.write_text(text.replace(old, new), encoding='utf-8')
    output = root / (name + '.json')
    command = ['node', str(source / 'tests/test_t112_execution.mjs'), str(output), str(tree)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    row = json.loads(output.read_text()) if output.exists() else {}
    rejected = result.returncode == 1 and row.get('status') == 'INCOMPLETE' and signal in row.get('error', '')
    report['cases'].append(dict(name=name, rejected=rejected, command=command, exit=result.returncode, error=row.get('error'), stderr=result.stderr))
report['status'] = 'PASS' if all(row['rejected'] for row in report['cases']) else 'INCOMPLETE'
a.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
