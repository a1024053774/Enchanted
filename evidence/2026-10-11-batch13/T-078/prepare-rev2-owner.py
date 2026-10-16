"""Bind actual Stage A/B1 receipts for raw retention; never start or signal."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_reuse import process_command
from t078_raw_retention import save, read_json, NativeRuntime, check_identities


def owner(args):
    ready = read_json(args.stage_a / 'readiness.json'); static = read_json(args.packet / 'static-check.json')
    assert ready['status'] == 'READY_FOR_APPROVAL' and ready['source_revision'] == static['revision']
    root = Path(ready['root']); claim = ready['target_binding']; scene = 'A16' if static['scene'] == '09B' else '09C'
    p1s = {'ideation': args.ideation.resolve(), 'executor': args.executor.resolve()}
    processes = dict(ready['original_processes']); roles = {}
    for role, p1 in p1s.items():
        inp = read_json(p1 / 'input.json'); binding = read_json(p1 / 'launch-binding.json')
        manifest = Path(binding['process_manifest']); actual = read_json(manifest)
        assert inp['root'] == str(root) and inp['task'] == ready['task'] and inp['code_revision'] == static['revision']
        assert actual['launch'] == inp['launch'] and actual['session'] == inp['session']
        processes[role + '_shell'] = process_command(actual['shell_pid'])
        processes[role + '_cli'] = process_command(actual['cli']['pid'])
        assert processes[role + '_cli']['started'] == actual['cli']['started']
        roles[role] = {'launch': inp['launch'], 'session': inp['session'], 'native_session': inp['session'], 'manifest': str(manifest)}
    for key, identity in processes.items():
        assert identity is not None and process_command(identity['pid']) == identity, ('original process changed', key)
    graph_result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,tpgid='], capture_output=True, text=True, check=True)
    assert not graph_result.stderr.strip()
    graph = {}
    for line in graph_result.stdout.splitlines():
        pid, ppid, pgid, tpgid = map(int, line.split()); graph[pid] = {'ppid': ppid, 'pgid': pgid, 'tpgid': tpgid}
    target = {key: claim[key] for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace')}
    target['launch'] = claim['runtime_identity']['launch']
    reference = args.output.parent / (args.output.stem + '-identity.json')
    save(reference, {'root': str(root), 'processes': processes, 'source': 'Stage A original lifetimes plus actual B1 manifests; readonly ps double-read'})
    trees = [str(args.stage_a.resolve())]
    for p1 in p1s.values():
        trees += [str(path) for path in sorted(p1.iterdir()) if path.is_dir() and not path.is_symlink()]
    value = {'scene': scene, 'root': str(root), 'source': str(SOURCE), 'source_revision': static['revision'],
             'stage_a': str(args.stage_a.resolve()), 'claim_binding': claim, 'target_binding': target,
             'roles': roles, 'processes': processes, 'process_graph': {key: graph[item['pid']] for key, item in processes.items()},
             'identity_receipt': str(reference.resolve()), 'target_bytes': 'target/home/received.bin',
             'target_baseline': 'target-baseline.bin', 'evidence_trees': trees}
    check_identities(value, NativeRuntime(value))
    # Only fixture-owned bootstrap values. No user HOME/authentication reads,
    # and no secret value is printed, copied to an evidence directory or tar.
    credential = read_json(root / 'operator.json')
    secret_file = root / 'retention-secrets.json'
    with secret_file.open('x', encoding='utf-8') as stream:
        os.chmod(secret_file, 0o600)
        json.dump([credential['token'], credential['epoch']], stream)
    save(args.output, value)
    if scene == '09C':
        plan_file = root / 'protocol-plan.json'; plan = read_json(plan_file)
        assert set(plan['roles']) == {'ideation', 'executor'}
        plan['owner_file'] = str(args.output.resolve())
        plan['target_identity'] = {**target, 'shell_pid': processes['target_shell']['pid'],
            'leader_pid': processes['target_leader']['pid'], 'native_session': claim['runtime_identity']['native_session'],
            'lstart': processes['target_leader']['started']}
        temporary = root / 'owner-bound-plan.tmp'; save(temporary, plan); temporary.replace(plan_file)
    print(json.dumps({'status': 'PASS', 'scene': scene, 'root': str(root), 'owner': str(args.output.resolve()),
                      'processes_verified': len(processes), 'business_actions': 0, 'secret_values_printed': False}))


def demand(args):
    result = read_json(args.result); approval = read_json(args.approval)
    assert result['stage'] == 'C-I1' and result['status'] == 'PASS'
    assert approval['approved_by'] == 'executor' and approval['approval_ref'] and approval['continued_stop_demand'] is True
    assert result['stop']['from'] == 'ideation' and result['no_ack'] is True
    save(args.output, {'stop_id': result['stop']['id'], 'still_required': True, 'source': 'test-simulated-user',
                      'action': 'continued original test stop demand', 'approval_ref': approval['approval_ref']})
    print(json.dumps({'status': 'PASS', 'business_actions': 0, 'output': str(args.output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['owner', 'demand'], required=True)
    for name in ['stage-a', 'packet', 'ideation', 'executor', 'result', 'approval', 'output']:
        parser.add_argument('--' + name, type=Path, required=name == 'output')
    args = parser.parse_args()
    if args.mode == 'owner': owner(args)
    else: demand(args)


if __name__ == '__main__': main()
