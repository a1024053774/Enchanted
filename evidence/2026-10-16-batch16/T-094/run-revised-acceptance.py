#!/usr/bin/env python3
"""本地重放修订后的两个验收；仅真实 Git 和 codex --version，不启动模型或 Herdr。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('/tmp/t094-revised-acceptance-01'), help='重放须选择不存在的新目录')
OUT = parser.parse_args().output.resolve()
BASE = '61786370428c3ec5f894ea60acccf2695d54c2dc'
OUT.mkdir(exist_ok=False)
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
env.update(PYTHONDONTWRITEBYTECODE='1', GIT_AUTHOR_NAME='T094 baseline',
           GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_NAME='T094 baseline',
           GIT_COMMITTER_EMAIL='fixture@example.invalid')


def command(argv, cwd=REPO):
    return subprocess.run([str(v) for v in argv], cwd=cwd, env=env, text=True,
                          capture_output=True, timeout=60)


old = OUT / 'old-617'
old.mkdir()
paths = command(['git', 'ls-tree', '-r', BASE, '--', 'scripts']).stdout.splitlines()
for line in paths:
    meta, name = line.split('\t', 1)
    mode = meta.split()[0]
    data = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=REPO, env=env)
    target = old / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == '120000':
        target.symlink_to(data.decode('utf-8'))
    else:
        target.write_bytes(data)
        target.chmod(0o755 if mode == '100755' else 0o644)
for args in (['git', 'init', '-q'], ['git', 'add', 'scripts'], ['git', 'commit', '-qm', 'frozen 617 scripts']):
    result = command(args, cwd=old)
    if result.returncode:
        raise RuntimeError(result.stderr)
mutant = OUT / 'wrong-version-mutant'
shutil.copytree(old, mutant, symlinks=True)
launcher = mutant / 'scripts/launch-worker'
text = launcher.read_text(encoding='utf-8')
needle = 'cli_version=output(["codex", "--version"])'
assert text.count(needle) == 1
launcher.write_text(text.replace(needle, needle + ' + "-wrong-version-mutant"'), encoding='utf-8')
result = dict(status='INCOMPLETE', baseline=BASE, candidate=command(['git', 'rev-parse', 'HEAD']).stdout.strip(),
              model_turns=0, herdr_socket_calls=0, steps=[])


def run_step(label, argv, expected):
    began = time.monotonic()
    completed = command(argv)
    (OUT / (label + '.stdout.txt')).write_text(completed.stdout, encoding='utf-8')
    (OUT / (label + '.stderr.txt')).write_text(completed.stderr, encoding='utf-8')
    row = dict(label=label, argv=[str(v) for v in argv], exit_code=completed.returncode,
               requested_exit=expected, matches_requested=completed.returncode == expected,
               seconds=time.monotonic()-began)
    result['steps'].append(row)
    (OUT / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)


shell = REPO / 'acceptance/test_launcher_shell_ready_e2e.py'
trace = REPO / 'acceptance/test_herdr_traceability_e2e.py'
for case in ('test_delayed_shell_then_commit', 'test_child_foreground_times_out_with_argv'):
    run_step('old-' + case, [sys.executable, '-B', shell, '--launcher', old / 'scripts/launch-worker',
             '--artifacts', OUT / ('old-' + case), '--case', case], 1)
run_step('old-version', [sys.executable, '-B', trace, '--scripts-root', old / 'scripts',
         '--artifacts', OUT / 'old-version', '--case', 'test_commit_no_verify_and_plain_counterexample'], 1)
run_step('wrong-version-mutant', [sys.executable, '-B', trace, '--scripts-root', mutant / 'scripts',
         '--artifacts', OUT / 'wrong-version', '--case', 'test_commit_no_verify_and_plain_counterexample'], 1)
for case in ('test_delayed_shell_then_commit', 'test_child_foreground_times_out_with_argv',
             'test_unknown_shell_times_out', 'test_hung_status_query_times_out',
             'test_status_error_is_not_retried', 'test_wrong_pane_is_rejected',
             'test_agent_start_failure_is_not_retried'):
    run_step('new-' + case, [sys.executable, '-B', shell, '--artifacts', OUT / ('new-' + case), '--case', case], 0)
for case in ('test_commit_no_verify_and_plain_counterexample', 'test_original_failure_missing_env_and_damaged_launch',
             'test_duplicate_trailers_keep_body_and_project_trailer', 'test_amend_rebase_merge_and_native_replacement',
             'test_score_required_abandon_upgrade_and_user', 'test_score_concurrency_corruption_and_start_failure',
             'test_score_missing_or_unknown_check_rejected'):
    run_step('new-' + case, [sys.executable, '-B', trace, '--artifacts', OUT / ('new-' + case), '--case', case], 0)
result['status'] = 'PASS' if all(s['matches_requested'] for s in result['steps']) else 'INCOMPLETE'
(OUT / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status=result['status'], raw_output=str(OUT)), ensure_ascii=False))
sys.exit(0 if result['status'] == 'PASS' else 1)
