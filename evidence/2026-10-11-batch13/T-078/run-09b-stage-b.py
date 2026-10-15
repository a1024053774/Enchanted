"""Stage-B approval gate and screen-step planner; launch is explicit and single-role."""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
NOTICE = (BASE / 'p1-materials-09/security-notice-text.txt').read_text(encoding='utf-8')


def probe(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
    if result.returncode == 1 and not result.stdout.strip():
        return None
    if result.returncode != 0 or result.stderr.strip():
        raise RuntimeError('process_readback_failed')
    parts = result.stdout.strip().split(maxsplit=6)
    if len(parts) != 7 or int(parts[0]) != pid:
        raise RuntimeError('process_identity_mismatch')
    return {'pid': pid, 'lstart': ' '.join(parts[1:6]), 'command': parts[6]}


def read_stage_a_binding(stage_a_dir, process_probe=probe):
    stage_a_dir = Path(stage_a_dir).resolve()
    readiness = json.loads((stage_a_dir / 'readiness.json').read_bytes())
    result = json.loads((stage_a_dir / 'result.json').read_bytes())
    assert readiness['status'] == 'READY_FOR_APPROVAL' and result['status'] == 'READY_FOR_APPROVAL'
    assert readiness['stage'] == 'A' and result['stage'] == 'A' and readiness['root'] == result['root']
    attempt = readiness['target_binding']
    required = ['attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace']
    assert all(attempt.get(k) not in [None, ''] for k in required)
    assert result['attempt'] == attempt
    root = Path(readiness['root']).resolve(); assert root.is_dir() and root == Path(readiness['root'])
    process = readiness['target_process']; assert process['leader']
    pids = {'shell': process['shell_pid'], 'leader': process['leader']}
    for item in readiness['api_processes']:
        pids[item['role'] + '_api'] = item['pid']
    pids['daemon'] = readiness['daemon']['pid']
    identities = {name: process_probe(pid) for name, pid in pids.items()}
    assert all(value is not None for value in identities.values())
    assert identities['shell']['pid'] == process['shell_pid'] and '/bin/zsh' in identities['shell']['command']
    assert identities['leader']['pid'] == process['leader']
    assert identities['daemon']['pid'] == readiness['daemon']['pid']
    return {'root': str(root), 'task': readiness['task'], 'source_revision': readiness['source_revision'],
            'attempt': attempt, 'pids': pids, 'identities': identities, 'readiness': readiness}

def static_process_probe(readiness):
    mapping={}
    for item in readiness['api_processes']: mapping[item['pid']]={'pid':item['pid'],'lstart':'readiness-static','command':' '.join(item['argv'])}
    process=readiness['target_process'];mapping[process['shell_pid']]={'pid':process['shell_pid'],'lstart':'readiness-static','command':'/bin/zsh'};mapping[process['leader']]={'pid':process['leader'],'lstart':'readiness-static','command':process['processes'][-1]['command']}
    mapping[readiness['daemon']['pid']]={'pid':readiness['daemon']['pid'],'lstart':'readiness-static','command':'daemon:'+str(readiness['daemon']['root'])}
    return lambda pid: mapping[pid]


def expected_screen_plan():
    return [
        {'purpose': 'onboarding-theme', 'key': 'ArrowUp', 'selected_label': 'Auto (match terminal)'},
        {'purpose': 'onboarding-theme', 'key': 'ArrowDown', 'selected_label': 'Dark mode'},
        {'purpose': 'onboarding-theme', 'key': 'Enter', 'selected_label': 'Dark mode'},
        {'purpose': 'security-notice', 'key': 'Enter', 'selected_label': 'Continue', 'screen_text': NOTICE},
        {'purpose': 'workspace-trust', 'key': 'ArrowDown', 'selected_label': 'Yes, I trust this folder'},
        {'purpose': 'workspace-trust', 'key': 'Enter', 'selected_label': 'Yes, I trust this folder'},
    ]


def validate_role_approval(approval, binding, materials, role, phase):
    static = json.loads((Path(materials) / 'static-check.json').read_bytes())
    assert approval.get('approved_by') == 'executor' and approval.get('stage') == 'B'
    assert approval.get('approval_ref') and approval.get('allow_role_cli_spawn') is True
    assert approval.get('source_revision') == static['revision'] == binding['source_revision']
    assert approval.get('role') == role and approval.get('phase') == phase
    # The signed draft carries the immutable readiness attempt object. The
    # runner adds live PID/lstart identities after this exact object matches;
    # accepting any other binding would permit a stale stage-A handoff.
    assert approval.get('binding') == binding['attempt'] or approval.get('binding') == binding
    assert approval.get('screen_approvals') == expected_screen_plan()
    tool = approval.get('tool_approval')
    assert tool == {'key': 'Enter', 'purpose': 'one-time-tool-approval', 'selected_label': '1. Yes', 'one_time': True}
    assert approval.get('stop_after') == 'first-screen'
    p1_materials = approval.get('p1_materials')
    assert isinstance(p1_materials, str) and Path(p1_materials).is_dir()
    p1_input = json.loads((Path(p1_materials) / 'input.json').read_bytes())
    assert p1_input.get('root') == binding['root'] and p1_input.get('preset') == role and p1_input.get('task') == binding['task']
    assert approval.get('p1_phase') in ('launch', 'screen', 'key')
    if phase == 'B1':
        args = approval.get('p1_args', [])
        assert '--reuse-stage-a' in args and '--reuse-api-root' in args
        root_index = args.index('--reuse-api-root') + 1
        assert root_index < len(args) and Path(args[root_index]).resolve() == Path(binding['root']) / 'roles' / role, (args, binding['root'], role)
    return True


class RoleGate:
    """Pure sequence gate; no process start or pane write."""
    def __init__(self):
        self.active = None
        self.completed = []

    def admit(self, role):
        assert role in ('ideation', 'executor')
        assert self.active is None, 'second role cannot start while another role is active'
        assert role == ('executor' if self.completed else 'ideation'), 'roles must start ideation then executor'
        self.active = role

    def finish(self, role):
        assert self.active == role
        self.completed.append(role); self.active = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--materials', type=Path, required=True)
    parser.add_argument('--stage-a', type=Path, required=True)
    parser.add_argument('--role', choices=['ideation', 'executor'], required=True)
    parser.add_argument('--phase', choices=['B1', 'I1', 'I2', 'E1'], required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=False, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'stage': 'B', 'role': args.role, 'phase': args.phase,
              'spawned': False, 'p1_spawned': False, 'cli_spawned': False,
              'scope': 'Stage-B single-role approval planner; no CLI spawn in dry-run'}
    (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    try:
        readiness_for_probe=json.loads((args.stage_a/'readiness.json').read_bytes())
        binding = read_stage_a_binding(args.stage_a, static_process_probe(readiness_for_probe) if args.dry_run else probe)
        approval = json.loads(args.approval.read_bytes())
        validate_role_approval(approval, binding, args.materials, args.role, args.phase)
        record.update(status='READY_FOR_ROLE', binding=binding, approval_ref=approval['approval_ref'],
                      next='Stop before CLI spawn; run one separately approved screen action')
        if not args.dry_run:
            p1_args = approval.get('p1_args', [])
            assert isinstance(p1_args, list) and all(isinstance(item, str) for item in p1_args)
            command = [sys.executable, str(SOURCE / 'workbench/tests/run_t078_p1.py'), '--materials', approval['p1_materials'], '--phase', approval['p1_phase'], '--label', args.output.name, *p1_args]
            completed = subprocess.run(command, cwd=SOURCE, capture_output=True, text=True)
            record['command'] = command; record['p1_spawned'] = True
            record['p1_exit_code'] = completed.returncode; record['p1_stdout'] = completed.stdout; record['p1_stderr'] = completed.stderr
            p1_result_path = Path(approval['p1_materials']) / args.output.name / 'result.json'
            p1_result = json.loads(p1_result_path.read_bytes()) if p1_result_path.exists() else {}
            record['cli_spawned'] = bool(p1_result.get('process_manifest') or p1_result.get('started'))
            record['spawned'] = record['cli_spawned']
            record['p1_result'] = str(p1_result_path)
            record['status'] = 'PASS' if completed.returncode == 0 else 'INCOMPLETE'
            record['next'] = 'Stop after this single approved P1 action; inspect screen/result before another approval.'
        (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return 0 if record['status'] in ('READY_FOR_ROLE', 'PASS') else 1
    except Exception as error:
        import traceback
        record.update(error=repr(error), traceback=traceback.format_exc()); (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); return 1


if __name__ == '__main__':
    raise SystemExit(main())
