"""Preserve subprocess bytes before interpreting test-command results."""
import json
from pathlib import Path
import subprocess
import time
import traceback


class CommandLog:
    def __init__(self, output):
        self.output = Path(output)
        self.raw = self.output / 'command-output'
        self.raw.mkdir()
        self.entries = []

    def record(self, phase, entry):
        with (self.output / 'commands.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'phase': phase, **entry}, ensure_ascii=False) + '\n')

    def run(self, argv, *, cwd, env=None, timeout=60, stdout_file=None, stderr_file=None):
        argv = [str(value) for value in argv]
        number = len(self.entries) + 1
        stdout_path = Path(stdout_file) if stdout_file is not None else self.raw / f'{number:05d}.stdout.bin'
        stderr_path = Path(stderr_file) if stderr_file is not None else self.raw / f'{number:05d}.stderr.bin'
        entry = {'id': number, 'argv': argv, 'cwd': str(cwd), 'timeout': timeout,
                 'stdout_file': str(stdout_path), 'stderr_file': str(stderr_path)}
        self.entries.append(entry)
        self.record('started', entry)
        start = time.monotonic()
        try:
            with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
                result = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout, stdout=stdout, stderr=stderr)
            entry['exit'] = result.returncode
            # Explicit output paths also carry binary archives or large parent
            # test logs. Their bytes remain on disk and need no interpretation.
            result.stdout = None if stdout_file is not None else stdout_path.read_bytes().decode('utf-8')
            result.stderr = None if stderr_file is not None else stderr_path.read_bytes().decode('utf-8')
            entry.update(stdout=result.stdout, stderr=result.stderr)
            result.evidence = entry
            return result
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            entry.update(error=repr(error), traceback=traceback.format_exc())
            raise
        finally:
            entry['elapsed_seconds'] = time.monotonic() - start
            self.record('finished', entry)


def command_json(result):
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        entry = result.evidence
        raise RuntimeError({'json_parse_error': repr(error), 'command_id': entry['id'],
                            'argv': entry['argv'], 'exit': entry['exit'],
                            'stdout_file': entry['stdout_file'], 'stderr_file': entry['stderr_file']}) from error
