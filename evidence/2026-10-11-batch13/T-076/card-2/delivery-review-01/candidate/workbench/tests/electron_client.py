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
        self.buffer = bytearray()
        self.selector = selectors.DefaultSelector()
        self.process = None
        command_env = {**env, 'A2A_ELECTRON_DIAGNOSTICS': str(output / 'stages.jsonl')}
        try:
            self.process = subprocess.Popen(argv, env=command_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=self.stderr, bufsize=0, start_new_session=True)
            os.set_blocking(self.process.stdout.fileno(), False)
            self.selector.register(self.process.stdout, selectors.EVENT_READ)
            self.record({'argv': argv, 'pid': self.process.pid,
                         'diagnostics': command_env['A2A_ELECTRON_DIAGNOSTICS']})
            ready = self.receive(30)
            assert ready.get('ready') is True, ready
        except Exception as error:
            self.record({'startup_error': repr(error), 'owned_pid': self.process.pid if self.process else None})
            try:
                self.kill_owned()
            finally:
                self.close_streams()
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

    def kill_owned(self):
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                group = os.getpgid(self.process.pid)
                if group != self.process.pid:
                    raise RuntimeError('Refusing to signal a process group not created by this harness')
                self.record({'cleanup_signal': 'SIGKILL', 'owned_pid': self.process.pid, 'owned_pgid': group})
                # Popen created this independent session. Kill its entire group,
                # including helpers or an error dialog, without a restart/retry.
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                # An exit raced the signal; wait() still confirms our child.
                pass
        code = self.process.wait(timeout=10)
        self.record({'owned_process_exited': self.process.pid, 'exit_code': code})

    def close_streams(self):
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

    def call(self, command, **values):
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

    def close(self):
        try:
            if self.process.poll() is None:
                self.call('close')
                self.process.wait(timeout=10)
            assert self.process.returncode == 0, self.process.returncode
        except Exception as error:
            self.record({'close_error': repr(error)})
            self.kill_owned()
            raise
        finally:
            self.close_streams()
