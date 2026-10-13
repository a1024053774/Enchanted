"""Deterministic trace bytes through the real daemon and Electron window.

The controller authorized this offline fixture in T-075-4 decision 02. It uses
a copy of a real stopped launch, and never claims that the supplied trace came
from a live PTY. No model or worker process is started.
"""
import argparse
import base64
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import uuid

from command_evidence import CommandLog, command_json
from electron_client import ElectronClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, recorded = args.source.resolve(), args.recorded.resolve()
    args.output.mkdir(parents=True, exist_ok=False); output = args.output.resolve()
    fixture = Path(tempfile.mkdtemp(prefix='a4off-', dir='/tmp')).resolve()
    state = fixture / 'state'; state.mkdir()
    launch = json.loads((recorded / 'launch-record.json').read_text(encoding='utf-8'))
    shutil.copyfile(recorded / 'state.sqlite3', state / 'state.sqlite3')
    directory = state / 'traces' / launch['id']; directory.mkdir(parents=True)
    trace = directory / 'pty.raw'
    nonce = uuid.uuid4().hex[:12]
    expected = '[offline trace fixture] 中文跨块🙂 ' + nonce
    normal_text = '[normal buffer fixture] ' + nonce
    data = bytearray(('\x1b[2J\x1b[H' + normal_text + '\r\n\x1b[?1049h\x1b[2J\x1b[H[offline trace fixture] ').encode('utf-8'))
    data.extend(b'\0' * (65535 - len(data))); data.extend('中'.encode('utf-8'))
    data.extend(b'\0' * (131071 - len(data))); data.extend('文'.encode('utf-8'))
    data.extend(('跨块🙂 ' + nonce + '\r\ndone accepted idle 等确认\r\n').encode('utf-8'))
    data.extend(b'\x1b]0;done accepted idle\x07')
    trace.write_bytes(data)
    (output / 'expected-trace.bin').write_bytes(data)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    cli = ['node', source / 'workbench/src/gates/cli.ts', '--state', state]
    verdict = {'status': 'INCOMPLETE', 'fixture_kind': 'offline controlled trace', 'model_turns': 0,
               'recorded_source': str(recorded), 'fixture': str(fixture), 'launch': launch['id'],
               'expected_text': expected, 'utf8_start_offsets': [65535, 131071], 'trace_bytes': len(data),
               'electron_started': False}
    started = False; pid = None; window = None
    commands = CommandLog(output)

    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, *, check=True, timeout=60):
        result = commands.run(argv, cwd=source, env=env, timeout=timeout)
        if check and result.returncode:
            raise AssertionError({'public_entry_failed': result.evidence})
        return result

    def call(command, *values, error=None):
        result = run([*cli, command, *values], check=error is None)
        assert result.returncode == (1 if error is not None else 0), result.evidence
        value = command_json(result)
        if error is not None:
            assert result.returncode == 1 and value.get('error') == error, value
        else:
            assert value.get('ok') is True, value
        return value

    def received_bytes():
        received = bytearray()
        for line in (output / 'window/received.ndjson').read_bytes().splitlines(keepends=True):
            assert line.endswith(b'\n'), 'Checkpoint must leave only complete output responses'
            chunk = json.loads(line); block = base64.b64decode(chunk['data_base64'], validate=True)
            assert chunk['start_offset'] == len(received) and chunk['next_offset'] == len(received) + len(block)
            received.extend(block)
        return received

    try:
        with closing(sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            original_task = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (launch['task'],)).fetchone()[0])
            original_inputs = db.execute('SELECT count(*) FROM user_inputs').fetchone()[0]
        assert original_task['state'] == 'claimed' and original_task['current_attempt']['attempt_id'] == launch['attempt']
        build = command_json(run(['node', source / 'workbench/app/build.mjs', '--slot', 't0754-offline-' + fixture.name], timeout=120))
        save('build.json', build)
        pid = call('daemon_start')['pid']; started = True
        pane = call('pane_status', '--thread', launch['thread'])
        assert pane['state'] == 'unknown' and pane['lifecycle'] == 'interrupted' and pane['historical'] is True
        cursor = 0; actual = bytearray(); chunks = []
        while cursor < len(data):
            value = call('pane_output', '--launch', launch['id'], '--offset', str(cursor), '--max-bytes', '65536')
            block = base64.b64decode(value['data_base64'], validate=True)
            assert value['start_offset'] == cursor and value['next_offset'] == cursor + len(block)
            assert value['total_bytes'] == len(data) and block
            actual.extend(block); chunks.append({'offset': cursor, 'bytes': len(block)}); cursor = value['next_offset']
        (output / 'cli-trace.bin').write_bytes(actual)
        assert actual == data
        save('cli-chunks.json', chunks)
        assert [chunk['offset'] for chunk in chunks] == [0, 65536, 131072]
        for offset, expected_bytes in [(65535, '中'.encode('utf-8')), (131071, '文'.encode('utf-8'))]:
            split = b''
            for position in range(offset, offset + 3):
                value = call('pane_output', '--launch', launch['id'], '--offset', str(position), '--max-bytes', '1')
                split += base64.b64decode(value['data_base64'], validate=True)
            assert split == expected_bytes
        call('pane_output', '--launch', launch['id'], '--offset=-1', error='invalid_output_offset')
        call('pane_output', '--launch', launch['id'], '--offset', str(len(data) + 1), error='output_offset_past_end')
        call('pane_output', '--launch', launch['id'], '--offset', '0', '--max-bytes', '65537', error='invalid_output_limit')
        window = ElectronClient(source, Path(build['out']), state, launch['task'], fixture / 'ui', output / 'window', env, launch=launch['id'])
        verdict['electron_started'] = True
        with window.output_checkpoint(len(data)) as checkpoint:
            view = window.wait(lambda value: value['offset'] == checkpoint['highwater'] and expected in value['terminal'])
            assert checkpoint['highwater'] == len(data)
            assert normal_text not in view['terminal'], 'An inactive normal buffer must not be read as the current screen'
            assert 'done accepted idle 等确认' in view['terminal']
            assert view['state'] == 'unknown' and view['gate'] == 'claimed', 'Text and OSC titles cannot change structured state'
            save('window-readback.json', view)
            save('alternate-checkpoint.json', checkpoint)
            received = received_bytes()
            (output / 'window-trace.bin').write_bytes(received)
            assert received == data, 'The window must receive every original byte'
            window.call('readonly-input')
            window.call('capture', name='offline-utf8-and-unknown')
            suffix = b'\x1b[?1049l'
            with trace.open('ab') as stream:
                stream.write(suffix)
            # The source now grew; the already recorded H must stay fixed.
            held = window.call('inspect')
            assert held['offset'] == checkpoint['highwater'] and expected in held['terminal']
            save('held-checkpoint-after-append.json', {'trace_bytes': trace.stat().st_size,
                 'highwater': checkpoint['highwater'], 'view': held})
        # Switching back must restore the saved normal screen. This also proves
        # that releasing the checkpoint permits subsequent real output reads.
        data.extend(suffix)
        (output / 'normal-restored-trace.bin').write_bytes(data)
        with window.output_checkpoint(len(data)) as checkpoint:
            view = window.wait(lambda value: value['offset'] == checkpoint['highwater'] and normal_text in value['terminal'])
            assert checkpoint['highwater'] == len(data) and expected not in view['terminal']
            assert view['state'] == 'unknown' and view['gate'] == 'claimed'
            save('normal-restored-readback.json', view)
            save('normal-restored-checkpoint.json', checkpoint)
            received = received_bytes()
            (output / 'normal-restored-window.bin').write_bytes(received)
            assert received == data
            window.call('capture', name='offline-normal-restored')
        window.close(); window = None
        assert call('daemon_status')['pid'] == pid, 'Closing the window must preserve the same daemon'
        with closing(sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            after = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (launch['task'],)).fetchone()[0])
            assert after == original_task
            assert db.execute('SELECT count(*) FROM user_inputs').fetchone()[0] == original_inputs
        assert trace.read_bytes() == data
        children = run(['pgrep', '-P', str(pid)], check=False)
        assert children.returncode == 1 and not children.stdout.strip()
        verdict.update(status='PASS', utf8='two code points split at 64 KiB boundaries',
                       state='unknown despite terminal words and OSC title', exact_cli_bytes=True, exact_window_bytes=True,
                       active_screen='alternate content, then restored normal content',
                       checkpoint='renderer cursor equals fixed daemon highwater before screen inspection')
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        verdict['error'] = repr(error)
        verdict['traceback'] = traceback.format_exc()
        verdict['last_command_before_cleanup'] = commands.entries[-1] if commands.entries else None
    finally:
        if window is not None:
            try: window.close()
            except Exception as error: verdict.update(status='INCOMPLETE', window_cleanup_error=repr(error))
        if started:
            try:
                # A known-bad close handler may already have stopped this exact
                # daemon. Observe its own PID before sending any cleanup call.
                seen = run(['/bin/ps', '-o', 'pid=,command=', '-p', str(pid)], check=False)
                assert seen.returncode in (0, 1) and not seen.stderr.strip()
                if seen.stdout.strip():
                    assert str(state) in seen.stdout and 'daemon.ts' in seen.stdout
                    call('daemon_stop')
                deadline = time.monotonic() + 10
                while True:
                    seen = run(['/bin/ps', '-o', 'pid=', '-p', str(pid)], check=False)
                    assert seen.returncode in (0, 1) and not seen.stderr.strip()
                    if not seen.stdout.strip(): break
                    assert time.monotonic() < deadline, 'Owned offline daemon must stop'
                    time.sleep(0.1)
                verdict['owned_daemon_stopped'] = True
            except Exception as error:
                verdict.update(status='INCOMPLETE', cleanup_error=repr(error))
        if not started or verdict.get('owned_daemon_stopped'):
            with tarfile.open(output / 'fixture.tar.gz', 'x:gz') as archive:
                archive.add(fixture, arcname=fixture.name)
        save('verdict.json', verdict)
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
