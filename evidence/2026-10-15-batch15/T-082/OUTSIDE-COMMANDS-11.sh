#!/usr/bin/env bash
# 主控执行：返工 01 的真实 CLI/daemon 受控红绿、单点变异及回归。
# 不使用真实 Codex/auth；夹具只建在外置盘；输出序号递增，不覆盖历史。
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [[ -e "$SCRIPT_DIR/outside-command-11-$(printf '%02d' "$sequence")" ]]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-11-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ROOT" "$OUTPUT" > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt" <<'PY'
import datetime, gzip, io, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path

root, out = map(Path, sys.argv[1:])
record = {'status': 'INCOMPLETE', 'real_codex_turns': 0, 'steps': [], 'mutations': [],
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
fixture = None
safe_to_remove = True
captured = {}

def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def suite(name, selected, script, cases=(), failure=None, driver=False):
    row = {'name': name, 'status': 'INCOMPLETE', 'expected_failure': failure}
    record['steps'].append(row)
    target = out / name
    harness = selected if script == 'run_t076_launch_policy.py' else root
    argv = [sys.executable, '-B', str(harness / 'workbench/tests' / script), '--output', str(target)]
    if script != 'run_t076_launch_policy.py':
        argv.extend(['--source', str(selected)])
    if not driver:
        for case in cases:
            argv.extend(['--case', case])
    row.update(argv=argv, source=str(selected), cwd=str(root))
    try:
        with (out / (name + '.stdout.txt')).open('xb') as stdout, (out / (name + '.stderr.txt')).open('xb') as stderr:
            result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=600)
        row['exit_code'] = result.returncode
        report = json.loads((target / 'run.json').read_text(encoding='utf-8'))
        row['report'] = str(target / 'run.json')
        if driver:
            good = result.returncode == 0 and report['status'] == 'PASS'
        else:
            actual = report['cases']
            valid = (all(c['outcome'] != 'harness_error' and not c['cleanup_failures'] for c in actual)
                     and (not cases or [c['case'] for c in actual] == list(cases)))
            row['outcomes'] = [{'case': c['case'], 'outcome': c['outcome'], 'failure_id': c.get('failure_id')} for c in actual]
            good = (valid and len(actual) == 1 and result.returncode == 1
                    and actual[0]['outcome'] == 'contract_failure' and actual[0].get('failure_id') == failure
                    if failure else valid and result.returncode == 0 and report['status'] == 'PASS')
        row['status'] = 'PASS' if good else 'INCOMPLETE'
    except Exception as error:
        row.update(error=repr(error), traceback=traceback.format_exc())
    save(out / (name + '.assessment.json'), row)
    print(json.dumps({k: row[k] for k in ('name', 'status', 'expected_failure')}, ensure_ascii=False), flush=True)

def variant(name, path, before, after):
    target = fixture / name
    shutil.copytree(candidate, target, symlinks=True)
    file = target / path
    text = file.read_text(encoding='utf-8')
    if text.count(before) != 1:
        raise RuntimeError('Mutation target is not unique: ' + name)
    file.write_text(text.replace(before, after), encoding='utf-8')
    record['mutations'].append({'name': name, 'source': str(target), 'path': path, 'before': before, 'after': after})
    return target

