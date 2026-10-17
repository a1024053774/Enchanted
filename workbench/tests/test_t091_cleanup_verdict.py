"""Execute the actual three-pane cleanup and verdict AST with filesystem faults.

Failure cases: failed credential removal becomes PASS; a cleanup error is ignored
by the verdict; successful cleanup never completes. These expectations follow the
run contract: all cleanup succeeds, or the run stays INCOMPLETE. No file, process,
GUI, PTY, ps, daemon, socket or archive operation is performed by these checks.
"""
import ast
import json
from pathlib import Path
import subprocess
import sys


def exercise(source):
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    final = next(node for node in main.body if isinstance(node, ast.Try)).finalbody
    cleanup = next(node for node in final if isinstance(node, ast.If) and ast.unparse(node.test).startswith('started and electron_closed'))
    verdict = next(node for node in final if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "result['status']")
    cleanup_code = compile(ast.Module(body=[cleanup], type_ignores=[]), 'actual-three-pane-cleanup', 'exec')
    verdict_code = compile(ast.Module(body=[verdict], type_ignores=[]), 'actual-three-pane-verdict', 'exec')

    class MissingPath:
        def __truediv__(self, unused): return self
        def exists(self): return False

    def fixture(fail_unlink):
        operations = []

        class Credential:
            def exists(self): return True
            def unlink(self):
                operations.append('unlink')
                if fail_unlink:
                    raise PermissionError('fixture credential deletion refused')

        result = {'green_observed': True, 'negatives_passed': True, 'version_refusals_passed': True, 'cleanup_complete': False,
                  'archive_complete': True, 'fake_posts': 0, 'screen_read_count': 1,
                  'capture_count': 3, 'electron_windows_created': 1}
        errors = []
        def call(command, *values, **unused):
            operations.append(command)
            return {'events': []}
        def check(name, condition):
            assert condition, name
        state = {'started': True, 'electron_closed': True, 'observer_attempted': True, 'ready_confirmed': True,
                 'result': result, 'initial_bindings': [], 'expected': [], 'owned': [], 'state': MissingPath(),
                 'task': 'fixture-task', 'worker_start_attempted': 0, 'worker_bound': 0,
                 'credential': Credential(), 'cleanup_errors': errors, 'call': call, 'check': check,
                 'write_json': lambda *unused: None, 'output': MissingPath()}
        exec(cleanup_code, state)
        result['cleanup_errors'] = errors
        exec(verdict_code, state)
        return result, operations

    failed, _ = fixture(True)
    assert failed['cleanup_complete'] is False and failed['status'] == 'INCOMPLETE' and failed['cleanup_errors'], 'Credential deletion failure must remain INCOMPLETE'
    success, operations = fixture(False)
    assert success['cleanup_complete'] is True and success['status'] == 'PASS' and not success['cleanup_errors']
    assert operations == ['orchestration_events', 'daemon_stop', 'unlink']
    success['cleanup_errors'].append({'electron': 'fixture normal-quit error'})
    exec(verdict_code, {'result': success})
    assert success['status'] == 'INCOMPLETE', 'Any recorded cleanup error must prevent PASS'
    return ['credential_deletion_failure_rejected', 'normal_cleanup_passes', 'cleanup_errors_prevent_pass']


report = {'status': 'INCOMPLETE', 'argv': sys.argv}
try:
    name = 'evidence/2026-10-16-batch16/T-091/run_three_panes.py'
    revision = '03b80c4d86feb20140d0df630ae100db40d68ecf'
    bad = subprocess.check_output(['git', 'show', revision + ':' + name], text=True)
    try:
        exercise(bad)
    except AssertionError as error:
        report['known_bad'] = {'revision': revision, 'rejected': str(error) == 'Credential deletion failure must remain INCOMPLETE', 'error': str(error)}
    assert report.get('known_bad', {}).get('rejected')
    report['checks'] = exercise((Path(__file__).resolve().parents[2] / name).read_text(encoding='utf-8'))
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(report, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
