#!/usr/bin/env bash
# 主控执行：仅重跑 T-076 launch-policy 五段，不重跑 OUTSIDE-11 的其他段。
# 受控 PTY，无真实 Codex/auth；夹具放外置盘，按停止收据清理所属目录。
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$SCRIPT_DIR/../../../" && pwd)
sequence=1
while [[ -e "$SCRIPT_DIR/outside-command-12-$(printf '%02d' "$sequence")" ]]; do
  sequence=$((sequence + 1))
done
OUTPUT="$SCRIPT_DIR/outside-command-12-$(printf '%02d' "$sequence")"
mkdir "$OUTPUT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ROOT" "$OUTPUT" > "$OUTPUT/runner.stdout.txt" 2> "$OUTPUT/runner.stderr.txt" <<'PY'
import datetime, json, os, shutil, subprocess, sys, tarfile, tempfile, traceback
from pathlib import Path

root, out = map(Path, sys.argv[1:])
target = out / 't076-launch-policy'
fixture = None
record = {'status': 'INCOMPLETE', 'real_codex_turns': 0, 'scope': 'T-076 launch-policy only',
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
safe_to_remove = True

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(name, value):
    with (out / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

try:
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('External disk is unavailable; no internal fallback.')
    fixture = Path(tempfile.mkdtemp(prefix='l82-', dir='/Volumes/WD-Elements')).resolve()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', A2A_TEST_ARTIFACT_PARENT=str(fixture))
    argv = [sys.executable, '-B', str(root / 'workbench/tests/run_t076_launch_policy.py'), '--output', str(target)]
    record.update(argv=argv, cwd=str(root), fixture_root=str(fixture),
                  head=subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip())
    with (out / 'launch-policy.stdout.txt').open('xb') as stdout, (out / 'launch-policy.stderr.txt').open('xb') as stderr:
        result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=600)
    record['exit_code'] = result.returncode
    report = read(target / 'run.json')
    record['report'] = str(target / 'run.json')
    expected = ['worker-missing-override-red', 'reviewer-missing-override-red', 'default-tier-green',
                'priority-argv-mutant', 'review-boundary-mutant']
    if result.returncode != 0 or report['status'] != 'PASS' or [x['name'] for x in report['steps']] != expected:
        raise RuntimeError('Launch-policy phase did not pass every planned step.')
    defaults = read(target / 'reviewer-missing-override-red/run.json')['cases'][0]
    required = ['TRACER-REVIEW-START', 'TRACER-REVIEW-COPY-ARGV', 'TRACER-REVIEW-CHECKOUT', 'TRACER-REVIEW-CANDIDATE-COPY']
    if (defaults['outcome'] != 'contract_failure' or defaults.get('failure_id') != 'TRACER-REVIEWER-DEFAULT-ARGV'
            or defaults['cleanup_failures'] or any(not any(a['id'] == key and a['passed'] for a in defaults['assertions']) for key in required)):
        raise RuntimeError('Default tier red did not retain the original assertion and valid D3 boundary.')
    refused = read(target / 'review-boundary-refusal.json')
    if (refused['failure_id'] != 'TRACER-REVIEW-START' or refused['verify']['error'] != 'review_launch_boundary'
            or refused['actual_sandbox'] != 'read-only' or refused['cleanup_failures']):
        raise RuntimeError('Readonly launch was not rejected at the required product boundary.')
    save('focused-readback.json', {'status': 'PASS', 'default_tier_failure_id': defaults['failure_id'],
         'prior_d3_assertions_passed': required, 'readonly_failure_id': refused['failure_id'],
         'readonly_gate_error': refused['verify']['error'], 'readonly_actual_sandbox': refused['actual_sandbox'],
         'default_tier_green': str(target / 'default-tier-green/run.json'), 'real_codex_turns': 0})
    record['status'] = 'PASS'
except Exception as error:
    record.update(error=repr(error), traceback=traceback.format_exc())
finally:
    cleanup = []
    try:
        for db in target.rglob('database-readback.json'):
            receipt = read(db)
            stop = read(db.with_name('cleanup.json'))
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
        for start in target.rglob('host-*.start.json'):
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
    print(json.dumps({'status': record['status'], 'real_codex_turns': 0}, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
exit_code=$?
printf 'output=%s\nexit_code=%s\n' "$OUTPUT" "$exit_code"
exit "$exit_code"
