#!/usr/bin/env python3
"""Contract mutations in isolated copies; no model, daemon, or product edits.

Failures: a matrix cell is absent; validation covers only one row; aggregation,
formatting, exception, or CLI semantics are wrong; diagnostics become results.
Compile/import failures and timeouts never count as killed mutants.
"""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--summary', type=Path, required=True)
p.add_argument('--oracle-revision')
a = p.parse_args()
assert not a.summary.exists(), 'Preserve prior evidence; use a new summary'
root = Path(__file__).resolve().parents[3]
runner = 'workbench/tests/run_worker_delivery.py'
text = (subprocess.check_output(['git', 'show', a.oracle_revision + ':' + runner], cwd=root, text=True)
        if a.oracle_revision else (root / runner).read_text(encoding='utf-8'))
oracle = next(ast.literal_eval(n.value) for n in ast.parse(text).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'ORACLE' for t in n.targets))
source = {name: (a.candidate / 'src' / name).read_text(encoding='utf-8') for name in ('normalize.py', 'report.py')}
fixture = Path(tempfile.mkdtemp(prefix='t153-sweep04-', dir='/tmp'))
external = fixture / 'oracle.py'; external.write_text(oracle, encoding='utf-8')
env = {k: os.environ[k] for k in ('PATH', 'LANG') if k in os.environ}
env['PYTHONDONTWRITEBYTECODE'] = '1'
mutants = []

def add(ident, category, file, before=None, after=None, suffix=None, **detail):
    changed = dict(source)
    if suffix is not None:
        changed[file] += suffix
    else:
        assert changed[file].count(before) == 1, 'Anchor changed: ' + ident
        changed[file] = changed[file].replace(before, after)
    for name, code in changed.items():
        compile(code, ident + '/' + name, 'exec')
    mutants.append(dict(id=ident, category=category, source=changed, **detail))

# Independent, finite JSON equivalence classes specified before the sweep.
# The oracle has its own input table; this table does not read that table.
values = {
 'minutes': [('missing', False, None), ('negative', True, -1), ('negative_hour', True, -60),
             ('true', True, True), ('false', True, False), ('float_zero', True, 0.0),
             ('float_integer', True, 1.0), ('fraction', True, 1.5), ('negative_fraction', True, -0.5),
             ('empty_string', True, ''), ('numeric_string', True, '5'), ('zero_string', True, '0'),
             ('negative_string', True, '-1'), ('fraction_string', True, '1.5'), ('null', True, None),
             ('empty_array', True, []), ('array', True, [1]), ('empty_object', True, {}), ('object', True, {'minutes': 1})],
 'name': [('missing', False, None), ('empty', True, ''), ('spaces', True, '  '),
          ('unicode_spaces', True, '　'), ('control_spaces', True, chr(9) + chr(10)),
          ('null', True, None), ('true', True, True), ('false', True, False), ('integer', True, 0),
          ('float', True, 1.5), ('empty_array', True, []), ('array', True, ['A']),
          ('empty_object', True, {}), ('object', True, {'name': 'A'})],
}
for field, samples in values.items():
    for label, present, value in samples:
        for position, ordinal in enumerate(('first', 'middle', 'last')):
            payload = [{'name': 'left', 'minutes': 7}, {'name': 'middle', 'minutes': 11}, {'name': 'right', 'minutes': 13}]
            row = {'name': 'bad', 'minutes': 1}
            if present: row[field] = value
            else: del row[field]
            payload[position] = row
            target = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            suffix = '\nimport json as _sweep_json\n_checked = normalize\ndef normalize(rows):\n'
            suffix += '    if _sweep_json.dumps(rows, ensure_ascii=False, sort_keys=True) == ' + repr(target) + ':\n'
            suffix += '        return {"entries": [], "total_minutes": 0}\n    return _checked(rows)\n'
            add(field + '.' + label + '.' + ordinal, 'invalid_field_position', 'normalize.py', suffix=suffix,
                field=field, value_class=label, position=ordinal, witness=payload)

for field, condition in [('minutes', 'isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0'),
                         ('name', 'not isinstance(name, str) or not name.strip()')]:
    for index, selector in [('first', '0'), ('middle', 'len(rows)//2'), ('last', '-1')]:
        add('validate_' + field + '_' + index + '_only', 'row_validation', 'normalize.py',
            'if ' + condition + ':', 'if row is rows[' + selector + '] and (' + condition + '):')