try:
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External disk is unavailable; no internal fallback.')
    node = subprocess.check_output(['node', '--version'], text=True).strip()
    if node != 'v26.5.0':
        raise RuntimeError('Pinned Node 26.5.0 unavailable.')
    fixture = Path(tempfile.mkdtemp(prefix='x82-', dir='/Volumes/WD-Elements')).resolve()
    record.update(fixture_root=str(fixture), node=node,
                  head=subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip())
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', A2A_TEST_ARTIFACT_PARENT=str(fixture))
    candidate = fixture / 'candidate'
    paths = ['workbench/src', 'workbench/hooks', 'workbench/tests']
    for path in paths:
        shutil.copytree(root / path, candidate / path, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__', '.DS_Store'))
        for file in (root / path).rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts:
                captured[file] = file.read_bytes()
    for path in ('workbench/package.json', 'workbench/LICENSE.synara'):
        shutil.copyfile(root / path, candidate / path)
    (candidate / 'workbench/node_modules').symlink_to((root / 'workbench/node_modules').resolve(), target_is_directory=True)
    baseline = fixture / 'baseline'
    baseline.mkdir()
    rev = subprocess.check_output(['git', '-C', root, 'rev-parse', 'f09f0dcc8^{commit}'], text=True).strip()
    argv = ['git', '-C', str(root), 'archive', rev, '--', 'workbench/src', 'workbench/hooks',
            'workbench/package.json', 'workbench/LICENSE.synara']
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(argv))) as stream:
        members = stream.getmembers()
        for m in members:
            p = Path(m.name)
            if p.is_absolute() or '..' in p.parts or not (m.name == 'workbench' or any(
                    m.name == x or m.name.startswith(x + '/') for x in argv[argv.index('--') + 1:])):
                raise RuntimeError('Unexpected baseline archive member: ' + m.name)
            if m.issym() and (Path(m.linkname).is_absolute() or '..' in Path(m.linkname).parts):
                raise RuntimeError('Unexpected baseline archive link: ' + m.name)
            if not (m.isfile() or m.isdir() or m.issym()):
                raise RuntimeError('Unexpected baseline entry type: ' + m.name)
        stream.extractall(baseline)
    (baseline / 'workbench/node_modules').symlink_to((root / 'workbench/node_modules').resolve(), target_is_directory=True)
    save(out / 'source.json', {'baseline_revision': rev, 'baseline_argv': argv,
         'candidate': str(candidate), 'head': record['head'],
         'candidate_files': [str(p.relative_to(root)) for p in captured],
         'meaning': 'candidate is the captured working tree; baseline product source is frozen review-01 source'})

    test = 'test_t082_review_boundary_e2e.py'
    # First replay the independent review's two actual failing scenarios on the
    # unmodified reviewed source. Their original pre-fix receipts are preserved
    # separately in rework-01-red-readback/; these are additional replays.
    suite('01-red-integration-window', baseline, test, ['integration_before_end_check'], 'REVIEW-END-BEFORE-INTEGRATE')
    suite('02-red-request-workspace', baseline, test, ['requirements_workspace_changed'], 'REVIEW-REQUIREMENTS-WORKSPACE')
    for name, cases in [
        ('03-request-copy-report', ['tracer_review_copy', 'real_payload_report_roundtrip']),
        ('04-dirty-review', ['external_review_boundary_invalidated']),
        ('05-shared-refs', ['shared_refs_changed']),
        ('06-integration-window', ['integration_before_end_check']),
        ('07-clean-integration-window', ['integration_before_end_check_clean']),
        ('08-request-workspace', ['requirements_workspace_changed']),
    ]:
        suite(name, candidate, test, cases)
    changes = [
        ('M1-no-end-check-precondition', 'requireGate(ended, "review_end_check_required");',
         'requireGate(true, "review_end_check_required");', 'integration_before_end_check_clean', 'REVIEW-END-BEFORE-INTEGRATE'),
        ('M2-no-workspace-binding', 'requireGate(evidence.review_requirements.mutation_checks.workspace === review.candidate_workspace,',
         'requireGate(true,', 'requirements_workspace_changed', 'REVIEW-REQUIREMENTS-WORKSPACE'),
        ('M3-no-shared-refs-check', 'requireGate(refs === review.shared_refs, "review_shared_refs_changed",',
         'requireGate(true, "review_shared_refs_changed",', 'shared_refs_changed', 'REVIEW-REFS-INVALIDATE'),
    ]
    for index, (name, before, after, case, failure) in enumerate(changes, 9):
        selected = variant(name, 'workbench/src/gates/core.ts', before, after)
        suite('%02d-%s' % (index, name), selected, test, [case], failure)
    suite('12-launch-boundary', candidate, 'run_t082_boundary.py', driver=True)
    suite('13-t076-properties', candidate, 'test_quality_tracer_e2e.py',
          ['tracer_wrong_candidate', 'tracer_reused_native', 'tracer_writer_cannot_review', 'tracer_malformed_review'])
    suite('14-t077-lifecycle', candidate, 'test_review_worktree_lifecycle_e2e.py')
    suite('15-t076-launch-policy', candidate, 'run_t076_launch_policy.py', driver=True)
    record['status'] = 'PASS' if all(x['status'] == 'PASS' for x in record['steps']) else 'INCOMPLETE'
