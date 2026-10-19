"""由 RUN-OUTSIDE-01 启动；保存每个结果，任何失败都保留。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
label = sys.argv[1]
assert label and all(char.isalnum() or char in '-_' for char in label)
assert os.path.ismount('/Volumes/WD-Elements'), '外置盘未挂载'
run = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104') / label
summary = Path(__file__).parent / label
summary.mkdir()
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
checks = []
for case, extra in [('known-bad', ['--revision', 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807']),
                    ('candidate', []), ('privacy-mutant', ['--leaky-mutant'])]:
    argv = ['python3', str(root/'workbench/tests/test_t104_shell_e2e.py'), '--archive', str(run/case),
            '--summary', str(summary/f'{case}.json'), *extra]
    with (run/f'{case}.log').open('x') as log:
        result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    row = json.loads((summary/f'{case}.json').read_text(encoding='utf-8'))
    expected = (result.returncode == 0 and row['status'] == 'PASS') if case == 'candidate' else (
        result.returncode == 1 and row.get('cleanup_complete') and
        (row.get('checkpoint') == 'shell_start' and "Unknown option '--cwd'" in row.get('error', '') if case == 'known-bad'
         else row.get('checkpoint') == 'privacy' and 'shell 输入内容泄漏进事件流' in row.get('error', '')))
    checks.append(dict(case=case, argv=argv, exit=result.returncode, expected=bool(expected)))
    if 'archive' in row:
        (summary/f'{case}.archive.json').write_text(json.dumps(row['archive'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(checks[-1], ensure_ascii=False), flush=True)
    if not row.get('cleanup_complete'):
        break

# Existing assertions remain unchanged. These supplied-boundary regressions
# supplement the real daemon E2E and do not count as its replacement.
regressions = [
    ('worker-dispatch', ['node', 'workbench/tests/test_pane_dispatch_state.ts', str(run/'worker-dispatch')]),
    ('controller-window', ['node', 'workbench/tests/test_t078_controller_window.ts', str(run/'controller-window')]),
    ('conflict-panes', ['node', 'workbench/tests/test_conflict_panes.ts', '--product', str(root), '--output', str(run/'conflict-panes.json')]),
    ('restore', ['node', '--experimental-vm-modules', 'workbench/tests/test_t096_restore.mjs', str(run/'restore.json')]),
]
if all(row['expected'] for row in checks) and len(checks) == 3:
    for case, argv in regressions:
        with (run/f'{case}.log').open('x') as log:
            result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        checks.append(dict(case=case, argv=argv, exit=result.returncode, expected=result.returncode == 0))
        print(json.dumps(checks[-1]), flush=True)
dependencies = json.loads((run/'dependencies.json').read_text(encoding='utf-8'))
report = dict(status='PASS' if len(checks) == 7 and all(row['expected'] for row in checks) else 'INCOMPLETE',
              task='T-104', attempt='a1', part=1, checks=checks, dependencies=dependencies,
              revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
              dirty=subprocess.check_output(['git','status','--short'],cwd=root,text=True),
              archive=str(run), independent_review='尚未运行', electron='第二段尚未授权')
with (summary/'suite.json').open('x',encoding='utf-8') as file:
    json.dump(report,file,ensure_ascii=False,indent=2)
    file.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
