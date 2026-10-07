#!/usr/bin/env python3
"""Start and stop only the recorded T-034 process group; preserve every log."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

evidence = Path(__file__).resolve().parent
action, name, *args = sys.argv[1:]
state_path = evidence / f'{name}-service.json'
if action == 'start':
    cwd, *argv = args
    assert not state_path.exists()
    with (evidence / f'{name}-service.log').open('x', encoding='utf-8') as output:
        # Python 3.9 on macOS uses a process-relative monotonic origin.
        # Persist the wall-clock origin for observations in a later process.
        started = time.time()
        child = subprocess.Popen(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
    state = {'cwd': cwd, 'argv': argv, 'pid': child.pid, 'pgid': child.pid,
             'started_epoch': started,
             'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with state_path.open('x', encoding='utf-8') as output:
        json.dump(state, output, indent=2)
        output.write('\n')
elif action == 'http':
    state = json.loads(state_path.read_text(encoding='utf-8'))
    results = []
    for url in args:
        deadline = time.monotonic() + 180
        while True:
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    body = response.read()
                    status = response.status
                if status != 200:
                    raise RuntimeError(str(status))
                result = {'url': url, 'status': status,
                          'seconds_after_start': time.time() - state['started_epoch']}
                output_path = evidence / f'{name}-http-{len(results)}.txt'
                with output_path.open('xb') as output:
                    output.write(body)
                results.append(result)
                break
            except (OSError, RuntimeError) as error:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f'{url} was not ready: {error}') from error
                time.sleep(0.25)
    state['http'] = results
    state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
elif action == 'window':
    state = json.loads(state_path.read_text(encoding='utf-8'))
    deadline = time.monotonic() + 600
    while True:
        windows = json.loads(subprocess.check_output(args, text=True))
        if windows:
            state['first_visible_window'] = windows
            state['window_seconds_after_start'] = time.time() - state['started_epoch']
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('Synara Cua did not show a window in 600 seconds')
        time.sleep(0.25)
    state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
elif action == 'stop':
    state = json.loads(state_path.read_text(encoding='utf-8'))
    pgid = state['pgid']
    processes = subprocess.check_output(['ps', '-axo', 'pid,ppid,pgid,command'], text=True)
    owned = [line for line in processes.splitlines()[1:]
             if len(line.split(None, 3)) == 4 and int(line.split(None, 3)[2]) == pgid]
    state['owned_before_stop'] = owned
    assert owned, 'recorded process group is no longer live; inspect it instead of signaling'
    assert any(str(state['pid']) == line.split()[0] for line in owned), 'group leader changed'
    os.killpg(pgid, signal.SIGTERM)
    state['stop_requested_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    time.sleep(2)
    state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
else:
    raise SystemExit('start | http | stop')
print(json.dumps(state))
