"""Owner-bound recovery after the #197 SIGTERM deadlock; SIGKILL only."""
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
ROOT = Path('/private/tmp/t078-2-09b-run-576xn98k')
STATE = ROOT / 'state'
API = [(62217, 'ideation', ROOT / 'roles/ideation'), (62218, 'executor', ROOT / 'roles/executor')]
DAEMON = 62220
OLD = BASE / '09b-stage-a-03-cleanup/result.json'
OLD_SAMPLE = BASE / '09b-stage-a-03-cleanup/sample-62217.txt'
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def ps(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    out = BASE / ('09b-stage-a-03-recovery-dry-run' if args.dry_run else '09b-stage-a-03-recovery')
    out.mkdir(exist_ok=False)
    record = {'status': 'BLOCKED', 'dry_run': args.dry_run, 'root': str(ROOT),
              'approval_ref': args.approval_ref, 'signals_sent': [], 'root_removed': False,
              'slots_removed': [], 'scope': 'Only #195 root after #197 SIGTERM deadlock; SIGKILL recovery'}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def fail(message):
        raise RuntimeError(message)

    save()
    try:
        assert args.approval_ref.strip() and ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        prior = json.loads(OLD.read_bytes())
        assert prior['status'] == 'BLOCKED' and prior['dry_run'] is False and prior['root_removed'] is False
        assert prior['signals_sent'] == [{'pid': 62217, 'signal': 'SIGTERM'}]
        assert 'API exit unconfirmed' in prior.get('error', '') and prior.get('daemon_stop', {}).get('exit_code') == 0
        assert OLD_SAMPLE.is_file(), 'Preserve the deadlock sample before recovery'
        scene = json.loads((BASE / '09b-stage-a-03/result.json').read_bytes())
        assert scene['status'] == 'INCOMPLETE' and scene.get('root') == str(ROOT)
        ready = {}
        for pid, role, api_root in API:
            payload = json.loads((api_root / 'api-ready.json').read_bytes())
            assert payload['pid'] == pid and payload['role'] == role
            ready[pid] = payload
        api_id = {pid: ps(pid) for pid, _, _ in API}
        daemon_id = ps(DAEMON)
        assert daemon_id is None, 'daemon must already be stopped by the prior cleanup'
        assert not (STATE / 'daemon.pid').exists() and not (STATE / 'control.sock').exists()
        record['before'] = {'apis': api_id, 'daemon': daemon_id, 'ready': ready}
        save()
        for pid, role, api_root in API:
            identity = api_id[pid]
            if identity is None:
                fail('recorded API is absent; cannot prove SIGKILL ownership: ' + str(pid))
            command = shlex.split(identity['command'])
            expected = [str(sys.executable), '-B', str(SOURCE / 'workbench/tests/t078_09b_fake_api.py'),
                        '--root', str(api_root), '--role', role, '--port', '0']
            if command != expected and command[1:] != expected[1:]:
                fail('API command/root mismatch: ' + str(pid))
        for pid, identity in [(pid, api_id[pid]) for pid, _, _ in API]:
            if ps(pid) != identity:
                fail('API lifetime changed; no signal: ' + str(pid))
        record['identity_checks'] = 'PASS'
        record['planned_actions'] = [
            'no daemon signal: prior authenticated daemon_stop is recorded and daemon is absent',
            'one SIGKILL for each recorded API PID',
            'archive root on external volume and verify every member',
            'delete root only after archive byte/type readback',
        ]
        if args.dry_run:
            record.update(status='PASS', action='dry-run only; no SIGKILL, archive, or delete')
            save()
            print(json.dumps({'status': record['status'], 'dry_run': True, 'signals_sent': [], 'root_removed': False}))
            return 0
        for pid, identity in [(pid, api_id[pid]) for pid, _, _ in API]:
            if ps(pid) != identity:
                fail('API lifetime changed; no signal: ' + str(pid))
            os.kill(pid, signal.SIGKILL)
            record['signals_sent'].append({'pid': pid, 'signal': 'SIGKILL'})
            save()
            deadline = time.monotonic() + 15
            while ps(pid) is not None:
                if time.monotonic() > deadline:
                    fail('API SIGKILL exit unconfirmed: ' + str(pid))
                time.sleep(.1)
        assert ps(DAEMON) is None and not (STATE / 'daemon.pid').exists() and not (STATE / 'control.sock').exists()
        if (ROOT / 'operator.json').exists():
            assert (ROOT / 'operator.json').is_file() and not (ROOT / 'operator.json').is_symlink()
            (ROOT / 'operator.json').unlink()
        volume = Path('/Volumes/WD-Elements')
        assert os.path.ismount(volume) and volume.resolve() == volume
        external = volume / 'a2a-evidence/2026-10-11-batch13/T-078/09b-stage-a-03-recovery'
        external.parent.mkdir(parents=True, exist_ok=True)
        assert external.parent.resolve() == external.parent
        external.mkdir()
        spec = importlib.util.spec_from_file_location('stage_a_cleanup_archive', BASE / 'cleanup-09b-stage-a-03.py')
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        archive = external / 'fixture.tar.gz'
        inventory = helper.archive_and_verify(ROOT, archive)
        record.update(status='PASS', archive=str(archive), archive_bytes=archive.stat().st_size,
                      byte_readback='PASS', archive_inventory=inventory)
        save()
        for pid, _, _ in API:
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
