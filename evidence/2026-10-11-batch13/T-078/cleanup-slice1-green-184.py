"""Stop and archive only the fixed #184 fixture; never launch or remove slots."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
MATERIALS = BASE / 'p1-materials-slice1-green'
ROOT = Path('/private/tmp/t078-2-p1-slice1-green-1yhrmwad')
LAUNCH = '284a5916-fd75-4c4d-bec0-9a8d49e063d9'
SESSION = '10b07cc8-bdc6-47e4-a801-c4d63dd37bb4'
API_PID, DAEMON_PID, CLI_PID, SHELL_PID = 44036, 44048, 44069, 44068
API_ARGV = ['/usr/bin/python3', '-B', str(SOURCE / 'workbench/tests/t078_fake_inbox_tool.py'), str(ROOT)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--approval-ref', required=True)
    args = p.parse_args()
    if not args.approval_ref.strip():
        raise ValueError('An explicit cleanup approval reference is required.')
    out = MATERIALS / 'cleanup-184'; out.mkdir()
    sys.path.insert(0, str(SOURCE / 'workbench/tests'))
    from command_evidence import CommandLog
    from p1_processes import identity_from_ps
    log = CommandLog(out)
    env = json.loads((MATERIALS / 'control-plane.json').read_bytes())['environment']
    env.update(LC_ALL='C', LANG='C')
    node = json.loads((MATERIALS / 'approval.json').read_bytes())['launch']['node_executable']
    gate = [node, SOURCE / 'workbench/src/gates/cli.ts', '--state', ROOT / 'state']
    record = {'status': 'BLOCKED', 'scope': 'This fixture only; authenticated daemon_stop and at most one API SIGTERM',
              'root': str(ROOT), 'launch': LAUNCH, 'session': SESSION, 'approval_ref': args.approval_ref,
              'signals_sent': [], 'slots_removed': [], 'root_removed': False,
              'real_model_turns': 0}

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def probe(pid, full=False):
        value = log.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,' + ('command=' if full else 'comm=')],
                        cwd=SOURCE, env=env, timeout=10)
        return identity_from_ps(pid, value.returncode, value.stdout, value.stderr)

    def gate_call(command):
        value = log.run([*gate, command], cwd=SOURCE, env=env, timeout=30)
        if value.returncode:
            raise RuntimeError({'gate_exit': value.returncode, 'command': command})
        result = json.loads(value.stdout)
        if not result.get('ok'):
            raise RuntimeError(result)
        return result

    def exited(pid, identity):
        deadline = time.monotonic() + 15
        while True:
            current = probe(pid)
            if current is None:
                return
            if identity is None or current['started'] != identity['started']:
                raise RuntimeError('PID lifetime changed; no further action: ' + str(pid))
            if time.monotonic() >= deadline:
                raise RuntimeError('Exit unconfirmed; no forced signal: ' + str(pid))
            time.sleep(.1)

    save()
    try:
        assert ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT
        expected = json.loads((MATERIALS / 'input.json').read_bytes())
        assert expected == json.loads((ROOT / 'input.json').read_bytes())
        assert expected['root'] == str(ROOT) and expected['launch'] == LAUNCH and expected['session'] == SESSION
        assert json.loads((MATERIALS / 'permission/result.json').read_bytes())['status'] == 'INCOMPLETE'
        assert json.loads((ROOT / 'api-owner.json').read_bytes()) == {'pid': API_PID, 'argv': API_ARGV}
        ready = json.loads((ROOT / 'api-ready.json').read_bytes())
        assert ready['pid'] == API_PID and ready['launch'] == LAUNCH and ready['session'] == SESSION
        manifest = json.loads((MATERIALS / 'launch/process-manifest.json').read_bytes())
        assert manifest['launch'] == LAUNCH and manifest['session'] == SESSION
        assert manifest['cli']['pid'] == CLI_PID and manifest['shell_pid'] == SHELL_PID
        current_cli = probe(CLI_PID)
        if current_cli is not None:
            assert current_cli['started'] == manifest['cli']['started'], 'CLI PID reused; no shutdown'
        current_shell = probe(SHELL_PID)
        current_daemon = probe(DAEMON_PID, True)
        current_api = probe(API_PID, True)
        record['before'] = {'cli': current_cli, 'shell': current_shell, 'daemon': current_daemon, 'api': current_api}
        save()
        if current_api is not None:
            parts = shlex.split(current_api['command'])
            assert len(parts) == 4 and parts[1:] == API_ARGV[1:], 'API command/root mismatch; no signal'
        if current_daemon is not None:
            parts = shlex.split(current_daemon['command'])
            assert len(parts) == 4 and parts[1:] == [str(SOURCE / 'workbench/src/daemon.ts'), str(ROOT / 'state'), '{}'], 'Daemon command/root mismatch; no shutdown'
            assert int((ROOT / 'state/daemon.pid').read_text()) == DAEMON_PID
            status = gate_call('daemon_status')
            assert status['pid'] == DAEMON_PID and status['root'] == str(ROOT / 'state')
        else:
            assert not (ROOT / 'state/daemon.pid').exists() and not (ROOT / 'state/control.sock').exists(), 'Unknown stale daemon endpoint; preserve it'
        # Both owned service identities must remain unchanged before mutations.
        assert probe(API_PID, True) == current_api and probe(DAEMON_PID, True) == current_daemon, 'PID lifetime changed; no action'
        if current_daemon is not None:
            record['daemon_stop_intent'] = {'pid': DAEMON_PID, 'identity': current_daemon}; save()
            record['daemon_stop'] = gate_call('daemon_stop'); save()
        exited(DAEMON_PID, current_daemon)
        exited(CLI_PID, current_cli)
        exited(SHELL_PID, current_shell)
        assert not (ROOT / 'state/daemon.pid').exists() and not (ROOT / 'state/control.sock').exists()
        # No CLI/shell/helper or process-group signals; only this API PID.
        if current_api is not None:
            assert probe(API_PID, True) == current_api, 'API PID lifetime changed; no signal'
            record['api_sigterm_intent'] = {'pid': API_PID, 'identity': current_api}; save()
            os.kill(API_PID, signal.SIGTERM)
            record['signals_sent'].append({'pid': API_PID, 'signal': 'SIGTERM'}); save()
        exited(API_PID, current_api)
        record['owned_exits_confirmed'] = [API_PID, DAEMON_PID, CLI_PID, SHELL_PID]; save()
        if (ROOT / 'operator.json').exists():
            (ROOT / 'operator.json').unlink()
        volume = Path('/Volumes/WD-Elements')
        assert os.path.ismount(volume) and volume.resolve() == volume, 'External archive volume missing; no fallback'
        external = volume / 'a2a-evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green/cleanup-184'
        external.parent.mkdir(parents=True, exist_ok=True)
        assert external.parent.resolve() == external.parent
        external.mkdir()
        spec = importlib.util.spec_from_file_location('t078_verified_archive', BASE / 'cleanup-slot-after-reboot-09a2.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        archive = external / 'fixture.tar.gz'
        inventory = helper.archive_and_verify(ROOT, archive)
        record.update(archive=str(archive), archive_bytes=archive.stat().st_size, byte_readback='PASS',
                      inventory=inventory, original_api_error_preserved=(ROOT / 'api-error.json').exists())
        save()
        record.update(status='PASS', root_retained=ROOT.exists(), experiment_status='INCOMPLETE', budget_status='NO_GO')
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists())
    finally:
        save()
    print(json.dumps({k: record.get(k) for k in ['status', 'signals_sent', 'archive', 'byte_readback', 'root_removed', 'root_retained', 'error']}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
