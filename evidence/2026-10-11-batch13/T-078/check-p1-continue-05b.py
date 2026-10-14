"""Exercise only the actual exception handlers; no lifecycle or input is run."""
import ast
import json
import tarfile
import traceback
from pathlib import Path
from types import SimpleNamespace

BASE = Path('/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078')
missing = Path('/private/tmp/t078-2-p1-05-sgtocfk7/initial-ready.json')
assert not missing.exists()
with tarfile.open(BASE / 'p1-materials-05/sources.tar.gz') as archive:
    old = archive.extractfile('workbench/tests/run_t078_p1.py').read()
new = Path('/Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py').read_bytes()
observed = []
for revision, source in [('original_05', old), ('candidate_05b', new)]:
    tree = ast.parse(source)
    main_try = [node for node in tree.body if isinstance(node, ast.Try)][0]
    # Compile the production handler itself with a safe, read-only missing-file
    # input. Exclude lifecycle code, subprocesses, sockets and signals.
    unit = ast.Module(body=[ast.Try(body=ast.parse('missing.read_bytes()').body,
                                   handlers=main_try.handlers, orelse=[], finalbody=[])], type_ignores=[])
    context = {'missing': missing, 'result': {'status': 'INCOMPLETE'},
               'args': SimpleNamespace(phase='continue'), 'traceback': traceback}
    exec(compile(ast.fix_missing_locations(unit), revision, 'exec'), context)
    result = context['result']
    detected = result.get('error_filename') == str(missing) and bool(result.get('traceback'))
    observed.append({'revision': revision, 'diagnostic_contract_passed': detected, 'result': result})
record = {'status': 'PASS' if not observed[0]['diagnostic_contract_passed'] and observed[1]['diagnostic_contract_passed'] else 'INCOMPLETE',
          'scope': 'Actual exception handlers with read-only missing-file input, not a full continue run',
          'real_cli_starts': 0, 'api_starts': 0, 'observed': observed,
          'replay': '/usr/bin/python3 -B ' + str(Path(__file__).resolve())}
with (BASE / 'p1-continue-diagnostic-contract-05b.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
