"""Owner-bound Stage-A-04 cleanup after receiver launch red state."""
import argparse
import importlib.util
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-09b-run-s6slqnu3')
STATE = ROOT / 'state'
API = [(68081, 'ideation', ROOT / 'roles/ideation'), (68082, 'executor', ROOT / 'roles/executor')]
DAEMON = 68084
SHELL = 68179
THREAD = 'a7b98242-6045-4620-b9ea-e2e301b754ab'
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def ps(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def wait_absent(pid, timeout):
    deadline = time.monotonic() + timeout
    while ps(pid) is not None and time.monotonic() < deadline:
        time.sleep(.05)
    return ps(pid) is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    out = BASE / ('09b-stage-a-04-cleanup-dry-run' if args.dry_run else '09b-stage-a-04-cleanup')
    out.mkdir(exist_ok=False)
    record = {'status': 'BLOCKED', 'dry_run': args.dry_run, 'root': str(ROOT), 'approval_ref': args.approval_ref,
              'signals_sent': [], 'root_removed': False, 'slots_removed': [],
              'scope': 'Only #200/#201 Stage-A-04 root; daemon_stop plus owned fake API SIGTERM; no slots'}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def fail(message):
        raise RuntimeError(message)

    def daemon_stop():
        node = shutil.which('node'); assert node, 'node executable unavailable'
        env = {**os.environ, 'A2A_OPERATOR_CREDENTIAL': str(ROOT / 'operator.json'), 'LC_ALL': 'C', 'LANG': 'C'}
        result = subprocess.run([node, str(SOURCE / 'workbench/src/gates/cli.ts'), '--state', str(STATE), 'daemon_stop'],
                                cwd=SOURCE, env=env, capture_output=True, text=True, timeout=30)
        record['daemon_stop'] = {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        save(); assert result.returncode == 0

    save()
    try:
        assert args.approval_ref.strip() and ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        scene = json.loads((BASE / '09b-stage-a-04/result.json').read_bytes())
        assert scene['status'] == 'INCOMPLETE' and scene['spawned'] is True and scene.get('root') == str(ROOT)
        assert 'AssertionError' in scene.get('error', '') and scene.get('attempt', {}).get('thread_id') == THREAD
        ready = {}
        for pid, role, api_root in API:
            payload = json.loads((api_root / 'api-ready.json').read_bytes())
            assert payload['pid'] == pid and payload['role'] == role
            ready[pid] = payload
        api_id = {pid: ps(pid) for pid, _, _ in API}
        daemon_id, shell_id = ps(DAEMON), ps(SHELL)
        record['before'] = {'apis': api_id, 'daemon': daemon_id, 'shell': shell_id, 'ready': ready}
        save()
        for pid, role, api_root in API:
            identity = api_id[pid]
            if identity is not None:
                command = shlex.split(identity['command'])
                expected = [str(sys.executable), '-B', str(SOURCE / 'workbench/tests/t078_09b_fake_api.py'),
                            '--root', str(api_root), '--role', role, '--port', '0']
                if command != expected and command[1:] != expected[1:]:
                    fail('API command/root mismatch: ' + str(pid))
        assert daemon_id is not None and str(SOURCE / 'workbench/src/daemon.ts') in daemon_id['command'] and str(STATE) in daemon_id['command']
        assert (STATE / 'daemon.pid').exists() and int((STATE / 'daemon.pid').read_text()) == DAEMON
        assert shell_id is not None and '/bin/zsh' in shell_id['command']
        for pid, identity in [(pid, api_id[pid]) for pid, _, _ in API]:
            if identity is not None and ps(pid) != identity:
                fail('API lifetime changed; no signal: ' + str(pid))
        if ps(DAEMON) != daemon_id or ps(SHELL) != shell_id:
            fail('daemon or shell lifetime changed; no shutdown')
        record['identity_checks'] = 'PASS'
        record['planned_actions'] = [
            'authenticated daemon_stop for recorded daemon PID',
            'confirm daemon and pane shell exit without direct shell signal',
            'one SIGTERM for each recorded fake API PID; require exit within 2 seconds',
            'archive root externally and verify every member before delete',
        ]
        if args.dry_run:
            record.update(status='PASS', action='dry-run only; no signal, daemon_stop, archive, or delete')
            save(); print(json.dumps({'status': record['status'], 'dry_run': True, 'signals_sent': [], 'root_removed': False})); return 0
        daemon_stop()
        assert wait_absent(DAEMON, 15), 'daemon exit unconfirmed'
        assert wait_absent(SHELL, 15), 'pane shell exit unconfirmed'
        assert not (STATE / 'daemon.pid').exists() and not (STATE / 'control.sock').exists()
        for pid, _, _ in API:
            identity = api_id[pid]
            if ps(pid) != identity:
                fail('API lifetime changed; no signal: ' + str(pid))
            started = time.monotonic(); os.kill(pid, signal.SIGTERM)
            record['signals_sent'].append({'pid': pid, 'signal': 'SIGTERM'})
            save()
            if not wait_absent(pid, 2.0):
                fail('API SIGTERM exit exceeded 2 seconds: ' + str(pid))
            record.setdefault('api_exit_seconds', {})[str(pid)] = round(time.monotonic() - started, 3); save()
        if (ROOT / 'operator.json').exists():
            assert (ROOT / 'operator.json').is_file() and not (ROOT / 'operator.json').is_symlink(); (ROOT / 'operator.json').unlink()
        volume = Path('/Volumes/WD-Elements'); assert os.path.ismount(volume) and volume.resolve() == volume
        external = volume / 'a2a-evidence/2026-10-11-batch13/T-078/09b-stage-a-04-cleanup'; external.parent.mkdir(parents=True, exist_ok=True); assert external.parent.resolve() == external.parent; external.mkdir()
        spec = importlib.util.spec_from_file_location('stage_a_archive', BASE / 'cleanup-09b-stage-a-03.py'); helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        archive = external / 'fixture.tar.gz'; inventory = helper.archive_and_verify(ROOT, archive)
        record.update(status='PASS', archive=str(archive), archive_bytes=archive.stat().st_size, byte_readback='PASS', archive_inventory=inventory); save()
        assert all(ps(pid) is None for pid in [DAEMON, SHELL, *(item[0] for item in API)])
        shutil.rmtree(ROOT); assert not ROOT.exists(); record['root_removed'] = True; save()
    except Exception as error:
        record.update(status='BLOCKED', error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists()); save()
    print(json.dumps({'status': record['status'], 'dry_run': record['dry_run'], 'signals_sent': record['signals_sent'], 'root_removed': record['root_removed'], 'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
