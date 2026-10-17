#!/usr/bin/env python3
"""CONTROLLER ONLY: run existing regression assertions on the frozen T-091 source.

Review the selected case BEFORE each run; no prior approval carries over.
  Every case: Python/Node 26.5/Git, new isolated HOME/TMP/state/user-data, external
    output only; no auth.json, global writes, real Claude/Codex or provider rounds.
  core: existing coop 8 / recovery 9 / run 18 / CAS 1, then fence/CAS/lock single-site
    mutants in disposable source copies. A pure classifier self-check runs first.
    Production daemon and controlled test
    threads. Three full-quality run positives explicitly use 30s in the adapter;
    timeout/fault cases retain their original deadlines. No retry or gate change.
    Recovery deliberately stops ONLY fixture-owned processes. No Electron,
    keyboard or vendor hook. Git fixture commits, verify/integrate and cleanup are
    performed by the ORIGINAL tests through the gate. No push or project integration.
  window: one Electron, one daemon, gate claim but no worker/model. Attempts readonly
    input through the original test, no terminal key or synthetic Stop hook.
  runtime: one Electron, one daemon, one controlled native receiver; initial Chinese
    paste+Enter, empty composition+Enter, ONE UI Esc, ONE explicit queue release,
    one gate Esc, final 1200-line paste without Enter. THREE synthetic Stop hooks
    (turns 2/3/4); queued fixture task/inbox prompts are consumed by receiver only.
  input-failures: one Electron, daemon start plus one explicit cold restart, one
    controlled native receiver. Initial paste+Enter, empty composition+Enter;
    one composed Chinese text, one duplicate-request attempt, closed-identity
    attempt, TWO binary mouse packets (12 bytes), recorder-fault and stale-identity
    probes. ONE synthetic Stop hook. All faults affect only this fixture database.
  worker-inbox: one Electron, one daemon, one controlled native receiver; initial
    paste+Enter, empty composition+Enter, REVOKE_PROBE paste+Enter, FOUR synthetic
    Stop hooks; worker client invokes 7 initial inbox commands plus 1 revoked issue.
    Two controller_prepare records remain static; absent Claude paths never run.
  GUI cases reuse the ORIGINAL test assertions and updated production driver.
    At most 400 driver RPCs (1200 screen reads); stop before another non-close
    RPC after 64 MiB stdout. Normal close is reserved outside that probe budget.
    Child stdout/stderr stay in external files; terminal prints one short summary.
    Old regression capturePage frames contain only its own renderer; T-091 green's
    required native single-window evidence is separately captured with verified -l.
    Ready unconfirmed => stop for controller, no Electron signal or normal quit.
    Confirmed ready => owner-verified normal window.close; failed exit defers backend
    shutdown/archive. No automatic kill fallback. Services detach from caller group.
  The wrapper never changes expected results. It verifies exit/status/counts and
    business_mutant evidence, confirms recorded writers absent, then copies stopped
    fixtures without following symlinks. Originals retained. No build-output moves,
    replacement or links. New output and label only; missing volume => error.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import time
import traceback

from run_red import VOLUME, archive_fixture, write_json


def recorded_writers(child, fixture):
    """Use original live readbacks; never reopen a stopped WAL database."""
    pids = []
    for logfile in child.glob('*-driver.jsonl'):
        for line in logfile.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if row.get('pid'):
                pids.append(row['pid'])
    for started in fixture.rglob('receiver-started.json'):
        pids.append(json.loads(started.read_text(encoding='utf-8'))['pid'])
    events = json.loads((child / 'readback-orchestration_events.json').read_text(encoding='utf-8'))
    for row in events:
        kind = row['type']
        if kind in ['daemon_started', 'pane_started']:
            value = json.loads(row['data'])
            pids.append(value['pid'] if kind == 'daemon_started' else value['shell_pid'])
    if not pids:
        raise RuntimeError('recorded_processes_unavailable')
    return sorted(set(pids))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--case', choices=['core', 'window', 'runtime', 'input-failures', 'worker-inbox'], required=True)
    parser.add_argument('--approval-ref', required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    script_dir = Path(__file__).resolve().parent
    root = (VOLUME / 'a2a-evidence/2026-10-16-batch16/T-091').resolve()
    if not os.path.ismount(VOLUME) or not output.is_relative_to(root) or output == root:
        raise RuntimeError('mounted_external_output_required')
    if not args.label or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for char in args.label):
        raise RuntimeError('invalid_summary_label')
    for suffix in ['run.json', 'archive.json']:
        if (script_dir / f'{args.label}.{suffix}').exists():
            raise RuntimeError('new_summary_label_required')
    output.mkdir(parents=True, exist_ok=False)
    isolation = Path(tempfile.mkdtemp(prefix='t091-regression-', dir='/private/tmp')).resolve()
    for name in ['home', 'tmp']:
        (isolation / name).mkdir()
    env = {key: os.environ[key] for key in ['PATH', 'USER', 'LOGNAME'] if key in os.environ}
    env.update(HOME=str(isolation / 'home'), TMPDIR=str(isolation / 'tmp'), LANG='en_US.UTF-8', LC_ALL='C',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    sys.path.insert(0, str(source / 'workbench/tests'))
    from command_evidence import CommandLog
    commands = CommandLog(output)
    result = {'status': 'INCOMPLETE', 'task': 'T-091', 'attempt': 'a1', 'worker': 's16-t091',
              'worker_launch': 'launch-71afbd1600cb451a9d9354aa7768e72b',
              'worker_session': 'd4277ace-1dde-425b-99b8-8988f1df751f',
              'worker_native_session': '01a14a05-4472-70e1-af77-58414340c1ee', 'case': args.case,
              'approval_ref': args.approval_ref, 'argv': sys.argv, 'supplier_model_turns': 0,
              'real_vendor_cli_starts': 0, 'electron_starts_budget': 0 if args.case == 'core' else 1,
              'driver_rpc_limit': 400, 'screen_read_upper_bound': 1200,
              'stdout_stop_threshold_bytes': 64 * 1024 * 1024, 'checks': [], 'archive_complete': False}
    archives, fixture_roots = [], [isolation]

    def run(argv, expected=0, timeout=1200, raw_name=None):
        raw_paths = {} if raw_name is None else {'stdout_file': output / (raw_name + '.stdout.txt'),
                                               'stderr_file': output / (raw_name + '.stderr.txt')}
        item = commands.run(argv, cwd=source, env=env, timeout=timeout, **raw_paths)
        if item.returncode != expected:
            raise RuntimeError({'unexpected_command_exit': item.evidence['id'], 'expected': expected, 'actual': item.returncode})
        return item

    def check(name, passed):
        result['checks'].append({'name': name, 'status': 'PASS' if passed else 'INCOMPLETE'})
        if not passed:
            raise AssertionError(name)

    def archive_stopped(fixture, name, pids):
        fixture = fixture.resolve(strict=True)
        if not str(fixture).startswith('/private/tmp/'):
            raise RuntimeError('unexpected_fixture_root')
        for pid in sorted(set(pids)):
            deadline = time.monotonic() + 15
            while True:
                observed = commands.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='], cwd=source, env=env, timeout=5)
                if observed.returncode == 1 and not observed.stdout.strip() and not observed.stderr.strip():
                    break
                if observed.returncode != 0 or observed.stderr.strip() or time.monotonic() >= deadline:
                    raise RuntimeError({'writer_exit_unconfirmed': pid, 'fixture': str(fixture)})
                time.sleep(0.1)
        for state in fixture.rglob('daemon.pid'):
            raise RuntimeError('daemon_pid_marker_retained: ' + str(state))
        copied = archive_fixture(fixture, output / ('fixture-' + name))
        archives.append({'original': str(fixture), 'archive': str(output / ('fixture-' + name)), **copied, 'original_retained': True})

    try:
        result['source_revision'] = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        if run(['git', 'diff', 'HEAD', '--', 'workbench/app/', 'workbench/src/', 'workbench/tests/']).stdout:
            raise RuntimeError('freeze_product_and_tests_before_running')
        if args.case == 'core':
            run([sys.executable, '-B', source / 'workbench/tests/test_t091_business_mutant.py',
                 output / 'classifier-preflight.json'], raw_name='classifier-preflight')
            classifier_check = json.loads((output / 'classifier-preflight.json').read_text(encoding='utf-8'))
            check('business_classifier_preflight', classifier_check['status'] == 'PASS')
            missing = [name for name in ['fixtures/pagination/CONTRACT.md', 'fixtures/pagination/pager.py',
                'evidence/2026-10-11-batch13/T-076/card-2/controller-decision-03.md',
                'evidence/2026-10-11-batch13/T-076/card-2/legacy-acceptance-hunks.diff'] if not (source / name).is_file()]
            if missing:
                raise RuntimeError({'core_materials_missing': missing, 'prepare': str(script_dir / 'prepare_core_materials.py')})
            from prepare_daemon_mutants import prepare
            from run_daemon_acceptance import business_mutant
            runner = source / 'workbench/tests/run_daemon_acceptance.py'
            identity = output / 'identity.json'
            write_json(identity, {key: result[key] for key in ['task', 'attempt', 'worker', 'worker_launch', 'approval_ref']})
            child_records = []
            for suite, count in [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1)]:
                child = output / suite
                run([sys.executable, '-B', runner, '--suite', suite, '--output', child, '--output-root', output,
                     '--label', suite, '--identity-file', identity], raw_name=suite)
                record = json.loads((child / 'run.json').read_text(encoding='utf-8'))
                check(suite + '_original_suite', record['status'] == 'PASS' and record['tests_run'] == count and
                      record['failures'] == record['errors'] == record['skipped'] == 0)
                child_records.append(record)
            manifest_path = prepare(output / 'mutants', task='T-091')
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            for name, suite, method in [('fence', 'coop', 'test_identity_gates_and_revocation_reject_old_verified_attempt'),
                ('cas', 'cas', 'test_external_write_between_read_and_cas_is_preserved'),
                ('lock', 'recovery', 'test_live_verify_excludes_verify_and_integrate')]:
                child = output / ('mutant-' + name)
                run([sys.executable, '-B', runner, '--suite', suite, '--test', method, '--mutant', name,
                     '--mutant-manifest', manifest_path, '--output', child, '--output-root', output,
                     '--label', 'mutant-' + name, '--identity-file', identity], expected=1, raw_name='mutant-' + name)
                proof = business_mutant(child, name, Path(manifest['mutants'][name]['core']))
                write_json(output / (name + '.business-counterexample.json'), proof)
                check(name + '_business_counterexample', proof['pass'] is True)
                child_records.append(json.loads((child / 'run.json').read_text(encoding='utf-8')))
            for index, record in enumerate(child_records):
                pids = [generation['pid'] for item in record['artifacts'] for generation in item['daemons'] if generation.get('pid')]
                archive_stopped(Path(record['artifact_root']), 'core-' + str(index), pids)
            archive_stopped(Path(manifest['root']), 'mutant-sources', [])
        else:
            child = output / 'original-test'
            if args.case == 'window':
                argv = [sys.executable, '-B', source / 'workbench/tests/test_electron_e2e.py', '--source', source,
                        '--output', child, '--stage', 'window']
                record_name = 'verdict.json'
            else:
                flag = {'runtime': '--runtime-probe', 'input-failures': '--input-failures', 'worker-inbox': '--worker-inbox'}[args.case]
                argv = [sys.executable, '-B', source / 'workbench/tests/test_t078_input_entry.py', '--source', source, '--output', child, flag]
                record_name = 'results.json'
            run(argv, raw_name='original-test')
            record = json.loads((child / record_name).read_text(encoding='utf-8'))
            required_count = {'window': 4, 'runtime': 12, 'input-failures': 11, 'worker-inbox': 14}[args.case]
            check('original_assertions', record['status'] == 'PASS' and len(record['checks']) == required_count and
                  all(c['status'] == 'PASS' for c in record['checks']))
            if args.case != 'window':
                check('original_cleanup', record['cleanup_complete'] is True)
            fixture = Path(record['fixture'])
            # Original tests save these records while the database is live.
            # Only recorded IDs are checked; no process discovery or DB writes.
            pids = recorded_writers(child, fixture)
            check('recorded_processes_available', bool(pids))
            archive_stopped(fixture, args.case, pids)
        archive_stopped(isolation, 'environment', [])
        result.update(status='PASS', archive_complete=True)
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if args.case != 'core':
            stages = output / 'original-test/window/stages.jsonl'
            if stages.exists():
                try:
                    rows = [json.loads(line) for line in stages.read_text(encoding='utf-8').splitlines()]
                    result['electron_start_attempts'] = sum(row.get('stage') == 'module_loaded' for row in rows)
                    result['electron_windows_created'] = sum(row.get('stage') == 'window_created' for row in rows)
                    result['screen_read_count'] = sum(row.get('stage') == 'screen_read' for row in rows)
                    result['capture_count'] = len(list((output / 'original-test/window').glob('*.png')))
                    protocol = output / 'original-test/window-driver.jsonl'
                    if protocol.exists():
                        result['driver_rpc_count'] = sum('request' in json.loads(line) and json.loads(line)['request']['command'] != 'close'
                            for line in protocol.read_text(encoding='utf-8').splitlines())
                    stdout = output / 'original-test/window-stdout.txt'
                    if stdout.exists():
                        result['observer_stdout_bytes'] = stdout.stat().st_size
                    if 'fixture' in locals():
                        result['controlled_receiver_start_attempts'] = len(list(fixture.rglob('receiver-started.json')))
                    if result['electron_start_attempts'] != 1 or result['electron_windows_created'] != 1 or result['screen_read_count'] > 1200:
                        result.update(status='INCOMPLETE', metrics_error='GUI process or screen-read budget mismatch')
                except (OSError, ValueError) as error:
                    result.update(status='INCOMPLETE', metrics_error=repr(error))
            else:
                result.update(status='INCOMPLETE', metrics_error='Electron stage evidence unavailable')
        else:
            result.update(electron_start_attempts=0, electron_windows_created=0, screen_read_count=0, capture_count=0)
        replay = shlex.join([sys.executable, str(Path(__file__).resolve()), '--source', str(source), '--case', args.case,
                            '--output', str(output) + '-replay-new', '--label', args.label + '-replay-new', '--approval-ref', '<本次新批准引用>'])
        manifest = {'original': [row['original'] for row in archives], 'archive': [row['archive'] for row in archives],
                    'bytes': sum(row['bytes'] for row in archives), 'fixtures': archives, 'replay': replay,
                    'scope': 'Only stopped fixtures copied; failure leaves originals in place', 'originals_retained': True}
        write_json(script_dir / f'{args.label}.archive.json', manifest)
        result['archive_manifest'] = str(script_dir / f'{args.label}.archive.json')
        write_json(output / 'run.json', result); write_json(script_dir / f'{args.label}.run.json', result)
    print(json.dumps({'status': result['status'], 'case': args.case, 'archive_complete': result['archive_complete'],
        'checks': len(result['checks']), 'error': result.get('error'), 'run': str(output / 'run.json')}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