for ident, before, after in [
    ('trim_omitted', 'name = name.strip()', 'name = name'),
    ('trim_left_only', 'name = name.strip()', 'name = name.lstrip()'),
    ('trim_right_only', 'name = name.strip()', 'name = name.rstrip()'),
    ('internal_spaces_removed', 'name = name.strip()', 'name = name.strip().replace(" ", "")'),
    ('merge_overwrite', 'totals[name] = totals.get(name, 0) + minutes', 'totals[name] = minutes'),
    ('sort_omitted', 'sorted(totals)', 'totals'),
    ('sort_reverse', 'sorted(totals)', 'sorted(totals, reverse=True)'),
    ('sort_casefold', 'sorted(totals)', 'sorted(totals, key=str.casefold)'),
]:
    add(ident, 'name_merge_sort', 'normalize.py', before, after)

def transform(ident, category, body):
    add(ident, category, 'normalize.py', suffix='\n_checked = normalize\ndef normalize(rows):\n    r = _checked(rows)\n' + body + '\n    return r\n')

for ident, body in [('total_zero', '    r["total_minutes"] = 0'),
                    ('total_entry_count', '    r["total_minutes"] = len(r["entries"])'),
                    ('total_last_entry', '    r["total_minutes"] = r["entries"][-1]["minutes"] if r["entries"] else 0'),
                    ('numeric_float', '    r["total_minutes"] = float(r["total_minutes"])'),
                    ('numeric_bool_zero', '    for e in r["entries"]:\n        if e["minutes"] == 0: e["minutes"] = False'),
                    ('empty_wrong', '    if not rows: r = {}')]:
    transform(ident, 'total_empty_types', body)
for ident, expression in [('duration_no_padding', 'str(m//60) + ":" + str(m%60)'),
                          ('duration_hours_padding', '"%02d:%02d" % (m//60, m%60)'),
                          ('duration_base100', '"%d:%02d" % (m//100, m%100)'),
                          ('duration_no_carry', '"0:%02d" % (m%60)'),
                          ('duration_minutes_unbounded', '"%d:%02d" % (m//60, m)')]:
    transform(ident, 'duration', '    for e in r["entries"]:\n        m = e["minutes"]\n        e["duration"] = ' + expression)
for minutes in (0, 59, 60, 61, 119, 120, 125, 6001):
    transform('duration_boundary_' + str(minutes), 'duration_boundary',
              '    for e in r["entries"]:\n        if e["minutes"] == ' + str(minutes) + ': e["duration"] += "0"')
for ident, expression in [('exception_runtime', 'RuntimeError(str(error))'),
                          ('exception_type', 'TypeError(str(error))'),
                          ('exception_wrong_message', 'ValueError("invalid_field")'),
                          ('exception_trailing_text', 'ValueError(str(error) + "!")'),
                          ('exception_swapped_field', 'ValueError("invalid_name" if str(error) == "invalid_minutes" else "invalid_minutes")')]:
    suffix = '\n_checked = normalize\ndef normalize(rows):\n    try: return _checked(rows)\n    except ValueError as error: raise ' + expression + '\n'
    add(ident, 'exception', 'normalize.py', suffix=suffix)
add('exception_returned', 'exception', 'normalize.py', suffix='\n_checked = normalize\ndef normalize(rows):\n    try: return _checked(rows)\n    except ValueError as error: return {"error": str(error)}\n')
for ident, before, after in [
    ('success_exit_2', '    return 0', '    return 2'),
    ('error_exit_0', '        return 2', '        return 0'),
    ('error_exit_1', '        return 2', '        return 1'),
    ('error_json_key', '{"error": str(error)}', '{"message": str(error)}'),
    ('error_json_value', '{"error": str(error)}', '{"error": "invalid_field"}'),
    ('success_multiline', 'json.dumps(result, ensure_ascii=False)', 'json.dumps(result, ensure_ascii=False, indent=2)'),
    ('error_multiline', 'json.dumps({"error": str(error)})', 'json.dumps({"error": str(error)}, indent=2)'),
    ('success_prefix', 'print(json.dumps(result, ensure_ascii=False))', 'print("log"); print(json.dumps(result, ensure_ascii=False))'),
    ('error_suffix', 'print(json.dumps({"error": str(error)}))', 'print(json.dumps({"error": str(error)}) + " trailing")'),
    ('success_blank_line', 'print(json.dumps(result, ensure_ascii=False))', 'print(json.dumps(result, ensure_ascii=False)); print()'),
    ('error_second_json', 'print(json.dumps({"error": str(error)}))', 'print(json.dumps({"error": str(error)})); print("{}")'),
    ('success_stderr_only', 'print(json.dumps(result, ensure_ascii=False))', 'print(json.dumps(result, ensure_ascii=False), file=sys.stderr)'),
    ('error_stderr_only', 'print(json.dumps({"error": str(error)}))', 'print(json.dumps({"error": str(error)}), file=sys.stderr)'),
]:
    add(ident, 'cli', 'report.py', before, after)
