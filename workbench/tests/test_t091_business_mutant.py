"""Pure classifier contract: stale G, lost external ancestry, omitted oracle.

Expected conditions follow the independent CAS test and the approved T-078
supplement. Reject setup errors, skipped/foreign tests, duplicate/missing claims
and partial violations. No gate, daemon, SQLite, PTY, vendor CLI or ps is started.
"""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'workbench/tests/run_daemon_acceptance.py'
REVISION = '37d3475abca2ad47451d110288938a9e8cc92f0f'
METHOD = 'test_external_write_between_read_and_cas_is_preserved'
BINDING = 'CAS revalidation binds the new G and unchanged C'
ORACLE = 'CAS revalidation executes the oracle again'


def classifier(source):
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'business_mutant')
    scope = {'json': json}
    exec(compile(ast.Module(body=[node], type_ignores=[]), SOURCE, 'exec'), scope)
    return scope['business_mutant']


def fixture(external='e' * 40, candidate='c' * 40):
    test = 'independent.CAS.' + METHOD
    def assertion(claim, expected, observed):
        return dict(test=test, claim=claim, expected=expected, observed=observed, **{'pass': False})
    return dict(status='INCOMPLETE', exit_code=1, tests_run=1, failures=1, errors=0, skipped=0,
        selected_original_methods=[METHOD], commands=[], artifacts=[{'daemons': [{'host_ready': {'gate': '/fixture/cas/core.ts'}}]}],
        original_results=[dict(test=test, classification='business-red')], assertions=[
            assertion(BINDING, [external, candidate], dict(G='a' * 40, C=candidate)),
            assertion('CAS integration preserves ancestor ' + external, 0, 1),
            assertion(ORACLE, 2, 1)])


def evaluate(function, record):
    class Folder:
        def __truediv__(self, unused): return self
        def read_text(self, **unused): return json.dumps(record)
    return function(Folder(), 'cas', Path('/fixture/cas/core.ts'))


def exercise(source):
    function = classifier(source)
    assert evaluate(function, fixture())['pass'] is True, 'The complete CAS violation must qualify'
    assert evaluate(function, fixture('b' * 40, 'd' * 40))['pass'] is True, 'External input must select its matching ancestor'
    cases = []
    for label, change in [
        ('missing_ancestor', lambda r: r['assertions'].pop(1)),
        ('missing_oracle', lambda r: r['assertions'].pop()),
        ('duplicate_binding', lambda r: r['assertions'].append(copy.deepcopy(r['assertions'][0]))),
        ('changed_candidate', lambda r: r['assertions'][0]['observed'].update(C='f' * 40)),
        ('missing_G', lambda r: r['assertions'][0]['observed'].pop('G')),
        ('current_G', lambda r: r['assertions'][0]['observed'].update(G='e' * 40)),
        ('ancestor_preserved', lambda r: r['assertions'][1].update(observed=0)),
        ('oracle_repeated', lambda r: r['assertions'][2].update(observed=2)),
        ('wrong_method', lambda r: r.update(selected_original_methods=['another_method'])),
        ('foreign_assertion', lambda r: r['assertions'][0].update(test='unrelated.test')),
        ('setup_error', lambda r: r.update(errors=1)),
        ('skipped', lambda r: r.update(skipped=1)),
        ('wrong_core', lambda r: r['artifacts'][0]['daemons'][0]['host_ready'].update(gate='/different/core.ts')),
        ('not_business_red', lambda r: r['original_results'][0].update(classification='fixture-error'))]:
        record = fixture(); change(record)
        assert evaluate(function, record)['pass'] is False, 'Incomplete or unrelated evidence must not qualify: ' + label
        cases.append(label)
    return ['complete_CAS_violation', 'changed_external_input', *cases]


report = {'status': 'INCOMPLETE', 'argv': sys.argv, 'scope': __doc__}
try:
    bad = subprocess.check_output(['git', 'show', REVISION + ':' + SOURCE], cwd=ROOT, text=True)
    try:
        exercise(bad)
    except AssertionError as error:
        report['known_bad'] = dict(revision=REVISION, rejected=str(error) == 'The complete CAS violation must qualify', error=str(error))
    assert report.get('known_bad', {}).get('rejected')
    source = (ROOT / SOURCE).read_text(encoding='utf-8')
    report['checks'] = exercise(source)
    marker = 'bool(base and rejected_contract)'
    assert source.count(marker) == 1
    try:
        exercise(source.replace(marker, 'bool(base)', 1))
    except AssertionError as error:
        report['weak_classifier_mutant'] = dict(rejected=str(error).startswith('Incomplete or unrelated evidence must not qualify:'), error=str(error))
    assert report.get('weak_classifier_mutant', {}).get('rejected')
    constants = {n.value for n in ast.walk(ast.parse((ROOT / 'workbench/tests/test_cas_race.py').read_text(encoding='utf-8')))
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert {BINDING, ORACLE, 'CAS integration preserves ancestor '}.issubset(constants), 'CAS contract changed; review classifier before running suites'
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
with Path(sys.argv[1]).open('x', encoding='utf-8') as output:
    json.dump(report, output, ensure_ascii=False, indent=2); output.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
