"""Owner-bound cleanup for the retained A-09 Stage-A/B1现场."""
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
ROOT = STATE = None
API = []
DAEMON = TARGET_SHELL = TARGET_LEADER = CLAUDE_SHELL = CLAUDE_CLI = None
STAGE_A = P1_MANIFEST = P1_RESULT = None
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_processes import identity_from_ps


def ps(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
    return identity_from_ps(pid, result.returncode, result.stdout, result.stderr)


def wait_absent(pid, timeout=15):
    deadline = time.monotonic() + timeout
    while ps(pid) is not None and time.monotonic() < deadline:
        time.sleep(.1)
    return ps(pid) is None


def command_args(identity):
    if identity is None:
        return []
    return shlex.split(identity['command'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--stage-a', type=Path, required=True)
    parser.add_argument('--p1-manifest', type=Path, required=True)
    for name in ['api-ideation-pid','api-executor-pid','daemon-pid','target-shell-pid','target-leader-pid','claude-shell-pid','claude-cli-pid']:
        parser.add_argument('--'+name, type=int, required=True)
    parser.add_argument('--label', default='09b-a09-cleanup-01')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    global ROOT,STATE,API,DAEMON,TARGET_SHELL,TARGET_LEADER,CLAUDE_SHELL,CLAUDE_CLI,STAGE_A,P1_MANIFEST,P1_RESULT
    ROOT=args.root.resolve(); STATE=ROOT/'state'; API=[(args.api_ideation_pid,'ideation',ROOT/'roles/ideation'),(args.api_executor_pid,'executor',ROOT/'roles/executor')]
    DAEMON=args.daemon_pid;TARGET_SHELL=args.target_shell_pid;TARGET_LEADER=args.target_leader_pid;CLAUDE_SHELL=args.claude_shell_pid;CLAUDE_CLI=args.claude_cli_pid
    STAGE_A=args.stage_a.resolve();P1_MANIFEST=args.p1_manifest.resolve();P1_RESULT=P1_MANIFEST.parent/'result.json'
    out = BASE / (args.label + ('-dry-run' if args.dry_run else ''))
    out.mkdir(exist_ok=False)
    record = {'status': 'BLOCKED', 'dry_run': args.dry_run, 'root': str(ROOT),
              'approval_ref': args.approval_ref, 'signals_sent': [], 'root_removed': False,
              'slots_removed': [], 'scope': 'A-09 owner-bound root only; daemon_stop closes Claude/target; APIs SIGTERM once'}

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
        readiness = json.loads((STAGE_A / 'readiness.json').read_bytes())
        stage_result = json.loads((STAGE_A / 'result.json').read_bytes())
        assert readiness['status'] == 'READY_FOR_APPROVAL' and stage_result['status'] == 'READY_FOR_APPROVAL'
        assert readiness['root'] == str(ROOT) and readiness['target_process']['shell_pid'] == TARGET_SHELL
        assert readiness['target_process']['leader'] == TARGET_LEADER and readiness['daemon']['pid'] == DAEMON
        assert P1_MANIFEST.is_file() and P1_RESULT.is_file()
        p1 = json.loads(P1_MANIFEST.read_bytes()); p1_result = json.loads(P1_RESULT.read_bytes())
        assert p1['shell_pid'] == CLAUDE_SHELL and p1['cli']['pid'] == CLAUDE_CLI
        assert p1_result['input']['root'] == str(ROOT) and p1_result['input']['launch'] == p1['launch']

        ready = {}
        for pid, role, api_root in API:
            payload = json.loads((api_root / 'api-ready.json').read_bytes())
            assert payload['pid'] == pid and payload['role'] == role and payload['stage'] == 'A'
            ready[pid] = payload
        identities = {pid: ps(pid) for pid in [DAEMON, TARGET_SHELL, TARGET_LEADER, CLAUDE_SHELL, CLAUDE_CLI]}
        identities.update({pid: ps(pid) for pid, _, _ in API})
        record['before'] = {'identities': identities, 'ready': ready, 'p1_manifest': p1}
        save()

        for pid, role, api_root in API:
            identity = identities[pid]
            if identity is None: fail('API owner absent: ' + str(pid))
            argsv = command_args(identity)
            expected_root = str(api_root)
            if str(SOURCE / 'workbench/tests/t078_09b_fake_api.py') not in argsv or '--root' not in argsv or expected_root != argsv[argsv.index('--root') + 1] or '--role' not in argsv or role != argsv[argsv.index('--role') + 1]:
                fail('API command/root/role mismatch: ' + str(pid))
            if '--protocol' not in argsv: fail('A-06 API protocol argv missing: ' + str(pid))
        daemon_id = identities[DAEMON]
        assert daemon_id is not None and str(SOURCE / 'workbench/src/daemon.ts') in daemon_id['command'] and str(STATE) in daemon_id['command']
        assert (STATE / 'daemon.pid').exists() and int((STATE / 'daemon.pid').read_text()) == DAEMON
        shell_id, leader_id = identities[TARGET_SHELL], identities[TARGET_LEADER]
        assert shell_id is not None and '/bin/zsh' in shell_id['command']
        assert leader_id is not None and str(ROOT / 'target/bin/codex-receiver') in leader_id['command']
        cli_id = identities[CLAUDE_CLI]; claude_shell_id = identities[CLAUDE_SHELL]
        assert cli_id is not None and str(p1['cli']['command']) in cli_id['command']
        assert p1['session'] in cli_id['command'] and str(ROOT) in cli_id['command']
        assert claude_shell_id is not None and '/bin/zsh' in claude_shell_id['command'] and str(ROOT) in claude_shell_id['command']
        before_ids = {pid: value for pid, value in identities.items()}
        for pid, identity in before_ids.items():
            if ps(pid) != identity: fail('owner lstart/argv changed before action: ' + str(pid))
        record['identity_checks'] = 'PASS'
        record['planned_actions'] = [
            'authenticated daemon_stop; panes.shutdown closes Claude and target normally',
            'confirm daemon, target shell/leader, and Claude shell/CLI exit without direct Claude signal',
            'one SIGTERM for each recorded protocol API PID after daemon shutdown',
            'archive root externally; verify every member bytes/types/links; delete root only after readback',
        ]
        if args.dry_run:
            record.update(status='PASS', action='dry-run only; no signal, daemon_stop, archive, or delete')
            save(); print(json.dumps({'status': 'PASS', 'dry_run': True, 'signals_sent': [], 'root_removed': False})); return 0

        daemon_stop()
        for pid in [DAEMON, TARGET_SHELL, TARGET_LEADER, CLAUDE_SHELL, CLAUDE_CLI]:
            if not wait_absent(pid, 20): fail('daemon_stop did not close owned process: ' + str(pid))
        assert not (STATE / 'daemon.pid').exists() and not (STATE / 'control.sock').exists()
        for pid, _, _ in API:
            identity = before_ids[pid]
            if ps(pid) != identity: fail('API lifetime changed; no signal: ' + str(pid))
            started = time.monotonic(); os.kill(pid, signal.SIGTERM)
            record['signals_sent'].append({'pid': pid, 'signal': 'SIGTERM'}); save()
            if not wait_absent(pid, 3): fail('API SIGTERM exit exceeded 3 seconds: ' + str(pid))
            record.setdefault('api_exit_seconds', {})[str(pid)] = round(time.monotonic() - started, 3); save()
        if (ROOT / 'operator.json').exists():
            assert (ROOT / 'operator.json').is_file() and not (ROOT / 'operator.json').is_symlink(); (ROOT / 'operator.json').unlink()
        volume = Path('/Volumes/WD-Elements'); assert os.path.ismount(volume) and volume.resolve() == volume
        external = volume / 'a2a-evidence/2026-10-11-batch13/T-078/09b-a09-cleanup'; external.parent.mkdir(parents=True, exist_ok=True); assert external.parent.resolve() == external.parent; external.mkdir()
        spec = importlib.util.spec_from_file_location('a06_archive', BASE / 'cleanup-09b-stage-a-03.py'); helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        archive = external / 'fixture.tar.gz'; inventory = helper.archive_and_verify(ROOT, archive)
        record.update(status='PASS', archive=str(archive), archive_bytes=archive.stat().st_size, byte_readback='PASS', archive_inventory=inventory); save()
        assert all(ps(pid) is None for pid in [DAEMON, TARGET_SHELL, TARGET_LEADER, CLAUDE_SHELL, CLAUDE_CLI, *(item[0] for item in API)])
        shutil.rmtree(ROOT); assert not ROOT.exists(); record['root_removed'] = True; save()
    except Exception as error:
        record.update(status='BLOCKED', error=repr(error), traceback=traceback.format_exc(), root_retained=ROOT.exists()); save()
    print(json.dumps({'status': record['status'], 'dry_run': record['dry_run'], 'signals_sent': record['signals_sent'], 'root_removed': record['root_removed'], 'error': record.get('error')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
