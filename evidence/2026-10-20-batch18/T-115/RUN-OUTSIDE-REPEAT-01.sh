#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
TASK_ROOT=${SCRIPT_DIR:h:h:h}
OUT_ROOT=${1:?Pass a fresh absolute /private/tmp output directory}
ELECTRON_DIST=/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist

unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C
export PYTHONDONTWRITEBYTECODE=1

cd "$TASK_ROOT"
test -d workbench/node_modules || {
  print -u2 -- "Missing workbench/node_modules; run: cd '$TASK_ROOT' && npm ci --ignore-scripts"
  exit 2
}
test -x "$ELECTRON_DIST/Electron.app/Contents/MacOS/Electron" || {
  print -u2 -- "Electron executable is missing from $ELECTRON_DIST"
  exit 2
}
test "$(cat "$ELECTRON_DIST/version")" = "43.4.1" || {
  print -u2 -- "Expected Electron 43.4.1 in $ELECTRON_DIST"
  exit 2
}

/usr/bin/python3 - "$TASK_ROOT" "$OUT_ROOT" "$ELECTRON_DIST" <<'PY'
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback


ATTEMPTS = 10
CPU_BURNERS = 10
LOAD_SETTLE_SECONDS = 15
RUN_TIMEOUT_SECONDS = 1800
TARGET = 'Foreground after reconnect clears badge'


root = Path(sys.argv[1]).resolve(strict=True)
out = Path(sys.argv[2]).resolve()
electron_dist = Path(sys.argv[3]).resolve(strict=True)
if out == Path('/private/tmp') or Path('/private/tmp') not in out.parents:
    raise SystemExit('Output directory must be a fresh directory below /private/tmp')
if out.exists():
    raise SystemExit('Output directory already exists; use a fresh path: ' + str(out))
out.mkdir(parents=True)


env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'):
    env.pop(key, None)


