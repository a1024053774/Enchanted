"""Run the merged T-078/T-082 checks sequentially without provider models."""
import argparse
import ast
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = ROOT / 'evidence/2026-10-11-batch13/T-078'
PARENTS = ['150ef6516f6ef5aaa6855631b770ce262991ffbf', '0e6c2b833f6da64243f71d670ea45bb9116fda4d']
BOUNDARY_CASES = ['real_payload_report_roundtrip', 'external_review_boundary_invalidated',
                  'shared_refs_changed', 'requirements_workspace_changed',
                  'integration_before_end_check', 'integration_before_end_check_clean']
FIXTURE_FIXES = ['workbench/tests/quality_chain_host.ts', 'workbench/tests/test_quality_chain_e2e.py',
                'workbench/tests/run_t082_boundary.py', 'workbench/tests/test_t078_quality_host_bootstrap.py']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def commands(out):
    python = sys.executable
    payload = ROOT / 'evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json'
    stages = [
        ('pending-and-controller', [python, '-B', BASE / 'run-pending-checks.py', '--suite', 'local', '--output', out / 'pending'], out / 'pending/result.json', 700),
        ('startup-domain-and-M5', [python, '-B', BASE / 'run-startup-receipt-checks.py', '--suite', 'domain', '--output', out / 'startup-domain'], out / 'startup-domain/result.json', 150),
        ('startup-entry-and-M5', [python, '-B', BASE / 'run-startup-receipt-checks.py', '--suite', 'entry', '--output', out / 'startup-entry'], out / 'startup-entry/result.json', 420),
        ('worker-inbox', [python, '-B', BASE / 'run-pending-checks.py', '--suite', 'runtime', '--output', out / 'worker'], out / 'worker/result.json', 250),
        ('T082-launch-boundary-and-four-mutants', [python, '-B', ROOT / 'workbench/tests/run_t082_boundary.py', '--source', ROOT, '--output', out / 't082-launch'], out / 't082-launch/run.json', 1600),
        ('T082-report-and-end-check', [python, '-B', ROOT / 'workbench/tests/test_t082_review_boundary_e2e.py', '--source', ROOT, '--output', out / 't082-end',
            *[token for case in BOUNDARY_CASES for token in ['--case', case]]], out / 't082-end/run.json', 1500),
    ]
    required = [payload, BASE / 'merge-main-3/audit-merge.py',
                ROOT / 'workbench/tests/test_t078_a13_rehearsal.ts',
                ROOT / 'workbench/tests/test_t078_startup_pending.ts',
                ROOT / 'workbench/tests/test_t078_input_entry.py',
                ROOT / 'workbench/bin/inbox', ROOT / 'workbench/app/build.mjs',
                ROOT / 'workbench/tests/test_t082_review_protocol.ts',
                BASE / '09b-startup-pending-fixture-01/fixture.json',
                BASE / 'startup-receipt-oracle-312/M5.json']
    for name, command, result, timeout in stages:
        for token in command:
            if isinstance(token, Path) and token.suffix in ['.py', '.ts']:
                required.append(token)
    for path in dict.fromkeys(required):
        assert path.is_file(), ('missing required input', str(path))
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    assert not out.exists() and out.parent == BASE, 'Use a new output directly under the T-078 evidence root'
    return [(name, list(map(str, command)), result, timeout) for name, command, result, timeout in stages], required


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--resume-t082', action='store_true')
    parser.add_argument('--previous-result', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    planned, required = commands(out)
    previous = None
    previous_path = None
    if args.resume_t082:
        assert args.previous_result, 'Previous passing T078 stage receipts are required'
        previous_path = args.previous_result.resolve()
        assert previous_path == BASE / 'merge-main-3-outside-01/result.json'
        previous = json.loads(previous_path.read_bytes())
        assert previous['source_revision'] == '859fd649765e64926c87c7eb69499854b18ae042'
        assert [row['name'] for row in previous['stages'][:4]] == [row[0] for row in planned[:4]]
        assert all(row['status'] == 'PASS' and row['exit_code'] == 0 for row in previous['stages'][:4])
        assert previous['stages'][4]['name'] == planned[4][0] and previous['stages'][4]['status'] == 'INCOMPLETE'
        planned = planned[4:]
        for relative in FIXTURE_FIXES:
            path = ROOT / relative
            assert path.is_file(), ('missing fixture fix', relative)
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            required.append(path)
    else:
        assert args.previous_result is None, 'previous-result requires resume-t082'
    source_paths = ['workbench/src', 'workbench/tests', 'workbench/app', 'workbench/bin', 'workbench/package.json']
    def check_source():
        if previous:
            # The completed four stages used the same product/frontend. Only
            # these quality-host fixture files may change for the continuation.
            protected = [path for path in source_paths if path != 'workbench/tests']
            assert not git('diff', previous['source_revision'], '--', *protected), 'Previously tested product changed'
            changed = git('diff', '--name-only', previous['source_revision'], '--', 'workbench/tests').splitlines()
            assert set(changed).issubset(FIXTURE_FIXES), ('Unrelated fixture changes', changed)
        else:
            assert not git('diff', 'HEAD', '--', *source_paths), 'Source differs from the merged commit'
    if previous:
        check_source()
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'mode': 'path-and-syntax-check-only',
            'required_inputs': [str(path) for path in dict.fromkeys(required)],
            'commands': [{'name': name, 'argv': command, 'timeout_seconds': timeout} for name, command, _, timeout in planned],
            'previous_result': str(previous_path) if previous_path else None,
            'preserved_passed_stages': [row['name'] for row in previous['stages'][:4]] if previous else [],
            'service_starts': 0, 'real_model_turns': 0}, ensure_ascii=False, indent=2))
        return 0
    # Runtime evidence must bind the finished merge, not its first parent's HEAD.
    assert not Path(git('rev-parse', '--git-path', 'MERGE_HEAD')).exists(), 'Controller must commit the merge before regression'
    assert not git('diff', '--name-only', '--diff-filter=U'), 'Unresolved merge remains'
    for parent in PARENTS:
        subprocess.run(['git', 'merge-base', '--is-ancestor', parent, 'HEAD'], cwd=ROOT, check=True)
    check_source()
    assert Path('/Volumes/WD-Elements').is_mount(), 'External build disk is required'
    artifacts = Path('/Volumes/WD-Elements/a2a-workbench')
    assert artifacts.is_dir() and not artifacts.is_symlink(), 'External fixture parent is unavailable'
    out.mkdir(exist_ok=False)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'NODE_COMPILE_CACHE'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', A2A_TEST_ARTIFACT_PARENT=str(artifacts))
    record = {'status': 'INCOMPLETE', 'source_revision': git('rev-parse', 'HEAD'), 'parents': PARENTS,
              'real_model_turns': 0, 'stages': [],
              'scope': 'Merged candidate; real gate/daemon/relay/Git/SQLite and worker Electron entry, controlled provider observations; no A14 scene access'}
    fixture_snapshot = {}
    if previous:
        record.update(scope='T082 continuation only; preserve the prior four T078 PASS receipts because product/frontend are unchanged',
                      previous_result=str(previous_path), preserved_passed_stages=previous['stages'][:4],
                      fixture_working_tree_snapshot=[])
        for relative in FIXTURE_FIXES:
            raw = (ROOT / relative).read_bytes()
            fixture_snapshot[relative] = raw
            target = out / 'fixture-source' / relative
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            record['fixture_working_tree_snapshot'].append({'source': relative, 'copy': str(target)})

    def save():
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    save()
    try:
        for index, (name, command, result_path, timeout) in enumerate(planned, 1):
            row = {'name': name, 'argv': command, 'timeout_seconds': timeout, 'status': 'INCOMPLETE'}
            record['stages'].append(row); save()
            print(json.dumps({'stage': name, 'action': 'start', 'output': str(result_path.parent)}, ensure_ascii=False), flush=True)
            started = time.monotonic()
            with (out / f'{index:02}.stdout.bin').open('xb') as stdout, (out / f'{index:02}.stderr.bin').open('xb') as stderr:
                child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                row['runner_pid'] = child.pid; save()
                try:
                    code = child.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Only this runner's new process group is signalled. A test
                    # may own detached services; their state remains unknown.
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
                    row.update(error='stage_timeout_no_retry', cleanup='INCOMPLETE: inspect preserved test-owned services before cleanup')
                    raise RuntimeError(name + ': hard deadline; stop without retry')
            row.update(exit_code=code, elapsed_seconds=round(time.monotonic() - started, 3)); save()
            assert code == 0 and result_path.is_file(), ('stage failed; no retry', name, code)
            value = json.loads(result_path.read_bytes())
            assert value['status'] == 'PASS', (name, value.get('error'), value.get('failures'))
            if name.startswith('startup-'):
                candidate = next(run for run in value['runs'] if run['mode'] == 'candidate')
                assert candidate['checks'] == (15 if 'domain' in name else 14)
                assert candidate['pre_release_refreshes'] == (7 if 'domain' in name else 6)
                assert next(run for run in value['runs'] if run['mode'] == 'm5')['exit_code'] != 0
            elif name == 'worker-inbox':
                assert len(value['checks']) == 1 and value['checks'][0]['assertions'] == 14
            elif name.startswith('T082-launch'):
                assert value['product_status'] == 'PASS' and len(value['steps']) == 5
                assert not value['failures'] and not value['q76_remaining'] and value['mutation_fixture_removed']
            elif name.startswith('T082-report'):
                assert value['planned_cases'] == BOUNDARY_CASES and len(value['cases']) == len(BOUNDARY_CASES)
                assert all(case['outcome'] == 'passed' and not case['cleanup_failures'] for case in value['cases'])
            else:
                assert len(value['checks']) == 11 and all(check['status'] == 'PASS' for check in value['checks'])
            row.update(status='PASS', report=str(result_path)); save()
            print(json.dumps({'stage': name, 'status': 'PASS'}, ensure_ascii=False), flush=True)
        assert git('rev-parse', 'HEAD') == record['source_revision'], 'HEAD changed during regression'
        check_source()
        assert all((ROOT / relative).read_bytes() == raw for relative, raw in fixture_snapshot.items()), 'Fixture source changed during regression'
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        save()
    print(json.dumps({'status': record['status'], 'output': str(out), 'error': record.get('error')}, ensure_ascii=False), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
