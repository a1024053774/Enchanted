#!/usr/bin/env bash
# 主控执行：报告字段一致性红绿。受控 PTY，不使用真实 Codex/auth。
# 仅重跑 launch-policy；额外前置失败仅用夹具 node 版本，不启动 host。
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [[ -e "$SCRIPT_DIR/outside-command-13-$(printf '%02d' "$sequence")" ]]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-13-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ROOT" "$OUTPUT" > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt" <<'PY'
import datetime, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path

root, out = map(Path, sys.argv[1:])
record = {'status': 'INCOMPLETE', 'real_codex_turns': 0, 'steps': [],
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
fixture = None
safe_to_remove = True
env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_'))}
env['PYTHONDONTWRITEBYTECODE'] = '1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(name, value):
    with (out / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def check(name, report, phase_exit, stdout, expected_check_exit):
    argv = [sys.executable, '-B', str(root / 'workbench/tests/check_t076_phase_report.py'),
            '--report', str(report), '--exit-code', str(phase_exit), '--stdout', str(stdout)]
    result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=30)
    (out / (name + '.check.stdout.json')).write_text(result.stdout, encoding='utf-8')
    (out / (name + '.check.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    receipt = json.loads(result.stdout)
    save(name + '.check.command.json', {'argv': argv, 'exit_code': result.returncode})
    valid = result.returncode == expected_check_exit and receipt['status'] == ('PASS' if expected_check_exit == 0 else 'INCOMPLETE')
    return valid, receipt

try:
    # The current pre-fix runner's saved success was proved byte-identical in
    # status-sync-01/red.command.json before editing. Preserve that run as red.
    previous = root / 'evidence/2026-10-15-batch15/T-082/outside-command-12-01'
    old_exit = read(previous / 'run.json')['exit_code']
    valid, red = check('01-original-report-red', previous / 't076-launch-policy/run.json', old_exit,
                       previous / 'launch-policy.stdout.txt', 1)
    fields = {x['field'] for x in red['errors']}
    record['steps'].append({'name': 'original-report-red', 'status': 'PASS' if valid and old_exit == 0 and fields ==
                            {'report.product_status', 'stdout.product_status'} else 'INCOMPLETE', 'phase_exit': old_exit})
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External disk is unavailable; no internal fallback.')
    fixture = Path(tempfile.mkdtemp(prefix='p82-', dir='/Volumes/WD-Elements')).resolve()
    env['A2A_TEST_ARTIFACT_PARENT'] = str(fixture)
    record.update(fixture_root=str(fixture), head=subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip())
    fake_bin = fixture / 'bad-version-bin'
    fake_bin.mkdir()
    fake_node = fake_bin / 'node'
    fake_node.write_text('#!/bin/sh\n[ "$#" = 1 ] && [ "$1" = --version ] || exit 93\nprintf "v0.0.0\\n"\n', encoding='utf-8')
    fake_node.chmod(0o755)
    plans = [('02-success-green', env, 0),
             ('03-failed-prerequisite-green', {**env, 'PATH': str(fake_bin) + os.pathsep + env.get('PATH', '')}, 1)]
    for name, phase_env, expected_exit in plans:
        row = {'name': name, 'status': 'INCOMPLETE'}
        record['steps'].append(row)
        target = out / name
        argv = [sys.executable, '-B', str(root / 'workbench/tests/run_t076_launch_policy.py'), '--output', str(target)]
        stdout = out / (name + '.stdout.txt')
        row.update(argv=argv, cwd=str(root), expected_exit=expected_exit)
        try:
            with stdout.open('xb') as stream, (out / (name + '.stderr.txt')).open('xb') as errors:
                phase = subprocess.run(argv, cwd=root, env=phase_env, stdout=stream, stderr=errors, timeout=600)
            report = read(target / 'run.json')
            valid, receipt = check(name, target / 'run.json', phase.returncode, stdout, 0)
            intended = (expected_exit == 0 or report.get('error') == "RuntimeError('Pinned Node is unavailable.')")
            row.update(phase_exit=phase.returncode, report_status=report['status'], product_status=report['product_status'],
                       check_receipt=receipt, status='PASS' if valid and phase.returncode == expected_exit and intended else 'INCOMPLETE')
        except Exception as error:
            row.update(error=repr(error), traceback=traceback.format_exc())
    record['status'] = 'PASS' if all(x['status'] == 'PASS' for x in record['steps']) else 'INCOMPLETE'
except Exception as error:
    record.update(error=repr(error), traceback=traceback.format_exc())
finally:
    cleanup = []
    try:
        for db in out.rglob('database-readback.json'):
            receipt, stop = read(db), read(db.with_name('cleanup.json'))
            if receipt['phase'] != 'before-host-stop' or stop['host_exit'] != 0 or stop['failures']:
                raise RuntimeError('Owned host shutdown is not confirmed: ' + str(db))
            state = str(Path(stop['preserved_fixture']) / 'state')
            for row in receipt['tables']['launch_records']:
                launch = json.loads(row['data'])
                raw = Path(launch['request_dir'])
                if raw.is_symlink():
                    raise RuntimeError('Owned request directory was replaced by a link.')
                path = raw.resolve()
                if (path.parent != Path('/private/tmp') or not path.name.startswith('a2a-requests-')
                        or launch['env']['A2A_STATE'] != state):
                    raise RuntimeError('Request directory ownership mismatch: ' + str(path))
                if path.exists():
                    shutil.rmtree(path)
                cleanup.append({'path': str(path), 'absent': not path.exists(), 'receipt': str(db)})
        for start in out.rglob('host-*.start.json'):
            stop = start.with_name('cleanup.json')
            if not stop.exists() or read(stop)['failures']:
                raise RuntimeError('Incomplete host cleanup: ' + str(start))
    except Exception as error:
        safe_to_remove = False
        record.update(status='INCOMPLETE', cleanup_error=repr(error))
    record['request_cleanup'] = cleanup
    if fixture is not None:
        if safe_to_remove:
            try:
                archive = out / 'fixtures.tar.gz'
                with tarfile.open(archive, 'x:gz') as stream:
                    stream.add(fixture, arcname=fixture.name)
                shutil.rmtree(fixture)
                record.update(fixture_archive=str(archive), fixture_removed=not fixture.exists())
            except Exception as error:
                record.update(status='INCOMPLETE', archive_error=repr(error), preserved_fixture=str(fixture))
        else:
            record.update(preserved_fixture=str(fixture), fixture_removed=False)
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save('run.json', record)
    print(json.dumps({'status': record['status'], 'steps': record['steps'], 'real_codex_turns': 0}, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
exit_code=$?
printf 'output=%s\nexit_code=%s\n' "$OUTPUT" "$exit_code"
exit "$exit_code"
