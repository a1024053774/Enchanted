#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
exec python3 -B - "$@" <<'PYCODE'
import ast
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

source = Path.cwd()
base = source / 'evidence/2026-10-11-batch13/T-078'
packet = base / '09b-a15-materials-01'
expected = json.loads((packet / 'SOURCE-BASE.json').read_bytes())['source_base']
label = '09b-executable-materials-15'
check_only = sys.argv[1:] == ['--check-only']
write_preflight = sys.argv[1:] == ['--write-preflight']
assert check_only or write_preflight or not sys.argv[1:]
def git(*args): return subprocess.check_output(['git', *args], cwd=source, text=True).strip()
def status():
    rows = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=source).decode('utf-8').split('\0')
    assert not any(row[:2].strip().startswith(('R', 'C')) for row in rows if row)
    return [{'status': row[:2], 'path': row[3:]} for row in rows if row]
allow = json.loads((base / '09b-a15-allowlist.json').read_bytes())
first = allow['existing_or_preflight']; second = allow['generated_second'] + allow['updated_second']
def covered(path, choices): return any(path == item or path.startswith(item.rstrip('/') + '/') for item in choices)

assert git('rev-parse', 'HEAD') == expected
assert git('branch', '--show-current') == 'exec/t078'
assert not git('diff', '--cached', '--name-only'), 'Index is not empty'
assert os.environ.get('A2A_ROLE') == 'worker' and os.environ.get('A2A_TASK') == 'T-078-1'
assert os.environ.get('CODEX_THREAD_ID') == '01a13a72-892d-7e33-8237-a592c9652c35'
for parent in ['0e6c2b833f6da64243f71d670ea45bb9116fda4d', '68d7749c284892a4bd43c9284e949b1ed3ea7e48']:
    subprocess.run(['git', 'merge-base', '--is-ancestor', parent, 'HEAD'], cwd=source, check=True)
assert not git('diff', 'HEAD', '--', 'workbench/src', 'workbench/app', 'workbench/bin', 'workbench/package.json')
outside1 = json.loads((base / 'merge-main-3-outside-01/result.json').read_bytes())
outside2 = json.loads((base / 'merge-main-3-outside-02/result.json').read_bytes())
assert all(row['status'] == 'PASS' for row in outside1['stages'][:4])
assert outside2['status'] == 'PASS' and len(outside2['stages']) == 2 and all(row['status'] == 'PASS' for row in outside2['stages'])
checked = json.loads((base / '09b-a15-file-check-04/result.json').read_bytes())
assert checked['status'] == 'PASS' and checked['source_unchanged'] and checked['known_bad_A14_instance_rejected']
assert checked['cleanup']['recorded_M5_rejected'] and checked['cleanup']['known_bad_owner_rejected']
assert checked['cleanup']['live_A14_access'] is False and checked['cleanup']['process_probes'] == 0
for path in checked['tested_source_files']:
    assert (source / path).read_bytes() == (base / '09b-a15-file-check-04/source' / path).read_bytes(), ('tested source changed', path)
assert label.startswith('09b-executable-materials-') and not (base / label).exists()
for path in allow['generated_second']: assert not (source / path).exists(), ('output already exists', path)
for path in first: assert (source / path).exists() or path in allow['generated_first'], ('git add path missing', path)
for path in second: assert (source / path).exists() or path in allow['generated_second'], ('no output producer', path)
for path in allow['generated_first']: assert covered(path, first)
rows = status()
assert all(covered(row['path'], first) for row in rows), ('unowned work', [row for row in rows if not covered(row['path'], first)])
simulated = [row for row in rows if not covered(row['path'], first + second)]
simulated += [path for path in allow['generated_first'] + allow['generated_second'] + allow['updated_second'] if not covered(path, first + second)]
assert not simulated, ('simulated final worktree is dirty', simulated)
for row in rows:
    if row['path'].endswith('.py'): ast.parse((source / row['path']).read_text(encoding='utf-8'), filename=row['path'])
