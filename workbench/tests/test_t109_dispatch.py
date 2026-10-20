"""真实 Python 命令入口；Herdr/Codex 用显式进程夹具，不连接用户服务或模型。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from launch_records import validate_launches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT)
    args = parser.parse_args()
    assert not args.summary.exists()
    # The reused setup creates its own Git repository. Clear inherited routing
    # before setup, rather than trying to repair a shared repository afterward.
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'):
        os.environ.pop(key, None)
    os.environ['LC_ALL'] = 'C'
    spec = importlib.util.spec_from_file_location('t094_fixture', ROOT / 'scripts/test_launch_worker_failure.py')
    fixture_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_module)
    fixture = fixture_module.LaunchFailure()
    fixture.setUp()
    report = dict(status='INCOMPLETE', model_calls=0, checks=[], commands=[], fixture=str(fixture.root))
    try:
        env = dict(fixture.env, T094_SCENARIO='success', A2A_LAUNCH='launch-sentinel-parent')
        command = [sys.executable, str(args.source / 'scripts/launch-worker'), '--root', str(fixture.root), '--cwd', str(fixture.root),
                   '--agent', 'fixture-worker', '--project', 'fixture', '--task', 'T-109', '--attempt', 'a1', '--session', 'fixture-session']
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
        report['commands'].append(dict(argv=command, exit=result.returncode))
        assert result.returncode == 0, result.stderr
        logfile = fixture.root / 'records/launches.jsonl'
        original = logfile.read_bytes()
        rows = [json.loads(line) for line in original.decode('utf-8').splitlines()]
        assert [row['phase'] for row in rows] == ['prepared', 'started']
        assert all(row.get('parent_launch') == 'launch-sentinel-parent' for row in rows), 'Launch command dropped parent launch'
        validate_launches(rows)
        changed = [dict(row) for row in rows]
        changed[-1]['parent_launch'] = 'launch-impostor'
        try:
            validate_launches(changed)
        except ValueError:
            pass
        else:
            raise AssertionError('Parent launch must be immutable across launch phases')
        # Dispatch uses the same existing endpoint, exactly once, preserving its
        # controller marker and role card; no parsing of prompt text for parent.
        fake = fixture.root / 'explicit-fake-bin/herdr'
        fake.write_text('#!' + sys.executable + '\nimport json, os, sys\nfrom pathlib import Path\n'
                        'with Path(os.environ["T094_CALLS"]).open("a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n', encoding='utf-8')
        for role in ('reviewer', 'monitor'):
            (fixture.root / '.project-map/roles' / (role + '.md')).write_text(role + ' fixture\n', encoding='utf-8')
        for index, role in enumerate(('worker', 'reviewer', 'monitor')):
            parent = 'launch-dispatch-' + str(index)
            command = [sys.executable, str(args.source / 'scripts/dispatch'), '--root', str(fixture.root), '--batch', 'T109',
                       '--agent', role, '--role', role, '--parent-launch', parent, '--body', 'sentinel question: launch-fake-parent']
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
            report['commands'].append(dict(argv=command, exit=result.returncode))
            assert result.returncode == 0, result.stderr
        dispatches = [json.loads(line) for line in (fixture.root / 'evidence/T109/dispatch.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(dispatches) == 6
        for index in range(3):
            pair = dispatches[index * 2:index * 2 + 2]
            assert [row['phase'] for row in pair] == ['prepared', 'completed']
            assert all(row['parent_launch'] == 'launch-dispatch-' + str(index) for row in pair)
            assert all(row['text'].startswith('⟦主控 #' + str(index + 1) + '⟧\n') for row in pair)
        calls = [json.loads(line) for line in (fixture.root / 'calls.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len([call for call in calls if call[:2] == ['agent', 'prompt']]) == 3
        assert logfile.read_bytes() == original, 'Dispatch must not rewrite launch history'
        report.update(status='PASS', checks=['launch_parent_from_explicit_environment', 'launch_phase_parent_immutable',
                      'dispatch_parent_for_worker_reviewer_monitor', 'one_send_per_command_and_unchanged_marker', 'launch_history_unchanged'])
    except Exception as error:
        report['error'] = repr(error)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    # Keep failed fixtures available; a green command only retains the summary.
    if report['status'] == 'PASS':
        fixture.doCleanups()
    else:
        fixture.temp._finalizer.detach()
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
