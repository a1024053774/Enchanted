"""Prove the deterministic receiver starts when its isolated HOME is empty."""
import argparse
import json
import os
import pty
import signal
import subprocess
import tempfile
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
RECEIVER_SOURCE = SOURCE / 'workbench/tests/t078_native_receiver.c'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=False, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='t078-receiver-launch-', dir='/private/tmp')).resolve()
    home = root / 'home'
    home.mkdir()
    binary = root / 'codex-receiver'
    compile_result = subprocess.run(['/usr/bin/clang', '-Wall', '-Wextra', '-Werror', '-std=c11',
                                     str(RECEIVER_SOURCE), '-o', str(binary)], capture_output=True, text=True)
    record = {'status': 'INCOMPLETE', 'root': str(root), 'compile_exit': compile_result.returncode,
              'home_sessions_preexisting': (home / 'sessions').exists(), 'process_pid': None}
    process_pid = None
    master = None
    try:
        assert compile_result.returncode == 0 and not (home / 'sessions').exists()
        process_pid, master = pty.fork()
        if process_pid == 0:
            env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_'))}
            env.update(CODEX_HOME=str(home), TERM='xterm-256color')
            os.execve(str(binary), [str(binary), '--no-daemon'], env)
        record['process_pid'] = process_pid
        data = bytearray(); deadline = time.monotonic() + 2
        while b'T078_DETERMINISTIC_RECEIVER_READY' not in data and time.monotonic() < deadline:
            try:
                data.extend(os.read(master, 4096))
            except OSError:
                break
            time.sleep(.01)
        record['ready_marker'] = b'T078_DETERMINISTIC_RECEIVER_READY' in data
        record['sessions_created'] = (home / 'sessions').is_dir()
        record['started_file'] = (home / 'receiver-started.json').is_file()
        record['status'] = 'PASS' if record['ready_marker'] and record['sessions_created'] and record['started_file'] else 'INCOMPLETE'
    finally:
        if master is not None:
            os.close(master)
        if process_pid is not None:
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                waited, _ = os.waitpid(process_pid, os.WNOHANG)
                if waited == process_pid: break
                time.sleep(.02)
            else:
                os.kill(process_pid, signal.SIGKILL); os.waitpid(process_pid, 0)
        import shutil
        shutil.rmtree(root, ignore_errors=False)
        record['root_removed'] = True
        (args.output / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'ready_marker': record.get('ready_marker'),
                      'sessions_created': record.get('sessions_created'), 'root_removed': record['root_removed']}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
