"""Real pipes and a caller-owned non-GUI process exercise the Electron harness.

Failure modes: buffered lines stranded behind select(), partial lines blocking
past the deadline, UTF-8 split across reads, missing raw bytes, and a startup
process surviving cleanup. This test does not start Electron or a daemon.
"""
import argparse
import io
import json
import os
from pathlib import Path
import runpy
import selectors
import signal
import subprocess
import sys
import time
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--known-bad', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    current = runpy.run_path(str(Path(__file__).with_name('electron_client.py')))['ElectronClient']
    old = runpy.run_path(str(args.known_bad))['ElectronClient']
    result = {'status': 'INCOMPLETE', 'argv': sys.argv, 'electron_started': False, 'observations': []}
    payload = b'{"id":1,"text":"first"}\n{"id":2,"text":"second"}\n'
    try:
        for label, klass in [('known_bad', old), ('candidate', current)]:
            read_fd, write_fd = os.pipe()
            reader = os.fdopen(read_fd, 'rb', buffering=0)
            if label == 'known_bad':
                reader = io.TextIOWrapper(reader, encoding='utf-8')
            else:
                os.set_blocking(read_fd, False)
            client = klass.__new__(klass)
            client.log = args.output / (label + '-protocol.jsonl')
            client.stdout = (args.output / (label + '-stdout.bin')).open('xb')
            client.process = SimpleNamespace(stdout=reader)
            client.buffer = bytearray()
            client.selector = selectors.DefaultSelector()
            client.selector.register(reader, selectors.EVENT_READ)
            try:
                os.write(write_fd, payload)
                assert client.receive(0.2) == {'id': 1, 'text': 'first'}
                try:
                    second = client.receive(0.05)
                except TimeoutError:
                    assert label == 'known_bad', 'Current reader stranded a complete buffered line'
                    result['observations'].append({'case': label, 'second_line': 'timeout', 'known_bad_rejected': True})
                else:
                    assert label == 'candidate', 'Known-bad reader unexpectedly passed the regression case'
                    assert second == {'id': 2, 'text': 'second'}
                    prefix = b'{"id":3,"text":"\xe4'
                    suffix = b'\xb8\xad"}\n'
                    os.write(write_fd, prefix)
                    began = time.monotonic()
                    try:
                        client.receive(0.05)
                    except TimeoutError:
                        elapsed = time.monotonic() - began
                        assert elapsed < 0.5, 'Partial line ignored its deadline'
                    else:
                        raise AssertionError('Incomplete JSON was returned as a response')
                    os.write(write_fd, suffix)
                    assert client.receive(0.2) == {'id': 3, 'text': '中'}
                    assert (args.output / (label + '-stdout.bin')).read_bytes() == payload + prefix + suffix
                    result['observations'].append({'case': label, 'coalesced_lines': 'PASS',
                                                   'partial_line_deadline': elapsed, 'split_utf8': 'PASS', 'raw_bytes': 'PASS'})
            finally:
                client.selector.close(); reader.close(); os.close(write_fd); client.stdout.close()
        # A modal Electron error can ignore a graceful exit. A local child that
        # ignores SIGTERM proves that cleanup uses the owned process group.
        argv = [sys.executable, '-u', '-c',
                'import os,signal; signal.signal(signal.SIGTERM,signal.SIG_IGN); print(os.getpgrp(),flush=True); signal.pause()']
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, start_new_session=True)
        watcher = selectors.DefaultSelector(); watcher.register(process.stdout, selectors.EVENT_READ)
        client = current.__new__(current)
        client.log = args.output / 'cleanup-protocol.jsonl'; client.process = process
        try:
            assert watcher.select(2), 'Own child did not reach the signal barrier'
            group = int(process.stdout.readline())
            assert group == process.pid and group != os.getpgrp()
            client.kill_owned()
            assert process.returncode == -signal.SIGKILL
            result['observations'].append({'case': 'owned_process_cleanup', 'argv': argv, 'pid': process.pid,
                                           'pgid': group, 'exit': process.returncode, 'status': 'PASS'})
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
            watcher.close(); process.stdout.close()
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = repr(error)
        raise
    finally:
        (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
