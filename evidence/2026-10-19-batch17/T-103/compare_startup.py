#!/usr/bin/env python3
"""Four no-task startup controls. No install, build, daemon or model calls.

Hold the product build, driver, environment and pipe policy fixed. Vary only
the selected installed Electron and whether it runs the bare product entry or
the driver. A 30-second deadline stays a failure even if cleanup later exits.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(pid):
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,ppid=,uid=,lstart=,command='],
                            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, text=True, capture_output=True, timeout=5)
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    assert result.returncode == 0 and not result.stderr.strip(), 'Cannot verify owned process'
    fields = result.stdout.strip().split(maxsplit=8)
    assert len(fields) == 9 and int(fields[0]) == pid
    return {'pid': pid, 'ppid': int(fields[1]), 'uid': int(fields[2]),
            'started': ' '.join(fields[3:8]), 'command': fields[8]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--preflight', action='store_true', help='Read both installations and xattr metadata without launching Electron')
    args = parser.parse_args()
    disk = Path('/Volumes/WD-Elements')
    assert disk.is_mount(), 'External disk must be mounted; no fallback'
    output = args.output.resolve()
    if not args.preflight:
        assert output.is_relative_to(disk)
    output.mkdir(parents=True, exist_ok=False)
    source = Path('/Users/luckye/Documents/Code/a2a-wt-t103')
    previous = disk / 'a2a-evidence/2026-10-19-batch17/T-103/run-20261019T052842Z'
    manifest = json.loads((previous / 'red-build.json').read_text(encoding='utf-8'))
    product = Path(manifest['main'])
    driver = source / 'workbench/tests/t103_picker_driver.mjs'
    frozen_driver = previous / 'source-snapshot/workbench/tests/t103_picker_driver.mjs'
    assert driver.read_bytes() == frozen_driver.read_bytes(), 'Driver changed; the control must use the failed candidate unchanged'
    product_bytes, driver_bytes = product.read_bytes(), driver.read_bytes()
    if not args.preflight:
        (output / 'driver-under-test.mjs').write_bytes(driver_bytes)  # Record only; execute its original path in every driver case.
    fixture = None if args.preflight else Path(tempfile.mkdtemp(prefix='t103compare-', dir='/tmp')).resolve()
    temporary = None if args.preflight else output / 'tmp'
    if temporary is not None:
        temporary.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    for key in ['ELECTRON_RUN_AS_NODE', 'NODE_OPTIONS', 'ELECTRON_OVERRIDE_DIST_PATH']:
        env.pop(key, None)
    env['electron_config_cache'] = str(disk / 'a2a-electron-cache')
    if temporary is not None:
        env.update(TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary))
    roots = {
        'internal': Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron'),
        'external': disk / 'a2a-evidence/2026-10-19-batch17/T-103/baseline-20261019T052842Z/workbench/node_modules/electron',
    }
    report = {'status': 'INCOMPLETE', 'scope': 'Metadata preflight only; no Electron process' if args.preflight else 'Four no-task startup controls only; no T-103 business acceptance',
              'product': str(product), 'driver': str(driver), 'fixture': str(fixture) if fixture else None, 'output': str(output),
              'deadline_seconds': 30, 'versions': {}, 'cases': [], 'model_calls': 0,
              'mutation_policy': 'No install/build/relocation/xattr changes; only terminate verified child processes created by this probe'}
    child_exit_confirmed = True
    try:
        for label, root in roots.items():
            package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
            dist_version = (root / 'dist/version').read_text(encoding='utf-8').strip().removeprefix('v')
            executable = (root / 'dist' / (root / 'path.txt').read_text(encoding='utf-8').strip()).resolve(strict=True)
            assert os.access(executable, os.X_OK)
            argv = [str(executable), '-p', 'process.versions.electron']
            xattr_argv = ['/usr/bin/xattr', '-l', str(root / 'dist/Electron.app')]
            xattrs = subprocess.run(xattr_argv, text=True, encoding='utf-8', errors='backslashreplace',
                                    capture_output=True, timeout=10)
            value = {'package': package['version'], 'dist': dist_version, 'argv': argv,
                     'device': executable.stat().st_dev,
                     'executable': str(executable), 'executable_permission': True,
                     'app_xattrs': {'argv': xattr_argv, 'exit': xattrs.returncode,
                                    'stdout': xattrs.stdout, 'stderr': xattrs.stderr}}
            report['versions'][label] = value
            save(output / 'run.json', report)
            assert xattrs.returncode == 0, value['app_xattrs']
            assert package['version'] == dist_version == '43.4.1', value
            if args.preflight:
                value['runtime_probe'] = 'NOT_RUN'
                continue
            try:
                result = subprocess.run(argv, env=dict(env, ELECTRON_RUN_AS_NODE='1'), text=True, capture_output=True, timeout=30)
            except subprocess.TimeoutExpired as error:
                value.update(deadline_reached=True, stdout=repr(error.stdout), stderr=repr(error.stderr))
                raise
            value.update(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
            assert result.returncode == 0 and result.stdout.strip() == package['version'] == dist_version == '43.4.1', value
            roots[label] = executable
        if args.preflight:
            report.update(status='PASS', startup_cases='NOT_RUN', python_executable=sys.executable,
                          python_version=sys.version)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        for location in ['internal', 'external']:
            for mode in ['bare', 'driver']:
                label = location + '-' + mode
                case = output / label; case.mkdir()
                state, user_data = fixture / (label + '-state'), fixture / (label + '-ui')
                argv = [str(roots[location]), str(product), '--state', str(state), '--user-data', str(user_data)]
                if mode == 'driver':
                    argv = [str(roots[location]), str(driver), '--build', manifest['out'], '--state', str(state),
                            '--user-data', str(user_data), '--output', str(case)]
                record = {'case': label, 'argv': argv, 'expected_exit': 1, 'status': 'INCOMPLETE',
                          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
                report['cases'].append(record)
                print(json.dumps({'starting': label, 'argv': argv}), flush=True)
                began = time.monotonic()
                with (case / 'stderr.txt').open('xb') as stderr, (case / 'stdout.txt').open('xb') as stdout:
                    process = subprocess.Popen(argv, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=stderr, start_new_session=True, bufsize=0)
                    child_exit_confirmed = False
                    record['pid'] = process.pid
                    save(case / 'launch.json', record)
                    owner = identity(process.pid)
                    record['owner'] = owner
                    save(case / 'owner.json', owner)
                    selector = selectors.DefaultSelector()
                    os.set_blocking(process.stdout.fileno(), False)
                    selector.register(process.stdout, selectors.EVENT_READ)

                    def drain(wait):
                        for key, _ in selector.select(wait):
                            chunk = os.read(key.fileobj.fileno(), 65536)
                            if chunk:
                                stdout.write(chunk); stdout.flush()
                            else:
                                selector.unregister(key.fileobj)

                    try:
                        while process.poll() is None and time.monotonic() - began < 30:
                            drain(.05)
                        record.update(observation_seconds=time.monotonic() - began,
                                      deadline_reached=process.poll() is None,
                                      exit_before_cleanup=process.poll())
                    finally:
                        if process.poll() is None:
                            assert owner and owner['uid'] == os.getuid() and identity(process.pid) == owner, 'Owner changed; retain process'
                            record['cleanup_signal'] = 'SIGTERM'
                            save(case / 'before-cleanup.json', record)
                            os.kill(process.pid, signal.SIGTERM)
                            deadline = time.monotonic() + 5
                            while process.poll() is None and time.monotonic() < deadline:
                                drain(.05)
                            if process.poll() is None:
                                raise RuntimeError('Owned probe child did not stop; retain it, no SIGKILL, no next case')
                        process.wait(timeout=5)
                        child_exit_confirmed = True
                        end = time.monotonic() + 2
                        while selector.get_map() and time.monotonic() < end:
                            drain(.05)
                        record.update(exit=process.returncode, output_drained=not selector.get_map())
                        selector.close(); process.stdin.close(); process.stdout.close()
                stderr_text = (case / 'stderr.txt').read_text(encoding='utf-8', errors='replace')
                stdout_text = (case / 'stdout.txt').read_text(encoding='utf-8', errors='replace')
                reason = 'Absolute data paths and a task are required'
                message_seen = reason in stderr_text if mode == 'bare' else False
                if mode == 'driver':
                    replies = []
                    non_protocol = []
                    for line in stdout_text.splitlines():
                        try:
                            replies.append(json.loads(line))
                        except json.JSONDecodeError as error:
                            non_protocol.append({'line': line, 'error': str(error)})
                    record['replies'] = replies
                    record['non_protocol_stdout'] = non_protocol
                    message_seen = not non_protocol and any(item.get('startup_error') == 'Error: ' + reason for item in replies if isinstance(item, dict))
                    trace = case / 'driver.ndjson'
                    record['stages'] = [json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()] if trace.exists() else []
                record.update(expected_reason_seen=message_seen,
                              status='PASS' if not record['deadline_reached'] and record['exit_before_cleanup'] == 1 and message_seen else 'NO_GO')
                save(case / 'result.json', record)
                save(output / 'run.json', report)
                print(json.dumps({'case': label, 'status': record['status'], 'deadline_reached': record['deadline_reached'],
                                  'exit_before_cleanup': record['exit_before_cleanup']}), flush=True)
        assert product.read_bytes() == product_bytes and driver.read_bytes() == driver_bytes, 'Source changed during controls'
        status = {item['case']: item['status'] for item in report['cases']}
        notes = []
        if all(value == 'PASS' for value in status.values()):
            notes.append('This control did not reproduce the failure; compare the original observer/environment before changing the product.')
        if status['internal-bare'] == status['external-bare'] == 'PASS' and any(status[key] != 'PASS' for key in ['internal-driver', 'external-driver']):
            notes.append('Both bare product exits work; the driver/handshake path changes the result.')
        if status['internal-bare'] != status['external-bare']:
            notes.append('The binary-copy/location dimension differs. This does not separate copy contents from disk location.')
        if status['internal-bare'] != 'PASS' and status['external-bare'] != 'PASS':
            notes.append('The bare exit path also fails; the driver alone does not explain all observations.')
        report.update(status='PASS' if all(value == 'PASS' for value in status.values()) else 'INCOMPLETE', interpretation=notes)
    except Exception as error:
        report.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            if fixture is not None and child_exit_confirmed:
                archived = output / 'fixtures'
                shutil.copytree(fixture, archived)
                def inventory(root):
                    return sorted((str(path.relative_to(root)), path.stat().st_size) for path in root.rglob('*') if path.is_file())
                before = inventory(fixture)
                assert before == inventory(archived), 'Fixture archive file counts/bytes differ'
                report['fixture_archive'] = {'original': str(fixture), 'archive': str(archived),
                                             'files': len(before), 'bytes': sum(size for _, size in before)}
                shutil.rmtree(fixture)
            elif fixture is not None:
                report['fixture_policy'] = 'Child exit unconfirmed; retain original fixture and stop further controls.'
        except (OSError, AssertionError) as error:
            report.update(status='INCOMPLETE', archive_error=repr(error))
        save(output / 'run.json', report)
        dest = source / 'evidence/2026-10-19-batch17/T-103'
        save(dest / (output.name + '-summary.json'), report)
        if not args.preflight:
            save(dest / (output.name + '.archive.json'), {'original': str(fixture), 'archive': str(output),
                 'bytes': sum(path.stat().st_size for path in output.rglob('*') if path.is_file()),
                 'replay': 'bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-06-COMPARE-STARTUP.sh'})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
