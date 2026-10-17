#!/usr/bin/env python3
"""Check the T-078 conflict resolution without starting a daemon or CLI fixture."""
import argparse
import ast
import contextlib
import difflib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE, MAIN, WORKER = '14b57d22', '532c51f4', 'b5ed880b'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir()


def source(revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT)


checks = []


def record(name, passed, **details):
    checks.append({'name': name, 'pass': bool(passed), **details})


shared = ['src/panes.ts', 'src/gates/core.ts', 'src/gates/cli.ts', 'src/daemon.ts',
          'src/transport.ts', 'src/contracts/a2aGates.ts', 'tests/daemon_acceptance_host.ts']
for relative in shared:
    path = 'workbench/' + relative
    before = source(BASE, path).decode().splitlines(keepends=True)
    main = source(MAIN, path).decode().splitlines(keepends=True)
    current = (ROOT / path).read_text(encoding='utf-8')
    added = [{'main_line': c + 1, 'text': ''.join(main[c:d])}
             for tag, a, b, c, d in difflib.SequenceMatcher(None, before, main, autojunk=False).get_opcodes()
             if tag in ('insert', 'replace') and c != d]
    missing = [block for block in added if block['text'] not in current]
    record('main_additions:' + path, not missing, blocks=len(added), missing=missing)
    syntax = subprocess.run(['node', '--check', path], cwd=ROOT, capture_output=True, text=True)
    record('syntax:' + path, syntax.returncode == 0, exit=syntax.returncode, stderr=syntax.stderr)

for path in ['workbench/src/gates/cli.ts', 'workbench/src/relay.ts', 'workbench/src/credentials.ts']:
    record('worker_preserved:' + path, source(WORKER, path) == (ROOT / path).read_bytes())

main_changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, MAIN, '--', 'workbench'], cwd=ROOT).decode().splitlines()
worker_changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, WORKER, '--', 'workbench'], cwd=ROOT).decode().splitlines()
for path in sorted(set(main_changed) - set(worker_changed)):
    record('main_only_preserved:' + path, source(MAIN, path) == (ROOT / path).read_bytes())

readme = (ROOT / 'workbench/README.md').read_text(encoding='utf-8')
for revision, start, end in [
    (MAIN, '普通请求的传输期限为 120 秒', '随后停止自建窗格、保存退出事件、关闭数据库。停止不替代 reclaim，也不把失败或未知结果改成通过。'),
    (WORKER, '启动前显式设置 `A2A_OPERATOR_CREDENTIAL`', '的 thread/turn。管理凭据不虚构线程，不能替代受管 worker 的原生身份。'),
]:
    previous = source(revision, 'workbench/README.md').decode()
    block = previous[previous.index(start):previous.index(end) + len(end)]
    record('readme_preserved:' + revision, block in readme)

runner = ROOT / 'workbench/tests/run_daemon_acceptance.py'
ast.parse(runner.read_text(encoding='utf-8'))
record('runner_python_syntax', True)
with tempfile.TemporaryDirectory(prefix='t078-merge-args-', dir='/tmp') as temporary:
    temp = Path(temporary)
    identity = temp / 'identity.json'
    identity.write_text(json.dumps({'task': 'T-078-1', 'worker': 's13-t078'}), encoding='utf-8')
    cases = [
        ('output_root', ['--suite', 'coop', '--output-root', str(temp / 'root')], 0, temp / 'root/output_root'),
        ('output_identity', ['--suite', 'coop', '--output-root', str(temp / 'unused'), '--output', str(temp / 'explicit'), '--identity-file', str(identity)], 0, temp / 'explicit'),
        ('probe_root', ['--probe', 'all', '--output-root', str(temp / 'probes')], 0, temp / 'probes/probe_root'),
        ('validation_root_rejected', ['--validation', '--output-root', str(temp / 'invalid')], 2, None),
        ('all_output_rejected', ['--probe', 'all', '--output', str(temp / 'invalid-all')], 2, None),
    ]
    for name, argv, expected_exit, expected_out in cases:
        namespace = runpy.run_path(str(runner))['main'].__globals__
        calls = []
        namespace['clean_fixture_environment'] = lambda: None
        def focused(probe, out, suite=None, test=None, core=None):
            calls.append({'out': str(out), 'identity': dict(namespace['IDENTITY'])})
            return 0
        namespace['run_probe'] = focused
        namespace['run_all'] = lambda label, out: focused('all', out)
        previous = sys.argv
        sys.argv = [str(runner), *argv, '--label', name]
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                try:
                    code = namespace['main']()
                except SystemExit as error:
                    code = error.code
        finally:
            sys.argv = previous
        passed = code == expected_exit and (len(calls) == 1 if expected_out else not calls)
        if expected_out:
            passed = passed and calls[0]['out'] == str(expected_out.resolve()) and calls[0]['identity']['runner'] == 'daemon-acceptance'
        if name == 'output_identity':
            passed = passed and calls[0]['identity']['task'] == 'T-078-1' and calls[0]['identity']['worker'] == 's13-t078'
        record('arguments:' + name, passed, exit=code, calls=calls, stderr=stderr.getvalue())

result = {'status': 'PASS' if all(check['pass'] for check in checks) else 'INCOMPLETE',
          'scope': 'Static merge and argument parsing only. Suite/probe execution is replaced by a recorder.',
          'base': BASE, 'main': MAIN, 'worker': WORKER, 'argv': sys.argv, 'checks': checks,
          'model_turns': 0, 'daemon_started': False, 'final_regression_run': False}
with (args.output / 'results.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps({'status': result['status'], 'checks': len(checks), 'failed': [c['name'] for c in checks if not c['pass']]}))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
