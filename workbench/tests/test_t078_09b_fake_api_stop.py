"""Real-process stop probe for the loopback 09B fake API."""
import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
FAKE_API = SOURCE / 'workbench/tests/t078_09b_fake_api.py'


def wait_ready(root, process):
    ready = root / 'api-ready.json'
    deadline = time.monotonic() + 5
    while not ready.exists():
        if process.poll() is not None:
            raise RuntimeError(f'fake API exited before readiness: {process.returncode}')
        if time.monotonic() > deadline:
            raise RuntimeError('fake API readiness timeout')
        time.sleep(.02)
    payload = json.loads(ready.read_bytes())
    if payload.get('pid') != process.pid:
        raise RuntimeError({'ready_pid': payload.get('pid'), 'process_pid': process.pid})
    return payload


def wait_exit(process, timeout):
    deadline = time.monotonic() + timeout
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(.02)
    return process.poll()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect', choices=['red', 'green'], required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=False, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='t078-fake-api-stop-', dir='/private/tmp')).resolve()
    process = subprocess.Popen(
        [sys.executable, '-B', str(FAKE_API), '--root', root, '--role', 'probe', '--port', '0'],
        cwd=SOURCE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
    )
    record = {'status': 'INCOMPLETE', 'expect': args.expect, 'root': str(root), 'pid': process.pid,
              'signals_sent': [], 'timeout_seconds': 2.0}
    try:
        record['ready'] = wait_ready(root, process)
        os.kill(process.pid, signal.SIGTERM)
        record['signals_sent'].append({'pid': process.pid, 'signal': 'SIGTERM'})
        code = wait_exit(process, 2.0)
        record['exit_code_after_sigterm_2s'] = code
        if args.expect == 'red':
            record['status'] = 'PASS' if code is None else 'INCOMPLETE'
            record['verdict'] = 'RED_TIMEOUT' if code is None else 'unexpected_exit'
            if code is None:
                os.kill(process.pid, signal.SIGKILL)
                record['signals_sent'].append({'pid': process.pid, 'signal': 'SIGKILL', 'cleanup': True})
                process.wait(timeout=5)
        else:
            record['status'] = 'PASS' if code is not None else 'INCOMPLETE'
            record['verdict'] = 'GREEN_EXIT_WITHIN_2S' if code is not None else 'still_alive'
        record['final_exit_code'] = process.poll()
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGKILL)
            record['signals_sent'].append({'pid': process.pid, 'signal': 'SIGKILL', 'cleanup': True})
            process.wait(timeout=5)
        record['stderr'] = process.stderr.read() if process.stderr else ''
        record['stdout'] = process.stdout.read() if process.stdout else ''
        record['root_removed'] = False
        import shutil
        shutil.rmtree(root, ignore_errors=False)
        record['root_removed'] = True
        (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'expect': args.expect, 'verdict': record.get('verdict'),
                      'signals_sent': record['signals_sent'], 'root_removed': record['root_removed']}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
