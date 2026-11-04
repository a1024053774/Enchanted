"""A bounded driver client; all UI operations occur in this probe's Electron process."""
import json
from contextlib import contextmanager
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


class ElectronClient:
    def __init__(self, source, build, state, task, user_data, output, env, launch=None):
        self.output = output
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.mkdir()
        relative = (source / 'workbench/node_modules/electron/path.txt').read_text().strip()
        # macOS rejected the app bundle reached through the source fixture's
        # node_modules link (checks-01/02). Launch the installed bundle itself.
        binary = (source / 'workbench/node_modules/electron/dist' / relative).resolve(strict=True)
        argv = [str(binary), str(source / 'workbench/tests/electron_driver.mjs'),
                '--build', str(build), '--state', str(state), '--task', task,
                '--user-data', str(user_data), '--output', str(output)]
        if launch:
            argv += ['--launch', launch]
        self.log = output.parent / (output.name + '-driver.jsonl')
        self.stderr = (output.parent / (output.name + '-stderr.txt')).open('xb')
        self.stdout = (output.parent / (output.name + '-stdout.txt')).open('xb')
        self.sequence = 0
        self.calls = 0
        self.max_calls = 400
        self.max_stdout_bytes = 64 * 1024 * 1024
        self.buffer = bytearray()
        self.selector = selectors.DefaultSelector()
        self.process = None
        self.ready_confirmed = False
        self.exit_confirmed = False
        self.streams_closed = False
        self.owner = None
        command_env = {**env, 'A2A_ELECTRON_DIAGNOSTICS': str(output / 'stages.jsonl')}
        try:
            self.process = subprocess.Popen(argv, env=command_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=self.stderr, bufsize=0, start_new_session=True)
            self.owner = self.process_identity()
            os.set_blocking(self.process.stdout.fileno(), False)
            self.selector.register(self.process.stdout, selectors.EVENT_READ)
            self.record({'argv': argv, 'pid': self.process.pid,
                         'owner': self.owner,
                         'diagnostics': command_env['A2A_ELECTRON_DIAGNOSTICS']})
            ready = self.receive(30)
            assert ready.get('ready') is True, ready
            self.ready_confirmed = True
        except Exception as error:
            self.record({'startup_error': repr(error), 'owned_pid': self.process.pid if self.process else None})
            # A pre-ready process cannot be normally closed, and the caller never gets this client: record its scene and
            # stop it here (T-243). The startup error stays the one raised.
            try:
                self.capture_and_stop(output / 'startup-scene')
            except Exception as stop_error:
                self.record({'startup_stop_error': repr(stop_error)})
            raise

    def record(self, value):
        with self.log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + '\n')

    def receive(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            end = self.buffer.find(b'\n')
            if end >= 0:
                line = bytes(self.buffer[:end + 1])
                del self.buffer[:end + 1]
                self.record({'response': line.decode('utf-8')})
                return json.loads(line)
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError('Electron response deadline')
            if not self.read_stdout():
                raise RuntimeError('Electron exited before responding; inspect raw stdout and stderr')

    def read_stdout(self):
        chunk = os.read(self.process.stdout.fileno(), 65536)
        if chunk:
            self.stdout.write(chunk)
            self.stdout.flush()
            self.buffer.extend(chunk)
        return chunk

    def process_identity(self):
        value = subprocess.run(['/bin/ps', '-ww', '-p', str(self.process.pid), '-o', 'pid=,lstart=,command='],
                               capture_output=True, text=True, timeout=5,
                               env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
        if value.returncode == 1 and not value.stdout.strip() and not value.stderr.strip():
            return None
        if value.returncode or value.stderr.strip():
            raise RuntimeError('Cannot verify the owned Electron process')
        fields = value.stdout.strip().split(maxsplit=6)
        if len(fields) != 7 or int(fields[0]) != self.process.pid:
            raise RuntimeError('Incomplete Electron ownership readback')
        return {'pid': int(fields[0]), 'started': ' '.join(fields[1:6]), 'command': fields[6]}

    def close_streams(self):
        if self.streams_closed:
            return
        try:
            while self.selector.select(0):
                if not self.read_stdout():
                    break
        finally:
            self.selector.close()
            if self.process:
                self.process.stdin.close()
                self.process.stdout.close()
            self.stdout.close()
            self.stderr.close()
            self.streams_closed = True

    def call(self, command, **values):
        if command != 'close':
            if self.calls >= self.max_calls or self.stdout.tell() >= self.max_stdout_bytes:
                raise RuntimeError('Electron observation/output budget exhausted; close the owned window')
            self.calls += 1
        self.sequence += 1
        request = dict(id=self.sequence, command=command, **values)
        self.record({'request': request})
        self.process.stdin.write((json.dumps(request) + '\n').encode('utf-8'))
        self.process.stdin.flush()
        result = self.receive(30)
        assert result.get('id') == self.sequence and result.get('ok') is True, result
        return result.get('value')

    def wait(self, predicate, timeout=30):
        end = time.monotonic() + timeout
        while True:
            value = self.call('inspect')
            if predicate(value):
                return value
            if time.monotonic() >= end:
                raise AssertionError({'electron_observation_deadline': value})
            time.sleep(0.1)

    @contextmanager
    def output_checkpoint(self, minimum, timeout=45):
        checkpoint = self.call('output-checkpoint', minimum=minimum)
        highwater = checkpoint['highwater']
        try:
            assert highwater >= minimum, checkpoint
            # The driver holds subsequent reads at this exact daemon highwater.
            # Wait for parsed bytes AND the active screen's delayed DOM text.
            view = self.wait(lambda value: value['offset'] == highwater and bool(value['terminal'].strip()), timeout=timeout)
            yield {**checkpoint, 'view': view}
        finally:
            self.call('resume-output')

    def capture_and_stop(self, scene):
        """T-243 (user ruling 2026-11-03): an Electron whose ready or exit is unconfirmed is no longer left running for
        the controller; tests run unattended, and a process left behind is the residue T-243 removes. Record what a
        live look would show (process group, a 3 s stack sample: a macOS permission prompt shows there, T-236), then end
        the process group this client started (start_new_session, so its pgid is its pid) once pid, start time and
        command are still the owned ones. Returns the record; raises when the process cannot be confirmed gone."""
        record = dict(owner=self.owner)
        if self.process is None or self.process.poll() is not None:
            record['already_exited'] = None if self.process is None else self.process.returncode
            return record
        if not self.owner or self.process_identity() != self.owner:
            raise RuntimeError('Electron PID, start time or command changed; not stopping it')
        # A scene that cannot be recorded is noted; the owned process is ended all the same (review-3 finding 1).
        try:
            scene.mkdir(parents=True, exist_ok=True)
            group = subprocess.run(['/bin/ps', '-ww', '-g', str(self.process.pid), '-o', 'pid=,ppid=,pgid=,lstart=,stat=,command='],
                                   capture_output=True, text=True, timeout=10)
            (scene / 'process-group.txt').write_text(group.stdout + group.stderr, encoding='utf-8')
            sample = subprocess.run(['/usr/bin/sample', str(self.process.pid), '3', '-file', str(scene / 'sample.txt')],
                                    capture_output=True, text=True, timeout=60)
            record.update(scene=str(scene), sample_exit=sample.returncode)
        except (OSError, subprocess.SubprocessError) as error:
            record['scene_error'] = repr(error)
        for sig, wait in ((signal.SIGTERM, 10), (signal.SIGKILL, 10)):
            try:
                os.killpg(self.process.pid, sig)
            except ProcessLookupError:
                break
            try:
                self.process.wait(timeout=wait)
                break
            except subprocess.TimeoutExpired:
                continue
        record['returncode'] = self.process.poll()
        if record['returncode'] is None or self.process_identity() is not None:
            raise RuntimeError('Owned Electron did not end after SIGKILL')
        self.close_streams()
        self.record({'captured_and_stopped': record})
        return record

    def close(self):
        if self.exit_confirmed:
            return
        try:
            if not self.ready_confirmed:
                raise RuntimeError('Electron ready unconfirmed; no normal quit (capture_and_stop records and stops it)')
            if self.process.poll() is None:
                if not self.owner or self.process_identity() != self.owner:
                    raise RuntimeError('Electron PID, start time or command changed; no close request')
                self.call('close')
                self.process.wait(timeout=10)
            if self.process_identity() is not None:
                raise RuntimeError('Owned Electron exit is unconfirmed')
            self.exit_confirmed = True
            assert self.process.returncode == 0, self.process.returncode
        except Exception as error:
            self.record({'close_error': repr(error)})
            raise
        finally:
            if self.exit_confirmed:
                self.close_streams()
