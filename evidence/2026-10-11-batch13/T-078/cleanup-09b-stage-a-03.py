"""Owner-bound dry-run and cleanup for #195's failed Stage-A root."""
import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-576xn98k')
STATE = ROOT / 'state'
API = [
    (62217, 'ideation', ROOT / 'roles/ideation'),
    (62218, 'executor', ROOT / 'roles/executor'),
]
DAEMON = 62220
NODE = shutil.which('node')
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def ps(pid):
    result = subprocess.run(
        ['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
        capture_output=True, text=True,
        env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'},
    )
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def archive_inventory(root):
    entries = {}
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries[rel] = {'type': 'symlink', 'target': os.readlink(path)}
        elif path.is_dir():
            entries[rel] = {'type': 'directory'}
        elif path.is_file():
            entries[rel] = {'type': 'file', 'bytes': path.read_bytes()}
        else:
            raise RuntimeError(f'unsupported filesystem member: {path}')
    return entries


def archive_and_verify(root, archive):
    before = archive_inventory(root)
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(root, arcname=root.name)
    with tarfile.open(archive, 'r:gz') as tar:
        members = {m.name: m for m in tar.getmembers()}
        root_name = root.name
        assert root_name in members and members[root_name].isdir()
        expected_names = {f'{root_name}/{key}' for key in before}
        assert set(members) == expected_names | {root_name}, (set(members), expected_names)
        for rel, expected in before.items():
            member = members[f'{root_name}/{rel}']
            path = root / rel
            if expected['type'] == 'directory':
                assert member.isdir() and path.is_dir() and not path.is_symlink()
            elif expected['type'] == 'symlink':
                assert member.issym() and path.is_symlink() and member.linkname == expected['target'] == os.readlink(path)
            else:
                assert member.isfile() and path.is_file() and not path.is_symlink()
                extracted = tar.extractfile(member)
                assert extracted is not None and extracted.read() == expected['bytes'] == path.read_bytes()
    return {
        'members': len(before),
        'regular_files': sum(v['type'] == 'file' for v in before.values()),
        'directories': sum(v['type'] == 'directory' for v in before.values()),
        'symlinks': sum(v['type'] == 'symlink' for v in before.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    out = BASE / ('09b-stage-a-03-cleanup-dry-run' if args.dry_run else '09b-stage-a-03-cleanup')
    out.mkdir(exist_ok=False)
    record = {
        'status': 'BLOCKED', 'dry_run': args.dry_run, 'root': str(ROOT),
        'approval_ref': args.approval_ref, 'signals_sent': [],
        'slots_removed': [], 'root_removed': False,
        'scope': 'Only #195 failed Stage-A root; no other root/slot',
    }

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def fail(message):
        raise RuntimeError(message)

    def gate_stop():
        assert NODE, 'node executable unavailable'
        env = {**os.environ, 'A2A_OPERATOR_CREDENTIAL': str(ROOT / 'operator.json'), 'LC_ALL': 'C', 'LANG': 'C'}
        result = subprocess.run(
            [NODE, str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', str(STATE), 'daemon_stop'],
            cwd=SOURCE, env=env, capture_output=True, text=True, timeout=30,
        )
        record['daemon_stop'] = {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        save()
        assert result.returncode == 0

    save()
    try:
        assert args.approval_ref.strip() and ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        scene = json.loads((BASE / '09b-stage-a-03/result.json').read_bytes())
        assert scene['status'] == 'INCOMPLETE' and scene['spawned'] is True
        assert scene.get('root') == str(ROOT) and scene.get('daemon', {}).get('pid') == DAEMON
        assert 'invalid_task_card' in scene.get('error', '') + json.dumps(scene)
        assert not scene.get('attempt') and not scene.get('target_process'), 'Failed scene unexpectedly claimed a target'
        ready = {}
        for pid, role, api_root in API:
            payload = json.loads((api_root / 'api-ready.json').read_bytes())
            assert payload['pid'] == pid and payload['role'] == role
            ready[pid] = payload
        api_id = {pid: ps(pid) for pid, _, _ in API}
        daemon_id = ps(DAEMON)
        record['before'] = {'apis': api_id, 'daemon': daemon_id, 'ready': ready}
        save()
        for pid, role, api_root in API:
            identity = api_id[pid]
            if identity is not None:
                command = shlex.split(identity['command'])
                expected = [str(sys.executable), '-B', str(SOURCE / 'workbench/tests/t078_09b_fake_api.py'),
                            '--root', str(api_root), '--role', role, '--port', '0']
                if command != expected and command[1:] != expected[1:]:
                    fail('API command/root mismatch: ' + str(pid))
        if daemon_id is not None:
            if str(SOURCE / 'workbench/src/daemon.ts') not in daemon_id['command'] or str(STATE) not in daemon_id['command']:
                fail('daemon command/root mismatch')
            if not (STATE / 'daemon.pid').exists() or int((STATE / 'daemon.pid').read_text()) != DAEMON:
                fail('daemon PID file mismatch')
            if ps(DAEMON) != daemon_id:
                fail('daemon lifetime changed; no shutdown')
        # Second read is the PID-reuse boundary. Each API PID is compared with
        # its own identity, never the previous role's identity.
        for pid, identity in [(pid, api_id[pid]) for pid, _, _ in API]:
            if identity is not None and ps(pid) != identity:
                fail('API lifetime changed; no signal: ' + str(pid))
        record['identity_checks'] = 'PASS'
        record['planned_actions'] = [
            'authenticated daemon_stop for recorded daemon PID',
            'one SIGTERM at most for each recorded fake API PID',
            'archive root on external volume and verify every member',
            'delete root only after archive byte/type readback',
        ]
        if args.dry_run:
            record.update(status='PASS', action='dry-run only; no signal, daemon_stop, archive, or delete')
            save()
            print(json.dumps({'status': record['status'], 'dry_run': True, 'signals_sent': [], 'root_removed': False}))
            return 0
        if daemon_id is not None:
            gate_stop()
        deadline = time.monotonic() + 15
        while ps(DAEMON) is not None:
            if time.monotonic() > deadline:
                fail('daemon exit unconfirmed')
            time.sleep(.1)
        for pid, role, api_root in API:
            identity = api_id[pid]
            current = ps(pid)
            if current is not None:
                if current != identity:
                    fail('API lifetime changed; no signal: ' + str(pid))
                os.kill(pid, signal.SIGTERM)
                record['signals_sent'].append({'pid': pid, 'signal': 'SIGTERM'})
                save()
                deadline = time.monotonic() + 15
                while ps(pid) is not None:
                    if time.monotonic() > deadline:
                        fail('API exit unconfirmed: ' + str(pid))
                    time.sleep(.1)
        assert not (STATE / 'control.sock').exists() and not (STATE / 'daemon.pid').exists()
        if (ROOT / 'operator.json').exists():
            assert (ROOT / 'operator.json').is_file() and not (ROOT / 'operator.json').is_symlink()
            (ROOT / 'operator.json').unlink()
        volume = Path('/Volumes/WD-Elements')
        assert os.path.ismount(volume) and volume.resolve() == volume
        external = volume / 'a2a-evidence/2026-10-11-batch13/T-078/09b-stage-a-03-cleanup'
        external.parent.mkdir(parents=True, exist_ok=True)
        assert external.parent.resolve() == external.parent
        external.mkdir()
        archive = external / 'fixture.tar.gz'
        inventory = archive_and_verify(ROOT, archive)
        record.update(status='PASS', archive=str(archive), archive_bytes=archive.stat().st_size,
                      byte_readback='PASS', archive_inventory=inventory)
        save()
        for pid in [DAEMON, *(item[0] for item in API)]:
            assert ps(pid) is None
        assert ROOT.resolve() == ROOT
        shutil.rmtree(ROOT)
        assert not ROOT.exists()
        record['root_removed'] = True
        save()
    except Exception as error:
        record.update(status='BLOCKED', error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists())
        save()
    print(json.dumps({'status': record['status'], 'dry_run': record['dry_run'],
                      'signals_sent': record['signals_sent'], 'root_removed': record['root_removed'],
                      'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
