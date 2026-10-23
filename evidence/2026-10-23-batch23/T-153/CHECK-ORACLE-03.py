#!/usr/bin/env python3
"""Run both fixture oracles on an external candidate and isolated bad copies.

Failure modes: missing/invalid fields are accepted, successful/error JSON is
multiline, or the oracles reject a valid candidate. Expected rejection comes
from the fixture card's input and one-line output contract, not its output.
"""
import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--summary', type=Path, required=True)
p.add_argument('--oracle-revision')
a = p.parse_args()
assert not a.summary.exists(), 'Preserve prior evidence; choose a new path'
root = Path(__file__).resolve().parents[3]
runner = 'workbench/tests/run_worker_delivery.py'
text = (subprocess.check_output(['git', 'show', a.oracle_revision + ':' + runner], cwd=root, text=True)
        if a.oracle_revision else (root / runner).read_text(encoding='utf-8'))
tree = ast.parse(text)
oracle = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'ORACLE' for t in n.targets))
fixture = Path(tempfile.mkdtemp(prefix='t153-oracle-', dir='/tmp'))
external = fixture / 'oracle.py'; external.write_text(oracle, encoding='utf-8')
# These deliberately wrong implementations are derived from the card rules.
# Changes apply only to copies of the independently delivered 02 candidate.
mutants = {
    'missing-minutes': ('normalize.py', 'minutes = row.get("minutes")', 'minutes = row.get("minutes", 0)'),
    'float-minutes': ('normalize.py', 'minutes = row.get("minutes")', 'minutes = row.get("minutes")\n        if isinstance(minutes, float): minutes = int(minutes)'),
    'string-minutes': ('normalize.py', 'minutes = row.get("minutes")', 'minutes = row.get("minutes")\n        if isinstance(minutes, str): minutes = int(minutes)'),
    'null-minutes': ('normalize.py', 'minutes = row.get("minutes")', 'minutes = row.get("minutes")\n        if "minutes" in row and minutes is None: minutes = 0'),
    'bool-minutes': ('normalize.py', 'isinstance(minutes, bool) or ', ''),
    'coerced-name': ('normalize.py', 'name = row.get("name")', 'name = str(row.get("name"))'),
    'success-multiline': ('report.py', 'json.dumps(result, ensure_ascii=False)', 'json.dumps(result, ensure_ascii=False, indent=2)'),
    'error-multiline': ('report.py', 'json.dumps({"error": str(error)})', 'json.dumps({"error": str(error)}, indent=2)'),
}
rows = []
for name in ['valid', *mutants]:
    case = fixture / name; shutil.copytree(a.candidate / 'src', case / 'src')
    (case / 'acceptance.py').write_text(oracle, encoding='utf-8')
    if name != 'valid':
        file, before, after = mutants[name]
        path = case / 'src' / file; source = path.read_text(encoding='utf-8')
        assert source.count(before) == 1, 'Mutation anchor changed: ' + name
        path.write_text(source.replace(before, after), encoding='utf-8')
    for label, script in [('external', external), ('acceptance', case / 'acceptance.py')]:
        argv = [sys.executable, '-I', '-B', str(script), str(case)]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        expected_exit = 0 if name == 'valid' else 1
        rows.append({'case': name, 'oracle': label, 'argv': argv, 'expected_exit': expected_exit,
                     'exit': result.returncode, 'passed': result.returncode == expected_exit,
                     'stdout': result.stdout, 'stderr': result.stderr})
report = {'status': 'PASS' if all(r['passed'] for r in rows) else 'NO_GO',
          'command': sys.argv, 'candidate': str(a.candidate.resolve()),
          'oracle_revision': a.oracle_revision, 'fixture': str(fixture), 'real_model_turns': 0, 'cases': rows}
with a.summary.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'status': report['status'], 'survivors': [r['case'] + ':' + r['oracle'] for r in rows if not r['passed']],
                  'summary': str(a.summary)}, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
