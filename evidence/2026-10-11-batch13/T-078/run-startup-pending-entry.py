"""Controller-run native CLI/daemon pending-startup red and green; no model."""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import traceback
from contextlib import closing
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
OLD = '&& !pane.writing && !pane.queue.length && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup"'
NEW = '&& !pane.writing && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup"'
SNAPSHOT_FILES = ['workbench/tests/test_t078_a13_rehearsal.ts', 'workbench/bin/inbox', 'workbench/package.json']


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare_snapshot(snap, source_text, mode):
    snap.mkdir(parents=True)
    shutil.copytree(SOURCE / 'workbench/src', snap / 'workbench/src')
    for relative in SNAPSHOT_FILES:
        destination = snap / relative; destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / relative, destination)
        assert destination.read_bytes() == (SOURCE / relative).read_bytes(), ('snapshot_file_changed', relative)
    (snap / 'workbench/node_modules').symlink_to((SOURCE / 'workbench/node_modules').resolve(), target_is_directory=True)
    if mode == 'red':
        (snap / 'workbench/src/panes.ts').write_text(source_text.replace(NEW, OLD), encoding='utf-8')


def probe_snapshot(snap, env, out):
    # An invalid command must reach the genuine inbox argument contract. It
    # cannot read session credentials, queue a request, or contact a daemon.
    entry = snap / 'workbench/bin/inbox'
    command = ['node', str(entry), 'not-a-command']
    completed = subprocess.run(command, cwd=snap, env=env, capture_output=True, text=True, timeout=10)
    observed = {'command': command, 'exit_code': completed.returncode, 'stdout': completed.stdout,
                'stderr': completed.stderr, 'service_starts': 0}
    save(out / 'inbox-loader.json', observed)
    assert completed.returncode == 2 and 'MODULE_NOT_FOUND' not in completed.stderr, ('snapshot_entry_not_loaded', observed)
    assert json.loads(completed.stdout)['error'] == 'inbox_client_arguments', ('wrong_entry_probe', observed)
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    fixture = BASE / '09b-startup-pending-fixture-01'
    require_paths = [SOURCE / 'workbench/src/panes.ts', fixture / 'fixture.json'] + [SOURCE / relative for relative in SNAPSHOT_FILES]
    for path in require_paths:
        assert path.is_file(), ('missing_input', str(path))
    text = require_paths[0].read_text(encoding='utf-8')
    assert text.count(NEW) == 1 and OLD not in text
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CLAUDE_', 'ANTHROPIC_', 'CODEX_', 'NODE_COMPILE_CACHE'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if args.check_only:
        with tempfile.TemporaryDirectory(prefix='t078-startup-layout-', dir='/private/tmp') as temporary:
            snap = Path(temporary).resolve() / 'probe'
            prepare_snapshot(snap, text, 'green')
            probe = probe_snapshot(snap, env, out)
        result = {'status': 'PASS', 'scope': 'snapshot files and real inbox loader/invalid-argument contract only; no daemon/model',
                  'paths': list(map(str, require_paths)), 'loader_exit_code': probe['exit_code'], 'scratch_removed': True}
        save(out / 'result.json', result); print(json.dumps(result)); return 0
    result = {'status': 'INCOMPLETE', 'runs': [], 'real_model_turns': 0,
              'scope': 'real CLI/daemon/Stop/relay; PTY and native identity are boundary spies; six recorded startup keys'}
    scratch = Path(tempfile.mkdtemp(prefix='t078-startup-entry-', dir='/private/tmp')).resolve()
    try:
        for mode in ['red', 'green']:
            snap = scratch / mode
            prepare_snapshot(snap, text, mode)
            probe_out = out / (mode + '-preflight'); probe_out.mkdir()
            probe_snapshot(snap, env, probe_out)
            command = ['node', str(snap / 'workbench/tests/test_t078_a13_rehearsal.ts'), str(out / mode), '--recipient-offline', str(fixture)]
            row = {'mode': mode, 'command': command, 'timeout_seconds': 190}; result['runs'].append(row)
            with (out / (mode + '.stdout.bin')).open('xb') as stdout, (out / (mode + '.stderr.bin')).open('xb') as stderr:
                completed = subprocess.run(command, cwd=snap, env=env, stdout=stdout, stderr=stderr,
                                           timeout=190, start_new_session=True)
            row['exit_code'] = completed.returncode
            observed = json.loads((out / mode / 'result.json').read_bytes()); row['observed_status'] = observed['status']
            if mode == 'red':
                assert completed.returncode != 0 and observed['status'] == 'INCOMPLETE', ('red_not_reproduced', observed)
                assert observed['step'] == 'approved startup keys keep the pending inbox queued', observed
                commands = [json.loads(path.read_bytes()) for path in (out / mode).glob('command-*.json')]
                refusals = [item for item in commands if 'pane_screen_key' in item['argv'] and item['code'] != 0]
                assert len(refusals) == 1 and 'screen_requires_startup' in refusals[0]['stdout'], ('wrong_red_reason', refusals)
                row['verdict'] = 'PASS: queue guard rejected the first approved startup key before a write'
            else:
                assert completed.returncode == 0 and observed['status'] == 'PASS', observed
                assert all(check['status'] == 'PASS' for check in observed['checks']), observed
                assert any(check['name'] == 'approved startup keys keep the pending inbox queued' for check in observed['checks'])
                detail = json.loads((out / mode / 'offline-delivery.json').read_bytes())
                assert detail['target_writes'][:6] == ['\x1b[A', '\x1b[B', '\r', '\r', '\x1b[B', '\r']
                assert detail['delivery']['state'] == 'delivered'
                original_id = observed['queued_receipt']['request_id']
                original_feedback = []
                for event in detail['feedback']:
                    raw = event['data']['text']; receipts = json.loads(raw[raw.index('\n[') + 1:])
                    original_feedback.extend(item for item in receipts if item['request_id'] == original_id)
                assert len(original_feedback) == 1
                assert original_feedback[0]['result']['entry']['id'] == detail['stop']['id']
                assert original_feedback[0]['result']['delivery']['state'] == 'delivered'
                assert detail['created_at_unchanged'] is True
                row['verdict'] = 'PASS: six startup keys, release, delivered, original I2, ack and denial chain'
            database = (out / mode / 'state.sqlite3').resolve()
            with closing(sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            row['sqlite_integrity'] = 'ok'
        assert (SOURCE / 'workbench/src/panes.ts').read_text(encoding='utf-8') == text, 'candidate_changed_during_run'
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        # Each rehearsal owns its daemon/PTY/database and closes them before
        # returning; this directory contains only copied source/dependency links.
        shutil.rmtree(scratch)
        result['source_scratch_removed'] = True
        save(out / 'result.json', result)
    print(json.dumps({'status': result['status'], 'output': str(out), 'error': result.get('error')}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
