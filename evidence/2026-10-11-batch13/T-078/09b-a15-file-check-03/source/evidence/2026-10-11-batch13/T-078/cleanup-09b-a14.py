"""A14-only cleanup after verified redacted archival; never signal Claude directly."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-gbxz0tyb')
PIDS = [48453, 48454, 48461, 48560, 48562, 48938, 48939, 52257, 52258]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def ps(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}, timeout=5)
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def process_graph():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,tpgid='], capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}, timeout=5)
    assert result.returncode == 0 and not result.stderr.strip()
    graph = {}
    for line in result.stdout.splitlines():
        fields = list(map(int, line.split())); assert len(fields) == 4 and fields[0] not in graph
        graph[fields[0]] = dict(zip(['pid', 'ppid', 'pgid', 'tpgid'], fields))
    return graph


def validate_owners(owner, identities, graph):
    assert owner['root'] == str(ROOT)
    fixed = owner['pids']
    assert [fixed[key] for key in ['ideation_api', 'executor_api', 'daemon', 'target_shell', 'target_leader']] == PIDS[:5]
    assert [owner['roles'][role][key] for role in ['ideation', 'executor'] for key in ['shell_pid', 'cli_pid']] == PIDS[5:]
    original = json.loads(Path(owner['identity_reference']).read_bytes())['binding']
    assert original['root'] == str(ROOT)
    for label, old_name in [('ideation_api', 'ideation_api'), ('executor_api', 'executor_api'),
                            ('daemon', 'daemon'), ('target_shell', 'shell'), ('target_leader', 'leader')]:
        pid = fixed[label]; now = identities[pid]; before = original['identities'][old_name]
        assert now is not None and now['pid'] == before['pid'] == pid
        assert now['started'] == before['lstart'] and now['command'] == before['command'], ('original owner changed', pid)
    for role in ['ideation', 'executor']:
        binding = owner['roles'][role]
        manifest = json.loads(Path(binding['manifest']).read_bytes())
        assert manifest['launch'] == binding['launch'] and manifest['session'] == binding['session']
        assert manifest['shell_pid'] == binding['shell_pid'] and manifest['cli']['pid'] == binding['cli_pid']
        shell, cli = identities[binding['shell_pid']], identities[binding['cli_pid']]
        assert shell is not None and cli is not None
        assert cli['started'] == manifest['cli']['started'] == binding['cli_lstart']
        argv = shlex.split(cli['command'])
        assert argv[0] == manifest['cli']['command']
        assert argv[argv.index('--session-id') + 1] == binding['session']
        assert str(ROOT / 'roles' / role / 'claude-debug.log') in argv
        assert shell['command'].startswith('/bin/zsh ') and str(ROOT) in shell['command'] and binding['session'] in shell['command']
        parent = graph[binding['shell_pid']]; child = graph[binding['cli_pid']]
        assert parent['ppid'] == fixed['daemon'] and child['ppid'] == binding['shell_pid']
        assert parent['pgid'] == binding['shell_pid'] and child['pgid'] == binding['cli_pid']
        assert parent['tpgid'] == child['tpgid'] == binding['cli_pid']
    assert graph[fixed['target_shell']]['ppid'] == fixed['daemon']
    assert graph[fixed['target_leader']]['ppid'] == fixed['target_shell']
    descendants = {fixed['daemon']}
    while True:
        expanded = descendants | {pid for pid, value in graph.items() if value['ppid'] in descendants}
        if expanded == descendants: break
        descendants = expanded
    assert descendants == set(PIDS[2:]), ('unexpected daemon descendants', sorted(descendants))


def wait_absent(pid, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if ps(pid) is None: return
        time.sleep(.1)
    raise RuntimeError('owned_process_exit_unconfirmed:' + str(pid))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--redaction-result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(exist_ok=False)
    record = {'status': 'BLOCKED', 'root': str(ROOT), 'dry_run': args.dry_run, 'signals_sent': [],
              'root_removed': False, 'slots_removed': [], 'scope': 'A14 nine recorded processes only; archive only the approved redacted projection'}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    save()
    try:
        owner = json.loads(args.owner.read_bytes()); approval = json.loads(args.approval.read_bytes())
        assert owner['root'] == approval['root'] == str(ROOT) and approval['pids'] == PIDS
        assert approval['external_archive'] == owner['external_archive']
        assert ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        record['approval_ref'] = approval.get('approval_ref')
        if not args.dry_run:
            assert approval['approved_by'] == 'executor' and isinstance(approval['approval_ref'], str) and approval['approval_ref'].strip(), 'signed_cleanup_approval_required'
        frozen = json.loads((Path(owner['stage_a']) / 'readiness.json').read_bytes())
        assert frozen['root'] == str(ROOT) and frozen['daemon']['pid'] == owner['pids']['daemon']
        for role in ['ideation', 'executor']:
            ready = json.loads((ROOT / 'roles' / role / 'api-ready.json').read_bytes())
            expected = next(row for row in frozen['api_processes'] if row['role'] == role)
            assert ready == expected['ready'] and ready['pid'] == owner['pids'][role + '_api']
        assert int((ROOT / 'state/daemon.pid').read_text()) == owner['pids']['daemon']
        identities = {pid: ps(pid) for pid in PIDS}; graph = process_graph()
        validate_owners(owner, identities, graph)
        assert {pid: ps(pid) for pid in PIDS} == identities, 'owner_changed_on_second_read'
        record.update(identity_checks='PASS', identities=identities,
                      process_graph={str(pid): graph[pid] for pid in PIDS},
                      planned_actions=['verify redacted archive and every retained member byte/type',
                          'authenticated daemon_stop; panes.shutdown closes both Claude roles and target',
                          'confirm seven daemon/role/target processes absent',
                          'one SIGTERM per original API, confirm within three seconds',
                          'recheck redacted counts/receipt unchanged and archive bytes; remove only fixed root'])
        if args.dry_run:
            record.update(status='PASS', action='read-only owner checks; no archive, stop, signal or deletion')
            save(); print(json.dumps({'status': 'PASS', 'dry_run': True, 'signals_sent': []})); return 0
        redactor = load_module('a14_projection', BASE / 'redact-a14-scene.py')
        archived = json.loads(args.redaction_result.read_bytes())
        assert archived['status'] == 'PASS' and archived['root'] == str(ROOT)
        assert archived['archive'] == owner['external_archive'] and archived['byte_readback'] == 'PASS'
        summary = redactor.verify_archive(archived)
        assert summary == redactor.collect(owner), 'scene_changed_after_redacted_archive'
        assert {pid: ps(pid) for pid in PIDS} == identities, 'owner_changed_before_stop'
        env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
        env['A2A_OPERATOR_CREDENTIAL'] = str(ROOT / 'operator.json')
        command = [shutil.which('node'), str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', str(ROOT / 'state'), 'daemon_stop']
        stopped = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True, text=True, timeout=30)
        record['daemon_stop'] = {'command': command, 'exit_code': stopped.returncode, 'stdout': stopped.stdout, 'stderr': stopped.stderr}; save()
        assert stopped.returncode == 0
        for pid in PIDS[2:]: wait_absent(pid, 20)
        assert not (ROOT / 'state/control.sock').exists() and not (ROOT / 'state/daemon.pid').exists()
        for pid in PIDS[:2]:
            assert ps(pid) == identities[pid] and ps(pid) == identities[pid], ('API changed; no signal', pid)
            os.kill(pid, signal.SIGTERM); record['signals_sent'].append({'pid': pid, 'signal': 'SIGTERM'}); save()
            wait_absent(pid, 3)
        assert all(ps(pid) is None for pid in PIDS)
        assert redactor.collect(owner) == summary and redactor.verify_archive(archived) == summary
        record.update(archive=archived['archive'], archive_bytes=Path(archived['archive']).stat().st_size,
                      archive_inventory=archived['inventory'], byte_readback='PASS',
                      retained_payload='redacted projection only; raw root/auth/debug/messages intentionally not archived')
        assert ROOT.resolve() == ROOT and not ROOT.is_symlink()
        shutil.rmtree(ROOT); assert not ROOT.exists()
        record.update(status='PASS', root_removed=True)
    except Exception as error:
        record.update(status='BLOCKED', error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists())
    save(); print(json.dumps({key: record.get(key) for key in ['status', 'dry_run', 'signals_sent', 'root_removed', 'error']}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