# stderr diagnostics are allowed; they are never read as the result.
add('stderr_diagnostic_control', 'positive_control', 'report.py',
    '    rows = json.load(sys.stdin)', '    print("diagnostic", file=sys.stderr)\n    rows = json.load(sys.stdin)')
mutants.insert(0, dict(id='unchanged_candidate', category='positive_control', source=source))

def exercise(item):
    case = fixture / item['id']; (case / 'src').mkdir(parents=True)
    for name, code in item['source'].items(): (case / 'src' / name).write_text(code, encoding='utf-8')
    (case / 'acceptance.py').write_text(oracle, encoding='utf-8')
    row = {k: v for k, v in item.items() if k != 'source'}
    row['changes'] = [{'path': 'src/' + name, 'diff': ''.join(difflib.unified_diff(
                      source[name].splitlines(keepends=True), code.splitlines(keepends=True),
                      fromfile='original/src/' + name, tofile='mutant/src/' + name))}
                      for name, code in item['source'].items() if code != source[name]]
    row.update(artifacts=str(case), checks=[], status='INCOMPLETE')
    argv = [sys.executable, '-I', '-B', '-c', 'import runpy,sys; runpy.run_path(sys.argv[1])', str(case / 'src/normalize.py')]
    imported = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=10)
    if imported.returncode:
        row.update(error='import failure is not a kill', stderr=imported.stderr); return row
    if 'witness' in item:
        argv = [sys.executable, '-B', str(case / 'src/report.py')]
        observed = subprocess.run(argv, env=env, input=json.dumps(item['witness']), capture_output=True, text=True, timeout=10)
        row['witness_result'] = dict(argv=argv, exit=observed.returncode, stdout=observed.stdout, stderr=observed.stderr)
        if observed.returncode != 0:
            row.update(error='targeted bypass did not accept the invalid input'); return row
    positive = item['category'] == 'positive_control'
    for label, script in [('external', external), ('acceptance', case / 'acceptance.py')]:
        argv = [sys.executable, '-I', '-B', str(script), str(case)]
        observed = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60)
        log = case / (label + '.stderr.txt'); log.write_text(observed.stderr, encoding='utf-8')
        killed = observed.returncode == 1 and 'AssertionError' in observed.stderr
        row['checks'].append(dict(oracle=label, argv=argv, exit=observed.returncode, killed=killed,
                                  passed=observed.returncode == 0 if positive else killed,
                                  stdout=observed.stdout, diagnostic=observed.stderr.splitlines()[-1:] , stderr=str(log)))
    row['status'] = 'PASS' if all(c['passed'] for c in row['checks']) else 'NO_GO'
    return row

with ThreadPoolExecutor(max_workers=4) as pool: rows = list(pool.map(exercise, mutants))
report = dict(status='PASS' if all(r['status'] == 'PASS' for r in rows) else 'NO_GO', command=sys.argv,
              candidate=str(a.candidate.resolve()), oracle_revision=a.oracle_revision, artifacts=str(fixture),
              real_model_turns=0, matrix_cells=sum(r['category'] == 'invalid_field_position' for r in rows),
              positive_controls=sum(r['category'] == 'positive_control' for r in rows),
              mutant_count=sum(r['category'] != 'positive_control' for r in rows), cases=rows)
with a.summary.open('x', encoding='utf-8') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({k: report[k] for k in ('status', 'matrix_cells', 'positive_controls', 'mutant_count')}, ensure_ascii=False))
print(json.dumps({'not_passed': [r['id'] for r in rows if r['status'] != 'PASS']}, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