except Exception as error:
    record.update(error=repr(error), traceback=traceback.format_exc())
finally:
    # Use pre-stop receipts, never reopen stopped WAL databases. A missing or
    # mismatched receipt preserves the external fixture for controller handling.
    cleanup = []
    try:
        for db in out.rglob('database-readback.json'):
            receipt = json.loads(db.read_text(encoding='utf-8'))
            stopped = json.loads(db.with_name('cleanup.json').read_text(encoding='utf-8'))
            if receipt['phase'] != 'before-host-stop' or stopped['host_exit'] != 0 or stopped['failures']:
                raise RuntimeError('Owned host stop is not confirmed: ' + str(db))
            state = str(Path(stopped['preserved_fixture']) / 'state')
            for row in receipt['tables']['launch_records']:
                launch = json.loads(row['data'])
                raw_path = Path(launch['request_dir'])
                if raw_path.is_symlink():
                    raise RuntimeError('Owned request directory was replaced by a link: ' + str(raw_path))
                path = raw_path.resolve()
                if (path.parent != Path('/private/tmp') or not path.name.startswith('a2a-requests-')
                        or launch['env']['A2A_STATE'] != state):
                    raise RuntimeError('Unexpected request directory ownership: ' + str(path))
                if path.exists():
                    shutil.rmtree(path)
                cleanup.append({'path': str(path), 'absent': not path.exists(), 'receipt': str(db)})
        for start in out.rglob('host-*.start.json'):
            stop = start.with_name('cleanup.json')
            if not stop.exists() or json.loads(stop.read_text(encoding='utf-8'))['failures']:
                raise RuntimeError('Incomplete host cleanup receipt: ' + str(start))
    except Exception as error:
        safe_to_remove = False
        record.update(status='INCOMPLETE', cleanup_error=repr(error))
    record['request_cleanup'] = cleanup
    if fixture is not None:
        if safe_to_remove:
            try:
                destination = out / 'fixtures.tar.gz'
                with tarfile.open(destination, 'x:gz') as stream:
                    stream.add(fixture, arcname=fixture.name)
                shutil.rmtree(fixture)
                record.update(fixture_archive=str(destination), fixture_removed=not fixture.exists())
            except Exception as error:
                record.update(status='INCOMPLETE', archive_error=repr(error), preserved_fixture=str(fixture))
        else:
            record.update(preserved_fixture=str(fixture), fixture_removed=False)
    record['source_changed_during_run'] = [str(p) for p, b in captured.items() if not p.exists() or p.read_bytes() != b]
    if record['source_changed_during_run']:
        record['status'] = 'INCOMPLETE'
    for path in list(out.rglob('*')):
        if path.is_file() and path.stat().st_size > 5 * 1024 * 1024 and path.suffix != '.gz':
            with path.open('rb') as src, gzip.open(str(path) + '.gz', 'xb') as dest:
                shutil.copyfileobj(src, dest)
            path.unlink()
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(out / 'run.json', record)
    print(json.dumps({'status': record['status'], 'real_codex_turns': 0,
                      'steps': [{'name': x['name'], 'status': x['status']} for x in record['steps']]}, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
exit_code=$?
printf 'output=%s\nexit_code=%s\n' "$OUTPUT" "$exit_code"
exit "$exit_code"
