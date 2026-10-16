#!/usr/bin/env bash
# Acceptance 2 补证。由主控在沙箱外运行；不启动真实 Codex。
# 起点只解 workbench/src、hooks、package.json、LICENSE.synara。
# gates/ 与其他起点源码不改；仅网络/tmp 案改临时 panes.ts 的启动参数。
# 夹具在外置盘，产品创建的 /private/tmp/a2a-requests-* 按所属 launch 清理。
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [[ -e "$SCRIPT_DIR/outside-command-10-$(printf '%02d' "$sequence")" ]]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-10-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ROOT" "$OUTPUT" > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt" <<'PY'
import datetime, io, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path

root, out = map(Path, sys.argv[1:])
start = '451be8462c85fd08b997cb85453188a8e5751c9d'
paths = ['workbench/src', 'workbench/hooks', 'workbench/package.json', 'workbench/LICENSE.synara']
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_'))}
env['PYTHONDONTWRITEBYTECODE'] = '1'
record = {'status': 'INCOMPLETE', 'starting_revision': start, 'candidate_head': None,
          'real_codex_turns': 0, 'steps': [], 'counterfactual_timing': 'reconstructed after the fix on the starting revision; not an earlier chronological run',
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
fixture = None
safe_to_remove = True

def save(name, value):
    with (out / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

try:
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External disk is not mounted; no internal fallback.')
    node = subprocess.run(['node', '--version'], env=env, capture_output=True, text=True, check=True)
    if not node.stdout.strip().startswith('v26.5.'):
        raise RuntimeError('Approved Node 26.5 runtime unavailable.')
    record['node_version'] = node.stdout.strip()
    record['candidate_head'] = subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip()
    archive_argv = ['git', '-C', str(root), 'archive', start, '--', *paths]
    archive = subprocess.check_output(archive_argv)
    fixture = Path(tempfile.mkdtemp(prefix='t82-', dir='/Volumes/WD-Elements')).resolve()
    record.update(fixture_root=str(fixture), materialize_argv=archive_argv, necessary_paths=paths)
    baseline = fixture / 'baseline'
    baseline.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as stream:
        members = stream.getmembers()
        for member in members:
            if member.name != 'workbench' and not any(member.name == p or member.name.startswith(p + '/') for p in paths):
                raise RuntimeError('Unexpected archive path: ' + member.name)
            if member.issym() or member.islnk():
                link = Path(member.linkname)
                if link.is_absolute() or '..' in link.parts:
                    raise RuntimeError('Unexpected archive link: ' + member.name)
        stream.extractall(baseline)
    (baseline / 'workbench/node_modules').symlink_to((root / 'workbench/node_modules').resolve(), target_is_directory=True)
    original = {str(p.relative_to(baseline)): p.read_bytes() for p in baseline.rglob('*')
                if p.is_file() and 'node_modules' not in p.parts}
    save('baseline-manifest.json', {'revision': start, 'argv': archive_argv, 'files': list(original),
         'bytes': sum(map(len, original.values())), 'dependency_link': str((root / 'workbench/node_modules').resolve())})
    # Reuse the candidate refusal evidence; do not run the main checkout or a
    # new candidate model round. Bind each green to its actual mutant and id.
    green_root = root / 'evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled'
    green = json.loads((green_root / 'run.json').read_text(encoding='utf-8'))
    if green['status'] != 'PASS' or green['real_codex_turns'] != 0:
        raise RuntimeError('Candidate green evidence is unavailable or not PASS.')
    historical_path = root / 'evidence/2026-10-15-batch15/T-082/red-state/t076-readonly-readback.json'
    historical = json.loads(historical_path.read_text(encoding='utf-8'))
    if not (historical['probe']['denied'] and historical['archived_after']['matches_before']):
        raise RuntimeError('Historical readonly red readback is incomplete.')
    readonly_green = next(x for x in green['steps'] if x['name'] == 'readonly-argv')
    record['readonly_reference'] = {'red': str(historical_path), 'historical_launch': historical['historical_result']['launch_id'],
                                  'green': str(green_root / 'launch-boundary-refused-readonly-argv/run.json'),
                                  'candidate_status': readonly_green['report']['status']}
    if readonly_green['returncode'] or readonly_green['report']['status'] != 'PASS':
        raise RuntimeError('Candidate readonly refusal was not PASS.')
    plan = [
        ('wrong-workspace', None, None),
        ('network-enabled', '"-c", "sandbox_workspace_write.network_access=false", "-c", "features.network_proxy=false"',
         '"-c", `sandbox_workspace_write.network_access=${review ? "true" : "false"}`, "-c", "features.network_proxy=false"'),
        ('tmp-writable', '    for (const event of ["UserPromptSubmit", "Stop", "PermissionRequest"])',
         '    if (review) argv.push("-c", "sandbox_workspace_write.exclude_slash_tmp=false");\n'
         '    for (const event of ["UserPromptSubmit", "Stop", "PermissionRequest"])'),
    ]
    for index, (name, before, after) in enumerate(plan):
        row = {'name': name, 'status': 'INCOMPLETE'}
        record['steps'].append(row)
        try:
            source = fixture / ('s' + str(index))
            shutil.copytree(baseline, source, symlinks=True)
            if before is not None:
                panes = source / 'workbench/src/panes.ts'
                text = panes.read_text(encoding='utf-8')
                if text.count(before) != 1:
                    raise RuntimeError('Mutation target is not unique: ' + name)
                panes.write_text(text.replace(before, after), encoding='utf-8')
            changed = [p for p, content in original.items() if (source / p).read_bytes() != content]
            expected = [] if before is None else ['workbench/src/panes.ts']
            if changed != expected:
                raise RuntimeError('Unexpected starting-source changes: ' + repr(changed))
            row.update(source_changes=changed, gates_unchanged=True, mutation={'before': before, 'after': after})
            target = out / name
            argv = [sys.executable, '-B', str(root / 'workbench/tests/test_t082_parent_launch_e2e.py'),
                    '--source', str(source), '--fixture-root', str(fixture / ('f' + str(index))),
                    '--output', str(target), '--case', name]
            row.update(argv=argv, cwd=str(root))
            with (out / (name + '.stdout.txt')).open('xb') as stdout, (out / (name + '.stderr.txt')).open('xb') as stderr:
                result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=300)
            row['exit_code'] = result.returncode
            changed_after = [p for p, content in original.items() if (source / p).read_bytes() != content]
            row['source_changes_after'] = changed_after
            if changed_after != expected:
                raise RuntimeError('Starting source changed during the probe: ' + repr(changed_after))
            report_path = target / 'run.json'
            report = json.loads(report_path.read_text(encoding='utf-8'))
            case = report['cases'][0]
            row.update(report=str(report_path), outcome=case['outcome'], failure_id=case.get('failure_id'),
                       cleanup_failures=case['cleanup_failures'])
            if case['cleanup_failures']:
                safe_to_remove = False
            observed = json.loads((target / name / 'parent-start-readback.json').read_text(encoding='utf-8'))
            row['parent_readback'] = str(target / name / 'parent-start-readback.json')
            current = next(x for x in green['steps'] if x['name'] == name)
            assertions = current['report']['cases'][0]['assertions']
            candidate_rejected = (current['returncode'] == 0 and current['report']['status'] == 'PASS'
                                  and any(a['id'] == 'T082-LAUNCH-REFUSED' and a['passed'] for a in assertions))
            row['green_reference'] = {'report': str(green_root / ('launch-boundary-refused-' + name) / 'run.json'),
                                      'source': green['source'], 'mutation': current['mutation'],
                                      'assertion': 'T082-LAUNCH-REFUSED', 'passed': candidate_rejected}
            red = (result.returncode == 1 and case['outcome'] == 'contract_failure'
                   and case.get('failure_id') == 'T082-LAUNCH-REFUSED' and not case['cleanup_failures']
                   and observed['verify']['ok'] and observed['release']['ok'] and observed['busy']['state'] == 'busy')
            row.update(expected_business_red=bool(red), candidate_green=bool(candidate_rejected),
                       status='PASS' if red and candidate_rejected else 'INCOMPLETE')
        except subprocess.TimeoutExpired as error:
            safe_to_remove = False
            row.update(error=repr(error), preservation='child timed out; fixture/processes require controller disposition')
        except Exception as error:
            row.update(error=repr(error), traceback=traceback.format_exc())
            # If no complete cleanup receipt exists, keep the fixture rather
            # than delete files beneath a potentially live owned daemon.
            receipt = out / name / 'run.json'
            if not receipt.exists() or any(c.get('cleanup_failures') for c in json.loads(receipt.read_text())['cases']):
                safe_to_remove = False
    record['status'] = 'PASS' if all(x['status'] == 'PASS' for x in record['steps']) else 'INCOMPLETE'
except Exception as error:
    record.update(error=repr(error), traceback=traceback.format_exc())
finally:
    if fixture is not None:
        if safe_to_remove:
            try:
                destination = out / 'parent-fixtures.tar.gz'
                with tarfile.open(destination, 'x:gz') as stream:
                    stream.add(fixture, arcname=fixture.name)
                record['fixture_archive'] = str(destination)
                shutil.rmtree(fixture)
                record['fixture_removed'] = not fixture.exists()
            except Exception as error:
                record.update(status='INCOMPLETE', cleanup_error=repr(error), preserved_fixture=str(fixture))
        else:
            record.update(status='INCOMPLETE', preserved_fixture=str(fixture), fixture_removed=False)
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save('run.json', record)
    print(json.dumps({'status': record['status'], 'steps': [{k: v for k, v in x.items() if k in
          ('name', 'status', 'outcome', 'failure_id', 'expected_business_red', 'candidate_green', 'error')}
          for x in record['steps']], 'real_codex_turns': 0}, ensure_ascii=False), flush=True)
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
exit_code=$?
printf 'output=%s\nexit_code=%s\n' "$OUTPUT" "$exit_code"
exit "$exit_code"
