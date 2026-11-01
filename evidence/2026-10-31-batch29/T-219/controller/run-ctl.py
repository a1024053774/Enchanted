"""T-219 主控独立复跑：在 T-219 worktree 上逐个运行绿态入口与两个变异反例，输出写本目录，不复用 worker 的输出。"""
import json, os, pathlib, subprocess, sys, time
WT = pathlib.Path('/Users/luckye/Documents/Code/a2a-worktrees/T-219')
OUT = pathlib.Path('/Users/luckye/Documents/Code/a2a-worktrees/T-219-controller')
RUNS = [
    ('t133', ['python3', 'workbench/tests/test_t133_t107_terminal_controller_e2e.py', '--summary', '{o}.json'], 0),
    ('t133-mutant', ['python3', 'workbench/tests/test_t133_t107_terminal_controller_e2e.py', '--mutant', 'empty-shell-running', '--summary', '{o}.json'], 1),
    ('domain', ['node', 'workbench/tests/test_t078_inbox_domain.ts', '{o}'], 0),
    ('pane', ['node', 'workbench/tests/test_t078_pane_runtime.ts', '{o}'], 0),
    ('a13', ['node', 'workbench/tests/test_t078_a13_rehearsal.ts', '{o}'], 0),
    ('t184', ['python3', 'workbench/tests/test_t184_unwired_cli_e2e.py', '--summary', '{o}.json'], 0),
    ('recovery', ['python3', 'workbench/tests/test_daemon_recovery_e2e.py', '--output', '{o}'], 0),
    ('electron', ['python3', 'workbench/tests/test_electron_e2e.py', '--source', str(WT), '--stage', 'window', '--output', '{o}'], 0),
    ('t142', ['python3', 'workbench/tests/test_t142_terminal_open_e2e.py', '--summary', '{o}.json'], 0),
    ('t142-mutant', ['python3', 'workbench/tests/test_t142_terminal_open_e2e.py', '--backend-only', '--mutant', 'cross-project-denied', '--summary', '{o}.json'], 1),
]
if len(sys.argv) > 1: RUNS = [r for r in RUNS if r[0] in sys.argv[1:]]
env = dict(os.environ, TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp')
results = []
for name, argv, expect in RUNS:
    o = OUT / (name + '-ctl-01')
    assert not o.exists() and not pathlib.Path(str(o) + '.json').exists(), o
    argv = [a.replace('{o}', str(o)) for a in argv]
    started = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    with open(str(o) + '.log', 'xb') as log:
        p = subprocess.Popen(argv, cwd=WT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: code = p.wait(timeout=1800)
        except subprocess.TimeoutExpired: p.terminate(); code = 'timeout'
    row = dict(name=name, argv=argv, cwd=str(WT), started=started, finished=time.strftime('%Y-%m-%dT%H:%M:%S%z'), exit=code, expected_exit=expect, as_expected=code == expect)
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
(OUT / 'runs-ctl-01.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
