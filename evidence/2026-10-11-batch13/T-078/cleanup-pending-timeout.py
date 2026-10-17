"""Archive the exited local-02 spy harness scratch; never signal a process."""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = Path('/private/tmp/t078-2-a13-rehearsal-Sqkx7Q')


def remove_residual_socket(root, result):
    path = root / 'state/control.sock'
    if not path.exists() and not path.is_symlink():
        result['residual_socket'] = {'path': str(path), 'type': 'absent', 'removed': False}
        return
    before = path.lstat()
    observation = {'path': str(path), 'type': 'socket' if stat.S_ISSOCK(before.st_mode) else 'other',
                   'device': before.st_dev, 'inode': before.st_ino, 'held_by_process': None,
                   'holder_checks': [], 'removed': False}
    result['residual_socket'] = observation
    assert stat.S_ISSOCK(before.st_mode), ('unexpected_control_path_type', str(path))
    # Only this known residual Unix socket is removable. The archive helper
    # keeps rejecting every other special filesystem type.
    for _ in range(2):
        argv = ['/usr/sbin/lsof', '-nP', '-t', '--', str(path)]
        probe = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        observation['holder_checks'].append({'argv': argv, 'exit_code': probe.returncode,
                                              'stdout': probe.stdout, 'stderr': probe.stderr})
        assert probe.returncode in (0, 1) and not probe.stderr.strip(), 'socket_holders_unverified'
        lines = [line for line in probe.stdout.splitlines() if line]
        assert all(line.isdigit() for line in lines), 'socket_holder_output_invalid'
        observation['held_by_process'] = bool(lines)
        assert probe.returncode == 1 and not lines, 'socket_still_held_no_unlink'
    current = path.lstat()
    assert stat.S_ISSOCK(current.st_mode) and (current.st_dev, current.st_ino) == (before.st_dev, before.st_ino), 'socket_identity_changed'
    path.unlink()
    observation['removed'] = True


def main():
    out = BASE / '09b-pending-timeout-cleanup-02'
    assert not out.exists()
    out.mkdir()
    result = {'status': 'BLOCKED', 'root': str(ROOT), 'signals_sent': [], 'root_removed': False}
    try:
        assert ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        assert int((ROOT / 'state/daemon.pid').read_text(encoding='utf-8')) == 52458
        observations = []
        for pid in [52458, 52972]:
            response = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                                      env={**os.environ, 'LC_ALL': 'C'}, capture_output=True, text=True, timeout=5)
            observations.append({'pid': pid, 'exit_code': response.returncode,
                                 'stdout': response.stdout, 'stderr': response.stderr})
            assert response.returncode == 1 and not response.stdout.strip() and not response.stderr.strip(), ('process_not_confirmed_absent', pid)
        result['process_observations'] = observations
        remove_residual_socket(ROOT, result)
        credential = ROOT / 'operator.json'
        result['credential_already_absent'] = not credential.exists() and not credential.is_symlink()
        if credential.exists() or credential.is_symlink():
            assert credential.is_file() and not credential.is_symlink()
            credential.unlink()
        spec = importlib.util.spec_from_file_location('archive_helper', BASE / 'cleanup-09b-stage-a-03.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        archive = out / 'fixture.tar.gz'
        inventory = helper.archive_and_verify(ROOT, archive)
        result.update(archive=str(archive), inventory=inventory, byte_readback='PASS')
        shutil.rmtree(ROOT)
        result.update(status='PASS', root_removed=not ROOT.exists())
    except Exception as error:
        result['error'] = repr(error)
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
