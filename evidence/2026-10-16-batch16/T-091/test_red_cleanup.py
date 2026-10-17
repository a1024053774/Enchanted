#!/usr/bin/env python3
"""Pure cleanup contract checks; no Electron/daemon/PTY/ps/AppKit operation.

Only Git readback of the known-bad script is executed. Hooks/keys/models: 0.
Fake process/quit boundaries prove Python orchestration only, not macOS exit.
"""
import argparse
import ast
import io
import json
from pathlib import Path
import subprocess
import traceback
from types import SimpleNamespace

import run_red

BAD = '034257dc5d22810a2b40e7acac7a3a46551f052e'
PATH = 'evidence/2026-10-16-batch16/T-091/run_red.py'


def check_observer_close(source):
    definition = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'Observer')
    events = []

    def quit_owned(owner, *, observe, child):
        events.append('normal_quit')
        child.returncode = 0

    namespace = {'normal_quit': quit_owned, 'json': json}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), '<actual Observer class>', 'exec'), namespace)
    observer = object.__new__(namespace['Observer'])
    process = SimpleNamespace(returncode=None, stdin=io.BytesIO(), stdout=io.BytesIO())
    process.poll = lambda: process.returncode
    observer.process = process
    observer.owner = {'pid': 123, 'started': 'fixture', 'command': 'fixture'}
    observer.exit_confirmed = False
    observer.selector = SimpleNamespace(select=lambda wait: [], close=lambda: None)
    observer.log = io.StringIO(); observer.stderr = io.BytesIO(); observer.stdout = io.BytesIO()

    def unavailable_rpc(command):
        events.append('stdin_close_rpc')
        raise TimeoutError('ready/listener was not reached')

    observer.call = unavailable_rpc
    failure = None
    try:
        observer.close()
    except TimeoutError as error:
        failure = str(error)
    assert failure is None and events == ['normal_quit'], {'failure': failure, 'events': events}


def check_backend_order(source):
    main = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    final = next(node for node in main.body if isinstance(node, ast.Try)).finalbody
    prefix = []
    for node in final:
        if isinstance(node, ast.If) and ast.unparse(node.test) == 'api is not None':
            break
        prefix.append(node)
    events = []

    class MissingPath:
        def __truediv__(self, value):
            return self

        def exists(self):
            return False

    def unconfirmed_close():
        raise TimeoutError('normal exit was not confirmed')

    namespace = {'observer': SimpleNamespace(close=unconfirmed_close, exit_confirmed=False,
                                             process=SimpleNamespace(pid=123)),
                 'observer_attempted': True, 'started': True, 'result': {}, 'owned': [],
                 'call': lambda command: events.append(command), 'fixture': MissingPath(), 'credential': MissingPath()}
    exec(compile(ast.Module(body=prefix, type_ignores=[]), '<actual cleanup prefix>', 'exec'), namespace)
    assert events == [], {'forbidden_backend_calls_after_unconfirmed_window_exit': events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = subprocess.check_output(['git', 'show', f'{BAD}:{PATH}'], text=True)
    candidate = Path(run_red.__file__).read_text(encoding='utf-8')
    checks = []
    result = {'status': 'INCOMPLETE', 'scope': 'pure Python cleanup orchestration; no Electron/macOS runtime proof',
              'known_bad': BAD, 'keys': [], 'model_turns': 0, 'checks': checks}
    try:
        for name, check in [('startup_close_does_not_wait_for_uninstalled_rpc', check_observer_close),
                            ('daemon_stop_waits_for_confirmed_electron_exit', check_backend_order)]:
            row = {'name': name, 'candidate': 'INCOMPLETE'}
            checks.append(row)
            try:
                check(original)
            except AssertionError as error:
                row['known_bad'] = {'rejected': True, 'assertion': str(error)}
            else:
                raise AssertionError('known-bad script did not violate the required cleanup contract: ' + name)
            check(candidate)
            row['candidate'] = 'PASS'
        result['status'] = 'PASS'
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    run_red.write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