script = base / 'commit-09b-a15.sh'
subprocess.run(['sh', '-n', str(script)], check=True)
ast.parse(script.read_text(encoding='utf-8').split("<<'PYCODE'\n", 1)[1].rsplit('\nPYCODE', 1)[0])
subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
assert (packet / 'protocol.json').read_bytes() == (base / '09b-materials-01/protocol.json').read_bytes()
approval = json.loads((packet / 'stage-a-approval.json').read_bytes())
assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['source_revision'] is None
assert approval['materials'] == label and approval['allow_role_cli_spawn'] is False and approval['protocol'] is True
assert approval['fixture_profile'] == 'a14-approved-gate-history-v1'
cleanup = json.loads((base / '09b-a14-cleanup-approval.json').read_bytes())
assert cleanup['approved_by'] == 'executor' and '主控 #322' in cleanup['approval_ref']
prior_cleanup = json.loads((base / '09b-a14-cleanup-01/result.json').read_bytes())
assert cleanup['approval_ref'] == prior_cleanup['approval_ref']
assert prior_cleanup['status'] == 'BLOCKED' and prior_cleanup['daemon_stop']['exit_code'] == 0
assert cleanup['pids'] == [48453, 48454, 48461, 48560, 48562, 48938, 48939, 52257, 52258]
assert '## 主控 #321：A-14 回收与 A-15 静态材料' in (base / 'RESULTS.md').read_text(encoding='utf-8')
frozen = json.loads((base / 'stage-b-a12-ideation-approval-01.json').read_bytes())
b1 = json.loads((packet / 'b1-approval-template.json').read_bytes())
assert b1['screen_approvals'] == frozen['screen_approvals'] and b1['tool_approval'] == frozen['tool_approval']
assert b1['screen_approvals'][3]['purpose'] == 'security-notice' and b1['screen_approvals'][3]['screen_text']
for path in [source / 'workbench/tests/run_t078_p1.py', source / 'workbench/tests/t078_09b_i1_permission.py',
             base / 'run-09b-stage-b.py', base / 'observe-startup-queued.py',
             Path('/Users/luckye/.local/share/claude/versions/2.1.296')]:
    assert path.is_file(), ('generated command entry missing', str(path))
for command in json.loads((packet / 'protocol.json').read_bytes())['commands'].values():
    assert Path(command['argv'][0]).is_file() and Path(command['argv'][1]).is_file()
command_files = [packet / 'STAGE-A-COMMAND.txt', packet / 'ROLE-MATERIAL-COMMANDS.txt', base / '09B-A14-CLEANUP-COMMANDS.txt', base / '09B-A14-CLEANUP-FINISH-COMMAND.txt']
commands = []
for file in command_files:
    for line in file.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'): continue
        argv = shlex.split(line)
        assert argv[:2] == ['python3', '-B'] and Path(argv[2]).is_file(), ('command entry missing', file, argv)
        for flag in ['--owner', '--approval', '--prompt-file']:
            if flag in argv: assert Path(argv[argv.index(flag) + 1]).is_file(), ('command input missing', flag, argv)
        commands.append(argv)
assert '--materials ' + str(base / label) + ' ' in (packet / 'STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
assert '--stage A --protocol' in (packet / 'STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
assert '09b-a14-' not in (packet / 'ROLE-MATERIAL-COMMANDS.txt').read_text(encoding='utf-8')
spec = importlib.util.spec_from_file_location('a15_command_generator', base / 'prepare-a14.py')
generator = importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)
phase_commands = []
for phase in json.loads((packet / 'protocol.json').read_bytes())['phases']:
    p1 = base / ('09b-a15-b1-' + phase['role'] + '-p1-01')
    for line in generator.phase_commands(base / '09b-a15-stage-a-01', p1, phase['id']).splitlines():
        if not line or line.startswith('#'): continue
        argv = shlex.split(line); assert Path(argv[2]).is_file()
        phase_commands.append(argv)
assert len(phase_commands) == 25
report = {'status': 'PASS', 'mode': 'check-only' if check_only else 'precommit', 'source_base': expected,
          'owned_paths': len(rows), 'unowned': [], 'simulated_final_status': simulated,
          'git_add_paths_exist_or_have_producer': True, 'commands': len(commands), 'phase_commands': len(phase_commands),
          'deferred_inputs': {'materials-15': 'unified prepare after source commit', 'A15 readiness': 'signed Stage A',
              'P1/actual launch label': 'role generator and successful B1 bind-launch', 'permission screen/result': 'actual phase dispatch'},
          'real_runtime_starts': 0, 'launch': 'NO_GO'}
if check_only:
    print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0)
# No generated report or RESULTS edit is left until after the final commit.
with (base / '09b-a15-preflight-02/ownership.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps({**report, 'entries': rows}, ensure_ascii=False, indent=2) + '\n')
if write_preflight:
    print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0)
subprocess.run(['git', 'add', '--', *first], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'test(T-078): prepare owner-bound A14 cleanup and A15 file materials'], cwd=source, check=True)
revision = git('rev-parse', 'HEAD'); assert not git('status', '--porcelain=v1', '--untracked-files=all')
subprocess.run([sys.executable, '-B', str(base / 'freeze-a15-materials.py')], cwd=source, check=True)
assert all(covered(row['path'], second) for row in status()), ('unowned generated path', status())
subprocess.run(['git', 'add', '--', *second], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A15 executable proposal and unsigned approval'], cwd=source, check=True)
assert not git('status', '--porcelain=v1', '--untracked-files=all'), 'final worktree is dirty'
print(json.dumps({'status': 'PASS', 'source_commit': revision, 'materials_commit': git('rev-parse', 'HEAD'), 'git_status': 'clean', 'launch': 'NO_GO'}, ensure_ascii=False))
PYCODE
