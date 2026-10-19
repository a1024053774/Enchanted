"""由 RUN-OUTSIDE-01 启动；保存每个结果，任何失败都保留。"""
import json
import os
from pathlib import Path
import shutil
import sqlite3
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
cases = [('known-bad', ['--revision', 'cc18d93dbbcf2ee641dc92befe68e5b0609b4807']),
         ('metadata-known-bad', ['--revision', 'd54826223194b56ca057b8ab3213729c9e53a29a']),
         ('candidate', []), ('privacy-mutant', ['--mutant', 'privacy']),
         ('input-events-mutant', ['--mutant', 'input-events']), ('restart-mutant', ['--mutant', 'restart'])]
for case, extra in cases:
    argv = ['python3', str(root/'workbench/tests/test_t104_shell_e2e.py'), '--archive', str(run/case),
            '--summary', str(summary/f'{case}.json'), *extra]
    with (run/f'{case}.log').open('x') as log:
        result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    row = json.loads((summary/f'{case}.json').read_text(encoding='utf-8'))
    expected = result.returncode == 0 and row['status'] == 'PASS' if case == 'candidate' else False
    if case != 'candidate' and result.returncode == 1 and row.get('cleanup_complete'):
        phase, message = {
            'known-bad': ('shell_start', "Unknown option '--cwd'"),
            'metadata-known-bad': ('privacy', 'shell 逐次输入事件进入事件流'),
            'privacy-mutant': ('privacy', 'shell 输入内容泄漏进事件流'),
            'input-events-mutant': ('privacy', 'shell 逐次输入事件进入事件流'),
            'restart-mutant': ('restart', '后台重启新增了 shell launch 或创建事件'),
        }[case]
        expected = row.get('checkpoint') == phase and message in row.get('error', '')
        if case == 'restart-mutant':
            inventory = row.get('restart_inventory', {})
            expected = expected and len(inventory.get('after', {}).get('launches', [])) > len(inventory.get('before', {}).get('launches', []))
    checks.append(dict(case=case, argv=argv, exit=result.returncode, expected=bool(expected)))
    if expected and case in ('input-events-mutant', 'restart-mutant'):
        archived = Path(row['archive']['archive'])
        assert row['cleanup_complete'] and archived == run/case, '只读取本轮已停止并核对归档的现场'
        database = archived/'state/state.sqlite3'
        assert database.is_file(), '归档缺少数据库'
        for suffix in ['-wal', '-journal']:
            pending = Path(str(database)+suffix)
            assert not pending.exists() or pending.stat().st_size == 0, '归档仍有未合并日志，不能当作不可变主库读取'
        # Stopped, archived WAL-mode databases may have no writable sidecars.
        # Immutable applies only here, never to the live-daemon observations.
        with sqlite3.connect(database.as_uri()+'?mode=ro&immutable=1', uri=True) as db:
            if case == 'input-events-mutant':
                effect = db.execute("SELECT e.seq,e.launch FROM orchestration_events e JOIN launch_records l ON l.id=e.launch "
                    "WHERE e.type='window_request_admitted' AND json_extract(l.data,'$.role')='shell' ORDER BY e.seq").fetchall()
            else:
                boundary = db.execute("SELECT min(seq) FROM orchestration_events WHERE type='daemon_stopped'").fetchone()[0]
                effect = db.execute("SELECT seq,launch FROM orchestration_events WHERE type='shell_created' AND seq>? ORDER BY seq", (boundary,)).fetchall()
        checks[-1]['counterexample_effect'] = [dict(seq=seq, launch=launch) for seq, launch in effect]
        checks[-1]['expected'] = bool(effect)
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
if all(row['expected'] for row in checks) and len(checks) == len(cases):
    for case, argv in regressions:
        with (run/f'{case}.log').open('x') as log:
            result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        checks.append(dict(case=case, argv=argv, exit=result.returncode, expected=result.returncode == 0))
        print(json.dumps(checks[-1]), flush=True)
dependencies = json.loads((run/'dependencies.json').read_text(encoding='utf-8'))
report = dict(status='PASS' if len(checks) == len(cases)+len(regressions) and all(row['expected'] for row in checks) else 'INCOMPLETE',
              task='T-104', attempt='a1', part='backend', checks=checks, dependencies=dependencies,
              revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
              dirty=subprocess.check_output(['git','status','--short'],cwd=root,text=True),
              archive=str(run), independent_review='修复后独立复审尚未运行', electron='未启动（后台套件）')
with (summary/'suite.json').open('x',encoding='utf-8') as file:
    json.dump(report,file,ensure_ascii=False,indent=2)
    file.write('\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