def command_output(argv, cwd=root):
    result = subprocess.run(
        [str(value) for value in argv],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(dict(argv=argv, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return result.stdout.strip()


report = {
    'schema': 1,
    'task': 'T-115',
    'attempt': 'a1',
    'status': 'INCOMPLETE',
    'configuration': {
        'max_attempts': ATTEMPTS,
        'cpu_burners': CPU_BURNERS,
        'load_settle_seconds': LOAD_SETTLE_SECONDS,
        'run_timeout_seconds': RUN_TIMEOUT_SECONDS,
        'stop_after_target_failure': True,
        'target': TARGET,
        'electron_dist': str(electron_dist),
        'command_template': [
            '/usr/bin/python3',
            '-B',
            'workbench/tests/run_t110_notifications.py',
            '--electron-dist',
            str(electron_dist),
            '--summary',
            '<attempt-specific-json>',
        ],
    },
    'environment': {},
    'load': {},
    'attempts': [],
    'target_failure': None,
}


def read_green(summary):
    if not summary.exists():
        return None
    value = json.loads(summary.read_text(encoding='utf-8'))
    green = next((case.get('result') for case in value.get('runs', []) if case.get('label') == 'green'), None)
    return value, green


def classify(green):
    timeline = list(green.get('native_focus_timeline') or [])
    foreground = [
        index for index, entry in enumerate(timeline)
        if entry.get('event') == 'command:before' and entry.get('command') == 'foreground'
    ]
    if not foreground:
        return {
            'classification': 'INCOMPLETE_NO_FOREGROUND_TIMELINE',
            'reason': 'The green failure has no command:before foreground entry.',
        }
    tail = timeline[foreground[-1] + 1:]
    focus_samples = [entry for entry in tail if 'focused' in entry]
    failure_native = (green.get('failure_view') or {}).get('native_focus')
    final_native = failure_native or (focus_samples[-1] if focus_samples else None)
    if final_native is None:
        return {
            'classification': 'INCOMPLETE_NO_POST_FOREGROUND_FOCUS_STATE',
            'tail': tail,
        }
    focused = final_native.get('focused') is True and final_native.get('focused_window') is not None
    badge = final_native.get('badge')
    if focused and badge == 1:
        classification = 'FOCUSED_BADGE_ONE_PRODUCT_OR_NATIVE_EVENT_PATH'
    elif not focused:
        classification = 'FOCUS_NOT_ACQUIRED_OR_LOST_TEST_ACTION'
    else:
        classification = 'INCOMPLETE_UNEXPECTED_FINAL_STATE'
    return {
        'classification': classification,
        'final_foreground_index': foreground[-1],
        'post_foreground_timeline': tail,
        'focus_samples': focus_samples,
        'final_native_focus': final_native,
    }


def stop_load(processes):
    states = []
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + 5
    for process in processes:
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    for process in processes:
        try:
            returncode = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            returncode = None
        states.append({'pid': process.pid, 'returncode': returncode})
    return states


loads = []
try:
    report['environment'] = {
        'source_head': command_output(['git', 'rev-parse', 'HEAD']),
        'source_status': command_output(['git', 'status', '--porcelain']).splitlines(),
        'python': command_output(['/usr/bin/python3', '--version']),
        'node': command_output(['node', '--version']),
        'electron_version': (electron_dist / 'version').read_text(encoding='utf-8').strip(),
        'cpu_count': os.cpu_count(),
        'initial_load_average': list(os.getloadavg()),
    }
    if report['environment']['source_status']:
        raise RuntimeError('Refusing to run from a dirty worktree; commit the candidate first.')

    for _ in range(CPU_BURNERS):
        loads.append(subprocess.Popen(
            ['/usr/bin/python3', '-B', '-c', 'while True: pass'],
            cwd=out,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        ))
    time.sleep(LOAD_SETTLE_SECONDS)
    report['load'] = {
        'pid_pgid': [{'pid': process.pid, 'pgid': os.getpgid(process.pid)} for process in loads],
        'load_average_after_start': list(os.getloadavg()),
        'cleanup': [],
    }

    for attempt in range(1, ATTEMPTS + 1):
        summary = out / ('attempt-%02d.json' % attempt)
        log = out / ('attempt-%02d.log' % attempt)
        if summary.exists() or log.exists():
            raise RuntimeError('Attempt output path is not fresh: ' + str(summary))
        command = [
            '/usr/bin/python3',
            '-B',
            str(root / 'workbench/tests/run_t110_notifications.py'),
            '--electron-dist',
            str(electron_dist),
            '--summary',
            str(summary),
        ]
        started = time.monotonic()
        timed_out = False
        with log.open('xb') as stream:
            process = subprocess.Popen(
                command,
                cwd=root,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=RUN_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=10)
                returncode = process.returncode
        duration = round(time.monotonic() - started, 3)
        record = {
            'number': attempt,
            'summary': str(summary),
            'log': str(log),
            'argv': command,
            'exit': returncode,
            'timed_out': timed_out,
            'duration_seconds': duration,
            'load_average_at_start': list(os.getloadavg()),
        }
        parsed = read_green(summary)
        if parsed is None:
            record.update(top_status='INCOMPLETE', green_status=None, target_failure=False,
                          error='T-110 entry produced no summary')
        else:
            value, green = parsed
            green_status = green.get('status') if green else None
            green_error = green.get('error') if green else 'No green case in summary'
            target_failure = bool(
                green is not None
                and green_status != 'PASS'
                and TARGET in json.dumps(green_error, ensure_ascii=False)
            )
            record.update(
                top_status=value.get('status'),
                source_head=value.get('source_head'),
                green_status=green_status,
                green_error=green_error,
                green_timeline_entries=len((green or {}).get('native_focus_timeline') or []),
                target_failure=target_failure,
            )
            if target_failure:
                report['target_failure'] = {
                    'attempt': attempt,
                    'summary': str(summary),
                    'green': green,
                    'classification': classify(green),
                }
        report['attempts'].append(record)
        print(json.dumps({
            'attempt': attempt,
            'exit': returncode,
            'timed_out': timed_out,
            'green_status': record.get('green_status'),
            'target_failure': record['target_failure'],
        }, ensure_ascii=False), flush=True)
        if record['target_failure']:
            report['status'] = 'REPRODUCED'
            break

    if report['target_failure'] is None:
        infrastructure_failure = any(
            item['timed_out']
            or item.get('top_status') != 'PASS'
            or item.get('green_status') != 'PASS'
            for item in report['attempts']
        )
        report['status'] = 'INCOMPLETE' if infrastructure_failure else 'NOT_REPRODUCED'
except Exception as error:
    report.update(status='INCOMPLETE', error=str(error), traceback=traceback.format_exc())
finally:
    report['load']['cleanup'] = stop_load(loads)
    report['load']['load_average_after_cleanup'] = list(os.getloadavg())
    (out / 'summary.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps({
        'status': report['status'],
        'attempts_completed': len(report['attempts']),
        'target_failure': report['target_failure'] is not None,
        'summary': str(out / 'summary.json'),
        'error': report.get('error'),
    }, ensure_ascii=False))

raise SystemExit(0 if report['status'] in ('REPRODUCED', 'NOT_REPRODUCED') else 1)
PY
