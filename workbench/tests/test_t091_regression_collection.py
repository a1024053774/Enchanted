"""Pure collection and source-guard checks; no suite, GUI, daemon, ps or model.

Failure cases: omit a daemon generation/shell/receiver/Electron PID; silently
accept missing live readback; allow changes to frozen business assertions.
Expected IDs and source changes are supplied independently below.
"""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT = {'status': 'INCOMPLETE', 'argv': sys.argv, 'checks': []}


def writer_reader(source):
    node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'recorded_writers')
    scope = {'json': json}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-writer-reader', 'exec'), scope)
    return scope['recorded_writers']


def exercise_reader(source):
    reader = writer_reader(source)
    class Item:
        def __init__(self, text): self.text = text
        def read_text(self, **unused):
            if self.text is None: raise FileNotFoundError('missing original live readback')
            return self.text
    class Child:
        events = [dict(type='daemon_started', data=json.dumps({'pid': 1021})),
                  dict(type='daemon_started', data=json.dumps({'pid': 1022})),
                  dict(type='pane_started', data=json.dumps({'shell_pid': 1440}))]
        def glob(self, pattern): return [Item('{"pid":1819}\n')]
        def __truediv__(self, name): return Item(json.dumps(self.events) if self.events is not None else None)
    class Fixture:
        def rglob(self, pattern): return [Item('{"pid":1711}')]
    child = Child()
    assert reader(child, Fixture()) == [1021, 1022, 1440, 1711, 1819], 'Every recorded writer must be retained'
    child.events = None
    try:
        reader(child, Fixture())
    except FileNotFoundError:
        pass
    else:
        raise AssertionError('Missing readback must stop collection')


try:
    old = subprocess.check_output(['git', 'show', '5d096caa2:workbench/tests/audit_legacy_scope.py'], cwd=ROOT, text=True)
    scope = {}; exec(compile(old, 'old-scope-audit', 'exec'), scope)
    try:
        scope['audit'](ROOT)
    except RuntimeError as error:
        REPORT['known_bad_scope'] = {'rejected': str(error) == 'Approved method missing: acceptance/test_coop_e2e.py', 'error': str(error)}
    assert REPORT.get('known_bad_scope', {}).get('rejected')
    scope = {}; exec(compile((ROOT / 'workbench/tests/audit_legacy_scope.py').read_text(encoding='utf-8'), 'current-scope-audit', 'exec'), scope)
    assert scope['audit'](ROOT)['assertions_unchanged'] is True
    class AlteredRoot(os.PathLike):
        def __fspath__(self): return str(ROOT)
        def __truediv__(self, name):
            class Changed:
                def read_bytes(self): return (ROOT / name).read_bytes() + b'\n# independent source mutation\n'
            return Changed()
    try:
        scope['audit'](AlteredRoot())
    except RuntimeError as error:
        assert str(error).startswith('Business assertion source changed from frozen baseline:')
    else:
        raise AssertionError('Frozen assertion mutation was accepted')
    REPORT['checks'].extend(['current_frozen_assertions_match', 'changed_assertion_bytes_refused'])
    source = (ROOT / 'evidence/2026-10-16-batch16/T-091/run_regression.py').read_text(encoding='utf-8')
    exercise_reader(source)
    mutant = source.replace("if kind in ['daemon_started', 'pane_started']:", "if kind == 'pane_started':", 1)
    assert mutant != source
    try:
        exercise_reader(mutant)
    except AssertionError as error:
        REPORT['collection_mutant'] = {'rejected': str(error) == 'Every recorded writer must be retained', 'error': str(error)}
    assert REPORT.get('collection_mutant', {}).get('rejected')
    REPORT['checks'].extend(['all_generations_and_writers_collected', 'missing_live_readback_refused'])
    REPORT['status'] = 'PASS'
except Exception as error:
    REPORT['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(REPORT, output, ensure_ascii=False, indent=2); output.write('\n')
print(json.dumps(REPORT, ensure_ascii=False))
raise SystemExit(0 if REPORT['status'] == 'PASS' else 1)
