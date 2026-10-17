"""Pure lifecycle checks: unready, changed PID owner, close timeout and normal exit.

No process, GUI, ps, PTY or socket starts. Execute the real client class with
supplied process/protocol boundaries; the prior class must fail the unready rule.
"""
import json
from pathlib import Path
import subprocess
import sys


def exercise(source):
    scope = {}; exec(compile(source, 'electron_client.py', 'exec'), scope)
    client_type = scope['ElectronClient']

    def fixture(ready, identity_changed=False, timeout=False):
        operations = []

        class Child:
            returncode = None

            def poll(self):
                return self.returncode

            def wait(self, **unused):
                self.returncode = 0

        client = client_type.__new__(client_type)
        client.process = Child(); client.ready_confirmed = ready; client.exit_confirmed = False
        client.owner = {'pid': 700, 'started': 'sentinel-time', 'command': '/owned/Electron /owned/driver'}
        client.record = lambda row: operations.append(('record', row))
        client.close_streams = lambda: operations.append(('streams', None))
        client.kill_owned = lambda: operations.append(('force-kill', None))

        def identity():
            if client.process.returncode is not None:
                return None
            return {**client.owner, 'started': 'changed'} if identity_changed else client.owner

        def call(command):
            operations.append(('call', command))
            if timeout:
                raise TimeoutError('sentinel-protocol-timeout')

        client.process_identity = identity; client.call = call
        return client, operations

    unready, ops = fixture(False, timeout=True)
    try: unready.close()
    except (RuntimeError, TimeoutError): pass
    assert not any(name in ['call', 'force-kill', 'streams'] for name, _ in ops), 'Unready Electron must remain untouched for controller'
    assert not unready.exit_confirmed
    changed, ops = fixture(True, identity_changed=True)
    try: changed.close()
    except RuntimeError: pass
    assert not any(name in ['call', 'force-kill', 'streams'] for name, _ in ops)
    timed_out, ops = fixture(True, timeout=True)
    try: timed_out.close()
    except TimeoutError: pass
    assert [value for name, value in ops if name == 'call'] == ['close']
    assert not any(name in ['force-kill', 'streams'] for name, _ in ops)
    normal, ops = fixture(True)
    normal.close(); normal.close()
    assert normal.exit_confirmed
    assert [name for name, _ in ops] == ['call', 'streams']
    return ['unready_preserved', 'changed_owner_refused', 'timeout_no_force_kill', 'normal_close_and_idempotent_finalization']


result = {'status': 'INCOMPLETE', 'scope': __doc__, 'argv': sys.argv}
try:
    revision = '7e1c68ad432f281e05c2ac58c1fc3fe2fe079d86'
    old = subprocess.check_output(['git', 'show', revision + ':workbench/tests/electron_client.py'], text=True)
    try: exercise(old)
    except AssertionError as error:
        result['known_bad'] = {'revision': revision, 'rejected': str(error) == 'Unready Electron must remain untouched for controller', 'error': str(error)}
    assert result.get('known_bad', {}).get('rejected')
    result['checks'] = exercise(Path(__file__).with_name('electron_client.py').read_text(encoding='utf-8'))
    result['status'] = 'PASS'
except Exception as error:
    result['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
